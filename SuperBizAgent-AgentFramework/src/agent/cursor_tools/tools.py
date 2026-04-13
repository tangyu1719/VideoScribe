#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import subprocess
import textwrap
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

try:
    # langchain>=0.1 仍提供该入口；若未来拆包，可在此处兼容调整
    from langchain.tools import Tool
    from langchain.tools import StructuredTool
except Exception:  # pragma: no cover
    Tool = None  # type: ignore
    StructuredTool = None  # type: ignore


def _safe_abspath(base_dir: str, user_path: str) -> str:
    """
    将用户输入路径约束在 base_dir 下（防止越权读写）。
    - 允许传入绝对路径，但必须位于 base_dir 内。
    """
    base = Path(base_dir).resolve()
    p = Path(user_path)
    if not p.is_absolute():
        p = (base / user_path).resolve()
    else:
        p = p.resolve()
    try:
        p.relative_to(base)
    except Exception:
        raise ValueError(f"路径越界：{p} 不在允许目录 {base} 下")
    return str(p)


def _truncate(s: str, limit: int = 12000) -> str:
    if s is None:
        return ""
    s = str(s)
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n\n...[truncated {len(s) - limit} chars]..."


def _run_rg(query: str, root: str, glob: Optional[str], max_matches: int) -> Tuple[bool, str]:
    """
    优先使用 ripgrep（rg），没有则返回 (False, reason)。
    """
    try:
        cmd = ["rg", "--no-heading", "--line-number", "--hidden", "--max-count", str(max_matches), query, root]
        if glob:
            cmd.extend(["--glob", glob])
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = (cp.stdout or "") + (("\n" + cp.stderr) if cp.stderr else "")
        if not out.strip():
            return True, "未找到匹配内容。"
        return True, _truncate(out, 20000)
    except FileNotFoundError:
        return False, "未找到 rg（ripgrep）可执行文件，已回退到 Python 扫描。"
    except subprocess.TimeoutExpired:
        return True, "搜索超时（30s）。请缩小搜索范围或减少 max_matches。"


def search_tool_impl(query: str, root: str, glob: Optional[str] = None, max_matches: int = 50) -> str:
    """
    在 root 下进行文本搜索（类似 Cursor Search）。
    """
    ok, out = _run_rg(query=query, root=root, glob=glob, max_matches=max_matches)
    if ok:
        return out

    # Python fallback：逐文件扫描（仅文本）
    rootp = Path(root)
    if not rootp.exists():
        return f"root 不存在：{root}"

    patterns = None
    if glob:
        # 简单 glob：只支持 *xxx* / *.py 等；复杂 glob 仍交给 rg
        patterns = [glob]

    hits: List[str] = []
    scanned = 0
    for fp in rootp.rglob("*"):
        if fp.is_dir():
            continue
        if patterns and not any(fp.match(p) for p in patterns):
            continue
        # 跳过明显二进制
        if fp.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".exe", ".dll", ".zip", ".pdf"}:
            continue
        scanned += 1
        if scanned > 2500:
            break
        try:
            txt = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            if query in line:
                hits.append(f"{fp}:{i}:{line}")
                if len(hits) >= max_matches:
                    break
        if len(hits) >= max_matches:
            break

    if not hits:
        return f"{out}\n未找到匹配内容（Python 扫描 files={scanned}）。"
    return _truncate(out + "\n" + "\n".join(hits), 20000)


def read_file_tool_impl(path: str, start_line: int = 1, end_line: int = 200) -> str:
    p = Path(path)
    if not p.exists():
        return f"文件不存在：{path}"
    if start_line < 1:
        start_line = 1
    if end_line < start_line:
        end_line = start_line
    try:
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as e:
        return f"读取失败：{type(e).__name__}: {e}"
    start_idx = start_line - 1
    end_idx = min(len(lines), end_line)
    out_lines = []
    for i in range(start_idx, end_idx):
        out_lines.append(f"{i+1}|{lines[i]}")
    return "\n".join(out_lines) if out_lines else "（文件为空或行范围无内容）"


