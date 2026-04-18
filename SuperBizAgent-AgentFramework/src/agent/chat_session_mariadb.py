#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 聊天会话 MariaDB 存储。
- 建表：ai_chat_sessions
- 能力：加载、UPSERT、删除、按时间范围查询
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import db as _db
    DB_AVAILABLE = True
except Exception:
    _db = None  # type: ignore
    DB_AVAILABLE = False

_TABLE_ENSURED = False

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS ai_chat_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    messages_json LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted TINYINT(1) NOT NULL DEFAULT 0,
    INDEX idx_ai_chat_sessions_updated_at (updated_at),
    INDEX idx_ai_chat_sessions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def is_available() -> bool:
    return bool(DB_AVAILABLE and _db is not None)


def _ensure_table() -> None:
    global _TABLE_ENSURED
    if _TABLE_ENSURED or not is_available():
        return
    _db.execute_update(CREATE_SQL)
    _TABLE_ENSURED = True


def _parse_dt(raw: Optional[str], fallback: datetime) -> datetime:
    if not raw:
        return fallback
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return fallback


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def upsert_session(session: Dict[str, Any]) -> bool:
    if not is_available():
        return False
    _ensure_table()
    now = datetime.now()
    sid = str(session.get("id") or "").strip()
    if not sid:
        return False
    created_at = _parse_dt(session.get("created_at"), now)
    updated_at = _parse_dt(session.get("updated_at"), now)
    payload = json.dumps(session.get("messages") or [], ensure_ascii=False)
    title = str(session.get("title") or "新对话")[:255]
    sql = """
    INSERT INTO ai_chat_sessions (session_id, title, messages_json, created_at, updated_at, deleted)
    VALUES (%s, %s, %s, %s, %s, 0)
    ON DUPLICATE KEY UPDATE
      title=VALUES(title),
      messages_json=VALUES(messages_json),
      created_at=VALUES(created_at),
      updated_at=VALUES(updated_at),
      deleted=0
    """
    _db.execute_update(sql, (sid, title, payload, _fmt_dt(created_at), _fmt_dt(updated_at)))
    return True


def delete_session(session_id: str) -> bool:
    if not is_available():
        return False
    _ensure_table()
    _db.execute_update("UPDATE ai_chat_sessions SET deleted=1 WHERE session_id=%s", (session_id,))
    return True


def load_sessions(limit: int = 500) -> List[Dict[str, Any]]:
    if not is_available():
        return []
    _ensure_table()
    rows = _db.execute_query(
        """
        SELECT session_id, title, messages_json, created_at, updated_at
        FROM ai_chat_sessions
        WHERE deleted=0
        ORDER BY updated_at DESC
        LIMIT %s
        """,
        (int(limit),),
    )
    out: List[Dict[str, Any]] = []
    for r in rows or []:
        try:
            messages = json.loads(r.get("messages_json") or "[]")
            if not isinstance(messages, list):
                messages = []
        except Exception:
            messages = []
        out.append(
            {
                "id": r.get("session_id"),
                "title": r.get("title") or "新对话",
                "messages": messages,
                "created_at": (r.get("created_at").strftime("%Y-%m-%dT%H:%M:%S") if r.get("created_at") else datetime.now().isoformat()),
                "updated_at": (r.get("updated_at").strftime("%Y-%m-%dT%H:%M:%S") if r.get("updated_at") else datetime.now().isoformat()),
            }
        )
    return out


def query_sessions_by_time(start_at: Optional[datetime], end_at: Optional[datetime], limit: int = 500) -> List[Dict[str, Any]]:
    if not is_available():
        return []
    _ensure_table()
    conds = ["deleted=0"]
    params: List[Any] = []
    if start_at is not None:
        conds.append("updated_at >= %s")
        params.append(_fmt_dt(start_at))
    if end_at is not None:
        conds.append("updated_at <= %s")
        params.append(_fmt_dt(end_at))
    params.append(int(limit))
    sql = f"""
    SELECT session_id, title, messages_json, created_at, updated_at
    FROM ai_chat_sessions
    WHERE {' AND '.join(conds)}
    ORDER BY updated_at DESC
    LIMIT %s
    """
    rows = _db.execute_query(sql, tuple(params))
    out: List[Dict[str, Any]] = []
    for r in rows or []:
        try:
            messages = json.loads(r.get("messages_json") or "[]")
            if not isinstance(messages, list):
                messages = []
        except Exception:
            messages = []
        out.append(
            {
                "id": r.get("session_id"),
                "title": r.get("title") or "新对话",
                "messages": messages,
                "created_at": (r.get("created_at").strftime("%Y-%m-%dT%H:%M:%S") if r.get("created_at") else datetime.now().isoformat()),
                "updated_at": (r.get("updated_at").strftime("%Y-%m-%dT%H:%M:%S") if r.get("updated_at") else datetime.now().isoformat()),
            }
        )
    return out
