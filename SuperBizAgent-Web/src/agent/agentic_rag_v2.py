#!/usr/bin/env python3
"""
Agentic RAG 知识库系统 V2
- Milvus向量数据库
- BGE-Large向量嵌入（使用国内镜像）
- 动态语义分割（头尾完整，片间重合）
- 混合召回：语义相似度 + BM25 + RRF
- 动态TopK选择
- 详细来源信息（文档名+页号）
"""

import os
import re
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入依赖
try:
    from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("pymilvus未安装，将使用本地向量存储")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers未安装")

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank-bm25未安装，BM25功能不可用")

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba未安装，中文分词将使用简单方式")


@dataclass
class DocumentChunk:
    """文档分块"""
    id: str
    content: str
    source_file: str
    page_number: int
    chunk_index: int
    start_pos: int
    end_pos: int
    embedding: Optional[np.ndarray] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'source_file': self.source_file,
            'page_number': self.page_number,
            'chunk_index': self.chunk_index,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'created_at': self.created_at
        }


@dataclass
class SearchResult:
    """搜索结果"""
    chunk: DocumentChunk
    semantic_score: float
    bm25_score: float
    rrf_score: float
    final_score: float


class DynamicSemanticSplitter:
    """动态语义分割器 - 确保头尾完整，片间重合保证连续性"""
    
    def __init__(self, 
                 target_chunk_size: int = 512,
                 min_chunk_size: int = 256,
                 max_chunk_size: int = 1024,
                 overlap_ratio: float = 0.1):
        """
        Args:
            target_chunk_size: 目标块大小（字符数）
            min_chunk_size: 最小块大小
            max_chunk_size: 最大块大小
            overlap_ratio: 重合比例（0.1表示10%重合）
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio
        
        # 句子结束标记
        self.sentence_endings = '。！？.!?\n'
        # 段落标记
        self.paragraph_markers = '\n\n'
    
    def split(self, text: str, source_file: str = "", page_number: int = 0) -> List[DocumentChunk]:
        """
        动态语义分割文本
        
        Returns:
            文档块列表
        """
        if not text.strip():
            return []
        
        chunks = []
        chunk_index = 0
        start_pos = 0
        
        while start_pos < len(text):
            # 计算当前块的理想结束位置
            ideal_end = start_pos + self.target_chunk_size
            
            # 如果已到达文本末尾
            if ideal_end >= len(text):
                chunk_text = text[start_pos:].strip()
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk(
                        chunk_text, source_file, page_number, 
                        chunk_index, start_pos, len(text)
                    )
                    chunks.append(chunk)
                break
            
            # 寻找最佳分割点（在ideal_end附近找句子边界）
            actual_end = self._find_best_split_point(text, ideal_end)
            
            # 确保块大小在合理范围内
            if actual_end - start_pos > self.max_chunk_size:
                actual_end = start_pos + self.max_chunk_size
            elif actual_end - start_pos < self.min_chunk_size:
                actual_end = min(start_pos + self.min_chunk_size, len(text))
            
            chunk_text = text[start_pos:actual_end].strip()
            
            if chunk_text:
                chunk = self._create_chunk(
                    chunk_text, source_file, page_number,
                    chunk_index, start_pos, actual_end
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # 计算下一个起始位置（考虑重合）
            overlap_size = int((actual_end - start_pos) * self.overlap_ratio)
            start_pos = actual_end - overlap_size
        
        return chunks
    
    def _find_best_split_point(self, text: str, ideal_pos: int) -> int:
        """在理想位置附近寻找最佳分割点（句子边界）"""
        # 搜索范围：理想位置前后20%
        search_range = int(self.target_chunk_size * 0.2)
        start_search = max(0, ideal_pos - search_range)
        end_search = min(len(text), ideal_pos + search_range)
        
        # 优先找句子结束标记
        for i in range(ideal_pos, end_search):
            if i < len(text) and text[i] in self.sentence_endings:
                return i + 1
        
        for i in range(ideal_pos - 1, start_search, -1):
            if i >= 0 and text[i] in self.sentence_endings:
                return i + 1
        
        # 其次找段落边界
        paragraph_pos = text.find('\n\n', ideal_pos - 50, ideal_pos + 50)
        if paragraph_pos != -1:
            return paragraph_pos + 2
        
        # 最后找空格
        for i in range(ideal_pos, end_search):
            if i < len(text) and text[i] == ' ':
                return i + 1
        
        # 如果都找不到，返回理想位置
        return ideal_pos
    
    def _create_chunk(self, content: str, source_file: str, page_number: int,
                      chunk_index: int, start_pos: int, end_pos: int) -> DocumentChunk:
        """创建文档块"""
        chunk_id = hashlib.md5(
            f"{source_file}_{page_number}_{chunk_index}_{content[:50]}".encode()
        ).hexdigest()[:16]
        
        return DocumentChunk(
            id=chunk_id,
            content=content,
            source_file=source_file,
            page_number=page_number,
            chunk_index=chunk_index,
            start_pos=start_pos,
            end_pos=end_pos
        )


class BGEEmbeddingModel:
    """BGE-Large向量嵌入模型 - 使用国内镜像"""
    
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        self.model_name = model_name
        self.model = None
        self.dimension = 1024  # BGE-Large维度
        self._load_model()
    
    def _load_model(self):
        """加载模型 - 使用国内镜像源"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers未安装，无法加载BGE模型")
            return
        
        # 设置国内镜像环境变量
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        
        # 尝试多个模型源（优先国内镜像）
        model_sources = [
            ("BAAI/bge-large-zh-v1.5", "BGE-Large中文模型"),
            ("BAAI/bge-small-zh-v1.5", "BGE-Small中文模型"),
            ("shibing624/text2vec-base-chinese", "text2vec中文模型"),
            ("sentence-transformers/all-MiniLM-L6-v2", "MiniLM英文模型"),
        ]
        
        for model_source, model_desc in model_sources:
            try:
                logger.info(f"正在加载模型: {model_desc} ({model_source})")
                # 设置超时和缓存
                self.model = SentenceTransformer(
                    model_source,
                    device='cpu',
                    cache_folder='./model_cache'
                )
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"✓ 模型加载成功: {model_desc}, 维度: {self.dimension}")
                self.model_name = model_source
                return
            except Exception as e:
                logger.warning(f"加载模型 {model_source} 失败: {str(e)[:100]}")
                continue
        
        logger.error("所有模型源都加载失败，将使用随机向量")
        self.model = None
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """编码文本为向量"""
        if self.model is None:
            logger.warning("模型未加载，使用随机向量")
            # 使用随机向量作为fallback
            np.random.seed(42)
            return np.random.randn(len(texts), self.dimension).astype(np.float32)
        
        try:
            # BGE模型需要在文本前添加指令
            if 'bge' in self.model_name.lower():
                instruction = "为这个句子生成表示："
                texts_with_instruction = [f"{instruction}{text}" for text in texts]
            else:
                texts_with_instruction = texts
            
            embeddings = self.model.encode(
                texts_with_instruction,
                normalize_embeddings=True,  # 归一化
                show_progress_bar=False,
                batch_size=32
            )
            return embeddings
        except Exception as e:
            logger.error(f"编码失败: {e}")
            np.random.seed(42)
            return np.random.randn(len(texts), self.dimension).astype(np.float32)


