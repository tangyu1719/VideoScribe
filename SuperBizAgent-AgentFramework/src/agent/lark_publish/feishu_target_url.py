# -*- coding: utf-8 -*-
"""识别飞书云空间文件夹 URL、知识库节点/空间 URL，或裸 TOKEN。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import unquote, urlparse


class TargetKind(str, Enum):
    DRIVE_FOLDER = "drive_folder"
    WIKI_NODE = "wiki_node"
    WIKI_SPACE = "wiki_space"


@dataclass
class ParsedTarget:
    kind: TargetKind
    folder_token: str | None = None
    wiki_node: str | None = None
    wiki_space: str | None = None
    source: str = ""

    def summary(self) -> str:
        if self.kind == TargetKind.DRIVE_FOLDER:
            return f"云空间文件夹 folder_token={self.folder_token}"
        if self.kind == TargetKind.WIKI_NODE:
            return f"知识库节点 wiki_node={self.wiki_node}"
        if self.kind == TargetKind.WIKI_SPACE:
            return f"知识空间 wiki_space={self.wiki_space}"
        return "unknown"


_RAW_FOLDER = re.compile(r"^fld[a-z0-9_-]+$", re.I)
# 云空间文件夹 URL 中第三段 token 未必以 fld 开头（部分租户为该格式）
_DRIVE_FOLDER_PATH_TOKEN = re.compile(r"^[a-zA-Z0-9_-]{6,128}$")
_RAW_WIKI_NODE_LEGACY = re.compile(r"^wik[a-z0-9_-]+$", re.I)
# 新版知识库节点常为字母数字串（非 wik 前缀），与云空间 fld… 区分
_RAW_WIKI_NODE_ALNUM = re.compile(r"^[a-z0-9][a-z0-9_-]{7,}$", re.I)
_RAW_SPACE_ID = re.compile(r"^\d{10,}$")


def _is_wiki_node_token(node: str) -> bool:
    n = (node or "").strip()
    if not n or n.lower() in ("settings", "space", "help"):
        return False
    if _RAW_FOLDER.match(n):
        return False
    # 纯数字长串优先视为知识空间 ID，避免与新版字母数字 wiki token 规则冲突
    if _RAW_SPACE_ID.match(n):
        return False
    if _RAW_WIKI_NODE_LEGACY.match(n):
        return True
    return bool(_RAW_WIKI_NODE_ALNUM.match(n))


def parse_feishu_target(url_or_token: str) -> ParsedTarget:
    """
    支持：
    - 文件夹：https://*.feishu.cn/drive/folder/fldcnXXXX 或 larksuite.com
    - 知识库节点：https://*.feishu.cn/wiki/<节点token>（含 wikcn… 或新版字母数字 token，非 settings）
    - 知识空间：https://*.feishu.cn/wiki/settings/7000000000000000000
    - 裸 TOKEN：fldcn… / wikcn… 或新版 wiki 节点串 / 纯数字 space_id（≥10 位）
    """
    raw = (url_or_token or "").strip()
    if not raw:
        raise ValueError("空字符串，请传入飞书 URL 或 TOKEN")

    source = raw
    if not raw.lower().startswith(("http://", "https://")):
        return _parse_bare_token(raw, source)

    parsed = urlparse(raw)
    path = unquote(parsed.path or "")
    path = path.strip("/")
    parts = [p for p in path.split("/") if p]

    # .../drive/folder/<token>
    if (
        len(parts) >= 3
        and parts[0].lower() == "drive"
        and parts[1].lower() == "folder"
    ):
        token = parts[2]
        if not (_RAW_FOLDER.match(token) or _DRIVE_FOLDER_PATH_TOKEN.match(token)):
            raise ValueError(f"路径像文件夹但 token 格式异常: {token}")
        return ParsedTarget(TargetKind.DRIVE_FOLDER, folder_token=token, source=source)

    # .../wiki/settings/<space_id>
    if (
        len(parts) >= 3
        and parts[0].lower() == "wiki"
        and parts[1].lower() == "settings"
    ):
        space_id = parts[2]
        if not _RAW_SPACE_ID.match(space_id):
            raise ValueError(f"知识空间 ID 应为较长数字: {space_id}")
        return ParsedTarget(TargetKind.WIKI_SPACE, wiki_space=space_id, source=source)

    # .../wiki/<node_token>  （排除已知非节点段）
    if len(parts) >= 2 and parts[0].lower() == "wiki":
        second = parts[1].lower()
        if second in ("settings", "space", "help"):
            raise ValueError(f"无法从该 wiki 路径解析落点: /{'/'.join(parts)}")
        node = parts[1]
        if not _is_wiki_node_token(node):
            raise ValueError(
                f"无法识别知识库节点 token: {node!r}。"
                "请使用 …/wiki/<节点token>（wikcn… 或新版字母数字串），且勿把中文路径拼进 URL。"
            )
        return ParsedTarget(TargetKind.WIKI_NODE, wiki_node=node, source=source)

    raise ValueError(
        "无法识别 URL。请使用：\n"
        "  • 云空间文件夹 …/drive/folder/fldcn…\n"
        "  • 知识库节点 …/wiki/<节点token>（含 wikcn… 或新版 token）\n"
        "  • 知识空间设置 …/wiki/settings/<空间数字ID>\n"
        "或直接粘贴 fldcn… / wikcn… / 空间数字 ID"
    )


def _parse_bare_token(s: str, source: str) -> ParsedTarget:
    t = s.strip()
    if t.lower() == "my_library":
        return ParsedTarget(TargetKind.WIKI_SPACE, wiki_space="my_library", source=source)
    if _RAW_FOLDER.match(t):
        return ParsedTarget(TargetKind.DRIVE_FOLDER, folder_token=t, source=source)
    if _is_wiki_node_token(t):
        return ParsedTarget(TargetKind.WIKI_NODE, wiki_node=t, source=source)
    if _RAW_SPACE_ID.match(t):
        return ParsedTarget(TargetKind.WIKI_SPACE, wiki_space=t, source=source)
    raise ValueError(
        f"无法识别裸 TOKEN: {s!r}。请使用 fldcn…、wiki 节点 token、wikcn… 或知识空间数字 ID，或完整飞书 URL"
    )
