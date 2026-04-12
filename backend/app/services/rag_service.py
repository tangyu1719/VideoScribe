#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG服务 - 从本地工具移植
包含意图识别、Query改写、元数据管理、语义检索等功能
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
    QUESTION = "question"
    CHAT = "chat"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    THANKS = "thanks"
    UNKNOWN = "unknown"
    NEED_RAG = "need_rag"
    NO_RAG = "no_rag"


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float
    needs_rag: bool
    reason: str
    suggested_tags: Optional[Dict[str, str]] = None


@dataclass
class DocumentMetadata:
    """文档元数据"""
    domain: str
    module: str
    doc_type: str
    keyword1: str = ""
    keyword2: str = ""
    
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


class LLMClient:
    """LLM客户端封装"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def complete(self, prompt: str, max_tokens: int = 500) -> str:
        """调用LLM完成请求"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"LLM API调用失败: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"LLM API调用异常: {e}")
            return ""


class QueryRewriter:
    """Query改写器 - 使用大模型改写和优化查询"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
    
    def rewrite(self, query: str, intent_result: IntentResult,
                available_domains: Optional[List[str]] = None) -> QueryRewriteResult:
        """
        改写用户查询，使其更适合知识库检索
        
        Args:
            query: 原始查询
            intent_result: 意图识别结果
            available_domains: 可用的领域列表
        
        Returns:
            QueryRewriteResult: 改写结果
        """
        if not self.llm_client:
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
- 领域: {intent_result.suggested_tags.get('domain', '未知')}
- 模块: {intent_result.suggested_tags.get('module', '未知')}
- 文档类型: {intent_result.suggested_tags.get('doc_type', '未知')}
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
            r'\{.*\}'
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
    
    # 简单的规则预筛选
    SIMPLE_PATTERNS = {
        IntentType.GREETING: ['你好', '您好', '嗨', 'hello', 'hi', '早上好', '下午好', '晚上好'],
        IntentType.GOODBYE: ['再见', '拜拜', 'bye', 'goodbye', '回头见'],
        IntentType.THANKS: ['谢谢', '感谢', 'thank', 'thx', '多谢'],
        IntentType.CHAT: ['哈哈', '呵呵', '嗯', '哦', '好的', 'ok', '没问题'],
    }
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self._cache = {}
        self._lock = threading.Lock()
    
    def recognize(self, query: str, use_llm: bool = True) -> IntentResult:
        """
        识别用户意图
        
        Args:
            query: 用户输入
            use_llm: 是否使用大模型
        
        Returns:
            IntentResult: 意图识别结果
        """
        query = query.strip().lower()
        
        # 1. 规则预筛选
        for intent_type, patterns in self.SIMPLE_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                if len(query) < 20:
                    logger.info(f"【意图识别】规则匹配: {intent_type.value}, 查询: {query[:30]}")
                    return IntentResult(
                        intent=intent_type,
                        confidence=0.9,
                        needs_rag=False,
                        reason=f"规则匹配: {intent_type.value}"
                    )
        
        # 2. 检查缓存
        cache_key = query[:50]
        with self._lock:
            if cache_key in self._cache:
                logger.info(f"【意图识别】缓存命中: {query[:30]}")
                return self._cache[cache_key]
        
        # 3. 使用大模型进行意图识别
        if use_llm and self.llm_client:
            result = self._recognize_with_llm(query)
        else:
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
        prompt = f"""请分析以下用户输入的意图，并判断是否需要检索知识库。

用户输入: "{query}"

