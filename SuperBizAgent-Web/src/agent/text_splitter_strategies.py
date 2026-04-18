#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本分割策略模块 - 策略模式实现

支持多种文本分割策略：
1. 固定窗口分割 (FixedWindowSplitter)
2. 句子边界分割 (SentenceBoundarySplitter) 
3. 动态窗口+语义聚类分割 (DynamicSemanticSplitter)
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TextSplitterStrategy(ABC):
    """文本分割策略接口"""
    
    @abstractmethod
    def split(self, text: str, **kwargs) -> List[Tuple[str, int, int]]:
        """
        分割文本
        
        Args:
            text: 要分割的文本
            **kwargs: 策略特定参数
            
        Returns:
            List[Tuple[str, int, int]]: [(chunk_text, start_pos, end_pos), ...]
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass


class FixedWindowSplitter(TextSplitterStrategy):
    """固定窗口分割策略"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    @property
    def name(self) -> str:
        return "固定窗口分割"
    
    @property
    def description(self) -> str:
        return f"按固定大小({self.chunk_size}字符)分割，重叠{self.overlap}字符"
    
    def split(self, text: str, **kwargs) -> List[Tuple[str, int, int]]:
        """固定窗口分割"""
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        overlap = kwargs.get('overlap', self.overlap)
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))
            start = end - overlap if end < text_len else end
        
        logger.info(f"【固定窗口分割】文本长度: {text_len}, 生成 {len(chunks)} 个块")
        return chunks