def write_file_tool_impl(path: str, content: str, mode: str = "overwrite") -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        if mode not in ("overwrite", "append"):
            return "mode 仅支持 overwrite 或 append"
        if mode == "append":
            with open(p, "a", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
        return f"写入成功：{path}（mode={mode}，chars={len(content)}）"
    except Exception as e:
        return f"写入失败：{type(e).__name__}: {e}"


def replace_in_file_tool_impl(path: str, old: str, new: str, count: int = 1) -> str:
    p = Path(path)
    if not p.exists():
        return f"文件不存在：{path}"
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if old not in txt:
            return "未找到 old 字符串，未修改。"
        txt2 = txt.replace(old, new, count)
        p.write_text(txt2, encoding="utf-8")
        return f"替换成功：{path}（count={count}）"
    except Exception as e:
        return f"替换失败：{type(e).__name__}: {e}"


def terminal_tool_impl(command: str, cwd: Optional[str] = None, timeout_s: int = 30) -> str:
    try:
        cp = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_s)),
        )
        out = ""
        if cp.stdout:
            out += cp.stdout
        if cp.stderr:
            out += ("\n" if out else "") + cp.stderr
        out = out.strip()
        if not out:
            out = "（无输出）"
        return _truncate(f"exit_code={cp.returncode}\n{out}", 20000)
    except subprocess.TimeoutExpired:
        return f"命令超时（{timeout_s}s）：{command}"
    except Exception as e:
        return f"执行失败：{type(e).__name__}: {e}"


def preview_tool_impl(target: str) -> str:
    """
    预览入口：
    - 若是 http(s) URL：返回并尝试打开浏览器
    - 若是本地文件：返回 file:// 并尝试打开
    """
    try:
        if re.match(r"^https?://", target.strip(), flags=re.I):
            url = target.strip()
            try:
                webbrowser.open(url)
            except Exception:
                pass
            return f"预览URL：{url}"

        p = Path(target)
        if p.exists():
            url = p.resolve().as_uri()
            try:
                webbrowser.open(url)
            except Exception:
                pass
            return f"预览文件：{url}"
        return f"目标不存在：{target}"
    except Exception as e:
        return f"预览失败：{type(e).__name__}: {e}"