请按以下JSON格式输出分析结果:
{{
    "intent": "question|chat|greeting|goodbye|thanks|unknown",
    "confidence": 0.0-1.0,
    "needs_rag": true|false,
    "reason": "判断原因",
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
                    suggested_tags=suggested_tags
                )
            else:
                return IntentResult(
                    intent=IntentType.NEED_RAG,
                    confidence=0.5,
                    needs_rag=True,
                    reason="LLM输出解析失败，默认需要RAG"
                )
                
        except Exception as e:
            logger.error(f"【意图识别】LLM调用失败: {e}")
            return IntentResult(
                intent=IntentType.NEED_RAG,
                confidence=0.3,
                needs_rag=True,
                reason=f"LLM调用失败: {str(e)}"
            )
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON"""
        import re
        
        try:
            return json.loads(text)
        except:
            pattern = r'```json\s*(.*?)\s*```'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            
            pattern = r'\{.*\}'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        
        return None


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
        import re
        words = re.findall(r'\b[a-zA-Z]+\b', content_lower)
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
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


class RAGService:
    """RAG服务 - 封装RAG检索功能"""
    
    def __init__(self, kb_manager=None, llm_client: Optional[LLMClient] = None):
        """
        初始化RAG服务
        
        Args:
            kb_manager: 知识库管理器
            llm_client: LLM客户端
        """
        self.kb_manager = kb_manager
        self.intent_recognizer = IntentRecognizer(llm_client)
        self.query_rewriter = QueryRewriter(llm_client)
        self.metadata_manager = MetadataManager()
        self._metadata_index: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
    
    def search(self, query: str,
               metadata_filter: Optional[DocumentMetadata] = None,
               top_k: int = 5,
               skip_intent: bool = False) -> Tuple[IntentResult, List[RetrievedChunk]]:
        """
        RAG检索
        
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
            logger.info(f"【RAG服务】不需要检索: {intent_result.reason}")
            return intent_result, []
        
        # 3. Query改写
        rewrite_result = self.query_rewriter.rewrite(query, intent_result)
        
        if rewrite_result.needs_clarification:
            logger.info(f"【RAG服务】需要用户澄清: {rewrite_result.clarification_question}")
            return intent_result, []
        
        # 4. 执行RAG检索
        logger.info(f"【RAG服务】开始检索: {rewrite_result.rewritten_query[:50]}")
        
        # 合并元数据过滤条件
        if rewrite_result.suggested_tags and not metadata_filter:
            metadata_filter = rewrite_result.suggested_tags
        
        # 先进行元数据初筛，再语义计算
        chunks = self._search_with_metadata_filter(rewrite_result.rewritten_query, metadata_filter, top_k)
        
        logger.info(f"【RAG服务】检索完成，召回 {len(chunks)} 个片段")
        
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
        if not self.kb_manager:
            logger.warning("【RAG服务】知识库管理器未初始化")
            return []
        
        # 1. 元数据初筛
        candidate_doc_ids = self._filter_by_metadata(metadata_filter)
        
        if not candidate_doc_ids:
            logger.info("【RAG服务】元数据过滤无结果，搜索全部文档")
            candidate_doc_ids = None
        else:
            logger.info(f"【RAG服务】元数据初筛: {len(candidate_doc_ids)} 个候选文档")
        
        # 2. 语义检索
        try:
            raw_results = self.kb_manager.search(
                query,
                top_k=top_k * 2,
                doc_ids=candidate_doc_ids
            )
        except Exception as e:
            logger.error(f"【RAG服务】语义检索失败: {e}")
            return []
        
        # 3. 转换为RetrievedChunk
        chunks = []
        for result in raw_results[:top_k]:
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
            return None
        
        # 构建索引键
        index_keys = []
        
        if metadata_filter.domain:
            index_keys.append(f"domain:{metadata_filter.domain}")
        if metadata_filter.module:
            index_keys.append(f"module:{metadata_filter.module}")
        if metadata_filter.doc_type:
            index_keys.append(f"doc_type:{metadata_filter.doc_type}")
        
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


# 便捷函数
def create_rag_service(kb_manager=None, llm_config: Optional[Dict] = None) -> RAGService:
    """创建RAG服务实例"""
    llm_client = None
    if llm_config:
        llm_client = LLMClient(
            api_key=llm_config.get('api_key', ''),
            base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
            model=llm_config.get('model', 'gpt-3.5-turbo')
        )
    return RAGService(kb_manager, llm_client)
