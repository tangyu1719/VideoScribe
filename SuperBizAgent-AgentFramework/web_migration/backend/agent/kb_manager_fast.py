#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速知识库管理模块 - BGE-Large + 批量处理 + 详细日志

优化点：
1. 使用BGE-Large模型（1024维度）
2. 批量生成嵌入（比逐个生成快10倍）
3. 详细日志埋点，方便跟踪
4. 多线程处理
5. 支持MD、TXT、PDF、DOCX格式
"""

import os
import json
import hashlib
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入文本分割策略
from text_splitter_strategies import TextSplitterFactory, TextSplitterStrategy

# 导入RAG工具和元数据
from rag_tools import DocumentMetadata, MetadataManager, get_metadata_manager

# 配置详细日志
# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'kb_import.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局单例
_kb_instance = None

def get_fast_knowledge_base():
    """获取快速知识库实例"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = FastKnowledgeBaseManager()
    return _kb_instance


class DocumentChunk:
    """文档分块 - 支持元数据"""
    def __init__(self, content: str, source_file: str, chunk_id: int,
                 start_pos: int = 0, end_pos: int = 0,
                 metadata: Optional[DocumentMetadata] = None):
        self.content = content
        self.source_file = source_file
        self.chunk_id = chunk_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.embedding = None
        self.created_at = datetime.now().isoformat()
        self.metadata = metadata or DocumentMetadata(domain="", module="", doc_type="")

    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'source_file': self.source_file,
            'chunk_id': self.chunk_id,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'embedding': self.embedding.tolist() if self.embedding is not None else None,
            'created_at': self.created_at,
            'metadata': self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DocumentChunk':
        chunk = cls(
            content=data['content'],
            source_file=data['source_file'],
            chunk_id=data['chunk_id'],
            start_pos=data.get('start_pos', 0),
            end_pos=data.get('end_pos', 0),
            metadata=DocumentMetadata.from_dict(data.get('metadata', {}))
        )
        if data.get('embedding'):
            chunk.embedding = np.array(data['embedding'])
        chunk.created_at = data.get('created_at', datetime.now().isoformat())
        return chunk


