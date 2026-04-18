#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器 - MySQL操作封装
- 标签管理
- 文档管理
- 向量管理
- 初筛查询
"""

import logging
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager
import json
import os

from db_models import Tag, Document, VectorChunk, CREATE_TABLES_SQL

logger = logging.getLogger(__name__)


def _load_db_config():
    """加载数据库配置文件"""
    config_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'db_config.json'),
        os.path.join(os.path.dirname(__file__), '..', 'config', 'db_config.json'),
        os.path.join(os.getcwd(), 'config', 'db_config.json'),
    ]
    
    default_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'rag_kb'
    }

    # 优先复用项目统一 db.py 配置，避免 root 空密码导致 1045
    try:
        import db as project_db
        merged = default_config.copy()
        merged.update({
            'host': project_db.DB_CONFIG.get('host', merged['host']),
            'port': project_db.DB_CONFIG.get('port', merged['port']),
            'user': project_db.DB_CONFIG.get('user', merged['user']),
            'password': project_db.DB_CONFIG.get('password', merged['password']),
        })
        # db_manager 默认维护 rag_kb；若配置文件显式指定则后续覆盖
        default_config = merged
    except Exception:
        pass
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    merged = default_config.copy()
                    # 避免把空字符串密码覆盖掉已有可用配置
                    safe_config = dict(config or {})
                    if safe_config.get("password", None) == "":
                        safe_config.pop("password", None)
                    merged.update(safe_config)
                    return merged
            except Exception as e:
                logger.warning(f"加载数据库配置失败: {e}")
    
    return default_config


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, host=None, port=None, user=None, 
                 password=None, database=None):
        # 加载配置文件
        config = _load_db_config()
        
        self.host = host or config.get('host', 'localhost')
        self.port = port or config.get('port', 3306)
        self.user = user or config.get('user', 'root')
        self.password = password or config.get('password', '')
        self.database = database or config.get('database', 'rag_kb')
        self._connection = None
        
        # 延迟导入pymysql
        try:
            import pymysql
            self.pymysql = pymysql
        except ImportError:
            logger.error("未安装pymysql，请运行: pip install pymysql")
            raise
    
    def _get_connection(self):
        """获取数据库连接"""
        if self._connection is None or not self._connection.open:
            self._connection = self.pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=self.pymysql.cursors.DictCursor
            )
        return self._connection
    
    @contextmanager
    def _cursor(self):
        """上下文管理器获取游标"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def init_tables(self):
        """初始化数据库表"""
        try:
            with self._cursor() as cursor:
                # 执行建表SQL
                for sql in CREATE_TABLES_SQL.split(';'):
                    sql = sql.strip()
                    if sql:
                        cursor.execute(sql)
            logger.info("数据库表初始化成功")
        except Exception as e:
            logger.error(f"数据库表初始化失败: {e}")
            raise
    
    # ==================== 标签管理 ====================
    
    def get_or_create_tag(self, domain: str, module: str, doc_type: str,
                          keyword1: str = "", keyword2: str = "") -> Tag:
        """
        获取或创建标签
        如果标签组合已存在，返回现有标签；否则创建新标签
        """
        try:
            with self._cursor() as cursor:
                # 先查询是否存在
                sql = """
                    SELECT * FROM tags 
                    WHERE domain=%s AND module=%s AND doc_type=%s 
                    AND keyword1=%s AND keyword2=%s
                """
                cursor.execute(sql, (domain, module, doc_type, keyword1, keyword2))
                result = cursor.fetchone()
                
                if result:
                    return Tag.from_dict(result)
                
                # 创建新标签
                sql = """
                    INSERT INTO tags (domain, module, doc_type, keyword1, keyword2)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (domain, module, doc_type, keyword1, keyword2))
                tag_id = cursor.lastrowid
                
                return Tag(
                    tag_id=tag_id,
                    domain=domain,
                    module=module,
                    doc_type=doc_type,
                    keyword1=keyword1,
                    keyword2=keyword2
                )
        except Exception as e:
            logger.error(f"获取或创建标签失败: {e}")
            raise
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM tags WHERE tag_id=%s"
                cursor.execute(sql, (tag_id,))
                result = cursor.fetchone()
                return Tag.from_dict(result) if result else None
        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            return None
    
    def get_all_tags(self) -> List[Tag]:
        """获取所有标签"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM tags ORDER BY tag_id"
                cursor.execute(sql)
                results = cursor.fetchall()
                return [Tag.from_dict(r) for r in results]
        except Exception as e:
            logger.error(f"获取所有标签失败: {e}")
            return []
    
    # ==================== 文档管理 ====================
    
    def add_document(self, file_name: str, file_path: str, file_hash: str,
                     tag_id: int, file_size: int = 0, 
                     chunk_count: int = 0) -> Document:
        """添加文档"""
        try:
            with self._cursor() as cursor:
                # 检查是否已存在
                sql = "SELECT * FROM documents WHERE file_hash=%s"
                cursor.execute(sql, (file_hash,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有文档
                    sql = """
                        UPDATE documents 
                        SET file_name=%s, file_path=%s, tag_id=%s, 
                            file_size=%s, chunk_count=%s
                        WHERE file_hash=%s
                    """
                    cursor.execute(sql, (file_name, file_path, tag_id, 
                                        file_size, chunk_count, file_hash))
                    return Document.from_dict(existing)
                
                # 插入新文档
                sql = """
                    INSERT INTO documents (file_name, file_path, file_hash, 
                                          tag_id, file_size, chunk_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (file_name, file_path, file_hash, 
                                    tag_id, file_size, chunk_count))
                doc_id = cursor.lastrowid
                
                return Document(
                    doc_id=doc_id,
                    file_name=file_name,
                    file_path=file_path,
                    file_hash=file_hash,
                    tag_id=tag_id,
                    file_size=file_size,
                    chunk_count=chunk_count
                )
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    def get_document_by_hash(self, file_hash: str) -> Optional[Document]:
        """根据哈希获取文档"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM documents WHERE file_hash=%s"
                cursor.execute(sql, (file_hash,))
                result = cursor.fetchone()
                return Document.from_dict(result) if result else None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def get_document_by_id(self, doc_id: int) -> Optional[Document]:
        """根据ID获取文档"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM documents WHERE doc_id=%s"
                cursor.execute(sql, (doc_id,))
                result = cursor.fetchone()
                return Document.from_dict(result) if result else None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def get_all_documents(self) -> List[Document]:
        """获取所有文档"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM documents ORDER BY created_at DESC"
                cursor.execute(sql)
                results = cursor.fetchall()
                return [Document.from_dict(r) for r in results]
        except Exception as e:
            logger.error(f"获取所有文档失败: {e}")
            return []
    
    def delete_document(self, doc_id: int):
        """删除文档（级联删除向量）"""
        try:
            with self._cursor() as cursor:
                sql = "DELETE FROM documents WHERE doc_id=%s"
                cursor.execute(sql, (doc_id,))
                logger.info(f"删除文档: doc_id={doc_id}")
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            raise
    
    # ==================== 向量管理 ====================
    
    def add_vectors(self, vectors: List[VectorChunk]):
        """批量添加向量"""
        try:
            with self._cursor() as cursor:
                sql = """
                    INSERT INTO vectors (doc_id, tag_id, chunk_index, content, 
                                        embedding, start_pos, end_pos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                data = []
                for v in vectors:
                    embedding_json = json.dumps(v.embedding) if v.embedding else None
                    data.append((v.doc_id, v.tag_id, v.chunk_index, v.content,
                               embedding_json, v.start_pos, v.end_pos))
                
                cursor.executemany(sql, data)
                logger.info(f"批量添加向量: {len(vectors)}个")
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            raise
    
    def delete_vectors_by_doc(self, doc_id: int):
        """删除文档的所有向量"""
        try:
            with self._cursor() as cursor:
                sql = "DELETE FROM vectors WHERE doc_id=%s"
                cursor.execute(sql, (doc_id,))
                logger.info(f"删除文档向量: doc_id={doc_id}")
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise
    
    # ==================== 初筛查询 ====================
    
    def filter_vectors_by_metadata(self, domain: Optional[str] = None,
                                   module: Optional[str] = None,
                                   doc_type: Optional[str] = None,
                                   keyword1: Optional[str] = None,
                                   keyword2: Optional[str] = None) -> List[VectorChunk]:
        """
        根据元数据初筛向量
        
        效率分析:
        - 使用数据库索引，查询复杂度O(log n)
        - 只返回符合条件的向量，减少后续语义计算量
        """
        try:
            with self._cursor() as cursor:
                # 构建查询条件
                conditions = []
                params = []
                
                if domain:
                    conditions.append("t.domain=%s")
                    params.append(domain)
                if module:
                    conditions.append("t.module=%s")
                    params.append(module)
                if doc_type:
                    conditions.append("t.doc_type=%s")
                    params.append(doc_type)
                if keyword1:
                    conditions.append("(t.keyword1=%s OR t.keyword2=%s)")
                    params.extend([keyword1, keyword1])
                if keyword2:
                    conditions.append("(t.keyword1=%s OR t.keyword2=%s)")
                    params.extend([keyword2, keyword2])
                
                # 构建SQL
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
                else:
                    where_clause = ""
                
                sql = f"""
                    SELECT v.*, t.domain, t.module, t.doc_type, t.keyword1, t.keyword2
                    FROM vectors v
                    JOIN tags t ON v.tag_id = t.tag_id
                    {where_clause}
                    ORDER BY v.doc_id, v.chunk_index
                """
                
                cursor.execute(sql, tuple(params))
                results = cursor.fetchall()
                
                vectors = []
                for r in results:
                    v = VectorChunk.from_dict(r)
                    # 解析embedding JSON
                    if r.get('embedding'):
                        v.embedding = json.loads(r['embedding'])
                    vectors.append(v)
                
                logger.info(f"元数据初筛: 条件={conditions}, 返回{len(vectors)}个向量")
                return vectors
                
        except Exception as e:
            logger.error(f"元数据初筛失败: {e}")
            return []
    
    def get_vectors_by_doc_id(self, doc_id: int) -> List[VectorChunk]:
        """获取文档的所有向量"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM vectors WHERE doc_id=%s ORDER BY chunk_index"
                cursor.execute(sql, (doc_id,))
                results = cursor.fetchall()
                
                vectors = []
                for r in results:
                    v = VectorChunk.from_dict(r)
                    if r.get('embedding'):
                        v.embedding = json.loads(r['embedding'])
                    vectors.append(v)
                return vectors
        except Exception as e:
            logger.error(f"获取文档向量失败: {e}")
            return []
    
    def get_all_vectors(self) -> List[VectorChunk]:
        """获取所有向量"""
        try:
            with self._cursor() as cursor:
                sql = "SELECT * FROM vectors ORDER BY vector_id"
                cursor.execute(sql)
                results = cursor.fetchall()
                
                vectors = []
                for r in results:
                    v = VectorChunk.from_dict(r)
                    if r.get('embedding'):
                        v.embedding = json.loads(r['embedding'])
                    vectors.append(v)
                return vectors
        except Exception as e:
            logger.error(f"获取所有向量失败: {e}")
            return []


# 全局单例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(host='localhost', port=3306, user='root',
                   password='', database='rag_kb') -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(host, port, user, password, database)
    return _db_manager
