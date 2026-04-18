#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReAct Agent 核心实现
ReAct = Reasoning (思考) + Acting (行动)

核心思想：
1. Thought: 分析当前状态和目标
2. Action: 决定调用什么工具
3. Observation: 获取工具返回结果
4. 循环直到得出最终答案

支持：
- 多次RAG检索（自适应）
- 查询重写优化
- 信息充分性判断
"""

import json
import re
import logging
from typing import List, Dict, Callable, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """动作类型"""
    SEARCH_KB = "search_kb"           # 搜索知识库
    REWRITE_QUERY = "rewrite_query"   # 重写查询
    GENERATE_ANSWER = "generate_answer"  # 生成答案
    NEED_MORE_INFO = "need_more_info"    # 需要更多信息
    FINAL_ANSWER = "final_answer"        # 最终答案


@dataclass
class Thought:
    """思考步骤"""
    step: int
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Action:
    """行动步骤"""
    step: int
    action_type: ActionType
    params: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Observation:
    """观察结果"""
    step: int
    content: str
    success: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReActStep:
    """ReAct单步记录"""
    step: int
    thought: Thought
    action: Action
    observation: Observation


class Tool:
    """工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **params) -> Tuple[str, bool]:
        """执行工具，返回 (结果, 是否成功)"""
        raise NotImplementedError


class SearchKBTool(Tool):
    """知识库搜索工具"""
    
    def __init__(self, kb_manager):
        super().__init__(
            name="search_kb",
            description="搜索知识库获取相关信息。参数: query (str), top_k (int, 默认5)"
        )
        self.kb_manager = kb_manager
    
    def execute(self, query: str, top_k: int = 5) -> Tuple[str, bool]:
        """执行知识库搜索"""
        try:
            results = self.kb_manager.search(query, top_k=top_k)
            
            if not results:
                return "未找到相关信息", True
            
            # 格式化结果
            formatted = []
            for i, result in enumerate(results, 1):
                formatted.append(
                    f"[{i}] 来源: {result['source_file']} "
                    f"(相关度: {result['score']:.3f})\n"
                    f"内容: {result['content'][:300]}..."
                )
            
            return "\n\n".join(formatted), True
            
        except Exception as e:
            return f"搜索失败: {str(e)}", False