class FastKnowledgeBaseManager:
    """
    快速知识库管理器
    - BGE-Large模型（1024维）
    - 批量处理
    - 详细日志
    """

    SUPPORTED_EXTENSIONS = ['.txt', '.md', '.markdown', '.docx', '.pdf']

    def __init__(self, base_dir: str = None, text_splitter_strategy: str = 'sentence_boundary'):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.kb_dir = os.path.join(self.base_dir, "knowledge_base")
        self.index_file = os.path.join(self.kb_dir, "vector_index_fast.json")
        self.cache_file = os.path.join(self.kb_dir, "file_cache_fast.json")
        self.chunks: List[DocumentChunk] = []
        self.embedding_model = None
        self.embedding_dim = 1024  # BGE-Large维度
        self._initialized = False
        self._model_loaded = False
        self._file_cache = {}
        self._lock = threading.Lock()
        
        # 文本分割策略
        self._text_splitter_strategy_name = text_splitter_strategy
        self._text_splitter: Optional[TextSplitterStrategy] = None

        # 创建目录
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        self._initialize()

    def _initialize(self):
        """初始化"""
        if self._initialized:
            return

        logger.info("=" * 70)
        logger.info("【初始化】快速知识库管理器启动")
        logger.info("=" * 70)

        start_time = time.time()
        self._load_embedding_model()
        load_time = time.time() - start_time
        logger.info(f"【初始化】模型加载耗时: {load_time:.2f}秒")

        # 初始化文本分割策略
        self._init_text_splitter()

        self._load_index()
        self._load_cache()

        self._initialized = True

        logger.info("=" * 70)
        logger.info("【初始化完成】")
        logger.info(f"  - 嵌入维度: {self.embedding_dim}")
        logger.info(f"  - 文档块数: {len(self.chunks)}")
        logger.info(f"  - 模型状态: {'已加载' if self._model_loaded else '未加载'}")
        logger.info(f"  - 分割策略: {self._text_splitter_strategy_name}")
        logger.info("=" * 70)

    def _init_text_splitter(self):
        """初始化文本分割策略"""
        try:
            # 对于动态语义分割策略，需要传入embedding模型
            if self._text_splitter_strategy_name == 'dynamic_semantic':
                self._text_splitter = TextSplitterFactory.get_strategy(
                    self._text_splitter_strategy_name,
                    embedding_model=self.embedding_model if self._model_loaded else None,
                    chunk_size=500,
                    overlap=50
                )
            else:
                self._text_splitter = TextSplitterFactory.get_strategy(
                    self._text_splitter_strategy_name,
                    chunk_size=500,
                    overlap=50
                )
            logger.info(f"【分割策略】使用策略: {self._text_splitter.name}")
        except Exception as e:
            logger.error(f"【分割策略】初始化失败: {e}，使用默认策略")
            self._text_splitter = TextSplitterFactory.get_strategy('sentence_boundary')

    def set_text_splitter_strategy(self, strategy_name: str):
        """切换文本分割策略"""
        logger.info(f"【分割策略】切换策略: {strategy_name}")
        self._text_splitter_strategy_name = strategy_name
        self._init_text_splitter()

    def get_available_strategies(self) -> Dict[str, str]:
        """获取可用的分割策略列表"""
        return TextSplitterFactory.list_strategies()

    def _load_embedding_model(self):
        """加载BGE-Large模型 - 优先使用本地缓存"""
        try:
            from sentence_transformers import SentenceTransformer
            import os

            # 设置本地缓存目录（持久化）
            cache_dir = os.path.join(self.kb_dir, "models")
            os.environ['TRANSFORMERS_CACHE'] = cache_dir
            os.environ['HF_HOME'] = cache_dir
            
            logger.info(f"【模型加载】本地缓存目录: {cache_dir}")

            # 检查本地模型是否存在
            local_model_path = os.path.join(cache_dir, "models--BAAI--bge-large-zh-v1.5")
            
            if os.path.exists(local_model_path):
                logger.info(f"【模型加载】发现本地模型缓存: {local_model_path}")
                logger.info(f"【模型加载】使用离线模式加载...")
                # 使用模型名称，但transformers会从本地缓存加载
                model_name = "BAAI/bge-large-zh-v1.5"
                use_offline = True
            else:
                # 设置镜像源加速下载
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                logger.info("【模型加载】使用镜像源: https://hf-mirror.com")
                model_name = "BAAI/bge-large-zh-v1.5"
                logger.info(f"【模型加载】本地模型不存在，将下载: {model_name}")
                use_offline = False

            os.makedirs(cache_dir, exist_ok=True)

            logger.info(f"【模型加载】正在加载模型: {model_name}")
            start_time = time.time()
            
            if use_offline:
                # 离线模式 - 使用local_files_only
                self.embedding_model = SentenceTransformer(
                    model_name,
                    cache_folder=cache_dir,
                    device='cpu',
                    local_files_only=True
                )
            else:
                # 在线模式 - 允许下载
                self.embedding_model = SentenceTransformer(
                    model_name,
                    cache_folder=cache_dir,
                    device='cpu'
                )
            
            load_time = time.time() - start_time

            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self._model_loaded = True

            logger.info(f"【模型加载】✓ 成功，维度: {self.embedding_dim}, 耗时: {load_time:.2f}秒")

        except Exception as e:
            logger.error(f"【模型加载】✗ 失败: {e}")
            logger.info("【模型加载】尝试使用本地缓存或备用模型...")
            self._load_fallback_model()

    def _load_fallback_model(self):
        """加载备用模型（MiniLM）"""
        try:
            from sentence_transformers import SentenceTransformer

            model_name = "paraphrase-multilingual-MiniLM-L12-v2"
            cache_dir = os.path.join(self.kb_dir, "models")

            logger.info(f"【备用模型】正在加载: {model_name}")

            start_time = time.time()
            self.embedding_model = SentenceTransformer(
                model_name,
                cache_folder=cache_dir,
                device='cpu'
            )
            load_time = time.time() - start_time

            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self._model_loaded = True

            logger.info(f"【备用模型】✓ 成功，维度: {self.embedding_dim}, 耗时: {load_time:.2f}秒")
            logger.warning(f"【警告】使用备用模型 {model_name}，维度为 {self.embedding_dim} 而非 1024")

        except Exception as e:
            logger.error(f"【备用模型】✗ 也失败了: {e}")
            self._model_loaded = False

    def _load_index(self):
        """加载索引"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chunks = [DocumentChunk.from_dict(c) for c in data.get('chunks', [])]
                logger.info(f"【索引加载】成功加载 {len(self.chunks)} 个文档块")
            except Exception as e:
                logger.error(f"【索引加载】失败: {e}")
                self.chunks = []

    def _load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._file_cache = json.load(f)
                logger.info(f"【缓存加载】成功加载 {len(self._file_cache)} 个文件记录")
            except Exception as e:
                logger.error(f"【缓存加载】失败: {e}")
                self._file_cache = {}

    def _save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._file_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"【缓存保存】失败: {e}")

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"【文件哈希】计算失败: {e}")
            return ""

    def _is_file_changed(self, file_path: str) -> bool:
        """检查文件是否更改"""
        current_hash = self._get_file_hash(file_path)
        cached_hash = self._file_cache.get(file_path, "")
        return current_hash != cached_hash

    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Tuple[str, int, int]]:
        """分割文本 - 使用策略模式"""
        if self._text_splitter is None:
            # 如果策略未初始化，使用默认的句子边界分割
            logger.warning("【文本分割】分割策略未初始化，使用默认策略")
            self._text_splitter = TextSplitterFactory.get_strategy('sentence_boundary')
        
        # 使用策略进行分割
        return self._text_splitter.split(text, chunk_size=chunk_size, overlap=overlap)

    def _generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量生成嵌入 - 核心优化
        比逐个生成快10倍以上
        """
        if not self._model_loaded or not texts:
            return [None] * len(texts)

        try:
            start_time = time.time()

            # 批量编码
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            elapsed = time.time() - start_time
            logger.info(f"【嵌入生成】批量生成 {len(texts)} 个嵌入，耗时: {elapsed:.2f}秒，平均: {elapsed/len(texts):.3f}秒/个")

            return [emb for emb in embeddings]

        except Exception as e:
            logger.error(f"【嵌入生成】批量生成失败: {e}")
            return [None] * len(texts)

    def add_document(self, file_path: str, progress_callback=None, 
                     metadata: Optional[DocumentMetadata] = None) -> Tuple[bool, str]:
        """
        添加文档 - 带详细日志和元数据支持
        
        Args:
            file_path: 文件路径
            progress_callback: 进度回调函数
            metadata: 文档元数据（可选，会自动提取）
        """
        file_name = os.path.basename(file_path)
        logger.info(f"\n{'='*70}")
        logger.info(f"【导入开始】文件: {file_name}")
        logger.info(f"{'='*70}")

        total_start_time = time.time()

        try:
            # 检查文件
            if not os.path.exists(file_path):
                logger.error(f"【导入失败】文件不存在: {file_path}")
                return False, f"文件不存在: {file_path}"

            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                logger.error(f"【导入失败】不支持的格式: {file_ext}")
                return False, f"不支持的格式: {file_ext}"

            # 检查缓存
            if not self._is_file_changed(file_path):
                logger.info(f"【导入跳过】文件未更改: {file_name}")
                return True, "文件已是最新，跳过处理"

            # 读取文件
            logger.info(f"【读取文件】{file_name}")
            read_start = time.time()
            content = self._read_file(file_path)
            read_time = time.time() - read_start

            if not content or not content.strip():
                logger.error(f"【导入失败】文件内容为空: {file_name}")
                return False, "文件内容为空"

            content_size = len(content)
            logger.info(f"【读取完成】大小: {content_size} 字符，耗时: {read_time:.2f}秒")

            # 自动提取元数据（如果未提供）
            if metadata is None:
                logger.info(f"【元数据提取】自动提取元数据...")
                metadata_manager = get_metadata_manager()
                metadata = metadata_manager.auto_extract_metadata(content, file_name)
                logger.info(f"【元数据】domain={metadata.domain}, module={metadata.module}, doc_type={metadata.doc_type}")

            # 验证元数据
            metadata_manager = get_metadata_manager()
            is_valid, msg = metadata_manager.validate_metadata(metadata)
            if not is_valid:
                logger.error(f"【导入失败】元数据验证失败: {msg}")
                return False, f"元数据验证失败: {msg}"

            # 分割文本
            logger.info(f"【文本分割】开始分割...")
            split_start = time.time()
            text_chunks = self._split_text(content)
            split_time = time.time() - split_start
            logger.info(f"【分割完成】共 {len(text_chunks)} 个块，耗时: {split_time:.2f}秒")

            if progress_callback:
                progress_callback(0, len(text_chunks))

            # 批量生成嵌入
            logger.info(f"【嵌入生成】开始批量生成嵌入...")
            embed_start = time.time()
            chunk_texts = [chunk[0] for chunk in text_chunks]
            embeddings = self._generate_embeddings_batch(chunk_texts)
            embed_time = time.time() - embed_start

            # 创建文档块（带元数据）
            logger.info(f"【创建块】创建文档块对象...")
            new_chunks = []
            for i, ((chunk_text, start_pos, end_pos), embedding) in enumerate(zip(text_chunks, embeddings)):
                chunk = DocumentChunk(
                    content=chunk_text,
                    source_file=file_name,
                    chunk_id=i,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    metadata=metadata
                )
                chunk.embedding = embedding
                new_chunks.append(chunk)

                if progress_callback:
                    progress_callback(i + 1, len(text_chunks))

            # 添加到知识库
            logger.info(f"【更新索引】添加到知识库...")
            with self._lock:
                self.chunks = [c for c in self.chunks if c.source_file != file_name]
                self.chunks.extend(new_chunks)

            # 更新元数据索引
            logger.info(f"【更新元数据索引】...")
            doc_id = hashlib.md5(file_path.encode()).hexdigest()
            self._update_metadata_index(doc_id, metadata)

            # 保存
            logger.info(f"【保存数据】保存索引和缓存...")
            save_start = time.time()
            self._save_index()
            self._file_cache[file_path] = self._get_file_hash(file_path)
            self._save_cache()
            save_time = time.time() - save_start

            total_time = time.time() - total_start_time

            logger.info(f"{'='*70}")
            logger.info(f"【导入完成】✓ {file_name}")
            logger.info(f"  - 文档块数: {len(text_chunks)}")
            logger.info(f"  - 元数据: {metadata.domain}/{metadata.module}/{metadata.doc_type}")
            logger.info(f"  - 读取耗时: {read_time:.2f}秒")
            logger.info(f"  - 分割耗时: {split_time:.2f}秒")
            logger.info(f"  - 嵌入耗时: {embed_time:.2f}秒")
            logger.info(f"  - 保存耗时: {save_time:.2f}秒")
            logger.info(f"  - 总耗时: {total_time:.2f}秒")
            logger.info(f"{'='*70}\n")

            return True, f"成功添加 {len(text_chunks)} 个向量块，总耗时 {total_time:.2f}秒"

        except Exception as e:
            total_time = time.time() - total_start_time
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"【导入失败】✗ {file_name}: {e}")
            logger.error(f"【错误详情】\n{error_trace}")
            logger.error(f"  - 总耗时: {total_time:.2f}秒")
            logger.error(f"{'='*70}\n")
            return False, f"添加失败: {str(e)}"

    def _read_file(self, file_path: str) -> str:
        """读取文件 - 支持多种编码"""
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in ['.txt', '.md', '.markdown']:
            # 尝试多种编码读取
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp936']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        logger.info(f"【编码检测】使用 {encoding} 成功读取文件")
                        return content
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"【编码检测】{encoding} 读取失败: {e}")
                    continue
            logger.error(f"【读取失败】无法识别文件编码: {file_path}")
            return ""

        elif file_ext == '.docx':
            try:
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except ImportError:
                logger.error("未安装python-docx")
                return ""

        elif file_ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    return '\n'.join([page.extract_text() for page in reader.pages])
            except ImportError:
                logger.error("未安装PyPDF2")
                return ""

        return ""

    def _save_index(self):
        """保存索引"""
        try:
            with self._lock:
                data = {
                    'chunks': [c.to_dict() for c in self.chunks],
                    'updated_at': datetime.now().isoformat()
                }
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")

    def search(self, query: str, top_k: int = 5, 
               doc_ids: Optional[List[str]] = None,
               metadata_filter: Optional[DocumentMetadata] = None) -> List[Dict]:
        """
        搜索 - 支持元数据过滤
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_ids: 候选文档ID列表（元数据初筛后的结果）
            metadata_filter: 元数据过滤条件
        """
        if not self.chunks:
            logger.warning("【搜索】知识库为空，无法搜索")
            return []
        
        # 检查模型是否已加载
        if not self._model_loaded:
            logger.warning("【搜索】嵌入模型未加载，尝试加载...")
            self._load_embedding_model()
            
        if not self._model_loaded:
            logger.error("【搜索】模型加载失败，无法生成查询嵌入")
            return []

        try:
            logger.info(f"【搜索】开始生成查询嵌入: {query[:50]}...")
            query_embedding = self._generate_embeddings_batch([query])[0]

            if query_embedding is None:
                logger.warning("【搜索】查询嵌入生成失败")
                return []

            # 过滤候选文档
            candidate_chunks = self.chunks
            if doc_ids:
                candidate_chunks = [c for c in self.chunks 
                                   if hashlib.md5(c.source_file.encode()).hexdigest() in doc_ids]
                logger.info(f"【搜索】元数据过滤后候选: {len(candidate_chunks)} 个块")

            similarities = []
            for chunk in candidate_chunks:
                if chunk.embedding is not None:
                    # 元数据过滤
                    if metadata_filter and not self._match_metadata(chunk.metadata, metadata_filter):
                        continue
                    
                    sim = self._cosine_similarity(query_embedding, chunk.embedding)
                    similarities.append((chunk, sim))

            similarities.sort(key=lambda x: x[1], reverse=True)

            results = []
            for chunk, score in similarities[:top_k]:
                results.append({
                    'content': chunk.content,
                    'source_file': chunk.source_file,
                    'chunk_id': chunk.chunk_id,
                    'score': float(score),
                    'metadata': chunk.metadata.to_dict(),
                    'doc_id': hashlib.md5(chunk.source_file.encode()).hexdigest()
                })

            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _match_metadata(self, chunk_metadata: DocumentMetadata, 
                        filter_metadata: DocumentMetadata) -> bool:
        """检查元数据是否匹配过滤条件"""
        if filter_metadata.domain and chunk_metadata.domain != filter_metadata.domain:
            return False
        if filter_metadata.module and chunk_metadata.module != filter_metadata.module:
            return False
        if filter_metadata.doc_type and chunk_metadata.doc_type != filter_metadata.doc_type:
            return False
        if filter_metadata.keyword1 and filter_metadata.keyword1 not in [chunk_metadata.keyword1, chunk_metadata.keyword2]:
            return False
        if filter_metadata.keyword2 and filter_metadata.keyword2 not in [chunk_metadata.keyword1, chunk_metadata.keyword2]:
            return False
        return True

    def _update_metadata_index(self, doc_id: str, metadata: DocumentMetadata):
        """更新元数据索引（供RAGTool使用）"""
        # 这里可以添加额外的索引逻辑
        logger.info(f"【元数据索引】更新 doc_id={doc_id}, metadata={metadata.to_dict()}")

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_stats(self) -> Dict:
        """统计信息"""
        return {
            'total_chunks': len(self.chunks),
            'total_files': len(set(c.source_file for c in self.chunks)),
            'embedding_dim': self.embedding_dim,
            'model_loaded': self._model_loaded
        }

    def is_ready(self) -> bool:
        """是否就绪"""
        return self._initialized and self._model_loaded


# 保持向后兼容
KnowledgeBaseManager = FastKnowledgeBaseManager
get_knowledge_base = get_fast_knowledge_base
