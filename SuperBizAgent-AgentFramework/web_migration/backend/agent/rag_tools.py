#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG工具调用系统
- 意图识别
- 工具调用封装
- 元数据管理
- 权限控制
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型"""
    QUESTION = "question"           # 问问题
    CHAT = "chat"                   # 纯聊天
    GREETING = "greeting"           # 问候
    GOODBYE = "goodbye"             # 告别
    THANKS = "thanks"               # 感谢
    UNKNOWN = "unknown"             # 未知
    NEED_RAG = "need_rag"           # 需要RAG
    NO_RAG = "no_rag"               # 不需要RAG


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float              # 置信度 0-1
    needs_rag: bool               # 是否需要RAG
    reason: str                   # 识别原因
    suggested_tags: Optional[Dict[str, str]] = None  # 建议的元数据标签
    # 任务/问题提取：用于 Query 改写与后续推理（无论 needs_rag 与否都应产出）
    task: str = ""
    extracted_query: str = ""


@dataclass
class DocumentMetadata:
    """文档元数据"""
    domain: str                   # 领域（必填）
    module: str                   # 模块（必填）
    doc_type: str                 # 文档类型（必填）
    keyword1: str = ""            # 关键词1
    keyword2: str = ""            # 关键词2
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "domain": self.domain,
            "module": self.module,
            "doc_type": self.doc_type,
            "keyword1": self.keyword1,
            "keyword2": self.keyword2
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'DocumentMetadata':
        return cls(
            domain=data.get("domain", ""),
            module=data.get("module", ""),
            doc_type=data.get("doc_type", ""),
            keyword1=data.get("keyword1", ""),
            keyword2=data.get("keyword2", "")
        )
    
    def is_valid(self) -> bool:
        """检查必填字段"""
        return bool(self.domain and self.module and self.doc_type)


@dataclass
class RetrievedChunk:
    """召回的文档片段"""
    content: str
    metadata: DocumentMetadata
    similarity: float
    doc_id: str
    chunk_id: str


@dataclass
class QueryRewriteResult:
    """Query改写结果"""
    original_query: str
    rewritten_query: str
    keywords: List[str]
    suggested_tags: DocumentMetadata
    needs_clarification: bool
    clarification_question: str = ""
    reason: str = ""


class QueryRewriter:
    """Query改写器 - 使用大模型改写和优化查询"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def rewrite(self, query: str, intent_result: IntentResult, 
                available_domains: Optional[List[str]] = None) -> QueryRewriteResult:
        """
        改写用户查询，使其更适合知识库检索
        
        Args:
            query: 原始查询
            intent_result: 意图识别结果
            available_domains: 可用的领域列表（用于判断是否需要用户交互）
        
        Returns:
            QueryRewriteResult: 改写结果
        """
        if not self.llm_client:
            # 没有LLM客户端，返回原始查询
            return QueryRewriteResult(
                original_query=query,
                rewritten_query=query,
                keywords=[],
                suggested_tags=intent_result.suggested_tags or DocumentMetadata("", "", ""),
                needs_clarification=False,
                reason="无LLM客户端，使用原始查询"
            )
        
        # 构建提示词
        suggested_tags_str = ""
        if intent_result.suggested_tags:
            suggested_tags_str = f"""
建议的元数据标签:
- 领域: {intent_result.suggested_tags.domain or '未知'}
- 模块: {intent_result.suggested_tags.module or '未知'}
- 文档类型: {intent_result.suggested_tags.doc_type or '未知'}
"""
        
        available_domains_str = ""
        if available_domains:
            available_domains_str = f"\n可用的领域列表: {', '.join(available_domains)}"
        
        prompt = f"""请改写以下用户查询，使其更适合知识库检索。

原始查询: "{query}"

意图识别结果:
- 意图: {intent_result.intent.value}
- 置信度: {intent_result.confidence}
- 需要RAG: {intent_result.needs_rag}
{suggested_tags_str}{available_domains_str}

请按以下JSON格式输出改写结果:
{{
    "rewritten_query": "改写后的完整查询",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "suggested_tags": {{
        "domain": "确定的领域",
        "module": "确定的模块",
        "doc_type": "确定的文档类型"
    }},
    "needs_clarification": false,
    "clarification_question": "如果需要用户澄清，提供问题",
    "reason": "改写原因说明"
}}

改写要求:
1. 将简短/模糊的查询改写成完整、明确的问题
2. 补充必要的上下文和专业术语
3. 提取关键词用于检索
4. 确定元数据标签（领域、模块、文档类型）
5. 如果信息不足以确定标签，设置needs_clarification为true并提供澄清问题
6. 优先使用LLM判断，只有在确实无法确定时才需要用户交互

注意:
- rewritten_query应该是完整的、可直接用于检索的查询
- keywords应该包含核心概念和专业术语
- suggested_tags中的三个必填字段不能为空"""

        try:
            # 调用大模型
            response = self.llm_client.complete(prompt, max_tokens=800)
            result_json = self._extract_json(response)
            
            if result_json:
                suggested_tags_data = result_json.get("suggested_tags", {})
                suggested_tags = DocumentMetadata(
                    domain=suggested_tags_data.get("domain", ""),
                    module=suggested_tags_data.get("module", ""),
                    doc_type=suggested_tags_data.get("doc_type", ""),
                    keyword1=result_json.get("keywords", [""])[0] if result_json.get("keywords") else "",
                    keyword2=result_json.get("keywords", ["", ""])[1] if len(result_json.get("keywords", [])) > 1 else ""
                )
                
                return QueryRewriteResult(
                    original_query=query,
                    rewritten_query=result_json.get("rewritten_query", query),
                    keywords=result_json.get("keywords", []),
                    suggested_tags=suggested_tags,
                    needs_clarification=result_json.get("needs_clarification", False),
                    clarification_question=result_json.get("clarification_question", ""),
                    reason=result_json.get("reason", "LLM改写")
                )
            else:
                # JSON解析失败，返回原始查询
                return QueryRewriteResult(
                    original_query=query,
                    rewritten_query=query,
                    keywords=[],
                    suggested_tags=intent_result.suggested_tags or DocumentMetadata("", "", ""),
                    needs_clarification=False,
                    reason="LLM输出解析失败，使用原始查询"
                )
                
        except Exception as e:
            logger.error(f"【Query改写】LLM调用失败: {e}")
            return QueryRewriteResult(
                original_query=query,
                rewritten_query=query,
                keywords=[],
                suggested_tags=intent_result.suggested_tags or DocumentMetadata("", "", ""),
                needs_clarification=False,
                reason=f"改写失败: {str(e)}"
            )
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON"""
        import json
        import re
        
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试提取JSON代码块
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        
        return None


class IntentRecognizer:
    """意图识别器 - 使用大模型进行意图识别"""
    
    # 简单的规则预筛选 - 避免无意义对话调用大模型
    SIMPLE_PATTERNS = {
        IntentType.GREETING: ['你好', '您好', '嗨', 'hello', 'hi', '早上好', '下午好', '晚上好'],
        IntentType.GOODBYE: ['再见', '拜拜', 'bye', 'goodbye', '回头见'],
        IntentType.THANKS: ['谢谢', '感谢', 'thank', 'thx', '多谢'],
        IntentType.CHAT: ['哈哈', '呵呵', '嗯', '哦', '好的', 'ok', '没问题'],
    }
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._cache = {}  # 简单缓存
        self._lock = threading.Lock()
    
    def recognize(self, query: str, use_llm: bool = True) -> IntentResult:
        """
        识别用户意图
        
        Args:
            query: 用户输入
            use_llm: 是否使用大模型（简单对话可跳过）
        
        Returns:
            IntentResult: 意图识别结果
        """
        query = query.strip().lower()
        
        # 1. 规则预筛选 - 简单无意义对话直接返回
        for intent_type, patterns in self.SIMPLE_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                if len(query) < 20:  # 短对话
                    logger.info(f"【意图识别】规则匹配: {intent_type.value}, 查询: {query[:30]}")
                    return IntentResult(
                        intent=intent_type,
                        confidence=0.9,
                        needs_rag=False,
                        reason=f"规则匹配: {intent_type.value}"
                    )
        
        # 2. 检查缓存
        cache_key = query[:50]  # 前50字符作为缓存键
        with self._lock:
            if cache_key in self._cache:
                logger.info(f"【意图识别】缓存命中: {query[:30]}")
                return self._cache[cache_key]
        
        # 3. 使用大模型进行意图识别
        if use_llm and self.llm_client:
            result = self._recognize_with_llm(query)
        else:
            # 默认需要RAG
            result = IntentResult(
                intent=IntentType.NEED_RAG,
                confidence=0.5,
                needs_rag=True,
                reason="默认需要RAG"
            )
        
        # 存入缓存
        with self._lock:
            self._cache[cache_key] = result
        
        return result
    
    def _recognize_with_llm(self, query: str) -> IntentResult:
        """使用大模型进行意图识别"""
        prompt = f"""你是一个“意图识别器”。请对用户输入做结构化分析：