class RewriteQueryTool(Tool):
    """查询重写工具"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="rewrite_query",
            description="重写查询以提高检索质量。参数: query (str)"
        )
        self.llm_client = llm_client
    
    def execute(self, query: str) -> Tuple[str, bool]:
        """重写查询"""
        try:
            # 简单的查询扩展策略
            expanded_queries = []
            
            # 1. 添加同义词/相关词
            keywords = self._extract_keywords(query)
            expanded_queries.append(f"{query} {' '.join(keywords)}")
            
            # 2. 添加问句变体
            if not query.endswith('?'):
                expanded_queries.append(f"什么是{query}？")
                expanded_queries.append(f"请解释{query}")
            
            # 3. 返回扩展后的查询
            result = f"原始查询: {query}\n\n扩展查询:\n" + "\n".join(f"- {q}" for q in expanded_queries)
            return result, True
            
        except Exception as e:
            return f"重写失败: {str(e)}", False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（去除停用词）
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        words = text.split()
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        return keywords[:5]  # 返回前5个关键词


class JudgeSufficiencyTool(Tool):
    """信息充分性判断工具"""
    
    def __init__(self):
        super().__init__(
            name="judge_sufficiency",
            description="判断当前信息是否足以回答问题。参数: question (str), context (str)"
        )
    
    def execute(self, question: str, context: str) -> Tuple[str, bool]:
        """判断信息充分性"""
        try:
            # 简单的启发式判断
            if not context or len(context) < 50:
                return "信息不足：上下文太短", True
            
            # 检查是否包含关键信息
            question_keywords = set(question.lower().split())
            context_keywords = set(context.lower().split())
            
            overlap = question_keywords & context_keywords
            coverage = len(overlap) / len(question_keywords) if question_keywords else 0
            
            if coverage < 0.3:
                return f"信息可能不足：关键词覆盖率仅{coverage:.1%}，建议继续检索", True
            
            if coverage >= 0.6:
                return f"信息充足：关键词覆盖率{coverage:.1%}", True
            
            return f"信息部分充足：关键词覆盖率{coverage:.1%}", True
            
        except Exception as e:
            return f"判断失败: {str(e)}", False


class ReActAgent:
    """
    ReAct Agent 核心实现
    
    执行循环：
    Thought → Action → Observation → (循环或结束)
    """
    
    def __init__(self, 
                 max_iterations: int = 5,
                 llm_client=None,
                 kb_manager=None):
        """
        Args:
            max_iterations: 最大迭代次数
            llm_client: LLM客户端（用于生成thought）
            kb_manager: 知识库管理器
        """
        self.max_iterations = max_iterations
        self.llm_client = llm_client
        self.kb_manager = kb_manager
        
        # 注册工具
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
        
        # 执行历史
        self.history: List[ReActStep] = []
        self.current_iteration = 0
        
        logger.info("[ReAct] Agent初始化完成")
    
    def _register_default_tools(self):
        """注册默认工具"""
        if self.kb_manager:
            self.register_tool(SearchKBTool(self.kb_manager))
        
        self.register_tool(RewriteQueryTool(self.llm_client))
        self.register_tool(JudgeSufficiencyTool())
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"[ReAct] 注册工具: {tool.name}")
    
    def run(self, question: str, context: str = "") -> Dict:
        """
        执行ReAct循环
        
        Args:
            question: 用户问题
            context: 已有上下文
            
        Returns:
            {
                'success': bool,
                'answer': str,
                'steps': List[ReActStep],
                'retrieval_count': int,
                'final_context': str
            }
        """
        logger.info(f"[ReAct] 开始处理: {question}")
        
        self.history = []
        self.current_iteration = 0
        accumulated_context = context
        retrieval_count = 0
        
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration + 1
            
            # 1. Thought: 思考当前状态
            thought = self._generate_thought(question, accumulated_context, iteration)
            logger.info(f"[ReAct] Step {iteration+1} Thought: {thought.content[:100]}...")
            
            # 2. Action: 决定行动
            action = self._decide_action(thought, question, accumulated_context)
            logger.info(f"[ReAct] Step {iteration+1} Action: {action.action_type.value}")
            
            # 3. Observation: 执行行动并观察结果
            observation = self._execute_action(action)
            logger.info(f"[ReAct] Step {iteration+1} Observation: {observation.content[:100]}...")
            
            # 记录步骤
            step = ReActStep(
                step=iteration + 1,
                thought=thought,
                action=action,
                observation=observation
            )
            self.history.append(step)
            
            # 更新上下文
            if action.action_type == ActionType.SEARCH_KB:
                retrieval_count += 1
                if observation.success:
                    accumulated_context += f"\n\n[检索结果 {retrieval_count}]\n{observation.content}"
            
            # 检查是否结束
            if action.action_type == ActionType.FINAL_ANSWER:
                logger.info(f"[ReAct] 达到最终答案，共{iteration+1}步")
                break
            
            # 检查是否信息充足
            if action.action_type == ActionType.NEED_MORE_INFO and retrieval_count >= 3:
                logger.info("[ReAct] 已达到最大检索次数，强制结束")
                break
        
        # 生成最终答案
        final_answer = self._generate_final_answer(question, accumulated_context)
        
        result = {
            'success': True,
            'answer': final_answer,
            'steps': self.history,
            'retrieval_count': retrieval_count,
            'final_context': accumulated_context,
            'iterations': len(self.history)
        }
        
        logger.info(f"[ReAct] 处理完成，共{len(self.history)}步，检索{retrieval_count}次")
        return result
    
    def _generate_thought(self, question: str, context: str, iteration: int) -> Thought:
        """生成思考"""
        if iteration == 0:
            content = f"我需要回答用户的问题: '{question}'。首先应该搜索知识库获取相关信息。"
        elif not context:
            content = "之前的搜索没有返回结果，我需要尝试不同的查询方式或重写查询。"
        else:
            content = f"我已经获取了一些信息，需要判断是否足够回答问题，或者需要进一步搜索。"
        
        return Thought(step=iteration + 1, content=content)
    
    def _decide_action(self, thought: Thought, question: str, context: str) -> Action:
        """决定行动"""
        iteration = thought.step
        
        # 第一次迭代：搜索知识库
        if iteration == 1:
            return Action(
                step=iteration,
                action_type=ActionType.SEARCH_KB,
                params={'query': question, 'top_k': 5}
            )
        
        # 第二次迭代：判断信息充分性
        if iteration == 2 and context:
            return Action(
                step=iteration,
                action_type=ActionType.NEED_MORE_INFO,
                params={'question': question, 'context': context}
            )
        
        # 第三次迭代：如果需要更多信息，重写查询并再次搜索
        if iteration == 3:
            return Action(
                step=iteration,
                action_type=ActionType.REWRITE_QUERY,
                params={'query': question}
            )
        
        # 第四次迭代：使用重写后的查询搜索
        if iteration == 4:
            return Action(
                step=iteration,
                action_type=ActionType.SEARCH_KB,
                params={'query': question, 'top_k': 3}
            )
        
        # 最后一次：生成最终答案
        return Action(
            step=iteration,
            action_type=ActionType.FINAL_ANSWER,
            params={'question': question, 'context': context}
        )
    
    def _execute_action(self, action: Action) -> Observation:
        """执行行动"""
        if action.action_type == ActionType.FINAL_ANSWER:
            return Observation(
                step=action.step,
                content="准备生成最终答案",
                success=True
            )
        
        # 查找对应的工具
        tool_name = action.action_type.value
        if tool_name not in self.tools:
            return Observation(
                step=action.step,
                content=f"未找到工具: {tool_name}",
                success=False
            )
        
        tool = self.tools[tool_name]
        result, success = tool.execute(**action.params)
        
        return Observation(
            step=action.step,
            content=result,
            success=success
        )
    
    def _generate_final_answer(self, question: str, context: str) -> str:
        """生成最终答案"""
        if not context:
            return "抱歉，我在知识库中没有找到相关信息来回答您的问题。"
        
        # 简单的答案生成（实际应该调用LLM）
        answer = f"基于检索到的信息，我来回答您的问题：\n\n"
        answer += f"问题：{question}\n\n"
        answer += "相关信息：\n"
        
        # 提取关键信息
        lines = context.split('\n')
        for line in lines[:20]:  # 限制长度
            if line.strip() and not line.startswith('['):
                answer += f"- {line.strip()}\n"
        
        return answer
    
    def get_thought_process(self) -> str:
        """获取思考过程（用于展示）"""
        lines = []
        for step in self.history:
            lines.append(f"\n{'='*50}")
            lines.append(f"步骤 {step.step}")
            lines.append(f"{'='*50}")
            lines.append(f"🤔 思考: {step.thought.content}")
            lines.append(f"🔧 行动: {step.action.action_type.value}")
            lines.append(f"📊 参数: {json.dumps(step.action.params, ensure_ascii=False)}")
            lines.append(f"👁️ 观察: {step.observation.content[:200]}...")
        
        return "\n".join(lines)


class AgenticRAG:
    """
    Agentic RAG 实现
    结合ReAct Agent和RAG，支持自适应多次检索
    """
    
    def __init__(self, kb_manager=None, llm_client=None):
        self.kb_manager = kb_manager
        self.llm_client = llm_client
        self.agent = ReActAgent(
            max_iterations=5,
            llm_client=llm_client,
            kb_manager=kb_manager
        )
        logger.info("[AgenticRAG] 初始化完成")
    
    def query(self, question: str, stream: bool = False) -> Dict:
        """
        执行Agentic RAG查询
        
        Args:
            question: 用户问题
            stream: 是否流式返回
            
        Returns:
            {
                'answer': str,
                'sources': List[Dict],
                'retrieval_count': int,
                'thought_process': str
            }
        """
        logger.info(f"[AgenticRAG] 查询: {question}")
        
        # 执行ReAct循环
        result = self.agent.run(question)
        
        # 提取来源
        sources = self._extract_sources(result.get('final_context', ''))
        
        return {
            'answer': result['answer'],
            'sources': sources,
            'retrieval_count': result['retrieval_count'],
            'iterations': result['iterations'],
            'thought_process': self.agent.get_thought_process(),
            'success': result['success']
        }
    
    def _extract_sources(self, context: str) -> List[Dict]:
        """从上下文中提取来源信息"""
        sources = []
        
        # 简单的正则匹配提取来源
        import re
        pattern = r'来源:\s*([^\n]+)'
        matches = re.findall(pattern, context)
        
        for match in matches:
            sources.append({
                'file': match.strip(),
                'relevance': 'high'
            })
        
        return sources
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'agent_initialized': True,
            'kb_available': self.kb_manager is not None,
            'llm_available': self.llm_client is not None,
            'max_iterations': self.agent.max_iterations
        }


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("测试 ReAct Agent")
    print("=" * 60)
    
    # 创建模拟的知识库管理器
    class MockKBManager:
        def search(self, query, top_k=5):
            return [
                {
                    'content': '这是一个关于Python编程的示例文档。Python是一种高级编程语言。',
                    'source_file': 'python_guide.txt',
                    'score': 0.95,
                    'chunk_id': 0
                },
                {
                    'content': 'Python支持多种编程范式，包括面向对象和函数式编程。',
                    'source_file': 'python_advanced.txt',
                    'score': 0.88,
                    'chunk_id': 1
                }
            ]
    
    # 初始化Agent
    kb = MockKBManager()
    agent = ReActAgent(max_iterations=5, kb_manager=kb)
    
    # 执行查询
    question = "Python是什么编程语言？"
    result = agent.run(question)
    
    print(f"\n问题: {question}")
    print(f"\n执行了 {result['iterations']} 步")
    print(f"检索了 {result['retrieval_count']} 次")
    print(f"\n思考过程:")
    print(agent.get_thought_process())
    print(f"\n最终答案:")
    print(result['answer'])
    
    print("\n" + "=" * 60)
    print("测试 Agentic RAG")
    print("=" * 60)
    
    agentic_rag = AgenticRAG(kb_manager=kb)
    rag_result = agentic_rag.query(question)
    
    print(f"\nAgentic RAG 结果:")
    print(f"检索次数: {rag_result['retrieval_count']}")
    print(f"迭代次数: {rag_result['iterations']}")
    print(f"来源数量: {len(rag_result['sources'])}")
