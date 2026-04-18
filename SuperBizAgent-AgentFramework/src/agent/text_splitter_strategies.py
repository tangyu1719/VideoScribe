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
import statistics

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
                 max_chunk_size: int = 1000,
                 dynamic_max_chars: int = 800,
                 lap_overlap_sentences: int = 1,
                 valley_prominence_ratio: float = 0.85):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.dynamic_max_chars = dynamic_max_chars
        self.lap_overlap_sentences = max(0, int(lap_overlap_sentences))
        self.valley_prominence_ratio = valley_prominence_ratio
        self.separators = ['\n\n', '\n', '。', '！', '？', '. ', '! ', '? ']
    
    @property
    def name(self) -> str:
        return "动态语义聚类分割"
    
    @property
    def description(self) -> str:
        return "句边界+语义极小值切分，超长块动态二次切分并句级lap重叠"

    def _compute_similarity_profile(self, sentences: List[Tuple[str, int, int]], embeddings: np.ndarray) -> Dict[str, Any]:
        """计算句间相似度曲线，并给出局部极小值与动态阈值。"""
        similarities: List[float] = []
        for i in range(len(sentences) - 1):
            similarities.append(self._cosine_similarity(embeddings[i], embeddings[i + 1]))

        if not similarities:
            return {
                "similarities": [],
                "valleys": set(),
                "mean_diff": 0.0,
                "adaptive_prominence": 0.0
            }

        diffs = [abs(similarities[i] - similarities[i - 1]) for i in range(1, len(similarities))]
        mean_diff = float(statistics.mean(diffs)) if diffs else 0.0
        adaptive_prominence = max(0.02, mean_diff * self.valley_prominence_ratio)

        valleys = set()
        for j in range(len(similarities)):
            curr = similarities[j]
            left = similarities[j - 1] if j - 1 >= 0 else None
            right = similarities[j + 1] if j + 1 < len(similarities) else None

            if left is None and right is not None:
                if curr + adaptive_prominence < right:
                    valleys.add(j + 1)
            elif right is None and left is not None:
                if curr + adaptive_prominence < left:
                    valleys.add(j + 1)
            elif left is not None and right is not None:
                if curr + adaptive_prominence < min(left, right):
                    valleys.add(j + 1)

        return {
            "similarities": similarities,
            "valleys": valleys,
            "mean_diff": mean_diff,
            "adaptive_prominence": adaptive_prominence
        }

    def _build_chunk_with_lap(
        self,
        text: str,
        sentences: List[Tuple[str, int, int]],
        start_idx: int,
        end_idx: int
    ) -> Tuple[str, int, int]:
        """按句子索引构建块，并在前后做句级lap重叠。"""
        lap = self.lap_overlap_sentences
        lap_start = max(0, start_idx - lap)
        lap_end = min(len(sentences) - 1, end_idx + lap)

        start_pos = sentences[lap_start][1]
        end_pos = sentences[lap_end][2]
        chunk_text = text[start_pos:end_pos].strip()
        return chunk_text, start_pos, end_pos

    def _split_oversized_chunk(
        self,
        text: str,
        sentences: List[Tuple[str, int, int]],
        start_idx: int,
        end_idx: int,
        profile: Dict[str, Any]
    ) -> List[Tuple[int, int]]:
        """对超过dynamic_max_chars的块做二次动态分割，优先使用子区间语义极小值。"""
        ranges: List[Tuple[int, int]] = []
        cursor = start_idx
        valleys: set = profile.get("valleys", set())

        while cursor <= end_idx:
            # 先尝试按dynamic_max_chars推进
            char_count = 0
            forced_end = cursor
            while forced_end <= end_idx:
                char_count += len(sentences[forced_end][0])
                if char_count > self.dynamic_max_chars:
                    break
                forced_end += 1

            if forced_end > end_idx:
                ranges.append((cursor, end_idx))
                break

            # forced_end 当前是超界句子，下一个切分点应在 [cursor+1, forced_end]
            candidate_cuts = [
                idx for idx in valleys
                if cursor < idx <= min(end_idx, forced_end)
            ]
            if candidate_cuts:
                cut = candidate_cuts[-1]  # 选择靠后的语义谷，减少碎片
                ranges.append((cursor, cut - 1))
                cursor = cut
            else:
                ranges.append((cursor, forced_end - 1))
                cursor = forced_end

        return ranges
    
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
        
        min_chunk_size = kwargs.get('min_chunk_size', self.min_chunk_size)
        dynamic_max_chars = kwargs.get('dynamic_max_chars', self.dynamic_max_chars)
        
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
        
        # 3. 相似度曲线 + 极小值检测（带平均差动态精度控制）
        profile = self._compute_similarity_profile(sentences, embeddings)
        similarities = profile["similarities"]
        valleys = profile["valleys"]
        logger.info(
            "【动态语义分割】相似度样本=%s, mean_diff=%.4f, adaptive_prominence=%.4f, valley_count=%d",
            [round(v, 4) for v in similarities[:10]],
            profile["mean_diff"],
            profile["adaptive_prominence"],
            len(valleys)
        )

        # 4. 先按语义极小值粗分
        coarse_ranges: List[Tuple[int, int]] = []
        start_idx = 0
        for cut_idx in sorted(valleys):
            if cut_idx <= start_idx:
                continue
            char_count = sum(len(sentences[k][0]) for k in range(start_idx, cut_idx))
            if char_count >= min_chunk_size:
                coarse_ranges.append((start_idx, cut_idx - 1))
                start_idx = cut_idx
        if start_idx <= len(sentences) - 1:
            coarse_ranges.append((start_idx, len(sentences) - 1))

        # 5. 对超过dynamic_max_chars的块二次分割（>800）
        final_ranges: List[Tuple[int, int]] = []
        for s_idx, e_idx in coarse_ranges:
            char_count = sum(len(sentences[k][0]) for k in range(s_idx, e_idx + 1))
            if char_count > dynamic_max_chars:
                final_ranges.extend(self._split_oversized_chunk(text, sentences, s_idx, e_idx, profile))
            else:
                final_ranges.append((s_idx, e_idx))

        # 6. 组装最终块：前后一句lap重叠
        chunks = []
        for idx, (s_idx, e_idx) in enumerate(final_ranges, start=1):
            chunk_text, start_pos, end_pos = self._build_chunk_with_lap(text, sentences, s_idx, e_idx)
            if chunk_text:
                chunks.append((chunk_text, start_pos, end_pos))
                logger.info(
                    "  创建块 %d: 句子%d-%d, 长度%d, lap=%d句",
                    idx, s_idx, e_idx, len(chunk_text), self.lap_overlap_sentences
                )

        logger.info(f"【动态语义分割完成】共 {len(chunks)} 个块")
        return chunks

    def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """输出句间语义相似度与切分统计，便于调参与展示。"""
        if not text.strip():
            return {"error": "empty_text"}
        if not self.embedding_model:
            return {"error": "missing_embedding_model"}

        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            return {"sentence_count": len(sentences), "similarities": [], "valley_indices": [], "chunks": []}

        sentence_texts = [s[0] for s in sentences]
        embeddings = self.embedding_model.encode(
            sentence_texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        profile = self._compute_similarity_profile(sentences, embeddings)
        chunks = self.split(text, **kwargs)
        return {
            "sentence_count": len(sentences),
            "similarities": profile["similarities"],
            "valley_indices": sorted(list(profile["valleys"])),
            "mean_diff": profile["mean_diff"],
            "adaptive_prominence": profile["adaptive_prominence"],
            "chunks": [
                {"index": i + 1, "start": c[1], "end": c[2], "length": len(c[0])}
                for i, c in enumerate(chunks)
            ]
        }


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