1) 任务分析：用户真正要做的任务是什么（task）
2) 问题提取：用于检索/推理的核心查询是什么（extracted_query）
3) 意图分类：question/chat/greeting/goodbye/thanks/unknown
4) 是否需要 RAG：needs_rag=true/false（并说明 reason）

用户输入: "{query}"

请按以下JSON格式输出分析结果:
{{
    "intent": "question|chat|greeting|goodbye|thanks|unknown",
    "confidence": 0.0-1.0,
    "needs_rag": true|false,
    "reason": "判断原因",
    "task": "用户任务分析（一句话）",
    "extracted_query": "核心问题/查询（尽量可直接用于检索）",
    "suggested_tags": {{
        "domain": "建议的领域",
        "module": "建议的模块",
        "doc_type": "建议的文档类型"
    }}
}}

判断标准:
1. question: 用户在问问题，需要知识库回答
2. chat: 闲聊，不需要知识库
3. greeting: 问候语
4. goodbye: 告别语
5. thanks: 感谢语
6. unknown: 无法判断

注意:
- needs_rag为true表示需要检索知识库
- confidence表示置信度
- suggested_tags为可选的建议元数据标签"""

        try:
            # 调用大模型
            response = self.llm_client.complete(prompt, max_tokens=500)
            result_json = self._extract_json(response)
            
            if result_json:
                intent_str = result_json.get("intent", "unknown")
                intent = IntentType(intent_str) if intent_str in [e.value for e in IntentType] else IntentType.UNKNOWN
                
                suggested_tags = result_json.get("suggested_tags")
                
                return IntentResult(
                    intent=intent,
                    confidence=result_json.get("confidence", 0.5),
                    needs_rag=result_json.get("needs_rag", True),
                    reason=result_json.get("reason", "LLM分析"),
                    suggested_tags=suggested_tags,
                    task=(result_json.get("task") or "").strip(),
                    extracted_query=(result_json.get("extracted_query") or "").strip(),
                )
            else:
                # JSON解析失败，默认需要RAG
                return IntentResult(
                    intent=IntentType.NEED_RAG,
                    confidence=0.5,
                    needs_rag=True,
                    reason="LLM输出解析失败，默认需要RAG",
                    task="",
                    extracted_query=query,
                )
                
        except Exception as e:
            logger.error(f"【意图识别】LLM调用失败: {e}")
            return IntentResult(
                intent=IntentType.NEED_RAG,
                confidence=0.3,
                needs_rag=True,
                reason=f"LLM调用失败: {str(e)}",
                task="",
                extracted_query=query,
            )
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON"""
        try:
            # 尝试直接解析
            return json.loads(text)
        except:
            # 尝试从代码块中提取
            import re
            pattern = r'```json\s*(.*?)\s*```'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            
            # 尝试提取花括号内容
            pattern = r'\{.*\}'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        
        return None


