#!/usr/bin/env python3
"""
从 video_gui 的 history.json 中按时间取最近 N 条链接，调用本机 Web API 创建链接分析任务。

用法（先启动 web_api：python web_api.py）:
  python run_latest_links_from_history.py
  python run_latest_links_from_history.py --count 8 --api-base http://127.0.0.1:8000
  python run_latest_links_from_history.py --history "D:\\path\\history.json" --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests", file=sys.stderr)
    sys.exit(1)


def _task_sort_key(task: dict[str, Any]) -> float:
    ts = task.get("updated_at") or task.get("created_at") or ""
    if not isinstance(ts, str):
        return 0.0
    try:
        return datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return 0.0


def pick_latest_links(
    tasks: list[dict[str, Any]],
    count: int,
    dedupe: bool,
) -> list[tuple[str, dict[str, Any]]]:
    """返回 (link, task) 列表，按时间从新到旧。"""
    with_link = [
        t
        for t in tasks
        if isinstance(t.get("link"), str)
        and t["link"].strip().lower().startswith(("http://", "https://"))
    ]
    with_link.sort(key=_task_sort_key, reverse=True)
    out: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for t in with_link:
        link = t["link"].strip()
        if dedupe and link in seen:
            continue
        if dedupe:
            seen.add(link)
        out.append((link, t))
        if len(out) >= count:
            break
    return out


def main() -> int:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass

    parser = argparse.ArgumentParser(description="从历史 JSON 提交最近链接到 /api/link/tasks")
    here = Path(__file__).resolve().parent
    parser.add_argument(
        "--history",
        type=Path,
        default=here / "history.json",
        help="history.json 路径（默认与脚本同目录）",
    )
    parser.add_argument("--count", type=int, default=8, help="提交链接条数（默认 8）")
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="Web API 根地址（默认 http://127.0.0.1:8000）",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="不去重：同一 URL 可出现多次（仍按时间从新到旧截断）",
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印链接，不请求 API")
    args = parser.parse_args()

    path: Path = args.history
    if not path.is_file():
        print(f"找不到历史文件: {path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"读取 history 失败: {e}", file=sys.stderr)
        return 1

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        print("history.json 缺少 tasks 数组", file=sys.stderr)
        return 1

    picked = pick_latest_links(tasks, args.count, dedupe=not args.allow_duplicates)
    if not picked:
        print("没有可用的 http(s) 链接任务", file=sys.stderr)
        return 1

    base = args.api_base.rstrip("/")
    url = f"{base}/api/link/tasks"

    for i, (link, task) in enumerate(picked, 1):
        tid = task.get("id", "?")
        ts = task.get("updated_at") or task.get("created_at") or ""
        print(f"[{i}/{len(picked)}] {ts} id={tid}\n    {link}")
        if args.dry_run:
            continue
        try:
            r = requests.post(
                url,
                json={"url": link, "config": {}},
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
        except requests.RequestException as e:
            print(f"    请求失败: {e}", file=sys.stderr)
            return 1
        try:
            body = r.json()
        except ValueError:
            print(f"    HTTP {r.status_code} 非 JSON: {r.text[:500]}", file=sys.stderr)
            return 1
        if not body.get("success"):
            print(f"    API 错误: {body.get('error', body)}", file=sys.stderr)
            return 1
        task_id = (body.get("data") or {}).get("taskId")
        print(f"    -> taskId={task_id}")

    if args.dry_run:
        print("(dry-run，未调用 API)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
