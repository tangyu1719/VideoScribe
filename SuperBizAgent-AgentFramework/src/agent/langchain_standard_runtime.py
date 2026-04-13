#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准 LangChain 运行时（模型 + Agent + Memory + RAG Tool + Agentic RAG Tool）。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from langchain.tools import StructuredTool
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
except Exception:  # pragma: no cover
    StructuredTool = None  # type: ignore
    AgentExecutor = None  # type: ignore
    create_tool_calling_agent = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore
    MessagesPlaceholder = None  # type: ignore
    ConversationBufferWindowMemory = None  # type: ignore
    ConversationSummaryMemory = None  # type: ignore

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    try:
        from langchain.chat_models import ChatOpenAI  # type: ignore
    except Exception:
        ChatOpenAI = None  # type: ignore

from cursor_tools.tools import build_cursor_like_tools


@dataclass
class LLMEndpointConfig:
    provider: str = "ark"  # ark|qwen|kimi|deepseek|openai_compatible
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.2
    max_tokens: int = 1800


def _safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


class StandardLangChainRuntime:
    """
    标准 LangChain 运行时。
    - 模型：统一 OpenAI-compatible ChatModel
    - 工具：Cursor 风格工具 + RAG + Agentic RAG
    - Agent：Tool Calling Agent + AgentExecutor
    - Memory：窗口记忆 + 摘要记忆（可选）
    """

    def __init__(
        self,
        base_dir: str,
        llm_config: LLMEndpointConfig,
        rag_tool: Any = None,
        rag_kb: Any = None,
        logger: Optional[Any] = None,
    ):
        self.base_dir = base_dir
        self.llm_config = llm_config
        self.rag_tool = rag_tool
        self.rag_kb = rag_kb
        self._log = logger or (lambda *_args, **_kwargs: None)

        self._llm = None
        self._tools = []
        self._agent_executor = None
        self._memory = None
        self._summary_memory = None

        self._init_runtime()

    def _init_runtime(self):
        if ChatOpenAI is None or StructuredTool is None or AgentExecutor is None:
            self._log("[LangChainRuntime] 依赖不可用，回退旧链路。")
            return
        if not (self.llm_config.api_key or "").strip():
            self._log("[LangChainRuntime] api_key 为空，标准运行时禁用。")
            return

        try:
            self._llm = ChatOpenAI(
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
                model=self.llm_config.model,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
            )
        except Exception as e:
            self._log(f"[LangChainRuntime] 模型初始化失败: {type(e).__name__}: {e}")
            self._llm = None
            return

        self._tools = build_cursor_like_tools(self.base_dir)
        self._tools.extend(self._build_rag_tools())

        # 短窗 memory（主用）
        if ConversationBufferWindowMemory is not None:
            self._memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                k=10,
                return_messages=True,
                input_key="input",
                output_key="output",
            )
        # 长期摘要 memory（可选，不可用时自动忽略）
        if ConversationSummaryMemory is not None:
            try:
                self._summary_memory = ConversationSummaryMemory(
                    llm=self._llm,
                    memory_key="summary",
                    return_messages=False,
                )
            except Exception:
                self._summary_memory = None

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个工程助手。优先使用工具获取证据后再回答。"
                    "回答要简洁、结构化，必要时给出可执行步骤。",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self._llm, self._tools, prompt)
        self._agent_executor = AgentExecutor(
            agent=agent,
            tools=self._tools,
            memory=self._memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=6,
            return_intermediate_steps=True,
        )
        self._log(f"[LangChainRuntime] 初始化完成，tools={len(self._tools)}")

    def _build_rag_tools(self) -> List[Any]:
        if StructuredTool is None:
            return []
        tools = []

        def rag_search(query: str, top_k: int = 3) -> str:
            if not self.rag_tool:
                return "RAGTool 未初始化。"
            try:
                _intent, chunks = self.rag_tool.search(query, top_k=top_k, skip_intent=True)
                if not chunks:
                    return "RAG 无结果。"
                lines = []
                for i, c in enumerate(chunks[:top_k], 1):
                    lines.append(f"{i}. score={c.similarity:.3f} source={c.doc_id}\n{c.content[:400]}")
                return "\n\n".join(lines)
            except Exception as e:
                return f"RAG 搜索失败：{type(e).__name__}: {e}"

        tools.append(
            StructuredTool.from_function(
                name="rag_search",
                description="检索本地知识库。参数：query, top_k(可选)。",
                func=rag_search,
            )
        )

        def agentic_rag_query(question: str) -> str:
            if not self.rag_kb:
                return "Agentic RAG 不可用：知识库未初始化。"
            try:
                # 项目已有 AgenticRAG 实现
                from react_agent import AgenticRAG

                agentic = AgenticRAG(kb_manager=self.rag_kb, llm_client=None)
                result = agentic.query(question)
                answer = result.get("answer", "")
                retrieval_count = result.get("retrieval_count", 0)
                iterations = result.get("iterations", 0)
                return (
                    f"[AgenticRAG] retrieval_count={retrieval_count}, iterations={iterations}\n\n"
                    f"{answer}"
                )
            except Exception as e:
                return f"Agentic RAG 失败：{type(e).__name__}: {e}"

        tools.append(
            StructuredTool.from_function(
                name="agentic_rag_query",
                description="使用 Agentic RAG 回答复杂问题。参数：question。",
                func=agentic_rag_query,
            )
        )

        return tools

    @property
    def ready(self) -> bool:
        return self._agent_executor is not None

    def invoke(self, user_input: str) -> Dict[str, Any]:
        if not self.ready:
            return {"ok": False, "output": "LangChain 标准运行时不可用。"}
        try:
            payload = {"input": user_input}
            result = self._agent_executor.invoke(payload)
            output = result.get("output", "")
            steps = result.get("intermediate_steps", [])
            # 维护 summary memory（可选）
            if self._summary_memory is not None:
                try:
                    self._summary_memory.save_context({"input": user_input}, {"output": output})
                except Exception:
                    pass
            return {
                "ok": True,
                "output": output,
                "intermediate_steps": steps,
            }
        except Exception as e:
            return {"ok": False, "output": f"Agent 执行失败：{type(e).__name__}: {e}"}

