# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from lark_publish.feishu_target_url import ParsedTarget, TargetKind

CONFIG_VERSION = 1


def default_config_path() -> Path:
    env = os.environ.get("LARK_PUBLISH_CONFIG", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "lark_publish_config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    if not p.is_file():
        raise FileNotFoundError(f"未找到配置文件，请先执行 init: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") != CONFIG_VERSION:
        pass  # 向后兼容：仅警告
    return data


def save_config(
    target: ParsedTarget,
    *,
    as_identity: str = "user",
    path: Path | None = None,
) -> Path:
    p = path or default_config_path()
    payload: dict[str, Any] = {
        "version": CONFIG_VERSION,
        "target_type": target.kind.value,
        "folder_token": target.folder_token,
        "wiki_node": target.wiki_node,
        "wiki_space": target.wiki_space,
        "source_url": target.source,
        "as_identity": as_identity if as_identity in ("user", "bot") else "user",
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def config_to_parsed(data: dict[str, Any]) -> ParsedTarget:
    kind = TargetKind(data["target_type"])
    return ParsedTarget(
        kind=kind,
        folder_token=data.get("folder_token"),
        wiki_node=data.get("wiki_node"),
        wiki_space=data.get("wiki_space"),
        source=data.get("source_url") or "",
    )
