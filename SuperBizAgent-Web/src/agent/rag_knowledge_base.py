#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG知识库模块 - 基于向量索引的文档检索系统
功能：
1. 文档解析和文本分块
2. 向量嵌入生成和存储
3. 相似度检索
4. 与现有GUI集成
"""

import os
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import re

# 尝试导入sentence-transformers用于向量嵌入
SENTENCE_TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None

def _check_sentence_transformers():
    """检查sentence-transformers是否可用"""
    global SENTENCE_TRANSFORMERS_AVAILABLE, SentenceTransformer
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        return True
    try:
        from sentence_transformers import SentenceTransformer as ST
        SentenceTransformer = ST
        SENTENCE_TRANSFORMERS_AVAILABLE = True
        return True
    except ImportError:
        print("警告：sentence-transformers未安装，将使用简单的词袋模型")
        return False
    except Exception as e:
        print(f"警告：sentence-transformers加载失败: {e}，将使用简单的词袋模型")
        return False

# 尝试导入sklearn用于相似度计算
try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("警告：sklearn未安装，将使用简单的余弦相似度计算")


class DocumentChunk:
    """文档分块类"""
    def __init__(self, content: str, source_file: str, chunk_id: int, 
                 start_pos: int = 0, end_pos: int = 0):
        self.content = content
        self.source_file = source_file
        self.chunk_id = chunk_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.embedding = None
        self.created_at = datetime.now().isoformat()
        
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'source_file': self.source_file,
            'chunk_id': self.chunk_id,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'embedding': self.embedding.tolist() if self.embedding is not None else None,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DocumentChunk':
        chunk = cls(
            content=data['content'],
            source_file=data['source_file'],
            chunk_id=data['chunk_id'],
            start_pos=data.get('start_pos', 0),
            end_pos=data.get('end_pos', 0)
        )
        if data.get('embedding'):
            chunk.embedding = np.array(data['embedding'])
        chunk.created_at = data.get('created_at', datetime.now().isoformat())
        return chunk


class RAGKnowledgeBase:
    """RAG知识库主类"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(self.base_dir, "output")
        self.kb_dir = os.path.join(self.base_dir, "knowledge_base")
        self.index_file = os.path.join(self.kb_dir, "vector_index.json")
        self.chunks: List[DocumentChunk] = []
        self.embedding_model = None
        self.embedding_dim = 384  # 默认嵌入维度
        self._model_initialized = False  # 标记模型是否已初始化
        
        # 创建知识库目录
        os.makedirs(self.kb_dir, exist_ok=True)
        
        # 【优化】延迟初始化嵌入模型，先加载索引
        # 初始化嵌入模型移到 _ensure_model_initialized()
        
        # 加载现有索引
        self.load_index()
    
    def _init_embedding_model(self):
        """初始化嵌入模型 - 使用本地缓存的模型（离线模式）"""
        # 设置离线环境变量
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        
        # 检查本地是否有缓存的模型
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_name = "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
        model_path = os.path.join(cache_dir, model_name, "snapshots")
        
        if os.path.exists(model_path) and _check_sentence_transformers():
            try:
                # 找到snapshot目录
                snapshots = os.listdir(model_path)
                if snapshots:
                    model_full_path = os.path.join(model_path, snapshots[0])
                    print(f"使用本地模型: {model_full_path}")
                    
                    # 直接从本地路径加载模型
                    self.embedding_model = SentenceTransformer(model_full_path)
                    self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                    print(f"成功加载本地嵌入模型，维度: {self.embedding_dim}")
                else:
                    raise Exception("本地模型snapshot不存在")
            except Exception as e:
                print(f"加载本地模型失败: {e}，将使用备用方案")
                self.embedding_model = None
        else:
            print("本地模型不存在，将使用词袋模型")
            self.embedding_model = None
        
        if self.embedding_model is None:
            # 备用：使用简单的词袋模型
            self.embedding_dim = 100
            print("使用词袋模型作为备用方案")
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的词袋嵌入（备用方案）"""
        # 简单的字符级特征提取
        words = text.lower().split()
        embedding = np.zeros(self.embedding_dim)
        
        for i, word in enumerate(words[:self.embedding_dim]):
            # 使用单词的哈希值作为特征
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            embedding[i % self.embedding_dim] = hash_val % 1000 / 1000.0
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _ensure_model_initialized(self):
        """确保嵌入模型已初始化（延迟加载）"""
        if self._model_initialized:
            return
        
        print("[RAG] 首次使用，正在加载嵌入模型...")
        self._init_embedding_model()
        self._model_initialized = True
        print("[RAG] 嵌入模型加载完成")
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入向量"""
        # 延迟初始化模型
        self._ensure_model_initialized()
        
        if self.embedding_model is not None:
            try:
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                return embedding
            except Exception as e:
                print(f"模型嵌入失败: {e}，使用备用方案")
        
        return self._simple_embedding(text)
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Tuple[str, int, int]]:
        """
        将文本分割成块
        
        Args:
            text: 原始文本
            chunk_size: 每个块的大小（字符数）
            overlap: 块之间的重叠大小
            
        Returns:
            列表，每个元素为 (chunk_text, start_pos, end_pos)
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # 尝试在句子边界处分割
            if end < len(text):
                # 寻找最近的句号、问号或感叹号
                for i in range(end - 1, start, -1):
                    if text[i] in '。！？.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))
            
            # 移动起始位置，考虑重叠
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def add_document(self, file_path: str) -> bool:
        """
        添加文档到知识库
        
        Args:
            file_path: 文档路径
            
        Returns:
            是否成功添加
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return False
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"文件内容为空: {file_path}")
                return False
            
            # 分割文本
            file_name = os.path.basename(file_path)
            text_chunks = self._split_text(content)
            
            # 为每个块生成嵌入并保存
            for i, (chunk_text, start_pos, end_pos) in enumerate(text_chunks):
                chunk = DocumentChunk(
                    content=chunk_text,
                    source_file=file_name,
                    chunk_id=i,
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                
                # 生成嵌入向量
                chunk.embedding = self._generate_embedding(chunk_text)
                
                self.chunks.append(chunk)
                print(f"处理块 {i+1}/{len(text_chunks)}: {chunk_text[:50]}...")
            
            print(f"成功添加文档: {file_name}，共 {len(text_chunks)} 个块")
            
            # 保存索引
            self.save_index()
            
            return True
            
        except Exception as e:
            print(f"添加文档失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回最相关的k个结果
            
        Returns:
            搜索结果列表
        """
        if not self.chunks:
            print("知识库为空，请先添加文档")
            return []
        
        try:
            # 生成查询的嵌入向量
            query_embedding = self._generate_embedding(query)
            
            # 计算相似度
            similarities = []
            for chunk in self.chunks:
                if chunk.embedding is not None:
                    if SKLEARN_AVAILABLE:
                        # 使用sklearn的余弦相似度
                        sim = cosine_similarity(
                            query_embedding.reshape(1, -1),
                            chunk.embedding.reshape(1, -1)
                        )[0][0]
                    else:
                        # 手动计算余弦相似度
                        sim = self._cosine_similarity(query_embedding, chunk.embedding)
                    
                    similarities.append((chunk, sim))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 返回top_k结果
            results = []
            for chunk, score in similarities[:top_k]:
                results.append({
                    'content': chunk.content,
                    'source_file': chunk.source_file,
                    'chunk_id': chunk.chunk_id,
                    'score': float(score),
                    'start_pos': chunk.start_pos,
                    'end_pos': chunk.end_pos
                })
            
            return results
            
        except Exception as e:
            print(f"搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """手动计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def save_index(self):
        """保存向量索引到文件"""
        try:
            index_data = {
                'embedding_dim': self.embedding_dim,
                'chunks': [chunk.to_dict() for chunk in self.chunks],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            print(f"索引已保存: {self.index_file}")
            
        except Exception as e:
            print(f"保存索引失败: {e}")
    
    def load_index(self):
        """从文件加载向量索引"""
        try:
            if not os.path.exists(self.index_file):
                print("索引文件不存在，将创建新索引")
                return
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            self.embedding_dim = index_data.get('embedding_dim', 384)
            self.chunks = [DocumentChunk.from_dict(chunk_data) 
                          for chunk_data in index_data.get('chunks', [])]
            
            print(f"成功加载索引: {len(self.chunks)} 个文档块")
            
        except Exception as e:
            print(f"加载索引失败: {e}")
            self.chunks = []
    
    def clear_index(self):
        """清空索引"""
        self.chunks = []
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        print("索引已清空")
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        return {
            'total_chunks': len(self.chunks),
            'embedding_dim': self.embedding_dim,
            'source_files': list(set(chunk.source_file for chunk in self.chunks)),
            'index_file': self.index_file
        }


# 简单的命令行测试接口
if __name__ == "__main__":
    kb = RAGKnowledgeBase()
    
    print("=" * 50)
    print("RAG知识库系统")
    print("=" * 50)
    
    # 自动索引output目录中的所有文档
    output_dir = kb.output_dir
    if os.path.exists(output_dir):
        print(f"\n正在索引目录: {output_dir}")
        for filename in os.listdir(output_dir):
            if filename.endswith('.txt') or filename.endswith('.md'):
                file_path = os.path.join(output_dir, filename)
                kb.add_document(file_path)
    
    print(f"\n知识库统计:")
    stats = kb.get_stats()
    print(f"- 总块数: {stats['total_chunks']}")
    print(f"- 嵌入维度: {stats['embedding_dim']}")
    print(f"- 源文件: {stats['source_files']}")
    
    # 交互式搜索
    print("\n" + "=" * 50)
    print("输入查询内容（输入'quit'退出）:")
    print("=" * 50)
    
    while True:
        query = input("\n查询: ").strip()
        if query.lower() == 'quit':
            break
        
        if not query:
            continue
        
        results = kb.search(query, top_k=3)
        
        if results:
            print(f"\n找到 {len(results)} 个相关结果:")
            for i, result in enumerate(results, 1):
                print(f"\n[{i}] 相似度: {result['score']:.4f}")
                print(f"来源: {result['source_file']}")
                print(f"内容: {result['content'][:200]}...")
        else:
            print("未找到相关结果")
    
    print("\n再见!")
