#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级知识库管理模块 - P1技术升级版本
升级内容：
1. 文本分割：RecursiveCharacterTextSplitter（语义边界保持）
2. 向量存储：ChromaDB集成
3. 检索算法：Hybrid RAG（向量+BM25+RRF）
4. 嵌入模型：BGE-Large中文优化
"""

import os
import json
import hashlib
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局单例实例
_advanced_kb_instance = None

def get_advanced_knowledge_base():
    """获取高级知识库单例实例"""
    global _advanced_kb_instance
    if _advanced_kb_instance is None:
        _advanced_kb_instance = AdvancedKnowledgeBaseManager()
    return _advanced_kb_instance


@dataclass
class DocumentChunk:
    """文档分块类"""
    id: str
    content: str
    source_file: str
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
            'chunk_index': self.chunk_index,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'created_at': self.created_at
        }


@dataclass
class SearchResult:
    """搜索结果类"""
    chunk: DocumentChunk
    semantic_score: float
    bm25_score: float
    rrf_score: float
    final_score: float


class RecursiveTextSplitter:
    """
    递归文本分割器 - 保持语义边界
    升级自简单字符分割，采用LangChain风格的递归分割策略
    """
    
    def __init__(self, 
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 separators: List[str] = None):
        """
        Args:
            chunk_size: 目标块大小
            chunk_overlap: 块间重叠大小
            separators: 分隔符列表，按优先级排序
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",     # 换行
            "。", "！", "？",  # 中文句子
            ".", "!", "?",     # 英文句子
            " ",     # 空格
            "",      # 字符
        ]
    
    def split_text(self, text: str, source_file: str = "") -> List[DocumentChunk]:
        """
        递归分割文本，保持语义边界
        
        Returns:
            文档块列表
        """
        if not text.strip():
            return []
        
        chunks = self._recursive_split(text, self.separators)
        
        # 创建DocumentChunk对象
        document_chunks = []
        start_pos = 0
        
        for i, chunk_text in enumerate(chunks):
            # 计算在原文中的位置
            chunk_start = text.find(chunk_text, start_pos)
            chunk_end = chunk_start + len(chunk_text) if chunk_start >= 0 else start_pos + len(chunk_text)
            
            chunk_id = hashlib.md5(f"{source_file}_{i}_{chunk_text[:50]}".encode()).hexdigest()[:16]
            
            doc_chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                source_file=source_file,
                chunk_index=i,
                start_pos=chunk_start if chunk_start >= 0 else start_pos,
                end_pos=chunk_end
            )
            document_chunks.append(doc_chunk)
            start_pos = chunk_end - self.chunk_overlap if chunk_end > self.chunk_overlap else chunk_end
        
        return document_chunks
    
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """递归分割文本"""
        # 如果没有分隔符或文本已够短，直接返回
        if not separators or len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        separator = separators[0]
        new_separators = separators[1:]
        
        # 按当前分隔符分割
        if separator:
            splits = text.split(separator)
        else:
            # 字符级分割
            splits = list(text)
        
        # 合并小块
        chunks = []
        current_chunk = ""
        
        for split in splits:
            # 考虑分隔符（除了字符级分割）
            split_with_sep = split + separator if separator and split != splits[-1] else split
            
            if len(current_chunk) + len(split_with_sep) <= self.chunk_size:
                current_chunk += split_with_sep
            else:
                # 当前块已满，保存并递归处理
                if current_chunk.strip():
                    if len(current_chunk) > self.chunk_size:
                        # 递归细分
                        chunks.extend(self._recursive_split(current_chunk, new_separators))
                    else:
                        chunks.append(current_chunk)
                
                # 开始新块，考虑重叠
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + split_with_sep
                else:
                    current_chunk = split_with_sep
        
        # 处理最后一个块
        if current_chunk.strip():
            if len(current_chunk) > self.chunk_size:
                chunks.extend(self._recursive_split(current_chunk, new_separators))
            else:
                chunks.append(current_chunk)
        
        return chunks