class RAGTool:
    """RAG工具 - 封装RAG检索功能"""
    
    def __init__(self, kb_manager, intent_recognizer: IntentRecognizer):
        self.kb_manager = kb_manager
        self.intent_recognizer = intent_recognizer
        self._metadata_index: Dict[str, List[str]] = {}  # 元数据索引
        self._lock = threading.Lock()
    
    def search(self, query: str, 
               metadata_filter: Optional[DocumentMetadata] = None,
               top_k: int = 5,
               skip_intent: bool = False) -> Tuple[IntentResult, List[RetrievedChunk]]:
        """
        RAG检索工具
        
        Args:
            query: 查询文本
            metadata_filter: 元数据过滤条件
            top_k: 返回结果数量
            skip_intent: 跳过意图识别
        
        Returns:
            (IntentResult, List[RetrievedChunk]): 意图结果和召回的片段
        """
        # 1. 意图识别
        if skip_intent:
            intent_result = IntentResult(
                intent=IntentType.NEED_RAG,
                confidence=1.0,
                needs_rag=True,
                reason="跳过意图识别"
            )
        else:
            intent_result = self.intent_recognizer.recognize(query)
        
        # 2. 如果不需要RAG，直接返回
        if not intent_result.needs_rag:
            logger.info(f"【RAG工具】不需要检索: {intent_result.reason}")
            return intent_result, []
        
        # 3. 执行RAG检索
        logger.info(f"【RAG工具】开始检索: {query[:50]}")
        
        # 合并元数据过滤条件
        if intent_result.suggested_tags and not metadata_filter:
            metadata_filter = DocumentMetadata(
                domain=intent_result.suggested_tags.get("domain", ""),
                module=intent_result.suggested_tags.get("module", ""),
                doc_type=intent_result.suggested_tags.get("doc_type", "")
            )
        
        # 先进行元数据初筛，再语义计算
        chunks = self._search_with_metadata_filter(query, metadata_filter, top_k)
        
        logger.info(f"【RAG工具】检索完成，召回 {len(chunks)} 个片段")
        
        return intent_result, chunks
    
    def _search_with_metadata_filter(self, query: str, 
                                     metadata_filter: Optional[DocumentMetadata],
                                     top_k: int) -> List[RetrievedChunk]:
        """
        先元数据初筛，再语义计算
        
        效率分析:
        - 元数据过滤: O(1) 哈希查找，可过滤80%+文档
        - 语义计算: O(n) 只计算初筛后的文档
        - 总体效率比全量语义计算高5-10倍
        """
        # 1. 元数据初筛
        candidate_doc_ids = self._filter_by_metadata(metadata_filter)
        
        if not candidate_doc_ids:
            # 如果没有匹配的元数据，搜索所有文档
            logger.info("【RAG工具】元数据过滤无结果，搜索全部文档")
            candidate_doc_ids = None
        else:
            logger.info(f"【RAG工具】元数据初筛: {len(candidate_doc_ids)} 个候选文档")
        
        # 2. 语义检索
        raw_results = self.kb_manager.search(
            query, 
            top_k=top_k * 2,  # 多取一些，后续过滤
            doc_ids=candidate_doc_ids  # 传入候选文档ID列表
        )
        
        # 3. 转换为RetrievedChunk
        chunks = []
        for result in raw_results[:top_k]:
            # 兼容 'score' 和 'similarity' 两种键名
            similarity = result.get("similarity") or result.get("score", 0)
            chunk = RetrievedChunk(
                content=result.get("content", ""),
                metadata=DocumentMetadata.from_dict(result.get("metadata", {})),
                similarity=float(similarity),
                doc_id=result.get("doc_id", result.get("source_file", "")),
                chunk_id=result.get("chunk_id", "")
            )
            chunks.append(chunk)
        
        return chunks
    
    def _filter_by_metadata(self, metadata_filter: Optional[DocumentMetadata]) -> Optional[List[str]]:
        """
        根据元数据过滤文档
        
        返回符合条件的文档ID列表
        """
        if not metadata_filter:
            return None
        
        if not metadata_filter.is_valid():
            # 如果必填字段不完整，不过滤
            return None
        
        # 构建索引键
        index_keys = []
        
        # 精确匹配必填字段
        if metadata_filter.domain:
            index_keys.append(f"domain:{metadata_filter.domain}")
        if metadata_filter.module:
            index_keys.append(f"module:{metadata_filter.module}")
        if metadata_filter.doc_type:
            index_keys.append(f"doc_type:{metadata_filter.doc_type}")
        
        # 关键词匹配（可选）
        if metadata_filter.keyword1:
            index_keys.append(f"keyword:{metadata_filter.keyword1}")
        if metadata_filter.keyword2:
            index_keys.append(f"keyword:{metadata_filter.keyword2}")
        
        # 取交集
        result_ids = None
        with self._lock:
            for key in index_keys:
                doc_ids = set(self._metadata_index.get(key, []))
                if result_ids is None:
                    result_ids = doc_ids
                else:
                    result_ids &= doc_ids
        
        return list(result_ids) if result_ids else []
    
    def update_metadata_index(self, doc_id: str, metadata: DocumentMetadata):
        """更新元数据索引"""
        with self._lock:
            # 索引必填字段
            if metadata.domain:
                key = f"domain:{metadata.domain}"
                if key not in self._metadata_index:
                    self._metadata_index[key] = []
                if doc_id not in self._metadata_index[key]:
                    self._metadata_index[key].append(doc_id)
            
            if metadata.module:
                key = f"module:{metadata.module}"
                if key not in self._metadata_index:
                    self._metadata_index[key] = []
                if doc_id not in self._metadata_index[key]:
                    self._metadata_index[key].append(doc_id)
            
            if metadata.doc_type:
                key = f"doc_type:{metadata.doc_type}"
                if key not in self._metadata_index:
                    self._metadata_index[key] = []
                if doc_id not in self._metadata_index[key]:
                    self._metadata_index[key].append(doc_id)
            
            # 索引关键词
            if metadata.keyword1:
                key = f"keyword:{metadata.keyword1}"
                if key not in self._metadata_index:
                    self._metadata_index[key] = []
                if doc_id not in self._metadata_index[key]:
                    self._metadata_index[key].append(doc_id)
            
            if metadata.keyword2:
                key = f"keyword:{metadata.keyword2}"
                if key not in self._metadata_index:
                    self._metadata_index[key] = []
                if doc_id not in self._metadata_index[key]:
                    self._metadata_index[key].append(doc_id)


