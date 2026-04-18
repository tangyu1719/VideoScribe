#!/usr/bin/env python3
"""
Agentic RAG 知识库系统 - 最终版
- 本地向量存储（无需Milvus）
- 简化的向量嵌入（无需下载大模型）
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
from dataclasses import dataclass
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank-bm25未安装")

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


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
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio
        self.sentence_endings = '。！？.!?\n'
    
    def split(self, text: str, source_file: str = "", page_number: int = 0) -> List[DocumentChunk]:
        """动态语义分割文本"""
        text = text.strip()
        if not text:
            return []
        
        chunks = []
        chunk_index = 0
        start_pos = 0
        text_len = len(text)
        
        # 如果文本长度小于最小块大小，直接作为一个块
        if text_len < self.min_chunk_size:
            chunk = self._create_chunk(
                text, source_file, page_number,
                chunk_index, 0, text_len
            )
            chunks.append(chunk)
            return chunks
        
        while start_pos < text_len:
            ideal_end = start_pos + self.target_chunk_size
            
            if ideal_end >= text_len:
                # 处理剩余文本
                chunk_text = text[start_pos:].strip()
                # 如果剩余文本长度足够，或者这是第一个块，则添加
                if len(chunk_text) >= self.min_chunk_size or len(chunks) == 0:
                    chunk = self._create_chunk(
                        chunk_text, source_file, page_number, 
                        chunk_index, start_pos, text_len
                    )
                    chunks.append(chunk)
                break
            
            actual_end = self._find_best_split_point(text, ideal_end)
            
            if actual_end - start_pos > self.max_chunk_size:
                actual_end = start_pos + self.max_chunk_size
            elif actual_end - start_pos < self.min_chunk_size:
                actual_end = min(start_pos + self.min_chunk_size, text_len)
            
            chunk_text = text[start_pos:actual_end].strip()
            
            if chunk_text:
                chunk = self._create_chunk(
                    chunk_text, source_file, page_number,
                    chunk_index, start_pos, actual_end
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # 计算重合区域
            overlap_size = int((actual_end - start_pos) * self.overlap_ratio)
            start_pos = actual_end - overlap_size
        
        return chunks
    
    def _find_best_split_point(self, text: str, ideal_pos: int) -> int:
        """在理想位置附近寻找最佳分割点（句子边界）"""
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
        
        return ideal_pos
    
    def _create_chunk(self, content: str, source_file: str, page_number: int,
                      chunk_index: int, start_pos: int, end_pos: int) -> DocumentChunk:
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


class SimpleEmbeddingModel:
    """简化的嵌入模型 - 使用TF-IDF风格向量，无需下载大模型"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.vocab = {}
        self.vocab_size = 0
        logger.info(f"✓ 简化嵌入模型初始化完成 (维度: {dimension})")
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        if JIEBA_AVAILABLE:
            return list(jieba.cut(text))
        else:
            return text.lower().split()
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """编码文本为向量 - 使用简单的词频加权"""
        embeddings = []
        
        for text in texts:
            tokens = self._tokenize(text)
            
            # 创建词频向量
            token_counts = {}
            for token in tokens:
                if token not in self.vocab:
                    self.vocab[token] = self.vocab_size
                    self.vocab_size += 1
                token_counts[self.vocab[token]] = token_counts.get(self.vocab[token], 0) + 1
            
            # 构建稀疏向量并投影到目标维度
            vec = np.zeros(min(self.vocab_size, 10000))
            for idx, count in token_counts.items():
                if idx < len(vec):
                    vec[idx] = count
            
            # 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            
            # 投影到目标维度
            if len(vec) < self.dimension:
                vec = np.pad(vec, (0, self.dimension - len(vec)))
            else:
                vec = vec[:self.dimension]
            
            embeddings.append(vec)
        
        return np.array(embeddings)