class LocalVectorStore:
    """本地向量存储（当Milvus不可用时使用）"""
    
    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.chunks: List[DocumentChunk] = []
        self.embeddings: np.ndarray = np.array([])
    
    def insert(self, chunks: List[DocumentChunk]):
        """插入文档块"""
        for chunk in chunks:
            if chunk.embedding is not None:
                self.chunks.append(chunk)
                if self.embeddings.size == 0:
                    self.embeddings = chunk.embedding.reshape(1, -1)
                else:
                    self.embeddings = np.vstack([self.embeddings, chunk.embedding])
        
        logger.info(f"本地存储: 已插入 {len(chunks)} 个文档块，总计 {len(self.chunks)} 个")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 60) -> List[Dict]:
        """向量搜索 - 使用余弦相似度"""
        if len(self.chunks) == 0:
            return []
        
        # 计算余弦相似度
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        embeddings_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-8)
        
        similarities = np.dot(embeddings_norm, query_norm)
        
        # 获取top_k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            results.append({
                'id': chunk.id,
                'content': chunk.content,
                'source_file': chunk.source_file,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index,
                'distance': float(similarities[idx])
            })
        
        return results


class MilvusVectorStore:
    """Milvus向量存储"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: str = "19530",
                 collection_name: str = "agentic_rag"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        self.dimension = 1024
        self._connect()
    
    def _connect(self):
        """连接Milvus"""
        if not MILVUS_AVAILABLE:
            logger.warning("pymilvus未安装，使用本地存储")
            return
        
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"已连接到Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
    
    def create_collection(self, dimension: int = 1024):
        """创建集合"""
        self.dimension = dimension
        
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus不可用，跳过创建集合")
            return
        
        try:
            # 检查集合是否存在
            if utility.has_collection(self.collection_name):
                logger.info(f"集合 {self.collection_name} 已存在")
                self.collection = Collection(self.collection_name)
                return
            
            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="page_number", dtype=DataType.INT32),
                FieldSchema(name="chunk_index", dtype=DataType.INT32),
                FieldSchema(name="start_pos", dtype=DataType.INT32),
                FieldSchema(name="end_pos", dtype=DataType.INT32),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64)
            ]
            
            schema = CollectionSchema(fields, description="Agentic RAG Knowledge Base")
            self.collection = Collection(self.collection_name, schema)
            
            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64}
            }
            self.collection.create_index("embedding", index_params)
            logger.info(f"集合 {self.collection_name} 创建成功")
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
    
    def insert(self, chunks: List[DocumentChunk]):
        """插入文档块"""
        if not MILVUS_AVAILABLE or self.collection is None:
            logger.warning("Milvus不可用，跳过插入")
            return
        
        try:
            entities = [
                [chunk.id for chunk in chunks],
                [chunk.content for chunk in chunks],
                [chunk.source_file for chunk in chunks],
                [chunk.page_number for chunk in chunks],
                [chunk.chunk_index for chunk in chunks],
                [chunk.start_pos for chunk in chunks],
                [chunk.end_pos for chunk in chunks],
                [chunk.embedding.tolist() if chunk.embedding is not None else [0.0] * self.dimension for chunk in chunks],
                [chunk.created_at for chunk in chunks]
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            logger.info(f"成功插入 {len(chunks)} 个文档块到Milvus")
        except Exception as e:
            logger.error(f"插入失败: {e}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 60) -> List[Dict]:
        """向量搜索"""
        if not MILVUS_AVAILABLE or self.collection is None:
            logger.warning("Milvus不可用，返回空结果")
            return []
        
        try:
            self.collection.load()
            
            search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "content", "source_file", "page_number", "chunk_index"]
            )
            
            # 解析结果
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        'id': hit.entity.get('id'),
                        'content': hit.entity.get('content'),
                        'source_file': hit.entity.get('source_file'),
                        'page_number': hit.entity.get('page_number'),
                        'chunk_index': hit.entity.get('chunk_index'),
                        'distance': hit.distance
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []


class BM25Retriever:
    """BM25检索器"""
    
    def __init__(self):
        self.bm25 = None
        self.corpus = []
        self.chunk_map = {}
    
    def build_index(self, chunks: List[DocumentChunk]):
        """构建BM25索引"""
        if not BM25_AVAILABLE:
            logger.warning("BM25不可用")
            return
        
        self.corpus = []
        self.chunk_map = {}
        
        for chunk in chunks:
            # 分词
            tokens = self._tokenize(chunk.content)
            self.corpus.append(tokens)
            self.chunk_map[len(self.corpus) - 1] = chunk
        
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            logger.info(f"BM25索引构建完成，共 {len(self.corpus)} 个文档")
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        if JIEBA_AVAILABLE:
            return list(jieba.cut(text))
        else:
            # 简单分词
            return text.lower().split()
    
    def search(self, query: str, top_k: int = 60) -> List[Tuple[DocumentChunk, float]]:
        """BM25搜索"""
        if self.bm25 is None:
            return []
        
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取top_k结果
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                chunk = self.chunk_map.get(idx)
                if chunk:
                    results.append((chunk, float(scores[idx])))
        
        return results


class HybridRetriever:
    """混合检索器 - 语义相似度 + BM25 + RRF"""
    
    def __init__(self, vector_store, bm25_retriever: BM25Retriever):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.rrf_k = 60  # RRF参数
    
    def retrieve(self, 
                 query: str,
                 query_embedding: np.ndarray,
                 top_k: int = 60) -> List[SearchResult]:
        """
        混合检索
        
        Args:
            query: 查询文本
            query_embedding: 查询向量
            top_k: 返回结果数
            
        Returns:
            排序后的搜索结果
        """
        # 1. 语义相似度搜索
        semantic_results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # 2. BM25搜索
        bm25_results = self.bm25_retriever.search(query, top_k=top_k)
        
        # 3. RRF融合
        rrf_scores = {}
        
        # 语义相似度排名
        for rank, result in enumerate(semantic_results):
            chunk_id = result['id']
            rrf_scores[chunk_id] = {
                'chunk': DocumentChunk(
                    id=chunk_id,
                    content=result['content'],
                    source_file=result['source_file'],
                    page_number=result['page_number'],
                    chunk_index=result['chunk_index'],
                    start_pos=0,
                    end_pos=0
                ),
                'semantic_score': result['distance'],
                'bm25_score': 0.0,
                'rrf_score': 1.0 / (self.rrf_k + rank + 1)
            }
        
        # BM25排名
        for rank, (chunk, score) in enumerate(bm25_results):
            chunk_id = chunk.id
            if chunk_id in rrf_scores:
                rrf_scores[chunk_id]['bm25_score'] = score
                rrf_scores[chunk_id]['rrf_score'] += 1.0 / (self.rrf_k + rank + 1)
            else:
                rrf_scores[chunk_id] = {
                    'chunk': chunk,
                    'semantic_score': 0.0,
                    'bm25_score': score,
                    'rrf_score': 1.0 / (self.rrf_k + rank + 1)
                }
        
        # 4. 按RRF分数排序
        sorted_results = sorted(
            rrf_scores.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )[:top_k]
        
        # 5. 构建最终结果
        search_results = []
        for item in sorted_results:
            search_results.append(SearchResult(
                chunk=item['chunk'],
                semantic_score=item['semantic_score'],
                bm25_score=item['bm25_score'],
                rrf_score=item['rrf_score'],
                final_score=item['rrf_score']
            ))
        
        return search_results


class DynamicTopKSelector:
    """动态TopK选择器"""
    
    def __init__(self, 
                 base_k: int = 5,
                 max_k: int = 10,
                 threshold_factor: float = 0.7):
        """
        Args:
            base_k: 基础K值
            max_k: 最大K值
            threshold_factor: 阈值因子（用于判断是否增加K）
        """
        self.base_k = base_k
        self.max_k = max_k
        self.threshold_factor = threshold_factor
    
    def select(self, results: List[SearchResult], threshold: float = 0.5) -> int:
        """
        动态选择TopK
        
        Args:
            results: 搜索结果列表
            threshold: 相关性阈值（0-1）
            
        Returns:
            选择的K值
        """
        if not results:
            return self.base_k
        
        # 计算相关性指标
        high_relevance_count = sum(
            1 for r in results 
            if r.semantic_score > threshold or r.bm25_score > threshold
        )
        
        # 根据相关性文档数量动态调整K
        # 公式：如果高相关文档超过阈值比例，使用较小的K，否则使用较大的K
        total_docs = len(set(r.chunk.source_file for r in results))
        
        if total_docs > 3:
            # 多个文档相关，使用较小的K聚焦
            k = self.base_k
        else:
            # 文档较少，使用较大的K获取更多信息
            k = min(self.max_k, self.base_k + 2)
        
        # 根据相关性分数进一步调整
        if high_relevance_count < 3:
            # 高相关文档少，增加K值
            k = min(self.max_k, k + 2)
        
        return k


class AgenticRAG:
    """Agentic RAG主类"""
    
    def __init__(self, 
                 use_milvus: bool = False,
                 milvus_host: str = "localhost",
                 milvus_port: str = "19530",
                 embedding_model: str = "BAAI/bge-large-zh-v1.5"):
        """初始化Agentic RAG"""
        logger.info("=" * 60)
        logger.info("初始化 Agentic RAG 系统 V2")
        logger.info("=" * 60)
        
        # 1. 初始化动态语义分割器
        self.splitter = DynamicSemanticSplitter(
            target_chunk_size=512,
            min_chunk_size=256,
            max_chunk_size=1024,
            overlap_ratio=0.1
        )
        logger.info("✓ 动态语义分割器初始化完成")
        
        # 2. 初始化BGE嵌入模型
        self.embedding_model = BGEEmbeddingModel(embedding_model)
        logger.info(f"✓ BGE嵌入模型初始化完成 (维度: {self.embedding_model.dimension})")
        
        # 3. 初始化向量存储
        if use_milvus and MILVUS_AVAILABLE:
            self.vector_store = MilvusVectorStore(
                host=milvus_host,
                port=milvus_port,
                collection_name="agentic_rag"
            )
            self.vector_store.create_collection(self.embedding_model.dimension)
            logger.info("✓ Milvus向量存储初始化完成")
        else:
            self.vector_store = LocalVectorStore(self.embedding_model.dimension)
            logger.info("✓ 本地向量存储初始化完成")
        
        # 4. 初始化BM25检索器
        self.bm25_retriever = BM25Retriever()
        logger.info("✓ BM25检索器初始化完成")
        
        # 5. 初始化混合检索器
        self.hybrid_retriever = HybridRetriever(self.vector_store, self.bm25_retriever)
        logger.info("✓ 混合检索器初始化完成")
        
        # 6. 初始化动态TopK选择器
        self.topk_selector = DynamicTopKSelector(base_k=5, max_k=10)
        logger.info("✓ 动态TopK选择器初始化完成")
        
        # 本地存储（用于BM25）
        self.local_chunks: List[DocumentChunk] = []
        
        logger.info("=" * 60)
        logger.info("Agentic RAG 系统 V2 初始化完成")
        logger.info("=" * 60)
    
    def add_document(self, file_path: str) -> bool:
        """
        添加文档到知识库
        
        Args:
            file_path: 文档路径
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"正在添加文档: {file_path}")
            
            # 检查文件
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.error(f"文件内容为空: {file_path}")
                return False
            
            # 提取文件名和页号（如果有）
            file_name = os.path.basename(file_path)
            page_number = self._extract_page_number(file_name)
            
            # 动态语义分割
            chunks = self.splitter.split(content, file_name, page_number)
            logger.info(f"文档分割完成，共 {len(chunks)} 个块")
            
            # 生成向量嵌入
            logger.info("正在生成向量嵌入...")
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_model.encode(texts)
            
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i]
            
            # 存储到向量库
            self.vector_store.insert(chunks)
            
            # 存储到本地（用于BM25）
            self.local_chunks.extend(chunks)
            
            # 重建BM25索引
            self.bm25_retriever.build_index(self.local_chunks)
            
            logger.info(f"✓ 文档添加成功: {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_page_number(self, file_name: str) -> int:
        """从文件名提取页号"""
        # 尝试匹配常见的页号格式：page_001, p1, 第1页等
        patterns = [
            r'page[_-]?(\d+)',
            r'p(\d+)',
            r'第(\d+)页',
            r'(\d+)\.txt',
            r'(\d+)\.md'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_name, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def search(self, query: str, threshold: float = 0.5) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            threshold: 相关性阈值
            
        Returns:
            搜索结果，包含语段和详细来源信息
        """
        logger.info(f"执行搜索: {query}")
        
        if not self.local_chunks:
            logger.warning("知识库为空")
            return {
                'query': query,
                'results': [],
                'top_k': 0,
                'total_chunks': 0
            }
        
        # 1. 生成查询向量
        query_embedding = self.embedding_model.encode([query])[0]
        
        # 2. 混合检索（k=60）
        results = self.hybrid_retriever.retrieve(query, query_embedding, top_k=60)
        logger.info(f"混合检索完成，共 {len(results)} 个结果")
        
        # 3. 动态选择TopK
        k = self.topk_selector.select(results, threshold)
        logger.info(f"动态选择TopK: {k}")
        
        # 4. 截取TopK结果
        top_results = results[:k]
        
        # 5. 格式化结果（包含详细来源信息）
        formatted_results = []
        for result in top_results:
            formatted_results.append({
                'content': result.chunk.content,
                'source': {
                    'file_name': result.chunk.source_file,
                    'page_number': result.chunk.page_number,
                    'chunk_index': result.chunk.chunk_index,
                    'position': f"{result.chunk.start_pos}-{result.chunk.end_pos}"
                },
                'scores': {
                    'semantic': round(result.semantic_score, 4),
                    'bm25': round(result.bm25_score, 4),
                    'rrf': round(result.rrf_score, 4),
                    'final': round(result.final_score, 4)
                }
            })
        
        return {
            'query': query,
            'results': formatted_results,
            'top_k': k,
            'total_chunks': len(self.local_chunks),
            'threshold': threshold
        }


# 测试函数
def test_agentic_rag():
    """测试Agentic RAG"""
    print("\n" + "=" * 60)
    print("测试 Agentic RAG 系统 V2")
    print("=" * 60)
    
    # 初始化
    rag = AgenticRAG(use_milvus=False)  # 使用本地存储
    
    # 创建测试文档
    test_doc_path = "test_document.txt"
    test_content = """
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。

机器学习是AI的核心技术之一。它使计算机能够从数据中学习，而无需明确编程。深度学习是机器学习的一个子集，使用神经网络来处理复杂的数据模式。

自然语言处理（NLP）是AI的另一个重要领域。它使计算机能够理解、解释和生成人类语言。应用包括机器翻译、情感分析和聊天机器人。

计算机视觉让机器能够"看"和理解图像及视频。应用包括人脸识别、自动驾驶和医学影像分析。

AI的伦理问题也日益受到关注，包括隐私保护、算法偏见和就业影响等方面。

强化学习是一种通过与环境交互来学习的方法。它在游戏、机器人控制和资源管理等领域有广泛应用。

迁移学习允许模型将在一个任务上学到的知识应用到另一个相关任务上，大大提高了学习效率。

联邦学习是一种分布式机器学习方法，允许多个参与方在不共享原始数据的情况下协作训练模型。
"""
    
    with open(test_doc_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"\n创建测试文档: {test_doc_path}")
    
    # 添加文档
    success = rag.add_document(test_doc_path)
    
    if success:
        print("\n" + "-" * 60)
        print("执行搜索测试...")
        print("-" * 60)
        
        # 测试查询
        queries = [
            "什么是机器学习",
            "深度学习",
            "自然语言处理的应用",
            "联邦学习是什么"
        ]
        
        for query in queries:
            print(f"\n查询: {query}")
            result = rag.search(query)
            
            print(f"返回 {result['top_k']} 个结果:")
            for i, item in enumerate(result['results'], 1):
                print(f"\n[{i}] 内容: {item['content'][:100]}...")
                print(f"    来源: {item['source']['file_name']} (页{item['source']['page_number']})")
                print(f"    分数: 语义={item['scores']['semantic']}, BM25={item['scores']['bm25']}, RRF={item['scores']['rrf']}")
    
    # 清理
    if os.path.exists(test_doc_path):
        os.remove(test_doc_path)
        print(f"\n清理测试文件: {test_doc_path}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_agentic_rag()
