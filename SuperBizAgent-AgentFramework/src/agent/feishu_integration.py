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
                print(f"[Feishu] 获取 tenant_access_token 失败: {data}")
                return None
            tok = data.get("tenant_access_token")
            if not tok:
                return None
            self._tenant_token = tok
            self._tenant_expire = now + float(data.get("expire", 7200))
            return tok
        except Exception as e:
            print(f"[Feishu] tenant_access_token 异常: {e}")
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
                print(f"[Feishu] 解析飞书落点失败: {e}")
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
            print(
                "[Feishu] 纯中文路径无法作为 API 落点。请填写云空间文件夹 Token（fldcn…）或完整文件夹 URL"
                "（…/drive/folder/fldcn…），可在「AI配置」中设置「云空间文件夹 Token」，或环境变量 FEISHU_FOLDER_TOKEN。"
                f" 当前: {p[:120]}"
            )
        return None

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
            print("[Feishu] 未安装 requests，无法上传")
            return None

        ft = self._resolve_folder_token(feishu_folder_path, folder_token)
        if not ft or ft == "mock_folder":
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
                    print(f"[Feishu] upload_all 失败: {up}")
                    return None
                file_token = (up.get("data") or {}).get("file_token")
                if not file_token:
                    print(f"[Feishu] upload_all 无 file_token: {up}")
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
                print(f"[Feishu] import_tasks 失败: {im}")
                return None
            ticket = (im.get("data") or {}).get("ticket")
            if not ticket:
                print(f"[Feishu] import_tasks 无 ticket: {im}")
                return None

            # 轮询导入结果
            for _ in range(60):
                time.sleep(1.0)
                gr = requests.get(
                    f"{OPEN_API}/drive/v1/import_tasks/{ticket}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )
                gj = gr.json()
                if gj.get("code") != 0:
                    print(f"[Feishu] 查询 import 失败: {gj}")
                    return None
                data = gj.get("data") or {}
                job_status = data.get("job_status")
                # 0 成功 见飞书文档
                if job_status == 0:
                    result = data.get("result") or {}
                    doc_token = result.get("token") or result.get("doc_token")
                    if not doc_token:
                        return file_token
                    doc_token = str(doc_token)
                    cfg = _load_config_fragment()
                    if cfg.get("feishu_wiki_sync_enabled"):
                        wiki_nt = self._sync_docx_to_wiki_if_configured(token, doc_token)
                        if wiki_nt:
                            return f"wiki:{wiki_nt}"
                        print("[Feishu] 知识库迁入未完成，仍保留云文档 obj_token")
                    return doc_token
                if job_status in (3, 4):
                    print(f"[Feishu] 导入任务失败 job_status={job_status} data={data}")
                    return None
            print("[Feishu] 导入任务超时")
            return None
        except Exception as e:
            print(f"[Feishu] upload_document 异常: {e}")
            return None

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
        for it in all_items:
            nm = (it.get("name") or "").strip()
            if nm == name_key:
                return (it.get("space_id") or "").strip() or None
        for it in all_items:
            nm = (it.get("name") or "").strip()
            if name_key in nm:
                return (it.get("space_id") or "").strip() or None
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
            print("[Feishu] 知识库同步：无法解析 space_id，请配置 feishu_wiki_space_name / feishu_wiki_space_id 或 feishu_wiki_anchor_node_token")
            return None

        if anchor and segments:
            parent_wiki = self._wiki_ensure_path(access_token, space_id, start_parent, segments)
        elif anchor and not segments:
            parent_wiki = start_parent
        elif not anchor and segments:
            parent_wiki = self._wiki_ensure_path(access_token, space_id, None, segments)
        else:
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
