#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答系统 - 基于RAG和火山引擎的Reasoning-Acting模式
角色：资深Java和AI应用开发专家
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Generator
import threading

# 导入RAG知识库
try:
    from rag_knowledge_base_v2 import RAGKnowledgeBaseV2
    RAG_AVAILABLE = True
except ImportError:
    from rag_knowledge_base import RAGKnowledgeBase
    RAG_AVAILABLE = True
    print("使用V1版本RAG知识库")


class AIChatSystem:
    """
    AI问答系统
    
    核心功能：
    1. Reasoning-Acting模式：先思考，再行动（检索），再回答
    2. RAG增强：基于知识库的检索增强生成
    3. 角色扮演：Java和AI应用开发专家
    """
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        
        # 初始化RAG知识库
        try:
            self.kb = RAGKnowledgeBaseV2(self.base_dir)
        except:
            self.kb = RAGKnowledgeBase(self.base_dir)
        
        # 火山引擎API配置
        self.api_key = "5da00752-8f46-44eb-b162-5c52f2a249b3"
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.model = "Doubao-Seed-2.0-Code"
        
        # 角色设定
        self.system_prompt = self._get_expert_prompt()
        
        # 对话历史
        self.chat_history: List[Dict] = []
        self.max_history = 10
        
        # 统计信息
        self.total_queries = 0
        self.total_tokens = 0
    
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

【使用工具】
你可以使用以下工具来辅助回答：
- search_knowledge_base: 搜索知识库获取相关文档内容
- analyze_code: 分析代码片段
- suggest_architecture: 提供架构设计建议

【回答流程】
1. 理解用户问题的技术背景
2. 如有需要，搜索知识库获取相关上下文
3. 结合专业知识和检索结果给出回答
4. 提供具体的代码示例或架构图

