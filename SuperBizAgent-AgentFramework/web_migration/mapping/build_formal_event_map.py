#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 generated 事件表转为正式映射表骨架，便于逐项实现与回归跟踪。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def classify_domain(event_id: str) -> str:
    e = event_id.lower()
    if "workflow" in e or "node" in e or "scheduler" in e:
        return "workflow"
    if "session" in e or "chat" in e or "message" in e or "history" in e:
        return "chat"
    if "kb" in e or "rag" in e:
        return "knowledge_base"
    if "multimodal" in e or "upload" in e:
        return "multimodal"
    if "video" in e:
        return "video"
    if "config" in e or "settings" in e:
        return "settings"
    return "misc"


def main() -> None:
    base = Path(__file__).resolve().parent
    src = base / "event_api_map.generated.json"
    out = base / "event_api_map.formal.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    candidates: List[Dict[str, Any]] = data.get("candidates", [])

    formal_items: List[Dict[str, Any]] = []
    for c in candidates:
        event_id = c["event_id"]
        formal_items.append(
            {
                "event_id": event_id,
                "domain": classify_domain(event_id),
                "desktop_handler": c["desktop_handler"],
                "api": {
                    "path": c["api_path"],
                    "method": c.get("method", "POST"),
                    "sse_required": bool(c.get("sse_required", False)),
                },
                "schema": {"request": {}, "response": {"ok": "bool", "data": "object", "error": "string"}},
                "status": "planned",
                "test_case_id": f"evt_{event_id}",
                "notes": "",
            }
        )

    payload = {
        "meta": {
            "source_file": data.get("source_file"),
            "candidate_event_count": len(formal_items),
            "goal": "desktop_to_web_lossless_migration",
        },
        "items": formal_items,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {out} (items={len(formal_items)})")


if __name__ == "__main__":
    main()