def _hub_cache_roots() -> List[Path]:
    """HF Hub 缓存根目录（hub 目录本身），去重且仅保留存在的路径。"""
    roots: List[Path] = []
    hub_cache = os.environ.get("HF_HUB_CACHE")
    if hub_cache:
        roots.append(Path(hub_cache).expanduser())
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        roots.append(Path(hf_home).expanduser() / "hub")
    roots.append(Path.home() / ".cache" / "huggingface" / "hub")
    trans = os.environ.get("TRANSFORMERS_CACHE")
    if trans:
        t = Path(trans).expanduser()
        roots.append(t)
        roots.append(t / "hub")
    # 与 kb_manager_fast 等一致：模型可能放在本模块目录下的 models/（含 models--Org--name 结构）
    _agent_dir = Path(__file__).resolve().parent
    for rel in ("models", Path("models") / "hub", Path(".cache") / "huggingface" / "hub"):
        p = _agent_dir / rel
        if p.is_dir():
            roots.append(p)
    seen: Set[Path] = set()
    out: List[Path] = []
    for r in roots:
        try:
            x = r.resolve()
        except Exception:
            x = r.expanduser()
        if x in seen or not x.is_dir():
            continue
        seen.add(x)
        out.append(x)
    return out


def _repo_cache_folder_name(model_id: str) -> str:
    return "models--" + model_id.replace("/", "--").replace("\\", "--")


def _newest_snapshot_under(snapshots_dir: Path) -> Optional[Path]:
    """在 .../snapshots 下找含 config.json 的最新子目录。"""
    if not snapshots_dir.is_dir():
        return None
    best: Optional[Path] = None
    best_m = -1.0
    for child in snapshots_dir.iterdir():
        if not child.is_dir():
            continue
        if not (child / "config.json").is_file():
            continue
        try:
            m = child.stat().st_mtime
        except OSError:
            continue
        if m > best_m:
            best_m = m
            best = child
    return best


def _find_local_sentence_transformer_dir(model_id: str) -> Optional[Path]:
    """
    在 HuggingFace Hub 缓存中定位已下载模型的快照目录，避免走网络。
    model_id 形如 BAAI/bge-large-zh-v1.5
    """
    folder = _repo_cache_folder_name(model_id)
    for hub in _hub_cache_roots():
        snap = _newest_snapshot_under(hub / folder / "snapshots")
        if snap is not None:
            return snap
    return None


def _explicit_bge_local_dir() -> Optional[Path]:
    """
    用户指定本地模型目录（含 config.json），或含 snapshots 子目录的 repo 缓存根。
    环境变量：BGE_LOCAL_MODEL_PATH 或 ADVANCED_KB_BGE_MODEL_PATH
    """
    raw = os.environ.get("BGE_LOCAL_MODEL_PATH") or os.environ.get("ADVANCED_KB_BGE_MODEL_PATH")
    if not raw:
        return None
    p = Path(raw).expanduser()
    if not p.exists():
        logger.warning(f"[BGE] 环境变量指定的模型路径不存在: {p}")
        return None
    if p.is_file():
        p = p.parent
    if (p / "config.json").is_file():
        return p.resolve()
    snap_root = p / "snapshots"
    found = _newest_snapshot_under(snap_root)
    if found is not None:
        return found.resolve()
    logger.warning(f"[BGE] 环境变量路径下未找到有效模型快照: {p}")
    return None