class LocalVectorStore:
    """本地向量存储"""
    
    def __init__(self, dimension: int = 768):
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
            if similarities[idx] > 0:
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
            return text.lower().split()
    
    def search(self, query: str, top_k: int = 60) -> List[Tuple[DocumentChunk, float]]:
        """BM25搜索"""
        if self.bm25 is None:
            return []
        
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
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
    
    def __init__(self, vector_store: LocalVectorStore, bm25_retriever: BM25Retriever):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.rrf_k = 60  # RRF参数
    
    def retrieve(self, query: str, query_embedding: np.ndarray, top_k: int = 60) -> List[SearchResult]:
        """混合检索"""
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
    
    def __init__(self, base_k: int = 5, max_k: int = 10, threshold_factor: float = 0.7):
        self.base_k = base_k
        self.max_k = max_k
        self.threshold_factor = threshold_factor
    
    def select(self, results: List[SearchResult], threshold: float = 0.5) -> int:
        """动态选择TopK
        
        策略：
        - 检索到的相关文档数 > 3时，使用较小的K聚焦 (K=3)
        - 检索到的相关文档数 <= 3时，使用较大的K获取更多信息 (K=5)
        - 根据阈值动态调整
        """
        if not results:
            return self.base_k
        
        # 计算高相关性文档数
        high_relevance_count = sum(
            1 for r in results 
            if r.semantic_score > threshold or r.bm25_score > threshold
        )
        
        # 计算涉及的文档数
        total_docs = len(set(r.chunk.source_file for r in results))
        
        # 动态选择公式
        if total_docs > 3:
            # 多个文档相关，使用较小的K聚焦
            k = 3
        else:
            # 文档较少，使用较大的K
            k = 5
        
        # 如果高相关文档很少，适当增加K
        if high_relevance_count < 2:
            k = min(self.max_k, k + 2)
        
        return k


class AgenticRAG:
    """Agentic RAG主类"""
    
    def __init__(self):
        """初始化Agentic RAG"""
        logger.info("=" * 60)
        logger.info("初始化 Agentic RAG 系统")
        logger.info("=" * 60)
        
        # 1. 初始化动态语义分割器
        self.splitter = DynamicSemanticSplitter(
            target_chunk_size=512,
            min_chunk_size=256,
            max_chunk_size=1024,
            overlap_ratio=0.1
        )
        logger.info("✓ 动态语义分割器初始化完成")
        
        # 2. 初始化简化嵌入模型
        self.embedding_model = SimpleEmbeddingModel(dimension=768)
        
        # 3. 初始化本地向量存储
        self.vector_store = LocalVectorStore(dimension=768)
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
        
        # 本地存储
        self.local_chunks: List[DocumentChunk] = []
        
        logger.info("=" * 60)
        logger.info("Agentic RAG 系统初始化完成")
        logger.info("=" * 60)
    
    def add_document(self, file_path: str) -> bool:
        """添加文档到知识库"""
        try:
            logger.info(f"正在添加文档: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.error(f"文件内容为空: {file_path}")
                return False
            
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
        """搜索知识库"""
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


def test_agentic_rag():
    """测试Agentic RAG"""
    print("\n" + "=" * 70)
    print("测试 Agentic RAG 系统")
    print("=" * 70)
    
    # 初始化
    rag = AgenticRAG()
    
    # 创建测试文档
    test_doc_path = "test_ai_knowledge.txt"
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
    print(f"文档大小: {len(test_content)} 字符")
    
    # 添加文档
    success = rag.add_document(test_doc_path)
    
    if success:
        print("\n" + "-" * 70)
        print("执行搜索测试...")
        print("-" * 70)
        
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
                print(f"\n[{i}] 内容: {item['content'][:80]}...")
                print(f"    来源: {item['source']['file_name']} (页{item['source']['page_number']}, 块{item['source']['chunk_index']})")
                print(f"    位置: 字符{item['source']['position']}")
                print(f"    分数: 语义={item['scores']['semantic']}, BM25={item['scores']['bm25']}, RRF={item['scores']['rrf']}")
    
    # 清理
    if os.path.exists(test_doc_path):
        os.remove(test_doc_path)
        print(f"\n清理测试文件: {test_doc_path}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    test_agentic_rag()