class SentenceBoundarySplitter(TextSplitterStrategy):
    """句子边界分割策略 - 优化版"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = ['\n\n', '\n', '。', '！', '？', '. ', '! ', '? ', ' ']
    
    @property
    def name(self) -> str:
        return "句子边界分割"
    
    @property
    def description(self) -> str:
        return f"在句子边界分割，最大块大小{self.chunk_size}字符"
    
    def split(self, text: str, **kwargs) -> List[Tuple[str, int, int]]:
        """在句子边界分割"""
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        overlap = kwargs.get('overlap', self.overlap)
        
        chunks = []
        start = 0
        text_len = len(text)
        max_iterations = text_len // overlap + 100
        iterations = 0
        
        logger.info(f"【句子边界分割】文本长度: {text_len}，块大小: {chunk_size}")
        
        while start < text_len and iterations < max_iterations:
            iterations += 1
            end = min(start + chunk_size, text_len)
            
            # 在句子边界分割
            if end < text_len:
                found_sep = False
                for sep in self.separators:
                    pos = text.rfind(sep, start, end)
                    if pos != -1 and pos > start:
                        end = pos + len(sep)
                        found_sep = True
                        break
                
                if not found_sep:
                    end = min(start + chunk_size, text_len)
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))
            
            advance = max(end - overlap, start + 10)
            start = advance if advance > start else end
            
            if end >= text_len:
                break
        
        logger.info(f"【句子边界分割完成】共 {len(chunks)} 个块")
        return chunks


class DynamicSemanticSplitter(TextSplitterStrategy):
    """
    动态窗口 + 语义聚类分割策略
    
    核心思想: 根据语义边界动态调整窗口大小，对相似内容聚类保留上下文连贯性
    """
    
    def __init__(self, 
                 embedding_model=None,
                 chunk_size: int = 500,
                 overlap: int = 50,
                 similarity_threshold: float = 0.7,
                 min_chunk_size: int = 100,
                 max_chunk_size: int = 1000):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.separators = ['\n\n', '\n', '。', '！', '？', '. ', '! ', '? ']
    
    @property
    def name(self) -> str:
        return "动态语义聚类分割"
    
    @property
    def description(self) -> str:
        return "根据语义相似度动态调整窗口，保持上下文连贯性"
    
    def _split_into_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """将文本分割为句子"""
        sentences = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # 找下一个句子边界
            end = text_len
            for sep in self.separators:
                pos = text.find(sep, start)
                if pos != -1 and pos < end:
                    end = pos + len(sep)
            
            if end == text_len and start < text_len:
                # 最后一个句子
                sentence = text[start:].strip()
                if sentence:
                    sentences.append((sentence, start, text_len))
                break
            
            sentence = text[start:end].strip()
            if sentence:
                sentences.append((sentence, start, end))
            
            start = end
        
        return sentences
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)
    
    def split(self, text: str, **kwargs) -> List[Tuple[str, int, int]]:
        """
        动态语义分割 - 真正的语义边界检测
        
        核心逻辑:
        1. 先按句子分割
        2. 每句递推计算语义相似度
        3. 在语义极小值处切断（语义边界）
        4. 如果段落>500字符，则在500字符后的下一个句号处切断
        """
        if not self.embedding_model:
            logger.warning("【动态语义分割】没有提供embedding模型，回退到句子边界分割")
            fallback = SentenceBoundarySplitter(self.chunk_size, self.overlap)
            return fallback.split(text, **kwargs)
        
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        
        logger.info(f"【动态语义分割】文本长度: {len(text)}")
        
        # 1. 句子级分割
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            return [(text, 0, len(text))] if text.strip() else []
        
        logger.info(f"【动态语义分割】拆分为 {len(sentences)} 个句子")
        
        # 2. 获取每个句子的Embedding
        try:
            sentence_texts = [s[0] for s in sentences]
            embeddings = self.embedding_model.encode(
                sentence_texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
        except Exception as e:
            logger.error(f"【动态语义分割】Embedding生成失败: {e}")
            fallback = SentenceBoundarySplitter(self.chunk_size, self.overlap)
            return fallback.split(text, **kwargs)
        
        # 3. 计算相邻句子的语义相似度
        similarities = []
        for i in range(len(sentences) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
            logger.debug(f"  句子{i}与{i+1}相似度: {sim:.3f}")
        
        # 4. 检测语义边界（相似度极小值）
        # 同时考虑：语义边界 和 大小限制
        chunks = []
        chunk_start_idx = 0  # 当前块的起始句子索引
        current_chunk_char_count = len(sentences[0][0])  # 当前块的字符数
        
        for i in range(1, len(sentences)):
            sentence_len = len(sentences[i][0])
            
            # 判断是否需要切断
            should_cut = False
            cut_reason = ""
            
            # 条件1: 语义边界检测（相似度极小值）
            if i < len(similarities):
                # 检测局部极小值（比前后都小）
                is_local_min = False
                if i == 1:
                    # 第一个相似度，只需要比后一个小
                    is_local_min = similarities[0] < similarities[1] * 0.9
                elif i == len(similarities):
                    # 最后一个，只需要比前一个小
                    is_local_min = similarities[-1] < similarities[-2] * 0.9
                else:
                    # 中间的，比前后都小
                    is_local_min = (similarities[i-1] < similarities[i-2] * 0.9 and 
                                   similarities[i-1] < similarities[i] * 0.9)
                
                if is_local_min and current_chunk_char_count >= self.min_chunk_size:
                    should_cut = True
                    cut_reason = f"语义边界(相似度{similarities[i-1]:.3f})"
            
            # 条件2: 大小限制 - 如果超过chunk_size，在下一句号处切断
            if current_chunk_char_count + sentence_len > chunk_size:
                should_cut = True
                cut_reason = f"大小限制({current_chunk_char_count}+{sentence_len}>{chunk_size})"
            
            if should_cut:
                # 保存当前块
                start_pos = sentences[chunk_start_idx][1]
                end_pos = sentences[i-1][2] if i > 0 else sentences[0][2]
                chunk_text = text[start_pos:end_pos].strip()
                
                if chunk_text:
                    chunks.append((chunk_text, start_pos, end_pos))
                    logger.info(f"  创建块 {len(chunks)}: 句子{chunk_start_idx}-{i-1}, "
                               f"长度{len(chunk_text)}, 原因: {cut_reason}")
                
                # 开始新块
                chunk_start_idx = i
                current_chunk_char_count = sentence_len
            else:
                # 继续当前块
                current_chunk_char_count += sentence_len
        
        # 处理最后一个块
        if chunk_start_idx < len(sentences):
            start_pos = sentences[chunk_start_idx][1]
            end_pos = sentences[-1][2]
            chunk_text = text[start_pos:end_pos].strip()
            
            if chunk_text:
                chunks.append((chunk_text, start_pos, end_pos))
                logger.info(f"  创建块 {len(chunks)}: 句子{chunk_start_idx}-{len(sentences)-1}, "
                           f"长度{len(chunk_text)} (最后块)")
        
        logger.info(f"【动态语义分割完成】共 {len(chunks)} 个块")
        return chunks


class TextSplitterFactory:
    """文本分割策略工厂"""
    
    _strategies: Dict[str, type] = {
        'fixed_window': FixedWindowSplitter,
        'sentence_boundary': SentenceBoundarySplitter,
        'dynamic_semantic': DynamicSemanticSplitter,
    }
    
    @classmethod
    def get_strategy(cls, strategy_name: str, **kwargs) -> TextSplitterStrategy:
        """
        获取分割策略实例
        
        Args:
            strategy_name: 策略名称 ('fixed_window', 'sentence_boundary', 'dynamic_semantic')
            **kwargs: 策略参数
            
        Returns:
            TextSplitterStrategy: 策略实例
        """
        if strategy_name not in cls._strategies:
            logger.warning(f"未知策略 '{strategy_name}'，使用默认的句子边界分割")
            strategy_name = 'sentence_boundary'
        
        strategy_class = cls._strategies[strategy_name]
        return strategy_class(**kwargs)
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """注册新策略"""
        cls._strategies[name] = strategy_class
    
    @classmethod
    def list_strategies(cls) -> Dict[str, str]:
        """列出所有可用策略"""
        return {
            name: cls._strategies[name]().description 
            for name in cls._strategies.keys()
        }
