#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答系统 - 基于RAG和火山引擎的Reasoning-Acting模式
角色：资深Java和AI应用开发专家
主模型：Doubao-Seed-2.0-mini (ep-20260411182220-jv5qt)
备用模型：Doubao-Seed-2.0-mini (ep-20260320202115-9jqfp)
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Generator
import threading

# 导入RAG知识库
try:
    from kb_manager_advanced import get_advanced_knowledge_base
    KB_AVAILABLE = True
    print("[AIChat] 使用高级知识库管理器 (BGE-Large)")
except ImportError as e:
    KB_AVAILABLE = False
    print(f"[AIChat] 知识库管理器未加载: {e}")


class AIChatSystem:
    """
    AI问答系统
    
    核心功能：
    1. Reasoning-Acting模式：先思考，再行动（检索），再回答
    2. RAG增强：基于知识库的检索增强生成
    3. 角色扮演：Java和AI应用开发专家
    4. 支持知识库开关控制
    5. 支持多模型切换（主模型+备用模型）
    """
    
    # 模型配置
    PRIMARY_MODEL = "ep-20260411182220-jv5qt"  # 主接入点：Doubao-Seed-2.0-mini
    FALLBACK_MODEL = "ep-20260320202115-9jqfp"  # 备用接入点：Doubao-Seed-2.0-mini
    
    def __init__(self, base_dir: str = None, use_fallback_model: bool = False):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        
        # 初始化知识库
        self.kb = None
        if KB_AVAILABLE:
            try:
                self.kb = get_advanced_knowledge_base()
                print(f"[AIChat] 知识库初始化成功")
            except Exception as e:
                print(f"[AIChat] 知识库初始化失败: {e}")
        
        # 火山引擎API配置
        self.api_key = os.environ.get('VOLC_API_KEY', '5da00752-8f46-44eb-b162-5c52f2a249b3')
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3"
        
        # 选择模型（主模型或备用模型）
        self.use_fallback = use_fallback_model
        self.model = self.FALLBACK_MODEL if use_fallback_model else self.PRIMARY_MODEL
        print(f"[AIChat] 使用模型: {self.model} {'(备用)' if use_fallback_model else '(主模型)'}")
        
        # 角色设定
        self.system_prompt = self._get_expert_prompt()
        
        # 对话历史
        self.chat_history: List[Dict] = []
        self.max_history = 10
        
        # 统计信息
        self.total_queries = 0
        self.total_tokens = 0
    
    def switch_model(self, use_fallback: bool = False):
        """切换模型（主模型/备用模型）"""
        self.use_fallback = use_fallback
        self.model = self.FALLBACK_MODEL if use_fallback else self.PRIMARY_MODEL
        print(f"[AIChat] 已切换到: {self.model} {'(备用)' if use_fallback else '(主模型)'}")
        return self.model
    
    def _get_expert_prompt(self) -> str:
        """
        专家角色设定
        资深Java和AI应用开发专家
        """
        return """你是一位资深的Java和AI应用开发专家，拥有以下专业背景：

【技术专长】
1. Java生态：精通Spring Boot、Spring Cloud、JVM调优、高并发架构设计
2. AI应用开发：熟悉LangChain、向量数据库、RAG系统、模型微调
3. 高并发系统：精通分布式架构、缓存策略、消息队列、微服务
4. 工程实践：代码重构、性能优化、系统设计、技术选型

【回答风格】
1. 技术深度：提供具体的技术细节和最佳实践
2. 实用性：给出可落地的代码示例和架构建议
3. 系统性：从架构层面分析问题，提供完整解决方案
4. 前瞻性：结合最新技术趋势，提供演进建议

【知识库引用规范】
当使用知识库内容回答时，请：
1. 明确标注引用来源（文档名称）
2. 结合知识库内容和你的专业知识综合回答
3. 如果知识库内容不足，补充你的专业见解

请基于以上角色设定回答用户问题。"""
    
    def chat_with_knowledge_base(self, user_query: str, use_kb: bool = True, top_k: int = 5) -> Generator[str, None, None]:
        """
        支持知识库的聊天对话
        
        Args:
            user_query: 用户问题
            use_kb: 是否使用知识库
            top_k: 检索结果数量
            
        Yields:
            流式返回回答内容
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[AIChat] 开始处理查询: {user_query[:50]}...")
            
            # 知识库检索
            kb_context = ""
            kb_results = []
            if use_kb and self.kb and self.kb.is_ready():
                logger.info("[AIChat] 检索知识库...")
                yield "🔍 **正在检索知识库...**\n\n"
                
                kb_results = self.kb.search(user_query, top_k=top_k)
                
                if kb_results:
                    yield f"✅ **找到 {len(kb_results)} 个相关文档片段**\n\n"
                    
                    # 构建知识库上下文
                    context_parts = []
                    for i, result in enumerate(kb_results, 1):
                        source = result.get('source_file', '未知来源')
                        content = result.get('content', '')
                        score = result.get('score', 0)
                        context_parts.append(f"[文档{i}] 来源: {source} (相关度: {score:.2f})\n{content}")
                    
                    kb_context = "\n\n".join(context_parts)
                    
                    # 显示检索结果摘要
                    for i, result in enumerate(kb_results, 1):
                        source = result.get('source_file', '未知来源')
                        score = result.get('score', 0)
                        yield f"📄 **文档{i}** - {source} (相关度: {score:.2f})\n"
                    
                    yield "\n---\n\n"
                else:
                    yield "⚠️ **知识库中未找到相关内容，将基于通用知识回答**\n\n"
            
            # 生成回答
            logger.info("[AIChat] 调用API生成回答...")
            yield "🤖 **生成回答...**\n\n"
            
            # 构建完整提示词
            full_prompt = self._build_prompt_with_kb(user_query, kb_context)
            
            # 调用API
            for chunk in self._call_volcengine_api(full_prompt):
                yield chunk
            
            # 记录对话历史
            self._add_to_history(user_query, "回答已生成")
            self.total_queries += 1
            
        except Exception as e:
            logger.error(f"[AIChat] 处理出错: {str(e)}")
            yield f"\n\n❌ **错误**: {str(e)}"
    
    def _build_prompt_with_kb(self, user_query: str, kb_context: str = "") -> str:
        """构建包含知识库上下文的提示词"""
        prompt_parts = [self.system_prompt]
        
        # 添加知识库上下文
        if kb_context:
            prompt_parts.append(f"\n【知识库参考内容】\n{kb_context}\n")
            prompt_parts.append("请基于以上知识库内容回答用户问题，如果知识库内容不足以完整回答，请补充你的专业知识。")
        
        # 添加对话历史
        if self.chat_history:
            prompt_parts.append("\n【对话历史】")
            for msg in self.chat_history[-self.max_history:]:
                role = "用户" if msg['role'] == 'user' else "助手"
                prompt_parts.append(f"{role}: {msg['content'][:100]}...")
        
        # 添加当前问题
        prompt_parts.append(f"\n【当前问题】\n{user_query}")
        
        # 添加回答要求
        prompt_parts.append("""