class BGEEmbeddingModel:
    """
    BGE-Large中文嵌入模型
    升级自MiniLM，提供更好的中文语义理解
    """
    
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        self.model_name = model_name
        self.model = None
        self.dimension = 1024  # BGE-Large维度
        self._load_model()
    
    def _load_model(self):
        """加载模型：优先本地 Hub 快照目录 + local_files_only，避免访问 HuggingFace。"""
        try:
            # 在 import 前打开离线开关，避免 huggingface_hub 初始化后再连网
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
            os.environ.setdefault("HF_HUB_OFFLINE", "1")

            from sentence_transformers import SentenceTransformer

            allow_download = os.environ.get("ADVANCED_KB_ALLOW_MODEL_DOWNLOAD", "").strip().lower() in (
                "1",
                "true",
                "yes",
            )

            # 1) 用户显式目录
            explicit = _explicit_bge_local_dir()
            if explicit is not None:
                try:
                    logger.info(f"[BGE] 从本地目录加载（零网络）: {explicit}")
                    self.model = SentenceTransformer(
                        str(explicit),
                        local_files_only=True,
                        trust_remote_code=True,
                    )
                    self.dimension = self.model.get_sentence_embedding_dimension()
                    logger.info(f"[BGE] ✓ 模型加载成功, 维度: {self.dimension}")
                    return
                except Exception as e:
                    logger.warning(f"[BGE] 显式本地路径加载失败，尝试 Hub 缓存解析: {e}")

            # 2) 按模型 id 在 HF 缓存中找快照（已下载的 BAAI/bge-large-zh-v1.5）
            model_sources = [
                self.model_name,
                "shibing624/text2vec-base-chinese",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            ]
            for model_source in model_sources:
                local_snap = _find_local_sentence_transformer_dir(model_source)
                if local_snap is None:
                    logger.info(f"[BGE] 未在本地 Hub 缓存找到: {model_source}")
                    continue
                try:
                    logger.info(f"[BGE] 从 Hub 缓存快照加载（local_files_only）: {local_snap}")
                    self.model = SentenceTransformer(
                        str(local_snap),
                        local_files_only=True,
                        trust_remote_code=True,
                    )
                    self.model_name = model_source
                    self.dimension = self.model.get_sentence_embedding_dimension()
                    logger.info(
                        f"[BGE] ✓ 模型加载成功: {model_source}, 维度: {self.dimension}"
                    )
                    return
                except Exception as e:
                    logger.warning(f"[BGE] 本地快照加载失败 {local_snap}: {e}")
                    continue

            # 3) 仅当显式允许时才联网下载（默认禁止，防止启动卡死）
            if allow_download:
                for model_source in model_sources:
                    try:
                        logger.info(f"[BGE] 尝试联网加载（ADVANCED_KB_ALLOW_MODEL_DOWNLOAD 已开启）: {model_source}")
                        self.model = SentenceTransformer(model_source, trust_remote_code=True)
                        self.model_name = model_source
                        self.dimension = self.model.get_sentence_embedding_dimension()
                        logger.info(
                            f"[BGE] ✓ 模型加载成功: {model_source}, 维度: {self.dimension}"
                        )
                        return
                    except Exception as e:
                        logger.warning(f"[BGE] 加载模型 {model_source} 失败: {e}")
                        continue

            logger.error(
                "[BGE] 未找到本地 BGE 模型。请将模型放在 HF Hub 缓存 "
                "(例如 ~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/snapshots/<hash>/) "
                "或设置环境变量 BGE_LOCAL_MODEL_PATH 指向含 config.json 的目录；"
                "若必须联网下载可设置 ADVANCED_KB_ALLOW_MODEL_DOWNLOAD=1"
            )
            self.model = None

        except ImportError:
            logger.error("[BGE] sentence-transformers未安装")
            self.model = None
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """编码文本为向量"""
        if self.model is None:
            logger.error("[BGE] 模型未加载")
            return np.zeros((len(texts), self.dimension))
        
        try:
            # BGE模型需要在文本前添加指令
            if 'bge' in self.model_name.lower():
                instruction = "为这个句子生成表示："
                texts_with_instruction = [f"{instruction}{text}" for text in texts]
            else:
                texts_with_instruction = texts
            
            embeddings = self.model.encode(
                texts_with_instruction,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            logger.error(f"[BGE] 编码失败: {e}")
            return np.zeros((len(texts), self.dimension))


class ChromaVectorStore:
    """
    ChromaDB向量存储
    升级自JSON文件存储，提供更好的性能和可扩展性
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._init_chroma()
    
    def _init_chroma(self):
        """初始化ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"[Chroma] 向量存储初始化成功: {self.persist_directory}")
            
        except ImportError:
            logger.warning("[Chroma] chromadb未安装，使用内存存储")
            self.client = None
            self.collection = None
        except Exception as e:
            logger.error(f"[Chroma] 初始化失败: {e}")
            self.client = None
            self.collection = None
    
    def add_documents(self, chunks: List[DocumentChunk], embeddings: np.ndarray):
        """添加文档到向量存储"""
        if self.collection is None:
            logger.warning("[Chroma] 集合未初始化，跳过添加")
            return False
        
        try:
            ids = [chunk.id for chunk in chunks]
            texts = [chunk.content for chunk in chunks]
            metadatas = [
                {
                    "source_file": chunk.source_file,
                    "chunk_index": chunk.chunk_index,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos
                }
                for chunk in chunks
            ]
            
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings.tolist()
            )
            
            logger.info(f"[Chroma] 成功添加 {len(chunks)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"[Chroma] 添加文档失败: {e}")
            return False
    
    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict]:
        """向量搜索"""
        if self.collection is None:
            return []
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"[Chroma] 搜索失败: {e}")
            return []
    
    def delete_by_source(self, source_file: str):
        """根据源文件删除文档"""
        if self.collection is None:
            return False
        
        try:
            # 查询要删除的文档
            results = self.collection.get(
                where={"source_file": source_file}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"[Chroma] 删除 {len(results['ids'])} 个文档: {source_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"[Chroma] 删除失败: {e}")
            return False


class BM25Retriever:
    """BM25检索器"""
    
    def __init__(self):
        self.bm25 = None
        self.corpus = []
        self.chunk_map = {}
        self.tokenizer = None
        
        # 尝试导入jieba
        try:
            import jieba
            self.tokenizer = jieba
            logger.info("[BM25] 使用jieba分词")
        except ImportError:
            logger.warning("[BM25] jieba未安装，使用简单分词")
    
    def build_index(self, chunks: List[DocumentChunk]):
        """构建BM25索引"""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning("[BM25] rank_bm25未安装，BM25不可用")
            return
        
        self.corpus = []
        self.chunk_map = {}
        
        for chunk in chunks:
            tokens = self._tokenize(chunk.content)
            self.corpus.append(tokens)
            self.chunk_map[len(self.corpus) - 1] = chunk
        
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            logger.info(f"[BM25] 索引构建完成: {len(self.corpus)} 个文档")
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        if self.tokenizer:
            return list(self.tokenizer.cut(text))
        else:
            return text.lower().split()
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
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
    """
    混合检索器 - 向量相似度 + BM25 + RRF
    业界常用技术，提升检索准确率
    """
    
    def __init__(self, vector_store: ChromaVectorStore, bm25_retriever: BM25Retriever):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.rrf_k = 60  # RRF参数
    
    def retrieve(self, query: str, query_embedding: np.ndarray, top_k: int = 10) -> List[SearchResult]:
        """
        混合检索
        
        Args:
            query: 查询文本
            query_embedding: 查询向量
            top_k: 返回结果数
            
        Returns:
            排序后的搜索结果
        """
        # 1. 向量搜索
        vector_results = self.vector_store.search(query_embedding, top_k=top_k * 2)
        
        # 2. BM25搜索
        bm25_results = self.bm25_retriever.search(query, top_k=top_k * 2)
        
        # 3. RRF融合
        rrf_scores = {}
        
        # 向量搜索排名
        for rank, result in enumerate(vector_results):
            chunk_id = result['id']
            rrf_scores[chunk_id] = {
                'chunk': DocumentChunk(
                    id=chunk_id,
                    content=result['content'],
                    source_file=result['metadata'].get('source_file', ''),
                    chunk_index=result['metadata'].get('chunk_index', 0),
                    start_pos=result['metadata'].get('start_pos', 0),
                    end_pos=result['metadata'].get('end_pos', 0)
                ),
                'semantic_score': 1 - result['distance'],  # 转换距离为相似度
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


class AdvancedKnowledgeBaseManager:
    """
    高级知识库管理器 - P1技术升级版本
    
    升级内容：
    1. 文本分割：RecursiveCharacterTextSplitter
    2. 向量存储：ChromaDB
    3. 检索算法：Hybrid RAG（向量+BM25+RRF）
    4. 嵌入模型：BGE-Large
    """
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.kb_dir = os.path.join(self.base_dir, "knowledge_base_advanced")
        self.chroma_dir = os.path.join(self.kb_dir, "chroma_db")
        self.metadata_file = os.path.join(self.kb_dir, "metadata.json")
        
        self.chunks: List[DocumentChunk] = []
        self._initialized = False
        
        # 创建目录
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("高级知识库管理器初始化开始...")
        logger.info("=" * 60)
        
        # 1. 初始化文本分割器
        self.text_splitter = RecursiveTextSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        logger.info("[AdvancedKB] ✓ 递归文本分割器初始化完成")
        
        # 2. 初始化嵌入模型（BGE-Large）
        self.embedding_model = BGEEmbeddingModel()
        logger.info(f"[AdvancedKB] ✓ BGE嵌入模型初始化完成，维度: {self.embedding_model.dimension}")
        
        # 3. 初始化向量存储（ChromaDB）
        self.vector_store = ChromaVectorStore(persist_directory=self.chroma_dir)
        logger.info("[AdvancedKB] ✓ ChromaDB向量存储初始化完成")
        
        # 4. 初始化BM25检索器
        self.bm25_retriever = BM25Retriever()
        logger.info("[AdvancedKB] ✓ BM25检索器初始化完成")
        
        # 5. 初始化混合检索器
        self.hybrid_retriever = HybridRetriever(self.vector_store, self.bm25_retriever)
        logger.info("[AdvancedKB] ✓ 混合检索器初始化完成")
        
        # 6. 加载元数据
        self._load_metadata()
        
        self._initialized = True
        
        logger.info("=" * 60)
        logger.info("✓ 高级知识库管理器初始化完成")
        logger.info(f"  - 文档块数: {len(self.chunks)}")
        logger.info(f"  - 嵌入维度: {self.embedding_model.dimension}")
        logger.info(f"  - 向量存储: {'ChromaDB' if self.vector_store.client else '内存'}")
        logger.info("=" * 60)
    
    def _load_metadata(self):
        """加载元数据"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    self.chunks = [DocumentChunk(**chunk_data) for chunk_data in metadata.get('chunks', [])]
                    logger.info(f"[AdvancedKB] 加载元数据: {len(self.chunks)} 个文档块")
            else:
                self.chunks = []
        except Exception as e:
            logger.error(f"[AdvancedKB] 加载元数据失败: {e}")
            self.chunks = []
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            metadata = {
                'chunks': [chunk.to_dict() for chunk in self.chunks],
                'updated_at': datetime.now().isoformat()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[AdvancedKB] 保存元数据失败: {e}")
    
    def add_document(self, file_path: str) -> Tuple[bool, str]:
        """添加文档到知识库"""
        try:
            # 检查文件
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}"
            
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.txt', '.md']:
                return False, f"不支持的文件格式: {file_ext}"
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return False, "文件内容为空"
            
            file_name = os.path.basename(file_path)
            
            # 1. 文本分割（递归分割器）
            chunks = self.text_splitter.split_text(content, source_file=file_name)
            if not chunks:
                return False, "文本分割失败"
            
            # 2. 生成嵌入（BGE-Large）
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_model.encode(texts)
            
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i]
            
            # 3. 添加到向量存储（ChromaDB）
            self.vector_store.add_documents(chunks, embeddings)
            
            # 4. 更新BM25索引
            self.chunks.extend(chunks)
            self.bm25_retriever.build_index(self.chunks)
            
            # 5. 保存元数据
            self._save_metadata()
            
            logger.info(f"[AdvancedKB] 成功添加文档: {file_name}, {len(chunks)} 个块")
            return True, f"成功添加 {len(chunks)} 个向量块"
            
        except Exception as e:
            logger.error(f"[AdvancedKB] 添加文档失败: {e}")
            return False, f"添加失败: {str(e)}"
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索知识库（混合检索）"""
        if not self.chunks:
            logger.warning("[AdvancedKB] 知识库为空")
            return []
        
        try:
            # 1. 生成查询嵌入
            query_embedding = self.embedding_model.encode([query])[0]
            
            # 2. 混合检索（向量+BM25+RRF）
            results = self.hybrid_retriever.retrieve(query, query_embedding, top_k=top_k)
            
            # 3. 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'content': result.chunk.content,
                    'source_file': result.chunk.source_file,
                    'chunk_id': result.chunk.chunk_index,
                    'score': result.final_score,
                    'semantic_score': result.semantic_score,
                    'bm25_score': result.bm25_score,
                    'rrf_score': result.rrf_score,
                    'start_pos': result.chunk.start_pos,
                    'end_pos': result.chunk.end_pos
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"[AdvancedKB] 搜索失败: {e}")
            return []
    
    def delete_document(self, file_name: str) -> bool:
        """删除文档"""
        try:
            # 1. 从向量存储删除
            self.vector_store.delete_by_source(file_name)
            
            # 2. 从内存删除
            original_count = len(self.chunks)
            self.chunks = [c for c in self.chunks if c.source_file != file_name]
            removed_count = original_count - len(self.chunks)
            
            # 3. 重建BM25索引
            if removed_count > 0:
                self.bm25_retriever.build_index(self.chunks)
                self._save_metadata()
                logger.info(f"[AdvancedKB] 删除文档 {file_name}, 移除 {removed_count} 个块")
            
            return True
            
        except Exception as e:
            logger.error(f"[AdvancedKB] 删除文档失败: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        source_files = list(set(chunk.source_file for chunk in self.chunks))
        return {
            'total_chunks': len(self.chunks),
            'total_files': len(source_files),
            'embedding_dim': self.embedding_model.dimension,
            'model_loaded': self.embedding_model.model is not None,
            'vector_store_type': 'ChromaDB' if self.vector_store.client else '内存',
            'initialized': self._initialized
        }
    
    def is_ready(self) -> bool:
        """检查是否就绪"""
        return self._initialized


def health_check_advanced() -> Dict:
    """高级知识库健康检查"""
    try:
        kb = get_advanced_knowledge_base()
        stats = kb.get_stats()
        
        return {
            'status': 'healthy' if kb.is_ready() else 'unhealthy',
            'initialized': stats['initialized'],
            'model_loaded': stats['model_loaded'],
            'vector_store': stats['vector_store_type'],
            'total_chunks': stats['total_chunks'],
            'total_files': stats['total_files'],
            'embedding_dim': stats['embedding_dim']
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    print("测试高级知识库管理器...")
    kb = get_advanced_knowledge_base()
    
    stats = kb.get_stats()
    print(f"\n知识库状态:")
    print(f"  - 初始化: {stats['initialized']}")
    print(f"  - 模型: {stats['model_loaded']}")
    print(f"  - 向量存储: {stats['vector_store_type']}")
    print(f"  - 文档块: {stats['total_chunks']}")
    print(f"  - 嵌入维度: {stats['embedding_dim']}")
    
    health = health_check_advanced()
    print(f"\n健康检查: {health}")
