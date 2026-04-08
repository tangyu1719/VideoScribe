#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级文件处理器 - 用于快速添加文件到 RAG 知识库
不加载嵌入模型，只处理文本分块和保存记录
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple


class SimpleChunkProcessor:
    """简单的文本分块处理器（不依赖嵌入模型）"""
    
    def __init__(self):
        self.chunk_size = 500
        self.overlap = 100
    
    def split_text(self, text: str) -> List[Tuple[str, int, int]]:
        """将文本分割成块"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # 尝试在句子边界处分割
            if end < len(text):
                for i in range(end - 1, start, -1):
                    if text[i] in '。！？.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))
            
            start = end - self.overlap if end < len(text) else end
        
        return chunks
    
    def process_file(self, file_path: str) -> Dict:
        """
        处理文件，返回文件信息
        
        Returns:
            {
                'file_name': str,
                'file_size': float,  # KB
                'file_type': str,
                'chunk_count': int,
                'added_at': str
            }
        """
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割文本
        chunks = self.split_text(content)
        
        # 返回文件信息
        return {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path) / 1024,
            'file_type': os.path.splitext(file_path)[1].lower(),
            'chunk_count': len(chunks),
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'vector_bound': False  # 标记为未向量化
        }


def add_file_to_records(file_path: str, records_file: str) -> Tuple[bool, str]:
    """
    快速添加文件到记录（不初始化 RAG）
    
    Args:
        file_path: 文件路径
        records_file: 记录文件路径
    
    Returns:
        (success, message)
    """
    try:
        # 检查文件
        if not os.path.exists(file_path):
            return False, f"文件不存在：{file_path}"
        
        # 检查格式
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ['.txt', '.md']:
            return False, f"不支持的文件格式：{file_ext}"
        
        # 处理文件
        processor = SimpleChunkProcessor()
        file_info = processor.process_file(file_path)
        
        # 加载现有记录
        records = []
        if os.path.exists(records_file):
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        
        # 检查是否已存在
        for record in records:
            if record.get('file_path') == file_path:
                return False, "文件已存在"
        
        # 添加记录
        records.append(file_info)
        
        # 保存记录
        os.makedirs(os.path.dirname(records_file), exist_ok=True)
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        return True, f"成功添加 {file_info['chunk_count']} 个块"
        
    except Exception as e:
        return False, f"处理失败：{str(e)}"


def add_folder_to_records(folder_path: str, records_file: str) -> Tuple[int, int, str]:
    """
    快速添加文件夹到记录
    
    Returns:
        (total_files, added_count, message)
    """
    try:
        # 扫描文件
        files_to_add = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.txt', '.md')):
                    files_to_add.append(os.path.join(root, file))
        
        total_files = len(files_to_add)
        if total_files == 0:
            return 0, 0, "文件夹中没有找到 .txt 或 .md 文件"
        
        # 加载现有记录
        records = []
        if os.path.exists(records_file):
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        
        existing_paths = {r.get('file_path') for r in records}
        
        # 处理文件
        added_count = 0
        processor = SimpleChunkProcessor()
        
        for file_path in files_to_add:
            if file_path in existing_paths:
                continue
            
            try:
                file_info = processor.process_file(file_path)
                records.append(file_info)
                added_count += 1
            except Exception as e:
                print(f"处理文件失败 {file_path}: {e}")
        
        # 保存记录
        os.makedirs(os.path.dirname(records_file), exist_ok=True)
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        return total_files, added_count, f"成功添加 {added_count}/{total_files} 个文件"
        
    except Exception as e:
        return 0, 0, f"处理失败：{str(e)}"


# 测试
if __name__ == "__main__":
    import sys
    
    records_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "knowledge_base",
        "file_records.json"
    )
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        success, msg = add_file_to_records(file_path, records_file)
        print(f"{'✓' if success else '✗'} {msg}")
    else:
        print("用法：python simple_file_processor.py <file_path>")