请基于以上角色设定回答用户问题。"""
    
    def reasoning_acting_chat(self, user_query: str, use_rag: bool = True) -> Generator[str, None, None]:
        """
        Reasoning-Acting模式的对话
        
        流程：
        1. Reasoning：分析问题，决定是否需要检索
        2. Acting：执行检索（如果需要）
        3. Answering：基于检索结果生成回答
        
        Yields:
            流式返回回答内容
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[AIChat] 开始处理查询: {user_query[:50]}...")
            
            # Step 1: Reasoning - 分析问题
            logger.info("[AIChat] Step 1: 分析问题")
            yield "🔍 **分析问题中...**\n\n"
            time.sleep(0.5)
            
            # 判断是否需要检索知识库
            need_search = self._should_search_knowledge_base(user_query)
            logger.info(f"[AIChat] 是否需要检索: {need_search}")
            
            context = ""
            if use_rag and need_search:
                # Step 2: Acting - 检索知识库
                logger.info("[AIChat] Step 2: 检索知识库")
                yield "📚 **检索知识库...**\n\n"
                
                search_results = self.kb.search(user_query, top_k=3)
                logger.info(f"[AIChat] 检索完成，找到 {len(search_results)} 个结果")
                
                if search_results:
                    yield f"✅ **找到 {len(search_results)} 个相关文档片段**\n\n"
                    
                    # 构建上下文
                    context_parts = []
                    for i, result in enumerate(search_results, 1):
                        context_parts.append(f"[文档{i}] 来源: {result['source_file']}\n{result['content']}")
                    
                    context = "\n\n".join(context_parts)
                    
                    # 显示检索到的内容摘要
                    for i, result in enumerate(search_results, 1):
                        yield f"📄 **文档{i}** (相似度: {result['score']:.2f})\n"
                        yield f"```\n{result['content'][:150]}...\n```\n\n"
                else:
                    yield "⚠️ **知识库中未找到相关内容，将基于通用知识回答**\n\n"
            
            # Step 3: Answering - 生成回答
            logger.info("[AIChat] Step 3: 调用API生成回答")
            yield "🤖 **生成回答...**\n\n"
            yield "---\n\n"
            
            # 构建完整提示词
            full_prompt = self._build_prompt(user_query, context)
            logger.info(f"[AIChat] 提示词长度: {len(full_prompt)}")
            
            # 调用火山引擎API生成回答
            api_chunk_count = 0
            for chunk in self._call_volcengine_api(full_prompt):
                api_chunk_count += 1
                yield chunk
            
            logger.info(f"[AIChat] API调用完成，共 {api_chunk_count} 个chunks")
            
            # 记录对话历史
            self._add_to_history(user_query, "完整回答已生成")
            self.total_queries += 1
            logger.info("[AIChat] 对话历史已更新")
            
        except Exception as e:
            logger.error(f"[AIChat] 处理出错: {str(e)}")
            yield f"\n\n❌ **错误**: {str(e)}"
    
    def _should_search_knowledge_base(self, query: str) -> bool:
        """
        判断是否需要搜索知识库
        
        策略：
        - 技术问题需要检索
        - 代码相关问题需要检索
        - 简单问候不需要检索
        """
        # 技术关键词
        tech_keywords = [
            'java', 'spring', '代码', '架构', '设计', '优化', '性能',
            '并发', '线程', 'jvm', '微服务', '分布式', '数据库',
            'ai', '模型', '向量', 'rag', '嵌入', 'llm',
            '框架', '实现', '方案', '问题', 'bug', '错误'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in tech_keywords)
    
    def _build_prompt(self, user_query: str, context: str = "") -> str:
        """构建完整的提示词"""
        prompt_parts = [self.system_prompt]
        
        # 添加检索到的上下文
        if context:
            prompt_parts.append(f"\n【参考文档】\n{context}\n")
        
        # 添加对话历史（最近几轮）
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
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[API] 开始调用火山引擎API，模型: {self.model}")
            logger.info(f"[API] API URL: {self.api_url}")
            logger.info(f"[API] API Key: {self.api_key[:10]}...")
            
            from volcenginesdkarkruntime import Ark
            
            logger.info("[API] 正在创建Ark客户端...")
            client = Ark(
                base_url=self.api_url,
                api_key=self.api_key,
            )
            logger.info("[API] Ark客户端创建成功")
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}]
                }
            ]
            logger.info(f"[API] 消息构建完成，长度: {len(prompt)}")
            
            # 流式调用
            logger.info("[API] 开始调用API...")
            response = client.responses.create(
                model=self.model,
                input=messages,
                stream=True  # 启用流式输出
            )
            logger.info("[API] API调用成功，开始接收流式响应...")
            
            full_response = ""
            event_count = 0
            for event in response:
                event_count += 1
                if hasattr(event, 'text'):
                    text = event.text
                    full_response += text
                    yield text
                elif hasattr(event, 'delta'):
                    delta = event.delta
                    if hasattr(delta, 'content'):
                        for content in delta.content:
                            if hasattr(content, 'text'):
                                text = content.text
                                full_response += text
                                yield text
            
            logger.info(f"[API] 流式响应完成，共 {event_count} 个events")
            
            # 记录token使用量（估算）
            self.total_tokens += len(full_response) + len(prompt)
            
        except Exception as e:
            yield f"\n\nAPI调用失败: {str(e)}\n"
            yield "请检查网络连接和API配置。"
    
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
        kb_stats = self.kb.get_stats()
        return {
            'kb_stats': kb_stats,
            'total_queries': self.total_queries,
            'total_tokens': self.total_tokens,
            'history_length': len(self.chat_history) // 2,
            'model': self.model
        }
    
    def index_output_documents(self) -> int:
        """
        索引output目录中的所有文档
        
        Returns:
            成功索引的文档数量
        """
        output_dir = os.path.join(self.base_dir, "output")
        if not os.path.exists(output_dir):
            print(f"输出目录不存在: {output_dir}")
            return 0
        
        indexed_count = 0
        print(f"\n开始索引文档...")
        
        for filename in os.listdir(output_dir):
            if filename.endswith('.txt') or filename.endswith('.md'):
                file_path = os.path.join(output_dir, filename)
                print(f"索引: {filename}")
                if self.kb.add_document(file_path):
                    indexed_count += 1
        
        print(f"\n成功索引 {indexed_count} 个文档")
        return indexed_count


# 简单测试
if __name__ == "__main__":
    print("=" * 60)
    print("AI问答系统测试")
    print("=" * 60)
    
    chat_system = AIChatSystem()
    
    # 显示统计
    stats = chat_system.get_stats()
    print(f"\n知识库状态:")
    print(f"- 文档块数: {stats['kb_stats']['total_chunks']}")
    print(f"- 向量库: {stats['kb_stats'].get('index_type', 'Unknown')}")
    
    # 索引文档
    chat_system.index_output_documents()
    
    # 测试问答
    test_queries = [
        "如何优化Java高并发系统？",
        "解释一下RAG系统的原理"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"问题: {query}")
        print('='*60)
        
        for chunk in chat_system.reasoning_acting_chat(query):
            print(chunk, end='', flush=True)
        
        print("\n")