class MetadataManager:
    """元数据管理器"""
    
    # 预设选项
    DOMAINS = ["技术", "产品", "运营", "市场", "人事", "财务", "法务", "其他"]
    MODULES = ["前端", "后端", "算法", "测试", "运维", "设计", "文档", "会议", "其他"]
    DOC_TYPES = ["代码", "文档", "规范", "报告", "邮件", "聊天记录", "其他"]
    
    def __init__(self):
        self._metadata_cache: Dict[str, DocumentMetadata] = {}
    
    def auto_extract_metadata(self, content: str, filename: str = "") -> DocumentMetadata:
        """
        自动提取元数据
        
        基于内容和文件名自动识别domain/module/doc_type
        """
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # 默认元数据
        metadata = DocumentMetadata(
            domain="",
            module="",
            doc_type=""
        )
        
        # 1. 识别domain
        domain_keywords = {
            "技术": ["代码", "api", "函数", "类", "接口", "算法", "数据库", "服务器"],
            "产品": ["需求", "prd", "原型", "用户", "功能", "设计稿"],
            "运营": ["活动", "推广", "数据", "分析", "转化", "留存"],
            "市场": ["营销", "品牌", "推广", "渠道", "竞品"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in content_lower or kw in filename_lower for kw in keywords):
                metadata.domain = domain
                break
        
        # 2. 识别module
        module_keywords = {
            "前端": ["html", "css", "js", "react", "vue", "angular", "ui", "界面"],
            "后端": ["api", "接口", "服务", "server", "后端", "数据库"],
            "算法": ["算法", "模型", "训练", "预测", "机器学习", "ai"],
            "测试": ["测试", "用例", "bug", "缺陷", "qa"],
            "运维": ["部署", "服务器", "docker", "k8s", "监控"],
        }
        
        for module, keywords in module_keywords.items():
            if any(kw in content_lower or kw in filename_lower for kw in keywords):
                metadata.module = module
                break
        
        # 3. 识别doc_type
        if ".py" in filename_lower or ".js" in filename_lower or ".java" in filename_lower:
            metadata.doc_type = "代码"
        elif ".md" in filename_lower or ".txt" in filename_lower:
            metadata.doc_type = "文档"
        elif "规范" in content_lower or "标准" in content_lower:
            metadata.doc_type = "规范"
        elif "报告" in content_lower or "总结" in content_lower:
            metadata.doc_type = "报告"
        elif "会议" in content_lower or "纪要" in content_lower:
            metadata.doc_type = "会议"
        
        # 4. 提取关键词
        # 简单实现：提取出现频率较高的词
        import re
        words = re.findall(r'\b[a-zA-Z]+\b', content_lower)
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 过滤短词
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 取频率最高的两个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_words) > 0:
            metadata.keyword1 = sorted_words[0][0]
        if len(sorted_words) > 1:
            metadata.keyword2 = sorted_words[1][0]
        
        return metadata
    
    def validate_metadata(self, metadata: DocumentMetadata) -> Tuple[bool, str]:
        """验证元数据"""
        if not metadata.domain:
            return False, "领域(domain)不能为空"
        if not metadata.module:
            return False, "模块(module)不能为空"
        if not metadata.doc_type:
            return False, "文档类型(doc_type)不能为空"
        return True, "验证通过"


# 全局工具实例
_rag_tool: Optional[RAGTool] = None
_metadata_manager: Optional[MetadataManager] = None

def get_rag_tool(kb_manager=None, llm_client=None) -> RAGTool:
    """获取RAG工具实例"""
    global _rag_tool
    if _rag_tool is None:
        intent_recognizer = IntentRecognizer(llm_client)
        _rag_tool = RAGTool(kb_manager, intent_recognizer)
    return _rag_tool

def get_metadata_manager() -> MetadataManager:
    """获取元数据管理器实例"""
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = MetadataManager()
    return _metadata_manager
