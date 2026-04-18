# -*- coding: utf-8 -*-
"""
video_gui 配置与 MariaDB 双写/合并加载（与 ai_api_config_gui 使用同一 db 模块）。
表：video_agent_config（单行 id=1，config_json 存完整 JSON 对象）。
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    import db as _db

    DB_AVAILABLE = True
except ImportError:
    _db = None  # type: ignore
    DB_AVAILABLE = False

_TABLE_ENSURED = False

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS video_agent_config (
    id INT PRIMARY KEY DEFAULT 1,
    config_json LONGTEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def is_available() -> bool:
    return bool(DB_AVAILABLE and _db is not None)


def _ensure_table() -> None:
    global _TABLE_ENSURED
    if _TABLE_ENSURED or not is_available():
        return
    try:
        _db.execute_update(CREATE_SQL)
        _TABLE_ENSURED = True
    except Exception as e:
        print(f"[video_config_mariadb] 建表 video_agent_config 失败（将仅用 config.json）：{e}")


def load_from_mariadb() -> Optional[Dict[str, Any]]:
    """读取 id=1 行，解析 config_json；失败返回 None。"""
    if not is_available():
        return None
    _ensure_table()
    try:
        rows = _db.execute_query(
            "SELECT config_json FROM video_agent_config WHERE id=1",
            (),
        )
        if not rows:
            return None
        raw = rows[0].get("config_json")
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[video_config_mariadb] 从 MariaDB 读取失败：{e}")
        return None


def save_to_mariadb(config: Dict[str, Any]) -> bool:
    """UPSERT 整份配置为 JSON。"""
    if not is_available():
        return False
    _ensure_table()
    try:
        payload = json.dumps(config, ensure_ascii=False)
        sql = """
            INSERT INTO video_agent_config (id, config_json)
            VALUES (1, %s)
            ON DUPLICATE KEY UPDATE config_json=VALUES(config_json)
        """
        _db.execute_update(sql, (payload,))
        return True
    except Exception as e:
        print(f"[video_config_mariadb] 写入 MariaDB 失败：{e}")
        return False
