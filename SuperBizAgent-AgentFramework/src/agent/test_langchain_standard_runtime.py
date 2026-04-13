#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
标准 LangChain 运行时接口测试（smoke test）。
"""

import os

from langchain_standard_runtime import StandardLangChainRuntime, LLMEndpointConfig

try:
    from kb_manager_fast import get_fast_knowledge_base
except Exception:
    get_fast_knowledge_base = None

try:
    from rag_tools import RAGTool, IntentRecognizer
except Exception:
    RAGTool = None
    IntentRecognizer = None


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    rag_kb = None
    rag_tool = None
    if get_fast_knowledge_base and RAGTool and IntentRecognizer:
        try:
            rag_kb = get_fast_knowledge_base()
            rag_tool = RAGTool(rag_kb, IntentRecognizer(None))
        except Exception:
            rag_kb = None
            rag_tool = None

    cfg = LLMEndpointConfig(
        provider="ark",
        api_key=os.environ.get("VOLC_API_KEY", ""),
        base_url=os.environ.get("VOLC_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        model=os.environ.get("VOLC_MODEL", "ep-20260411182220-jv5qt"),
        temperature=0.2,
        max_tokens=600,
    )
    if not cfg.api_key:
        print("[test] SKIP: 未设置 VOLC_API_KEY，跳过在线接口测试。")
        return
    rt = StandardLangChainRuntime(
        base_dir=base_dir,
        llm_config=cfg,
        rag_tool=rag_tool,
        rag_kb=rag_kb,
        logger=print,
    )
    print(f"[test] runtime.ready={rt.ready}")
    if not rt.ready:
        print("[test] SKIP: runtime not ready")
        return

    # 简单接口测试：让 Agent 自行决定是否调用工具
    out = rt.invoke("请读取 video_gui.py 的前3行并告诉我这是什么文件。")
    print(f"[test] ok={out.get('ok')}")
    print(f"[test] output={str(out.get('output', ''))[:500]}")
    print("[test] done")


if __name__ == "__main__":
    main()

