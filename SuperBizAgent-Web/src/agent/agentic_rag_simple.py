#!/usr/bin/env python3
"""
Agentic RAG 知识库系统 - 简化版（无需下载模型）
- 动态语义分割
- BM25检索
- 详细来源信息
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
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class SearchResult:
    """搜索结果"""
    chunk: DocumentChunk
    bm25_score: float


class DynamicSemanticSplitter:
    """动态语义分割器"""
    
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
        if not text.strip():
            return []
        
        chunks = []
        chunk_index = 0
        start_pos = 0
        
        while start_pos < len(text):
            ideal_end = start_pos + self.target_chunk_size
            
            if ideal_end >= len(text):
                chunk_text = text[start_pos:].strip()
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk(
                        chunk_text, source_file, page_number, 
                        chunk_index, start_pos, len(text)
                    )
                    chunks.append(chunk)
                break
            
            actual_end = self._find_best_split_point(text, ideal_end)
            
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
            
            overlap_size = int((actual_end - start_pos) * self.overlap_ratio)
            start_pos = actual_end - overlap_size
        
        return chunks
    
    def _find_best_split_point(self, text: str, ideal_pos: int) -> int:
        """寻找最佳分割点"""
        search_range = int(self.target_chunk_size * 0.2)
        start_search = max(0, ideal_pos - search_range)
        end_search = min(len(text), ideal_pos + search_range)
        
        for i in range(ideal_pos, end_search):
            if i < len(text) and text[i] in self.sentence_endings:
                return i + 1
        
        for i in range(ideal_pos - 1, start_search, -1):
            if i >= 0 and text[i] in self.sentence_endings:
                return i + 1
        
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
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
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


class SimpleRAG:
    """简化版RAG"""
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("初始化 简化版 RAG 系统")
        logger.info("=" * 60)
        
        self.splitter = DynamicSemanticSplitter(
            target_chunk_size=512,
            min_chunk_size=256,
            max_chunk_size=1024,
            overlap_ratio=0.1
        )
        logger.info("✓ 动态语义分割器初始化完成")
        
        self.bm25_retriever = BM25Retriever()
        logger.info("✓ BM25检索器初始化完成")
        
        self.local_chunks: List[DocumentChunk] = []
        
        logger.info("=" * 60)
        logger.info("简化版 RAG 系统初始化完成")
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
            
            chunks = self.splitter.split(content, file_name, page_number)
            logger.info(f"文档分割完成，共 {len(chunks)} 个块")
            
            self.local_chunks.extend(chunks)
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
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
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
        
        # 动态选择TopK
        total_docs = len(set(c.source_file for c in self.local_chunks))
        if total_docs > 3:
            k = min(top_k, 3)
        else:
            k = min(top_k + 2, 5)
        
        results = self.bm25_retriever.search(query, top_k=k)
        logger.info(f"检索完成，共 {len(results)} 个结果")
        
        formatted_results = []
        for result in results:
            chunk = result[0]
            formatted_results.append({
                'content': chunk.content,
                'source': {
                    'file_name': chunk.source_file,
                    'page_number': chunk.page_number,
                    'chunk_index': chunk.chunk_index,
                    'position': f"{chunk.start_pos}-{chunk.end_pos}"
                },
                'scores': {
                    'bm25': round(result[1], 4)
                }
            })
        
        return {
            'query': query,
            'results': formatted_results,
            'top_k': k,
            'total_chunks': len(self.local_chunks)
        }


def test_simple_rag():
    """测试简化版RAG"""
    print("\n" + "=" * 60)
    print("测试 简化版 RAG 系统")
    print("=" * 60)
    
    rag = SimpleRAG()
    
    # 创建测试文档
    test_doc_path = "test_document.txt"
    test_content = """
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。

机器学习是AI的核心技术之一。它使计算机能够从数据中学习，而无需明确编程。深度学习是机器学习的一个子集，使用神经网络来处理复杂的数据模式。

自然语言处理（NLP）是AI的另一个重要领域。它使计算机能够理解、解释和生成人类语言。应用包括机器翻译、情感分析和聊天机器人。

计算机视觉让机器能够"看"和理解图像及视频。应用包括人脸识别、自动驾驶和医学影像分析。

AI的伦理问题也日益受到关注，包括隐私保护、算法偏见和就业影响等方面。
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
        
        queries = [
            "什么是机器学习",
            "深度学习",
            "自然语言处理的应用"
        ]
        
        for query in queries:
            print(f"\n查询: {query}")
            result = rag.search(query)
            
            print(f"返回 {result['top_k']} 个结果:")
            for i, item in enumerate(result['results'], 1):
                print(f"\n[{i}] 内容: {item['content'][:80]}...")
                print(f"    来源: {item['source']['file_name']} (页{item['source']['page_number']})")
                print(f"    分数: BM25={item['scores']['bm25']}")
    
    # 清理
    if os.path.exists(test_doc_path):
        os.remove(test_doc_path)
        print(f"\n清理测试文件: {test_doc_path}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_simple_rag()