def web_search_tool_impl(query: str, max_results: int = 5) -> str:
    """
    轻量联网搜索（无需 API Key）。
    - 使用 DuckDuckGo HTML 结果页进行解析（尽量稳定，但不保证长期可用）。
    """
    q = query.strip()
    if not q:
        return "query 不能为空"
    try:
        url = "https://duckduckgo.com/html/"
        resp = requests.post(url, data={"q": q}, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text or ""
        # 粗解析
        results: List[Tuple[str, str]] = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            href = m.group(1)
            title = re.sub(r"<.*?>", "", m.group(2))
            title = re.sub(r"\s+", " ", title).strip()
            if href and title:
                results.append((title, href))
            if len(results) >= max_results:
                break
        if not results:
            return "未解析到搜索结果（可能被网络/站点策略限制）。"
        out = []
        for i, (title, href) in enumerate(results, 1):
            out.append(f"{i}. {title}\n   {href}")
        return "\n".join(out)
    except Exception as e:
        return f"联网搜索失败：{type(e).__name__}: {e}"


def github_tool_impl(
    action: str,
    repo: Optional[str] = None,
    query: Optional[str] = None,
    owner: Optional[str] = None,
    name: Optional[str] = None,
    max_results: int = 5,
) -> str:
    """
    GitHub 工具（MCP GitHub 的“项目内替代版”）。
    依赖：环境变量 GITHUB_TOKEN（可选，但无 token 限额很紧）。
    """
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def _get(url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        return requests.get(url, headers=headers, params=params, timeout=30)

    try:
        action = (action or "").strip().lower()
        if action == "repo_info":
            r = repo or (f"{owner}/{name}" if owner and name else "")
            if not r or "/" not in r:
                return "repo_info 需要 repo='owner/name' 或 owner+name"
            resp = _get(f"https://api.github.com/repos/{r}")
            if resp.status_code != 200:
                return f"GitHub API失败：{resp.status_code} {resp.text[:200]}"
            data = resp.json()
            keep = {k: data.get(k) for k in ["full_name", "description", "stargazers_count", "forks_count", "open_issues_count", "default_branch", "html_url"]}
            return json.dumps(keep, ensure_ascii=False, indent=2)

        if action == "search_code":
            # q 示例： "foo in:file repo:owner/name"
            if not query:
                return "search_code 需要 query"
            resp = _get("https://api.github.com/search/code", params={"q": query, "per_page": max_results})
            if resp.status_code != 200:
                return f"GitHub API失败：{resp.status_code} {resp.text[:200]}"
            data = resp.json()
            items = data.get("items", [])[:max_results]
            out = []
            for it in items:
                out.append(f"- {it.get('repository', {}).get('full_name')}:{it.get('path')} ({it.get('html_url')})")
            return "\n".join(out) if out else "无匹配结果。"

        return "action 仅支持 repo_info | search_code"
    except Exception as e:
        return f"GitHub工具失败：{type(e).__name__}: {e}"


def playwright_tool_impl(action: str, url: str, out_path: Optional[str] = None) -> str:
    """
    Playwright 工具（MCP Playwright 的“项目内替代版”）。
    - 若未安装 playwright，则返回提示信息。
    """
    action = (action or "").strip().lower()
    if action not in ("screenshot",):
        return "action 仅支持 screenshot"
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return "未安装 playwright（pip install playwright && playwright install）。"

    out_path = out_path or f"playwright_{int(time.time())}.png"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
        return f"截图完成：{out_path}"
    except Exception as e:
        return f"Playwright执行失败：{type(e).__name__}: {e}"


def build_cursor_like_tools(base_dir: str) -> List["Tool"]:
    if StructuredTool is None:
        return []

    root = str(Path(base_dir).resolve())

    def _search(query: str, glob: str = "", max_matches: int = 50) -> str:
        return search_tool_impl(query=query, root=root, glob=(glob or None), max_matches=max_matches)

    def _read(path: str, start_line: int = 1, end_line: int = 200) -> str:
        p = _safe_abspath(root, path)
        return read_file_tool_impl(p, start_line=start_line, end_line=end_line)

    def _write(path: str, content: str, mode: str = "overwrite") -> str:
        p = _safe_abspath(root, path)
        return write_file_tool_impl(p, content=content, mode=mode)

    def _replace(path: str, old: str, new: str, count: int = 1) -> str:
        p = _safe_abspath(root, path)
        return replace_in_file_tool_impl(p, old=old, new=new, count=count)

    def _terminal(command: str, timeout_s: int = 30) -> str:
        return terminal_tool_impl(command=command, cwd=root, timeout_s=timeout_s)

    def _preview(target: str) -> str:
        # 允许预览 base_dir 内文件 or URL
        if re.match(r"^https?://", (target or "").strip(), flags=re.I):
            return preview_tool_impl(target)
        p = _safe_abspath(root, target)
        return preview_tool_impl(p)

    def _web_search(query: str, max_results: int = 5) -> str:
        return web_search_tool_impl(query=query, max_results=max_results)

    def _github(action: str, repo: str = "", query: str = "", owner: str = "", name: str = "", max_results: int = 5) -> str:
        return github_tool_impl(action=action, repo=repo or None, query=query or None, owner=owner or None, name=name or None, max_results=max_results)

    def _playwright(action: str, url: str, out_path: str = "") -> str:
        # out_path 写到 base_dir 下
        op = out_path.strip() or ""
        if op:
            op = _safe_abspath(root, op)
        else:
            op = str(Path(root) / f"playwright_{int(time.time())}.png")
        return playwright_tool_impl(action=action, url=url, out_path=op)

    return [
        StructuredTool.from_function(
            name="search",
            description="在项目目录内搜索文本（类似 Cursor Search）。参数：query, glob(可选), max_matches(可选)",
            func=_search,
        ),
        StructuredTool.from_function(
            name="github",
            description="GitHub 工具（MCP GitHub 的替代版）。action=repo_info/search_code。需要时配置环境变量 GITHUB_TOKEN。",
            func=_github,
        ),
        StructuredTool.from_function(
            name="playwright",
            description="Playwright 工具（MCP Playwright 的替代版）。action=screenshot，参数：url, out_path(可选)。",
            func=_playwright,
        ),
        StructuredTool.from_function(
            name="read",
            description="读取项目内文件内容。参数：path, start_line(可选), end_line(可选)",
            func=_read,
        ),
        StructuredTool.from_function(
            name="write",
            description="写入项目内文件。参数：path, content, mode=overwrite|append",
            func=_write,
        ),
        StructuredTool.from_function(
            name="replace",
            description="对项目内文件执行字符串替换。参数：path, old, new, count(可选)",
            func=_replace,
        ),
        StructuredTool.from_function(
            name="terminal",
            description="在项目根目录执行命令并返回输出。参数：command, timeout_s(可选)",
            func=_terminal,
        ),
        StructuredTool.from_function(
            name="preview",
            description="预览URL或项目内文件（会尝试用系统浏览器打开）。参数：target",
            func=_preview,
        ),
        StructuredTool.from_function(
            name="web_search",
            description="联网搜索（无需API Key，尽力解析）。参数：query, max_results(可选)",
            func=_web_search,
        ),
    ]


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


def plan_tool_calls_with_llm(
    llm_call: Callable[[List[Dict[str, str]]], str],
    tools: List["Tool"],
    user_message: str,
    max_calls: int = 3,
) -> List[ToolCall]:
    """
    让模型输出 JSON tool_calls，然后在本地执行。
    - 兼容当前项目使用 Ark 客户端（无需依赖 LangChain 的 LLM 包）。
    """
    tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    prompt = f"""你可以调用工具来获取信息或执行操作，然后再回答用户。

可用工具：
{tool_desc}

规则：
1. 仅当确实需要外部信息/文件/命令时才调用工具
2. 最多调用 {max_calls} 次工具
3. 只输出 JSON（不要输出多余文字）

输出 JSON 格式：
{{
  "tool_calls": [
    {{"name": "tool_name", "arguments": {{...}}}}
  ]
}}

用户问题：
{user_message}
"""
    raw = llm_call([{"role": "user", "content": prompt}])
    try:
        # 提取 JSON（兼容代码块）
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return []
        data = json.loads(m.group(0))
        calls = data.get("tool_calls") or []
        out: List[ToolCall] = []
        for c in calls[:max_calls]:
            name = str(c.get("name") or "").strip()
            args = c.get("arguments") or {}
            if not name or not isinstance(args, dict):
                continue
            out.append(ToolCall(name=name, arguments=args))
        return out
    except Exception:
        return []


def execute_tool_calls(tools: List["Tool"], calls: List[ToolCall]) -> List[Dict[str, Any]]:
    tool_map = {t.name: t for t in tools}
    results: List[Dict[str, Any]] = []
    for c in calls:
        t = tool_map.get(c.name)
        if not t:
            results.append({"name": c.name, "ok": False, "result": "未知工具"})
            continue
        try:
            res = t.run(c.arguments)
            results.append({"name": c.name, "ok": True, "result": _truncate(res, 20000)})
        except Exception as e:
            results.append({"name": c.name, "ok": False, "result": f"{type(e).__name__}: {e}"})
    return results


def format_tool_results_for_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return ""
    parts = ["\n\n【工具调用结果】"]
    for r in results:
        name = r.get("name")
        ok = r.get("ok")
        result = r.get("result", "")
        parts.append(f"\n---\n工具：{name}\n状态：{'OK' if ok else 'FAIL'}\n输出：\n{result}")
    return "\n".join(parts) + "\n"