【回答要求】
1. 基于提供的参考文档（如果有）和你的专业知识回答
2. 提供具体的代码示例或架构建议
3. 解释技术原理和最佳实践
4. 如果涉及多个方案，对比优缺点并给出推荐
5. 使用Markdown格式，包含代码块、列表等

请给出详细的技术回答：""")
        
        return "\n".join(prompt_parts)
    
    def _call_volcengine_api(self, prompt: str) -> Generator[str, None, None]:
        """
        调用火山引擎API（流式输出）
        使用 Doubao-Seed-2.0-mini 模型
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[API] 开始调用火山引擎API，模型: {self.model}")
            
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
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 4096
            }
            
            logger.info(f"[API] 请求URL: {self.api_url}/chat/completions")
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = f"API错误: {response.status_code} - {response.text[:200]}"
                logger.error(f"[API] {error_msg}")
                yield f"\n\n❌ {error_msg}"
                return
            
            logger.info("[API] 开始接收流式响应...")
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data)
                            choices = chunk.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    yield content
                        except json.JSONDecodeError:
                            continue
            
            logger.info(f"[API] 流式响应完成，总长度: {len(full_response)}")
            self.total_tokens += len(full_response) + len(prompt)
            
        except Exception as e:
            logger.error(f"[API] 调用失败: {str(e)}")
            yield f"\n\n❌ API调用失败: {str(e)}"
    
    def _add_to_history(self, user_msg: str, assistant_msg: str):
        """添加对话到历史"""
        self.chat_history.append({
            'role': 'user',
            'content': user_msg,
            'timestamp': datetime.now().isoformat()
        })
        self.chat_history.append({
            'role': 'assistant',
            'content': assistant_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持历史记录在限制范围内
        if len(self.chat_history) > self.max_history * 2:
            self.chat_history = self.chat_history[-self.max_history * 2:]
    
    def clear_history(self):
        """清空对话历史"""
        self.chat_history = []
        print("对话历史已清空")
    
    def get_stats(self) -> Dict:
        """获取系统统计信息"""
        kb_stats = {}
        if self.kb:
            kb_stats = self.kb.get_stats()
        
        return {
            'kb_stats': kb_stats,
            'total_queries': self.total_queries,
            'total_tokens': self.total_tokens,
            'history_length': len(self.chat_history) // 2,
            'model': self.model,
            'kb_available': self.kb is not None and self.kb.is_ready()
        }


# 简单测试
if __name__ == "__main__":
    print("=" * 60)
    print("AI问答系统测试 - Doubao-Seed-2.0-mini")
    print("=" * 60)
    
    chat_system = AIChatSystem()
    
    # 显示统计
    stats = chat_system.get_stats()
    print(f"\n系统状态:")
    print(f"- 模型: {stats['model']}")
    print(f"- 知识库可用: {stats['kb_available']}")
    if stats['kb_available']:
        print(f"- 文档块数: {stats['kb_stats'].get('total_chunks', 0)}")
    
    # 测试问答
    test_queries = [
        "什么是RAG系统？",
        "如何优化Java高并发系统？"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"问题: {query}")
        print('='*60)
        
        for chunk in chat_system.chat_with_knowledge_base(query, use_kb=True):
            print(chunk, end='', flush=True)
        
        print("\n")
