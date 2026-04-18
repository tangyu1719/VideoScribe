#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tk 界面代码提取按钮/事件处理器候选项，辅助做 Web API 映射。

用法:
  py extract_event_api_map.py --src "..\\..\\src\\agent\\video_gui.py" --out "event_api_map.generated.json"
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set


def parse_method_defs(source: str) -> Set[str]:
    names: Set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
    return names


def extract_handlers(source: str) -> Dict[str, List[str]]:
    # command=self._xxx
    command_handlers = sorted(set(re.findall(r"command\s*=\s*self\.([a-zA-Z_][a-zA-Z0-9_]*)", source)))
    # bind("<Button-1>", lambda e: self._xxx())
    bind_handlers = sorted(
        set(
            re.findall(
                r'bind\("<?[^"]+>?"\s*,\s*lambda[^:]*:\s*self\.([a-zA-Z_][a-zA-Z0-9_]*)',
                source,
            )
        )
    )
    return {"command_handlers": command_handlers, "bind_handlers": bind_handlers}


def build_candidates(methods: Set[str], handlers: Dict[str, List[str]]) -> List[Dict]:
    all_handlers = sorted(set(handlers["command_handlers"]) | set(handlers["bind_handlers"]))
    rows = []
    for name in all_handlers:
        event_id = name.removeprefix("_")
        rows.append(
            {
                "event_id": event_id,
                "desktop_handler": name,
                "api_path": f"/api/gui/{event_id}",
                "method": "POST",
                "sse_required": any(k in event_id for k in ("stream", "chat", "send", "simulate_ai_response")),
                "implemented": False,
                "in_source_methods": name in methods,
                "note": "",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="源文件路径（如 video_gui.py）")
    parser.add_argument("--out", required=True, help="输出 json 路径")
    args = parser.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    text = src.read_text(encoding="utf-8", errors="ignore")
    methods = parse_method_defs(text)
    handlers = extract_handlers(text)
    candidates = build_candidates(methods, handlers)

    payload = {
        "source_file": str(src),
        "summary": {
            "method_count": len(methods),
            "command_handler_count": len(handlers["command_handlers"]),
            "bind_handler_count": len(handlers["bind_handlers"]),
            "candidate_event_count": len(candidates),
        },
        "handlers": handlers,
        "candidates": candidates,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {out} (events={len(candidates)})")


if __name__ == "__main__":
    main()
