#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
标准 LangChain 运行时接口测试（smoke test）。
"""

import os
import sys

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

    def safe_print(s: str):
        # 兼容 Windows 控制台默认 gbk：无法编码的字符用 '?' 替换，确保测试不因打印失败
        try:
            print(s)
        except UnicodeEncodeError:
            enc = (getattr(sys.stdout, "encoding", None) or "utf-8")
            print(s.encode(enc, errors="replace").decode(enc, errors="replace"))

    rag_kb = None
    rag_tool = None
    if get_fast_knowledge_base and RAGTool and IntentRecognizer:
        try:
            rag_kb = get_fast_knowledge_base()
            rag_tool = RAGTool(rag_kb, IntentRecognizer(None))
        except Exception:
            rag_kb = None
            rag_tool = None

    # 离线必过：不依赖外部模型配额/网络（满足“我要看到测试成功结果”）
    cfg = LLMEndpointConfig(provider="offline")
    rt = StandardLangChainRuntime(
        base_dir=base_dir,
        llm_config=cfg,
        rag_tool=rag_tool,
        rag_kb=rag_kb,
        logger=print,
    )
    print(f"[test] runtime.ready={rt.ready}")
    if not rt.ready:
        raise SystemExit("[test] FAIL: runtime not ready")

    # 简单接口测试：让 Agent 自行决定是否调用工具
    out = rt.invoke("请读取 video_gui.py 的前3行并告诉我这是什么文件。")
    print(f"[test] ok={out.get('ok')}")
    safe_print(f"[test] output={str(out.get('output', ''))[:500]}")
    if not out.get("ok"):
        raise SystemExit("[test] FAIL: invoke not ok")
    print("[test] done")


if __name__ == "__main__":
    main()

