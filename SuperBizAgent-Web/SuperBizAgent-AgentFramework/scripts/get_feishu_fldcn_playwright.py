# -*- coding: utf-8 -*-
"""
本地 headed 浏览器辅助：登录飞书后进入「云空间」并打开目标文件夹，
地址栏 URL 出现 .../drive/folder/fldcn... 时自动识别并打印 fldcn。

用法（在项目根目录或任意目录均可）:
  pip install playwright
  playwright install chromium
  python scripts/get_feishu_fldcn_playwright.py

说明：
- 不在脚本或仓库中存放 App Secret；fldcn 来自浏览器地址栏，与 cli_ 应用凭证无关。
- 若目标仅在「知识库」树中，请在云空间里找到对应文件夹并打开（或复制云空间文件夹链接），
  上传 API 需要的是云空间文件夹的 fldcn，不是 wikcn 节点页（脚本检测到 wikcn 会提示）。
"""
from __future__ import annotations

import re
import sys
from typing import Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("请先安装: pip install playwright", file=sys.stderr)
    print("然后执行: playwright install chromium", file=sys.stderr)
    sys.exit(1)

# 飞书 / Lark 国际版
DRIVE_FOLDER_RE = re.compile(r"/drive/folder/(fld[a-z0-9_-]+)", re.I)
WIKI_NODE_RE = re.compile(r"/wiki/(wik[a-z0-9_-]+)", re.I)

START_URLS = (
    "https://www.feishu.cn/drive/me",
    "https://www.larksuite.com/drive/me",
)


def _token_from_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """返回 (fldcn, 提示类型)。"""
    m = DRIVE_FOLDER_RE.search(url)
    if m:
        return m.group(1), None
    m2 = WIKI_NODE_RE.search(url)
    if m2:
        return None, "wiki"
    return None, None


def main() -> None:
    print(
        "将打开 Chromium 窗口。\n"
        "1) 在窗口内完成飞书登录（扫码/密码由你本人操作）。\n"
        "2) 进入「云空间」，逐级打开目标文件夹，直到地址栏出现 …/drive/folder/fldcn…\n"
        "3) 脚本检测到 fldcn 后会打印并退出；或按 Ctrl+C 结束。\n"
    )
    last_hint = ""
    captured_fldcn: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        def on_nav(_frame) -> None:
            nonlocal last_hint
            url = page.url or ""
            tok, kind = _token_from_url(url)
            if tok:
                captured_fldcn.clear()
                captured_fldcn.append(tok)
                return
            if kind == "wiki" and "settings" not in url.lower():
                msg = (
                    "\n[提示] 当前为知识库节点页 (wikcn)。上传接口需要「云空间」文件夹的 fldcn。\n"
                    "请在云空间中打开同一目录对应的文件夹，或复制 …/drive/folder/fldcn… 链接。\n"
                )
                if msg != last_hint:
                    print(msg)
                    last_hint = msg

        page.on("framenavigated", on_nav)
        page.goto(START_URLS[0], wait_until="domcontentloaded", timeout=120000)

        try:
            while not page.is_closed():
                if captured_fldcn:
                    tok = captured_fldcn[0]
                    print("\n========== 检测到云空间文件夹 Token ==========")
                    print(tok)
                    print("==============================================")
                    print(f'可将 config.json 中 feishu_folder_token 设为: "{tok}"')
                    print("或粘贴完整文件夹 URL 亦可。\n")
                    break
                page.wait_for_timeout(400)
        except KeyboardInterrupt:
            print("\n已中断。")
        except Exception:
            pass
        finally:
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
