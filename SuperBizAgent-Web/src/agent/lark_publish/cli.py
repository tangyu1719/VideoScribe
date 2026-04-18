# -*- coding: utf-8 -*-
"""
飞书固定落点文档发布 CLI（仅依赖 lark-cli）。

  初始化（一次）：解析 URL/TOKEN 并写入 lark_publish_config.json
    python -m lark_publish init --url "https://..."

  创建文档：
    python -m lark_publish create --title "标题" --markdown-file note.md
    python -m lark_publish create --title "标题" --markdown "## 正文"

  仅解析（不调飞书）：
    python -m lark_publish parse "https://..."
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lark_publish.config_store import (
    config_to_parsed,
    default_config_path,
    load_config,
    save_config,
)
from lark_publish.feishu_target_url import TargetKind, parse_feishu_target
from lark_publish import lark_cli


def cmd_parse(args: argparse.Namespace) -> int:
    try:
        t = parse_feishu_target(args.url_or_token)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    print(t.summary())
    print(
        json.dumps(
            {
                "target_type": t.kind.value,
                "folder_token": t.folder_token,
                "wiki_node": t.wiki_node,
                "wiki_space": t.wiki_space,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    try:
        target = parse_feishu_target(args.url)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    as_id = args.as_identity
    path = Path(args.config).expanduser() if args.config else None

    if args.validate and target.kind == TargetKind.WIKI_NODE:
        ok, msg = lark_cli.validate_wiki_node(target.wiki_node or "", as_identity=as_id)
        if not ok:
            print(f"[校验失败] wiki spaces get_node:\n{msg}", file=sys.stderr)
            return 1
        print("[校验] 知识库节点可访问")

    saved = save_config(target, as_identity=as_id, path=path)
    print(f"已写入: {saved}")
    print(target.summary())
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser() if args.config else default_config_path()
    try:
        data = load_config(path)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser() if args.config else None
    try:
        data = load_config(path)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    target = config_to_parsed(data)
    as_id = data.get("as_identity") or "user"

    if args.markdown_file:
        md_path = Path(args.markdown_file).expanduser()
        if not md_path.is_file():
            print(f"文件不存在: {md_path}", file=sys.stderr)
            return 1
        markdown = md_path.read_text(encoding="utf-8")
    elif args.markdown is not None:
        markdown = args.markdown
    else:
        print("请指定 --markdown-file 或 --markdown", file=sys.stderr)
        return 1

    title = args.title or "未命名文档"
    if len(markdown) > 7000:
        print(
            "警告: Markdown 较长，Windows 命令行可能失败；可改短或后续支持分段 +update",
            file=sys.stderr,
        )

    try:
        proc = lark_cli.docs_create(
            title=title,
            markdown=markdown,
            target=target,
            as_identity=as_id,
            timeout=args.timeout,
        )
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    lark_cli.print_proc(proc)
    return 0 if proc.returncode == 0 else proc.returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="飞书固定落点发布（lark-cli）")
    p.add_argument(
        "--config",
        help="配置文件路径（默认见环境变量 LARK_PUBLISH_CONFIG 或 agent/lark_publish_config.json）",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("parse", help="仅解析 URL/TOKEN，不写配置")
    sp.add_argument("url_or_token")
    sp.set_defaults(func=cmd_parse)

    si = sub.add_parser("init", help="初始化落点（写入配置）")
    si.add_argument("--url", required=True, help="飞书文件夹/知识库 URL 或裸 TOKEN")
    si.add_argument(
        "--as",
        dest="as_identity",
        choices=("user", "bot"),
        default="user",
        help="lark-cli 身份（默认 user）",
    )
    si.add_argument(
        "--validate",
        action="store_true",
        help="对 wiki 节点调用 get_node 校验（需 wiki:node:read）",
    )
    si.set_defaults(func=cmd_init)

    ss = sub.add_parser("show", help="打印当前配置")
    ss.set_defaults(func=cmd_show)

    sc = sub.add_parser("create", help="在已配置落点创建云文档")
    sc.add_argument("--title", default="", help="文档标题")
    g = sc.add_mutually_exclusive_group(required=True)
    g.add_argument("--markdown-file", help="Markdown 文件路径")
    g.add_argument("--markdown", help="Markdown 正文字符串")
    sc.add_argument("--timeout", type=int, default=300, help="lark-cli 超时秒数")
    sc.set_defaults(func=cmd_create)

    return p


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
