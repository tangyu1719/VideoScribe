#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型 - MySQL表结构定义
- 文档表 (documents)
- 标签表 (tags)
- 向量表 (vectors)
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
import json


@dataclass
class Tag:
    """标签模型 - 统一标签定义"""
    tag_id: int                      # 标签ID (主键)
    domain: str                      # 领域
    module: str                      # 模块
    doc_type: str                    # 文档类型
    keyword1: str = ""               # 关键词1
    keyword2: str = ""               # 关键词2
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'tag_id': self.tag_id,
            'domain': self.domain,
            'module': self.module,
            'doc_type': self.doc_type,
            'keyword1': self.keyword1,
            'keyword2': self.keyword2,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Tag':
        return cls(
            tag_id=data.get('tag_id', 0),
            domain=data.get('domain', ''),
            module=data.get('module', ''),
            doc_type=data.get('doc_type', ''),
            keyword1=data.get('keyword1', ''),
            keyword2=data.get('keyword2', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __hash__(self):
        return hash(self.tag_id)
    
    def __eq__(self, other):
        if isinstance(other, Tag):
            return self.tag_id == other.tag_id
        return False


@dataclass
class Document:
    """文档模型"""
    doc_id: int                      # 文档ID (主键)
    file_name: str                   # 文件名
    file_path: str                   # 文件路径
    file_hash: str                   # 文件哈希
    tag_id: int                      # 标签ID (外键)
    file_size: int = 0               # 文件大小
    chunk_count: int = 0             # 分块数量
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'doc_id': self.doc_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'tag_id': self.tag_id,
            'file_size': self.file_size,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Document':
        return cls(
            doc_id=data.get('doc_id', 0),
            file_name=data.get('file_name', ''),
            file_path=data.get('file_path', ''),
            file_hash=data.get('file_hash', ''),
            tag_id=data.get('tag_id', 0),
            file_size=data.get('file_size', 0),
            chunk_count=data.get('chunk_count', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


@dataclass
class VectorChunk:
    """向量块模型 - 每个向量绑定文档ID和标签ID"""
    vector_id: int                   # 向量ID (主键)
    doc_id: int                      # 文档ID (外键)
    tag_id: int                      # 标签ID (外键)
    chunk_index: int                 # 块索引
    content: str                     # 文本内容
    embedding: Optional[List[float]] = None  # 向量嵌入
    start_pos: int = 0               # 起始位置
    end_pos: int = 0                 # 结束位置
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'vector_id': self.vector_id,
            'doc_id': self.doc_id,
            'tag_id': self.tag_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'embedding': self.embedding,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VectorChunk':
        return cls(
            vector_id=data.get('vector_id', 0),
            doc_id=data.get('doc_id', 0),
            tag_id=data.get('tag_id', 0),
            chunk_index=data.get('chunk_index', 0),
            content=data.get('content', ''),
            embedding=data.get('embedding'),
            start_pos=data.get('start_pos', 0),
            end_pos=data.get('end_pos', 0),
            created_at=data.get('created_at')
        )


# SQL表结构定义
CREATE_TABLES_SQL = """
-- 标签表 - 统一标签定义
CREATE TABLE IF NOT EXISTS tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(50) NOT NULL COMMENT '领域',
    module VARCHAR(50) NOT NULL COMMENT '模块',
    doc_type VARCHAR(50) NOT NULL COMMENT '文档类型',
    keyword1 VARCHAR(100) DEFAULT '' COMMENT '关键词1',
    keyword2 VARCHAR(100) DEFAULT '' COMMENT '关键词2',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tag_combination (domain, module, doc_type, keyword1, keyword2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签表';

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    doc_id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_hash VARCHAR(64) NOT NULL COMMENT '文件哈希',
    tag_id INT NOT NULL COMMENT '标签ID',
    file_size INT DEFAULT 0 COMMENT '文件大小(字节)',
    chunk_count INT DEFAULT 0 COMMENT '分块数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id),
    UNIQUE KEY uk_file_hash (file_hash),
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档表';

-- 向量表 - 每个向量绑定文档ID和标签ID
CREATE TABLE IF NOT EXISTS vectors (
    vector_id INT AUTO_INCREMENT PRIMARY KEY,
    doc_id INT NOT NULL COMMENT '文档ID',
    tag_id INT NOT NULL COMMENT '标签ID',
    chunk_index INT NOT NULL COMMENT '块索引',
    content TEXT NOT NULL COMMENT '文本内容',
    embedding JSON COMMENT '向量嵌入(JSON数组)',
    start_pos INT DEFAULT 0 COMMENT '起始位置',
    end_pos INT DEFAULT 0 COMMENT '结束位置',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id),
    INDEX idx_doc_id (doc_id),
    INDEX idx_tag_id (tag_id),
    INDEX idx_tag_doc (tag_id, doc_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='向量表';
"""
