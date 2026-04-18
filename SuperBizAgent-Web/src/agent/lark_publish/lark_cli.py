# -*- coding: utf-8 -*-
"""调用本机 lark-cli（需已 config init / auth）。"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys

from lark_publish.feishu_target_url import ParsedTarget, TargetKind


def _which_lark_cli() -> str:
    exe = shutil.which("lark-cli")
    if not exe:
        raise FileNotFoundError(
            "未在 PATH 中找到 lark-cli，请先安装并确保可在终端执行 lark-cli"
        )
    return exe


def run_lark_cli(
    args: list[str],
    *,
    as_identity: str = "user",
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    cli = _which_lark_cli()
    prefix = [cli]
    if as_identity == "bot":
        prefix.extend(["--as", "bot"])
    elif as_identity == "user":
        prefix.extend(["--as", "user"])
    full = prefix + args
    return subprocess.run(
        full,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )


def validate_wiki_node(token: str, *, as_identity: str) -> tuple[bool, str]:
    """调用 wiki spaces get_node 校验节点可读。"""
    params = json.dumps({"token": token}, ensure_ascii=False)
    proc = run_lark_cli(
        ["wiki", "spaces", "get_node", "--params", params],
        as_identity=as_identity,
        timeout=60,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return False, out.strip() or f"exit {proc.returncode}"
    return True, out.strip()


def docs_create(
    *,
    title: str,
    markdown: str,
    target: ParsedTarget,
    as_identity: str,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    args = [
        "docs",
        "+create",
        "--title",
        title,
        "--markdown",
        markdown,
    ]
    if target.kind == TargetKind.DRIVE_FOLDER:
        args.extend(["--folder-token", target.folder_token or ""])
    elif target.kind == TargetKind.WIKI_NODE:
        args.extend(["--wiki-node", target.wiki_node or ""])
    elif target.kind == TargetKind.WIKI_SPACE:
        args.extend(["--wiki-space", target.wiki_space or ""])
    else:
        raise ValueError("未知 target kind")
    return run_lark_cli(args, as_identity=as_identity, timeout=timeout)


def print_proc(proc: subprocess.CompletedProcess[str]) -> None:
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
