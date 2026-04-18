#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库管理模块 - 服务启动时初始化版本
解决原有问题：点击功能时才初始化改为服务启动时初始化
"""

import os
import json
import hashlib
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入多模态工具
try:
    from multimodal_tool import MultimodalTool, ContentType
    MULTIMODAL_AVAILABLE = True
    logger.info("[KB] 多模态工具加载成功")
except ImportError as e:
    MULTIMODAL_AVAILABLE = False
    logger.warning(f"[KB] 多模态工具未加载: {e}")

# 全局单例实例
_kb_instance = None

def get_knowledge_base():
    """获取知识库单例实例"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBaseManager()
    return _kb_instance


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


class KnowledgeBaseManager:
    """
    知识库管理器 - 服务启动时初始化
    
    设计原则：
    1. 服务启动时完成所有重量级初始化（嵌入模型加载）
    2. 用户点击功能时立即可用，无需等待
    3. 支持延迟加载索引数据（首次查询时）
    """
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.kb_dir = os.path.join(self.base_dir, "knowledge_base")
        self.index_file = os.path.join(self.kb_dir, "vector_index.json")
        self.chunks: List[DocumentChunk] = []
        self.embedding_model = None
        self.embedding_dim = 384
        self._initialized = False
        self._model_loaded = False
        
        # 创建知识库目录
        os.makedirs(self.kb_dir, exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("知识库管理器初始化开始...")
        logger.info("=" * 60)
        
        # 1. 先加载索引（获取保存的维度信息）
        self._load_index_sync()
        
        # 2. 初始化嵌入模型（重量级操作，服务启动时完成）
        # 如果索引中有维度信息，使用索引的维度
        self._init_embedding_model()
        
        # 3. 如果模型加载成功，更新维度
        if self._model_loaded:
            logger.info(f"[KB] 使用模型维度: {self.embedding_dim}")
        else:
            logger.info(f"[KB] 使用备用维度: {self.embedding_dim}")
        
        self._initialized = True
        
        logger.info("=" * 60)
        logger.info("✓ 知识库管理器初始化完成")
        logger.info(f"  - 嵌入维度: {self.embedding_dim}")
        logger.info(f"  - 文档块数: {len(self.chunks)}")
        logger.info(f"  - 模型状态: {'已加载' if self._model_loaded else '未加载'}")
        logger.info("=" * 60)
    
    def _init_embedding_model(self):
        """
        初始化嵌入模型 - 服务启动时完成
        这是重量级操作，需要在服务启动时完成，避免用户等待
        """
        try:
            # 尝试加载 sentence-transformers
            from sentence_transformers import SentenceTransformer as ST
            
            # 设置离线模式环境变量
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_DATASETS_OFFLINE'] = '1'
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            # 检查本地缓存
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            model_name = "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
            model_path = os.path.join(cache_dir, model_name)
            
            if os.path.exists(model_path):
                # 使用本地模型
                snapshots = os.listdir(os.path.join(model_path, "snapshots"))
                if snapshots:
                    model_full_path = os.path.join(model_path, "snapshots", snapshots[0])
                    logger.info(f"[KB] 加载本地嵌入模型: {model_full_path}")
                    
                    self.embedding_model = ST(
                        model_full_path,
                        cache_folder=cache_dir,
                        local_files_only=True
                    )
                    self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                    self._model_loaded = True
                    logger.info(f"[KB] ✓ 嵌入模型加载成功，维度: {self.embedding_dim}")
                else:
                    logger.warning("[KB] 本地模型snapshot不存在，使用备用方案")
                    self._use_fallback_embedding()
            else:
                logger.warning("[KB] 本地模型不存在，使用备用方案")
                self._use_fallback_embedding()
                
        except ImportError:
            logger.warning("[KB] sentence-transformers未安装，使用备用方案")
            self._use_fallback_embedding()
        except Exception as e:
            logger.error(f"[KB] 加载嵌入模型失败: {e}，使用备用方案")
            self._use_fallback_embedding()
    
    def _use_fallback_embedding(self):
        """使用备用词袋嵌入方案"""
        self.embedding_model = None
        self.embedding_dim = 100
        self._model_loaded = False
        logger.info("[KB] 使用词袋模型作为备用方案")
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的词袋嵌入（备用方案）"""
        words = text.lower().split()
        embedding = np.zeros(self.embedding_dim)
        
        for i, word in enumerate(words[:self.embedding_dim]):
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            embedding[i % self.embedding_dim] = hash_val % 1000 / 1000.0
        
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入向量"""
        if self.embedding_model is not None:
            try:
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                return embedding
            except Exception as e:
                logger.warning(f"[KB] 模型嵌入失败: {e}，使用备用方案")
        
        return self._simple_embedding(text)
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Tuple[str, int, int]]:
        """将文本分割成块"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # 尝试在句子边界处分割
            if end < len(text):
                for i in range(end - 1, start, -1):
                    if text[i] in '。！？.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))
            
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def _load_index_sync(self):
        """同步加载索引（轻量级操作）"""
        try:
            if not os.path.exists(self.index_file):
                logger.info("[KB] 索引文件不存在，将创建新索引")
                self.chunks = []
                return
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            self.embedding_dim = index_data.get('embedding_dim', 384)
            self.chunks = [DocumentChunk.from_dict(chunk_data) 
                          for chunk_data in index_data.get('chunks', [])]
            
            logger.info(f"[KB] 成功加载索引: {len(self.chunks)} 个文档块")
            
        except Exception as e:
            logger.error(f"[KB] 加载索引失败: {e}")
            self.chunks = []
    
    def add_document(self, file_path: str) -> Tuple[bool, str]:
        """
        添加文档到知识库
        
        Returns:
            (success, message)
        """
        try:
            # 检查文件
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}"
            
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.txt', '.md']:
                return False, f"不支持的文件格式: {file_ext}，仅支持 .txt 和 .md"
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return False, "文件内容为空"
            
            # 分割文本
            file_name = os.path.basename(file_path)
            text_chunks = self._split_text(content)
            
            # 生成嵌入
            for i, (chunk_text, start_pos, end_pos) in enumerate(text_chunks):
                chunk = DocumentChunk(
                    content=chunk_text,
                    source_file=file_name,
                    chunk_id=i,
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                chunk.embedding = self._generate_embedding(chunk_text)
                self.chunks.append(chunk)
            
            # 保存索引
            self._save_index()
            
            logger.info(f"[KB] 成功添加文档: {file_name}，共 {len(text_chunks)} 个块")
            return True, f"成功添加 {len(text_chunks)} 个向量块"
            
        except Exception as e:
            logger.error(f"[KB] 添加文档失败: {e}")
            return False, f"添加失败: {str(e)}"
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索知识库"""
        if not self.chunks:
            logger.warning("[KB] 知识库为空")
            return []
        
        try:
            # 生成查询嵌入
            query_embedding = self._generate_embedding(query)
            
            # 计算相似度
            similarities = []
            for chunk in self.chunks:
                if chunk.embedding is not None:
                    sim = self._cosine_similarity(query_embedding, chunk.embedding)
                    similarities.append((chunk, sim))
            
            # 排序并返回top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
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
            logger.error(f"[KB] 搜索失败: {e}")
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _save_index(self):
        """保存索引到文件"""
        try:
            index_data = {
                'embedding_dim': self.embedding_dim,
                'chunks': [chunk.to_dict() for chunk in self.chunks],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[KB] 索引已保存: {self.index_file}")
            
        except Exception as e:
            logger.error(f"[KB] 保存索引失败: {e}")
    
    def save_index(self):
        """公共方法：保存索引（兼容旧版API）"""
        self._save_index()
    
    def delete_document(self, file_name: str) -> bool:
        """删除文档及其向量块"""
        try:
            original_count = len(self.chunks)
            self.chunks = [c for c in self.chunks if c.source_file != file_name]
            removed_count = original_count - len(self.chunks)
            
            if removed_count > 0:
                self._save_index()
                logger.info(f"[KB] 删除文档 {file_name}，移除 {removed_count} 个向量块")
                return True
            return False
            
        except Exception as e:
            logger.error(f"[KB] 删除文档失败: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        source_files = list(set(chunk.source_file for chunk in self.chunks))
        
        # 获取最后更新时间
        updated_at = "N/A"
        if os.path.exists(self.index_file):
            try:
                mtime = os.path.getmtime(self.index_file)
                updated_at = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        return {
            'total_chunks': len(self.chunks),
            'total_files': len(source_files),
            'embedding_dim': self.embedding_dim,
            'source_files': source_files,
            'model_loaded': self._model_loaded,
            'initialized': self._initialized,
            'index_file': self.index_file,
            'updated_at': updated_at
        }
    
    def is_ready(self) -> bool:
        """检查知识库是否已就绪"""
        return self._initialized


# 健康检查函数
def health_check() -> Dict:
    """知识库健康检查"""
    try:
        kb = get_knowledge_base()
        stats = kb.get_stats()
        
        return {
            'status': 'healthy' if kb.is_ready() else 'unhealthy',
            'initialized': stats['initialized'],
            'model_loaded': stats['model_loaded'],
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
    # 测试初始化
    print("测试知识库管理器初始化...")
    kb = get_knowledge_base()
    
    stats = kb.get_stats()
    print(f"\n知识库状态:")
    print(f"  - 初始化状态: {stats['initialized']}")
    print(f"  - 模型加载: {stats['model_loaded']}")
    print(f"  - 文档块数: {stats['total_chunks']}")
    print(f"  - 嵌入维度: {stats['embedding_dim']}")
    
    # 健康检查
    health = health_check()
    print(f"\n健康检查: {health}")
