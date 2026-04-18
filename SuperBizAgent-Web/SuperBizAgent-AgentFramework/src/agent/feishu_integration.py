# -*- coding: utf-8 -*-
"""
飞书云空间：上传 Markdown 为云文档（导入为 docx）。
需配置「云空间文件夹」的 fldcn Token 作为导入暂存（OpenAPI 要求）。
可选：导入后将文档迁入指定「知识库」路径（见 feishu_wiki_* 配置）。
知识库侧飞书不支持 API 直接创建「文件夹」，缺省时用空白云文档页作目录占位。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

OPEN_API = "https://open.feishu.cn/open-apis"


def _cfg_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def _load_config_fragment() -> Dict[str, Any]:
    try:
        import sys

        vg = sys.modules.get("video_gui")
        if vg is not None:
            cfg = getattr(vg, "CONFIG", None)
            if isinstance(cfg, dict):
                return cfg
    except Exception:
        pass
    p = _cfg_path()
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


class FeishuKnowledgeBase:
    """使用飞书开放平台：tenant_access_token + 云空间上传 + 导入为在线文档。"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id.strip()
        self.app_secret = app_secret.strip()
        self._tenant_token: Optional[str] = None
        self._tenant_expire: float = 0.0
        # 最近一次失败原因（供 GUI 展示；避免仅 print 到控制台导致“上传失败但无原因”）
        self.last_error: Optional[str] = None

    def _set_error(self, msg: str) -> None:
        self.last_error = msg

    def parse_feishu_folder_from_prompt(self, prompt: str) -> Optional[str]:
        """从 User Prompt 中解析「飞书路径：xxx」。"""
        if not prompt:
            return None
        m = re.search(r"飞书路径[：:]\s*([^\n\r]+)", prompt)
        if m:
            return m.group(1).strip() or None
        return None

    def _tenant_access_token(self) -> Optional[str]:
        if requests is None:
            self._set_error("未安装 requests，无法调用飞书 OpenAPI。请先安装依赖：pip install requests")
            return None
        now = time.time()
        if self._tenant_token and now < self._tenant_expire - 60:
            return self._tenant_token
        url = f"{OPEN_API}/auth/v3/tenant_access_token/internal"
        try:
            r = requests.post(
                url,
                json={"app_id": self.app_id, "app_secret": self.app_secret},
                timeout=30,
            )
            data = r.json()
            if data.get("code") != 0:
                self._set_error(f"获取 tenant_access_token 失败: {data}")
                return None
            tok = data.get("tenant_access_token")
            if not tok:
                self._set_error(f"获取 tenant_access_token 失败：响应无 tenant_access_token: {data}")
                return None
            self._tenant_token = tok
            self._tenant_expire = now + float(data.get("expire", 7200))
            return tok
        except Exception as e:
            self._set_error(f"tenant_access_token 异常: {e}")
            return None

    @staticmethod
    def _extract_drive_folder_token(s: Optional[str]) -> Optional[str]:
        """从 fld… 裸串、或云空间文件夹 URL 中取出文件夹 token（未必以 fld 开头）。"""
        raw = (s or "").strip()
        if not raw:
            return None
        m = re.search(r"/drive/folder/([a-zA-Z0-9_-]+)", raw)
        if m:
            return m.group(1)
        if raw.startswith("fld") and "http" not in raw and "/" not in raw:
            return raw
        if "drive/folder/" in raw or raw.lower().startswith("http"):
            try:
                from lark_publish.feishu_target_url import TargetKind, parse_feishu_target

                t = parse_feishu_target(raw)
                if t.kind == TargetKind.DRIVE_FOLDER and t.folder_token:
                    return t.folder_token
                if t.kind == TargetKind.WIKI_NODE:
                    print(
                        "[Feishu] 当前为知识库节点（wikcn…），云文档导入需使用「云空间」下的文件夹。"
                        "请打开该知识库在云空间中的对应文件夹，复制 …/drive/folder/fldcn… 链接或 fldcn Token。"
                    )
            except Exception as e:
                self._set_error(f"解析飞书落点失败: {e}")
        return None

    def _resolve_folder_token(
        self,
        feishu_folder_path: Optional[str],
        explicit_folder_token: Optional[str],
    ) -> Optional[str]:
        """优先显式 fldcn / 文件夹 URL；其次环境变量；再次 config.json 的 feishu_folder_token。"""
        if os.environ.get("FEISHU_MOCK_UPLOAD", "").strip() in ("1", "true", "yes"):
            return "mock_folder"
        cfg = _load_config_fragment()

        for candidate in (
            (explicit_folder_token or "").strip(),
            (os.environ.get("FEISHU_FOLDER_TOKEN") or "").strip(),
            (cfg.get("feishu_folder_token") or "").strip(),
        ):
            if not candidate:
                continue
            parsed = self._extract_drive_folder_token(candidate)
            if parsed:
                return parsed
            if candidate.startswith("fld") and "/" not in candidate:
                return candidate

        for path_like in (
            (feishu_folder_path or "").strip(),
            (cfg.get("feishu_default_folder_path") or "").strip(),
        ):
            if not path_like:
                continue
            parsed = self._extract_drive_folder_token(path_like)
            if parsed:
                return parsed

        p = (feishu_folder_path or "").strip()
        if p:
            self._set_error(
                "飞书落点无效：当前填写的是“路径字符串”，API 只能接收云空间文件夹 Token（fldcn…）或完整文件夹 URL（…/drive/folder/fldcn…）。"
                "请在「AI配置」里填写“云空间文件夹 Token”，或设置环境变量 FEISHU_FOLDER_TOKEN。"
                f" 当前输入: {p[:120]}"
            )
        return None

    def _run_lark_cli_json(self, args: List[str]) -> Optional[Dict[str, Any]]:
        """调用 lark-cli 并尽量解析 JSON 输出。"""
        try:
            exe = "lark-cli.cmd" if os.name == "nt" else "lark-cli"
            p = subprocess.run(
                [exe] + args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=120,
            )
            out = (p.stdout or "").strip()
            err = (p.stderr or "").strip()
            if not out and err:
                out = err
            if not out:
                self._set_error(f"lark-cli 无输出: {' '.join(args)}")
                return None
            try:
                return json.loads(out)
            except Exception:
                m = re.search(r"\{[\s\S]*\}\s*$", out)
                if m:
                    return json.loads(m.group(0))
                self._set_error(f"lark-cli 输出非 JSON: {out[:300]}")
                return None
        except Exception as e:
            self._set_error(f"调用 lark-cli 失败: {e}")
            return None

    def _run_lark_cli_api_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        args = ["api", method.upper(), path, "--as", "user"]
        if params:
            args.extend(["--params", json.dumps(params, ensure_ascii=False)])
        if data:
            args.extend(["--data", json.dumps(data, ensure_ascii=False)])
        return self._run_lark_cli_json(args)

    @staticmethod
    def _extract_doc_token_from_url(url: str) -> Optional[str]:
        if not url:
            return None
        m = re.search(r"/docx/([a-zA-Z0-9_-]+)", url)
        if m:
            return m.group(1)
        m = re.search(r"/wiki/([a-zA-Z0-9_-]+)", url)
        if m:
            return f"wiki:{m.group(1)}"
        return None

    @staticmethod
    def _sanitize_markdown_for_cli(markdown: str) -> str:
        """清理 CLI 参数中高风险字符，避免子进程调用异常。"""
        if not markdown:
            return ""
        # NUL 会直接破坏命令参数；统一替换为空格。
        return markdown.replace("\x00", " ")

    @staticmethod
    def _split_markdown_chunks(markdown: str, chunk_size: int = 1500) -> List[str]:
        """按段落尽量切分，避免单次 CLI 参数过长。"""
        text = markdown or ""
        if len(text) <= chunk_size:
            return [text] if text else []

        chunks: List[str] = []
        cursor = 0
        n = len(text)
        while cursor < n:
            end = min(cursor + chunk_size, n)
            if end < n:
                # 优先按空行切分，避免破坏 markdown 结构
                cut = text.rfind("\n\n", cursor, end)
                if cut != -1 and cut > cursor + 200:
                    end = cut + 2
            chunks.append(text[cursor:end])
            cursor = end
        return chunks

    def _upload_via_user_cli_fallback(self, title: str, md_content: str, folder_token: str) -> Optional[str]:
        """
        当应用态上传被权限拒绝时，降级到用户态 lark-cli：
        1) 在目标云空间文件夹创建文档；
        2) 若启用知识库同步，则尽量创建到配置的 wiki 锚点。
        """
        create = self._run_lark_cli_json(
            [
                "docs", "+create",
                "--as", "user",
                "--folder-token", folder_token,
                "--title", title[:200],
                "--markdown", "# 文档初始化\n",
            ]
        )
        if not create or not create.get("ok"):
            self._set_error(f"用户态创建文档失败: {create or self.last_error}")
            return None
        data = create.get("data") or {}
        doc_url = str(data.get("doc_url") or "")
        doc_id = str(data.get("doc_id") or "")
        base_ret = doc_id or self._extract_doc_token_from_url(doc_url)
        if not base_ret:
            self._set_error(f"用户态创建文档成功但未解析到 token: {create}")
            return None

        # 再分块写入正文，避免一次性长 markdown 触发 CLI/服务端异常。
        doc_ref = doc_url or doc_id
        sanitized_md = self._sanitize_markdown_for_cli(md_content or "")
        chunks = self._split_markdown_chunks(sanitized_md, chunk_size=1500)
        for idx, chunk in enumerate(chunks):
            upd = self._run_lark_cli_json(
                [
                    "docs", "+update",
                    "--as", "user",
                    "--doc", doc_ref,
                    "--mode", "append",
                    "--markdown", chunk,
                ]
            )
            if not upd or not upd.get("ok"):
                self._set_error(
                    f"用户态写入文档失败（chunk {idx + 1}/{len(chunks)}）: "
                    f"{upd or self.last_error}"
                )
                return None

        cfg = _load_config_fragment()
        if not cfg.get("feishu_wiki_sync_enabled"):
            return str(base_ret)

        anchor = (cfg.get("feishu_wiki_anchor_node_token") or "").strip()
        if not anchor:
            self._set_error(
                "已完成云空间上传，但知识库同步需要 feishu_wiki_anchor_node_token。"
                "当前未配置锚点，已保留云文档 token。"
            )
            return str(base_ret)

        # 用户态：先解析锚点所在空间并按配置路径逐级确保节点存在，再把文档写到最终节点
        node_res = self._run_lark_cli_api_json(
            "GET",
            "/wiki/v2/spaces/get_node",
            params={"token": anchor},
        )
        if not node_res or int(node_res.get("code", -1)) != 0:
            self._set_error(f"知识库同步失败：无法读取锚点节点信息: {node_res}")
            return str(base_ret)
        node = ((node_res.get("data") or {}).get("node") or {})
        space_id = str(node.get("space_id") or "").strip()
        if not space_id:
            self._set_error(f"知识库同步失败：锚点缺少 space_id: {node_res}")
            return str(base_ret)

        def _list_children(parent_token: Optional[str]) -> List[Dict[str, Any]]:
            out: List[Dict[str, Any]] = []
            page_token: Optional[str] = None
            for _ in range(100):
                q: Dict[str, Any] = {"page_size": 50}
                if parent_token:
                    q["parent_node_token"] = parent_token
                if page_token:
                    q["page_token"] = page_token
                r = self._run_lark_cli_api_json(
                    "GET",
                    f"/wiki/v2/spaces/{space_id}/nodes",
                    params=q,
                )
                if not r or int(r.get("code", -1)) != 0:
                    self._set_error(f"知识库同步失败：列子节点失败: {r}")
                    return out
                d = r.get("data") or {}
                out.extend(d.get("items") or [])
                if not d.get("has_more"):
                    break
                page_token = str(d.get("page_token") or "").strip() or None
            return out

        def _find_child(parent_token: Optional[str], seg_title: str) -> Optional[str]:
            for it in _list_children(parent_token):
                if str(it.get("title") or "").strip() == seg_title:
                    nt = str(it.get("node_token") or "").strip()
                    if nt:
                        return nt
            return None

        def _create_child(parent_token: Optional[str], seg_title: str) -> Optional[str]:
            body: Dict[str, Any] = {
                "obj_type": "docx",
                "node_type": "origin",
                "title": seg_title[:500],
            }
            if parent_token:
                body["parent_node_token"] = parent_token
            r = self._run_lark_cli_api_json(
                "POST",
                f"/wiki/v2/spaces/{space_id}/nodes",
                data=body,
            )
            if r and int(r.get("code", -1)) == 0:
                nd = ((r.get("data") or {}).get("node") or {})
                nt = str(nd.get("node_token") or "").strip()
                if nt:
                    return nt

            # API 创建节点权限不足时，降级为 docs +create 在父节点下创建占位页，再使用新 wiki token 作为下一级父节点
            placeholder = self._run_lark_cli_json(
                [
                    "docs", "+create",
                    "--as", "user",
                    "--wiki-node", str(parent_token or anchor),
                    "--title", seg_title[:200],
                    "--markdown", f"# {seg_title}\n\n目录占位",
                ]
            )
            if not placeholder or not placeholder.get("ok"):
                self._set_error(f"知识库同步失败：创建路径节点失败: {r or placeholder}")
                return None
            purl = str((placeholder.get("data") or {}).get("doc_url") or "")
            ptoken = self._extract_doc_token_from_url(purl)
            if ptoken and ptoken.startswith("wiki:"):
                return ptoken.split("wiki:", 1)[1]
            self._set_error(f"知识库同步失败：创建路径占位后未解析到 wiki token: {placeholder}")
            return None

        cur_parent = anchor
        path_str = (cfg.get("feishu_wiki_path_ensure") or "").strip()
        for seg in self._wiki_parse_path_segments(path_str):
            s = seg.strip()
            if not s:
                continue
            found = _find_child(cur_parent, s)
            if found:
                cur_parent = found
                continue
            created = _create_child(cur_parent, s)
            if not created:
                return str(base_ret)
            cur_parent = created

        wiki_create = self._run_lark_cli_json(
            [
                "docs", "+create",
                "--as", "user",
                "--wiki-node", cur_parent,
                "--title", title[:200],
                "--markdown", md_content or "",
            ]
        )
        if not wiki_create or not wiki_create.get("ok"):
            self._set_error(f"知识库同步（用户态）失败: {wiki_create}")
            return str(base_ret)
        wurl = str((wiki_create.get("data") or {}).get("doc_url") or "")
        wtoken = self._extract_doc_token_from_url(wurl)
        self.last_error = None
        return str(wtoken or base_ret)

    def upload_document(
        self,
        title: str,
        md_content: str,
        feishu_folder_path: Optional[str] = None,
        folder_token: Optional[str] = None,
    ) -> Optional[str]:
        """
        上传 Markdown 到云空间文件夹并导入为 docx。
        folder_token: 显式 fldcn，优先于路径字符串。
        设置 FEISHU_MOCK_UPLOAD=1 时返回 mock token（回归测试）。
        """
        if os.environ.get("FEISHU_MOCK_UPLOAD", "").strip() in ("1", "true", "yes"):
            return "mock_doc_token_ok"

        if requests is None:
            self._set_error("未安装 requests，无法上传到飞书。请先安装依赖：pip install requests")
            return None

        ft = self._resolve_folder_token(feishu_folder_path, folder_token)
        if not ft or ft == "mock_folder":
            if not self.last_error:
                self._set_error("未能解析到云空间文件夹 token（fldcn…）。")
            return None

        token = self._tenant_access_token()
        if not token:
            return None

        safe_name = re.sub(r'[\\/:*?"<>|]', "_", title)[:200] or "export"
        if not safe_name.lower().endswith(".md"):
            fname = f"{safe_name}.md"
        else:
            fname = safe_name

        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, fname)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(md_content or "")
                size = os.path.getsize(path)
                upload_url = f"{OPEN_API}/drive/v1/files/upload_all"
                headers = {"Authorization": f"Bearer {token}"}
                with open(path, "rb") as fb:
                    files = {
                        "file_name": (None, fname),
                        "parent_type": (None, "explorer"),
                        "parent_node": (None, ft),
                        "size": (None, str(size)),
                        "file": (fname, fb, "application/octet-stream"),
                    }
                    r = requests.post(upload_url, headers=headers, files=files, timeout=120)
                up = r.json()
                if up.get("code") != 0:
                    code = int(up.get("code", -1))
                    if code == 1061004:
                        self._set_error(
                            "upload_all 权限被拒绝（1061004 forbidden）。"
                            "通常是飞书应用对目标云空间文件夹无权限，或 folder token 不是当前应用可访问目录。"
                            f"当前 parent_node={ft}。请在飞书开放平台检查应用 Drive 权限与可见范围，"
                            "并确认填写的是可访问的云空间文件夹 token/URL。"
                        )
                        # 权限被拒绝时，自动尝试用户态 CLI 上传兜底（成功则直接返回 token）
                        fallback_token = self._upload_via_user_cli_fallback(title, md_content, ft)
                        if fallback_token:
                            self.last_error = None
                            return fallback_token
                    else:
                        self._set_error(f"upload_all 失败: {up}")
                    raise RuntimeError(self.last_error)
                file_token = (up.get("data") or {}).get("file_token")
                if not file_token:
                    self._set_error(f"upload_all 无 file_token: {up}")
                    return None

            imp_url = f"{OPEN_API}/drive/v1/import_tasks"
            payload = {
                "file_extension": "md",
                "file_token": file_token,
                "type": "docx",
                "file_name": safe_name[:200],
                "point": {"mount_type": 1, "mount_key": ft},
            }
            r2 = requests.post(
                imp_url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            im = r2.json()
            if im.get("code") != 0:
                self._set_error(f"import_tasks 失败: {im}")
                raise RuntimeError(self.last_error)
            ticket = (im.get("data") or {}).get("ticket")
            if not ticket:
                self._set_error(f"import_tasks 无 ticket: {im}")
                raise RuntimeError(self.last_error)

            # 轮询导入结果（大型文档导入耗时可超过 60 秒）
            for _ in range(180):
                time.sleep(1.0)
                gr = requests.get(
                    f"{OPEN_API}/drive/v1/import_tasks/{ticket}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )
                gj = gr.json()
                if gj.get("code") != 0:
                    self._set_error(f"查询 import 失败: {gj}")
                    raise RuntimeError(self.last_error)
                data = gj.get("data") or {}
                result = data.get("result") or {}
                job_status = data.get("job_status")
                if job_status is None:
                    job_status = result.get("job_status")
                # 0 成功 见飞书文档
                if job_status == 0:
                    doc_token = result.get("token") or result.get("doc_token")
                    if not doc_token:
                        return file_token
                    doc_token = str(doc_token)
                    cfg = _load_config_fragment()
                    if cfg.get("feishu_wiki_sync_enabled"):
                        wiki_nt = self._sync_docx_to_wiki_if_configured(token, doc_token)
                        if wiki_nt:
                            return f"wiki:{wiki_nt}"
                        self._set_error("知识库迁入未完成，仍保留云文档 token")
                    return doc_token
                if job_status in (3, 4):
                    self._set_error(f"导入任务失败 job_status={job_status} data={data}")
                    raise RuntimeError(self.last_error)
            self._set_error("导入任务超时（180 秒轮询仍未完成）")
            raise RuntimeError(self.last_error)
        except Exception as e:
            self._set_error(f"upload_document 异常: {e}")
            raise RuntimeError(self.last_error) from e

    # ---------- 知识库：解析空间、补全路径、迁入文档 ----------

    def _auth_headers(self, access_token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _wiki_get_node(self, access_token: str, node_token: str) -> Optional[Dict[str, Any]]:
        if requests is None or not node_token:
            return None
        r = requests.get(
            f"{OPEN_API}/wiki/v2/spaces/get_node",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"token": node_token},
            timeout=30,
        )
        j = r.json()
        if j.get("code") != 0:
            print(f"[Feishu] wiki get_node 失败: {j}")
            return None
        node = (j.get("data") or {}).get("node") or {}
        if not node.get("space_id"):
            return None
        return node

    def _wiki_resolve_space_id(self, access_token: str, cfg: Dict[str, Any]) -> Optional[str]:
        sid = (cfg.get("feishu_wiki_space_id") or "").strip()
        if sid:
            return sid
        name_key = (cfg.get("feishu_wiki_space_name") or "").strip()
        if not name_key or requests is None:
            return None
        page_token = None
        all_items: List[Dict[str, Any]] = []
        for _ in range(100):
            params: Dict[str, Any] = {"page_size": 50}
            if page_token:
                params["page_token"] = page_token
            r = requests.get(
                f"{OPEN_API}/wiki/v2/spaces",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
                timeout=30,
            )
            j = r.json()
            if j.get("code") != 0:
                print(f"[Feishu] wiki 列举知识空间失败: {j}")
                return None
            data = j.get("data") or {}
            all_items.extend(data.get("items") or [])
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        if not all_items:
            self._set_error(
                "知识库同步失败：当前应用未枚举到任何知识空间。请检查应用权限（wiki 相关 scope）和可见范围；"
                "或直接在配置里填写 feishu_wiki_space_id / feishu_wiki_anchor_node_token 以跳过空间枚举。"
            )
            print("[Feishu] wiki spaces 返回为空，建议配置 space_id 或 anchor_node_token")
            return None
        for it in all_items:
            nm = (it.get("name") or "").strip()
            if nm == name_key:
                return (it.get("space_id") or "").strip() or None
        for it in all_items:
            nm = (it.get("name") or "").strip()
            if name_key in nm:
                return (it.get("space_id") or "").strip() or None
        self._set_error(
            f"知识库同步失败：未匹配到知识空间名称（含「{name_key}」）。"
            "请核对 feishu_wiki_space_name，或直接填写 feishu_wiki_space_id / feishu_wiki_anchor_node_token。"
        )
        print(f"[Feishu] 未匹配到知识空间名称（含「{name_key}」），请核对 feishu_wiki_space_name 或填写 feishu_wiki_space_id")
        return None

    def _wiki_iter_children(
        self,
        access_token: str,
        space_id: str,
        parent_node_token: Optional[str],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        if requests is None:
            return out
        page_token = None
        for _ in range(200):
            params: Dict[str, Any] = {"page_size": 50}
            if parent_node_token:
                params["parent_node_token"] = parent_node_token
            if page_token:
                params["page_token"] = page_token
            r = requests.get(
                f"{OPEN_API}/wiki/v2/spaces/{space_id}/nodes",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
                timeout=30,
            )
            j = r.json()
            if j.get("code") != 0:
                print(f"[Feishu] wiki 列子节点失败: {j}")
                break
            data = j.get("data") or {}
            out.extend(data.get("items") or [])
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        return out

    def _wiki_find_child_node_token(
        self,
        access_token: str,
        space_id: str,
        parent_node_token: Optional[str],
        title: str,
    ) -> Optional[str]:
        want = title.strip()
        for it in self._wiki_iter_children(access_token, space_id, parent_node_token):
            if (it.get("title") or "").strip() == want:
                nt = (it.get("node_token") or "").strip()
                if nt:
                    return nt
        return None

    def _wiki_create_docx_node(
        self,
        access_token: str,
        space_id: str,
        parent_node_token: Optional[str],
        title: str,
    ) -> Optional[str]:
        if requests is None:
            return None
        body: Dict[str, Any] = {
            "obj_type": "docx",
            "node_type": "origin",
            "title": title.strip()[:500],
        }
        if parent_node_token:
            body["parent_node_token"] = parent_node_token
        r = requests.post(
            f"{OPEN_API}/wiki/v2/spaces/{space_id}/nodes",
            headers=self._auth_headers(access_token),
            json=body,
            timeout=60,
        )
        j = r.json()
        if j.get("code") != 0:
            print(f"[Feishu] wiki 创建节点失败 title={title!r}: {j}")
            return None
        node = (j.get("data") or {}).get("node") or {}
        nt = (node.get("node_token") or "").strip()
        if nt:
            print(f"[Feishu] 已在知识库创建目录占位页（空 docx）: {title!r} node_token={nt}")
        return nt or None

    def _wiki_ensure_path(
        self,
        access_token: str,
        space_id: str,
        start_parent_node_token: Optional[str],
        segments: List[str],
    ) -> Optional[str]:
        """逐级按标题查找；不存在则创建空 docx 作为目录占位。返回最后一级 node_token。"""
        cur = start_parent_node_token
        for seg in segments:
            s = seg.strip()
            if not s:
                continue
            found = self._wiki_find_child_node_token(access_token, space_id, cur, s)
            if found:
                cur = found
                continue
            created = self._wiki_create_docx_node(access_token, space_id, cur, s)
            if not created:
                return None
            cur = created
        return cur

    def _wiki_parse_path_segments(self, path_str: str) -> List[str]:
        return [p for p in path_str.replace("\\", "/").split("/") if p.strip()]

    def _wiki_poll_move_task(self, access_token: str, task_id: str, timeout_sec: int = 90) -> Optional[str]:
        if requests is None:
            return None
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            r = requests.get(
                f"{OPEN_API}/wiki/v2/tasks/{task_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"task_type": "move"},
                timeout=30,
            )
            j = r.json()
            if j.get("code") != 0:
                print(f"[Feishu] wiki 查询 move 任务失败: {j}")
                return None
            task = (j.get("data") or {}).get("task") or {}
            results = task.get("move_result") or []
            if not results:
                time.sleep(0.8)
                continue
            mr = results[0]
            st = mr.get("status")
            if st == 0:
                node = mr.get("node") or {}
                return (node.get("node_token") or "").strip() or None
            if st == 1:
                time.sleep(0.8)
                continue
            print(f"[Feishu] wiki 迁入失败: {mr.get('status_msg')}")
            return None
        print("[Feishu] wiki 迁入任务超时")
        return None

    def _wiki_move_doc_under_parent(
        self,
        access_token: str,
        space_id: str,
        parent_wiki_token: str,
        obj_token: str,
        obj_type: str = "docx",
    ) -> Optional[str]:
        if requests is None:
            return None
        r = requests.post(
            f"{OPEN_API}/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki",
            headers=self._auth_headers(access_token),
            json={
                "parent_wiki_token": parent_wiki_token,
                "obj_type": obj_type,
                "obj_token": obj_token,
            },
            timeout=60,
        )
        j = r.json()
        if j.get("code") != 0:
            self._set_error(f"wiki move_docs_to_wiki 失败: {j}")
            print(f"[Feishu] wiki move_docs_to_wiki 失败: {j}")
            return None
        data = j.get("data") or {}
        if data.get("wiki_token"):
            return str(data["wiki_token"])
        tid = data.get("task_id")
        if tid:
            return self._wiki_poll_move_task(access_token, str(tid))
        return None

    def _sync_docx_to_wiki_if_configured(self, access_token: str, docx_obj_token: str) -> Optional[str]:
        """
        将已导入的云文档（obj_token）迁入知识库配置路径下。
        成功返回新知识库节点 node_token；失败返回 None（调用方仍可保留云文档）。
        """
        cfg = _load_config_fragment()
        if not cfg.get("feishu_wiki_sync_enabled"):
            return None
        if os.environ.get("FEISHU_MOCK_UPLOAD", "").strip() in ("1", "true", "yes"):
            return "mock_wiki_node_ok"

        path_str = (cfg.get("feishu_wiki_path_ensure") or "").strip()
        segments = self._wiki_parse_path_segments(path_str)
        anchor = (cfg.get("feishu_wiki_anchor_node_token") or "").strip()

        space_id: Optional[str] = None
        start_parent: Optional[str] = None

        if anchor:
            node = self._wiki_get_node(access_token, anchor)
            if not node:
                return None
            space_id = (node.get("space_id") or "").strip() or None
            start_parent = (node.get("node_token") or "").strip() or anchor
        else:
            space_id = self._wiki_resolve_space_id(access_token, cfg)

        if not space_id:
            self._set_error(
                "知识库同步失败：无法解析 space_id。请配置 feishu_wiki_space_id，"
                "或配置 feishu_wiki_anchor_node_token 作为迁入锚点。"
            )
            print("[Feishu] 知识库同步：无法解析 space_id，请配置 feishu_wiki_space_name / feishu_wiki_space_id 或 feishu_wiki_anchor_node_token")
            return None

        if anchor and segments:
            parent_wiki = self._wiki_ensure_path(access_token, space_id, start_parent, segments)
        elif anchor and not segments:
            parent_wiki = start_parent
        elif not anchor and segments:
            parent_wiki = self._wiki_ensure_path(access_token, space_id, None, segments)
        else:
            self._set_error(
                "知识库同步失败：缺少路径锚点。请配置 feishu_wiki_path_ensure（如 就业技术文档集/AI相关）"
                "或 feishu_wiki_anchor_node_token。"
            )
            print("[Feishu] 知识库同步：请在 feishu_wiki_path_ensure 填写路径（如 就业技术文档集/AI相关），或填写 feishu_wiki_anchor_node_token")
            return None

        if not parent_wiki:
            return None

        wiki_node = self._wiki_move_doc_under_parent(
            access_token, space_id, parent_wiki, docx_obj_token, "docx"
        )
        if wiki_node:
            print(f"[Feishu] 已迁入知识库，wiki 节点: {wiki_node}")
        return wiki_node
