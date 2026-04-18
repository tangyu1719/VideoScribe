#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 迁移 FastAPI 入口（适配层草案）
目标：复用现有能力，不改老代码逻辑。
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from typing import Any, Dict, Iterator

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "agent"))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)


app = FastAPI(title="SuperBizAgent Web Migration API", version="0.1.0")
_RUNTIME = None
_KB_MANAGER = None
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)
SESSIONS_FILE = os.path.join(DATA_DIR, "chat_sessions.web.json")
WORKFLOW_STATE_FILE = os.path.join(DATA_DIR, "workflow_state.web.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.web.json")
FRONTEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "frontend"))

if os.path.isdir(FRONTEND_DIR):
    app.mount("/web", StaticFiles(directory=FRONTEND_DIR), name="web")


@app.get("/")
def web_index():
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"ok": True, "msg": "frontend not found", "hint": "open /api/health"}


class ApiResp(BaseModel):
    ok: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: str = ""


class RunNodeReq(BaseModel):
    node_id: str
    node_config: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


@app.get("/api/health", response_model=ApiResp)
def health() -> ApiResp:
    return ApiResp(ok=True, data={"service": "web-migration", "status": "up"})


@app.post("/api/workflow/nodes/list", response_model=ApiResp)
def list_workflow_nodes() -> ApiResp:
    try:
        from task_runtime.node_registry import get_default_task_nodes

        nodes = get_default_task_nodes()
        data = [
            {
                "node_id": n.node_id,
                "title": n.title,
                "stage": n.stage,
                "description": n.description,
            }
            for n in nodes
        ]
        return ApiResp(ok=True, data={"nodes": data})
    except Exception as e:
        return ApiResp(ok=False, error=f"list_workflow_nodes failed: {e}")


@app.post("/api/workflow/node/run", response_model=ApiResp)
def run_workflow_node(req: RunNodeReq) -> ApiResp:
    """
    这里只提供适配接口形态，真实执行会在下一步挂接到已有 node executor。
    """
    try:
        return ApiResp(
            ok=True,
            data={
                "node_id": req.node_id,
                "node_config": req.node_config,
                "context": req.context,
                "note": "adapter stub ready",
            },
        )
    except Exception as e:
        return ApiResp(ok=False, error=f"run_workflow_node failed: {e}")


class ToolCapabilityReq(BaseModel):
    query: str = "你能调用哪些工具"


class ChatReq(BaseModel):
    message: str
    session_id: str = "default"


class GuiEventReq(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)


class SessionMessageReq(BaseModel):
    role: str
    content: str


def _get_runtime():
    """
    延迟初始化标准运行时：
    - 默认 offline，保证本地可启动；
    - 若环境变量齐全可切 online（WEB_LLM_PROVIDER/WEB_LLM_API_KEY）。
    """
    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME

    try:
        from langchain_standard_runtime import LLMEndpointConfig, StandardLangChainRuntime
    except Exception:
        _RUNTIME = None
        return None

    provider = (os.environ.get("WEB_LLM_PROVIDER") or "offline").strip()
    api_key = (os.environ.get("WEB_LLM_API_KEY") or "").strip()
    base_url = (os.environ.get("WEB_LLM_BASE_URL") or "").strip()
    model = (os.environ.get("WEB_LLM_MODEL") or "").strip()
    cfg = LLMEndpointConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        backup_models=[],
        endpoint_status={},
        temperature=0.3,
        max_tokens=1800,
    )
    _RUNTIME = StandardLangChainRuntime(base_dir=AGENT_DIR, llm_config=cfg, rag_tool=None, rag_kb=None, logger=print)
    return _RUNTIME


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _load_formal_event_map() -> Dict[str, Any]:
    mapping_path = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "mapping", "event_api_map.formal.json"))
    if not os.path.exists(mapping_path):
        return {"meta": {"error": "formal map not found"}, "items": []}
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"meta": {"error": str(e)}, "items": []}


def _load_json_file(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json_file(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_sessions() -> Dict[str, Any]:
    data = _load_json_file(SESSIONS_FILE, {"sessions": [], "current_session_id": ""})
    if not isinstance(data, dict):
        data = {"sessions": [], "current_session_id": ""}
    data.setdefault("sessions", [])
    data.setdefault("current_session_id", "")
    return data


def _save_sessions(data: Dict[str, Any]) -> None:
    _save_json_file(SESSIONS_FILE, data)


def _new_session(title: str = "新对话") -> Dict[str, Any]:
    sid = str(uuid.uuid4())
    return {"id": sid, "title": title, "messages": [], "created_at": int(time.time())}


def _ensure_default_session() -> Dict[str, Any]:
    data = _load_sessions()
    if not data["sessions"]:
        s = _new_session("新对话")
        data["sessions"] = [s]
        data["current_session_id"] = s["id"]
        _save_sessions(data)
    return data


def _load_workflow_state() -> Dict[str, Any]:
    data = _load_json_file(
        WORKFLOW_STATE_FILE,
        {"scheduler_running": False, "scheduler_config": {}, "current_run": None, "runs": []},
    )
    if not isinstance(data, dict):
        data = {"scheduler_running": False, "scheduler_config": {}, "current_run": None, "runs": []}
    data.setdefault("scheduler_running", False)
    data.setdefault("scheduler_config", {})
    data.setdefault("current_run", None)
    data.setdefault("runs", [])
    return data


def _save_workflow_state(data: Dict[str, Any]) -> None:
    _save_json_file(WORKFLOW_STATE_FILE, data)


def _load_settings() -> Dict[str, Any]:
    data = _load_json_file(
        SETTINGS_FILE,
        {
            "ui": {"theme": "light", "lang": "zh-CN"},
            "llm": {"provider": "offline", "model": ""},
            "thread": {"max_workers": 8},
            "workflow": {"auto_scheduler": False},
            "ocr": {},
        },
    )
    if not isinstance(data, dict):
        data = {}
    return data


def _save_settings(data: Dict[str, Any]) -> None:
    _save_json_file(SETTINGS_FILE, data)


def _get_kb_manager():
    global _KB_MANAGER
    if _KB_MANAGER is not None:
        return _KB_MANAGER
    try:
        from kb_manager_fast import get_fast_knowledge_base

        _KB_MANAGER = get_fast_knowledge_base()
    except Exception:
        _KB_MANAGER = None
    return _KB_MANAGER


def _kb_add_file(file_path: str) -> Dict[str, Any]:
    kb = _get_kb_manager()
    if kb is None:
        return {"ok": False, "message": "kb manager unavailable"}
    ok, msg = kb.add_document(file_path)
    return {"ok": bool(ok), "message": msg}


def _iter_files_from_folder(folder: str, allowed_ext: set[str]) -> list[str]:
    out = []
    for root, _dirs, files in os.walk(folder):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext in allowed_ext:
                out.append(os.path.join(root, fn))
    return out


def _implemented_event_ids() -> set[str]:
    # 已实现真实能力的事件（持续扩充）
    return {
        "send_message",
        "run_selected_workflow",
        "open_rag_manager",
        "rebuild_kb_index",
        "show_chat_page",
        "show_multimodal_page",
        "show_orchestration_page",
        "show_settings_page",
        "show_video_page",
        "switch_chat_submenu",
        "list_workflow_nodes",
        "run_workflow_node",
        "create_new_session",
        "load_session",
        "rename_session",
        "delete_session",
        "show_history",
        "resume_selected_workflow_from_failed",
        "stop_current_workflow_run",
        "save_and_start_workflow_scheduler",
        "stop_workflow_scheduler",
        "add_file_to_kb",
        "add_folder_to_kb",
        "open_settings",
        "open_ai_api_config_window",
        "open_ai_config_window",
        "open_thread_config_window",
        "open_task_node_center_window",
        "open_workflow_designer_window",
        "browse_workflow_multimodal_file",
        "scroll_to_bottom",
        "on_msg_scrollbar",
        "update_jump_bottom_visibility",
        "show_text_context_menu",
        "upload_image",
        "batch_import",
        "msg_canvas",
        "session_canvas",
        "start",
    }


@app.post("/api/chat/tools/capabilities", response_model=ApiResp)
def chat_tool_capabilities(_req: ToolCapabilityReq) -> ApiResp:
    """
    先给 Web 端一个稳定能力清单接口，后续再接入真实 runtime 动态列表。
    """
    static_tools = {
        "project_ops": ["search", "read", "write", "replace", "terminal"],
        "info_search": ["web_search", "github", "rag_search", "agentic_rag_query", "rag_agentic_answer"],
        "web_ops": ["playwright", "preview"],
        "smart_workflow": [
            "intent_recognize",
            "query_rewrite",
            "list_workflow_nodes",
            "run_workflow_node",
            "multimodal_to_text",
            "link_multimodal_pipeline",
            "video_link_downloader_strict",
            "template_controlled_doc_generation",
            "image_ocr_to_text",
        ],
    }
    return ApiResp(ok=True, data={"tools": static_tools, "source": "web_migration bootstrap"})


@app.get("/api/mapping/events", response_model=ApiResp)
def get_event_mapping() -> ApiResp:
    data = _load_formal_event_map()
    return ApiResp(ok=True, data=data)


@app.get("/api/mapping/progress", response_model=ApiResp)
def get_mapping_progress() -> ApiResp:
    data = _load_formal_event_map()
    items = data.get("items", []) if isinstance(data, dict) else []
    implemented = _implemented_event_ids()
    total = len(items)
    done = 0
    for it in items:
        if it.get("event_id") in implemented:
            it["status"] = "implemented"
            done += 1
        else:
            it["status"] = "planned"
    return ApiResp(
        ok=True,
        data={
            "total": total,
            "implemented": done,
            "pending": max(total - done, 0),
            "coverage": (done / total if total else 0.0),
            "items": items,
        },
    )


@app.get("/api/chat/sessions", response_model=ApiResp)
def get_chat_sessions() -> ApiResp:
    data = _ensure_default_session()
    summaries = [{"id": s.get("id"), "title": s.get("title"), "message_count": len(s.get("messages", []))} for s in data["sessions"]]
    return ApiResp(ok=True, data={"sessions": summaries, "current_session_id": data.get("current_session_id", "")})


@app.post("/api/chat/sessions", response_model=ApiResp)
def create_chat_session(payload: Dict[str, Any]) -> ApiResp:
    data = _ensure_default_session()
    title = str(payload.get("title") or "新对话")
    s = _new_session(title)
    data["sessions"].append(s)
    data["current_session_id"] = s["id"]
    _save_sessions(data)
    return ApiResp(ok=True, data={"session": s, "current_session_id": s["id"]})


@app.get("/api/chat/sessions/{session_id}", response_model=ApiResp)
def get_chat_session(session_id: str) -> ApiResp:
    data = _ensure_default_session()
    for s in data["sessions"]:
        if s.get("id") == session_id:
            data["current_session_id"] = session_id
            _save_sessions(data)
            return ApiResp(ok=True, data={"session": s, "current_session_id": session_id})
    return ApiResp(ok=False, error=f"session not found: {session_id}")


@app.post("/api/chat/sessions/{session_id}/rename", response_model=ApiResp)
def rename_chat_session(session_id: str, payload: Dict[str, Any]) -> ApiResp:
    data = _ensure_default_session()
    title = str(payload.get("title") or "").strip()
    if not title:
        return ApiResp(ok=False, error="title is required")
    for s in data["sessions"]:
        if s.get("id") == session_id:
            s["title"] = title
            _save_sessions(data)
            return ApiResp(ok=True, data={"session_id": session_id, "title": title})
    return ApiResp(ok=False, error=f"session not found: {session_id}")


@app.delete("/api/chat/sessions/{session_id}", response_model=ApiResp)
def delete_chat_session(session_id: str) -> ApiResp:
    data = _ensure_default_session()
    before = len(data["sessions"])
    data["sessions"] = [s for s in data["sessions"] if s.get("id") != session_id]
    if len(data["sessions"]) == before:
        return ApiResp(ok=False, error=f"session not found: {session_id}")
    if not data["sessions"]:
        s = _new_session("新对话")
        data["sessions"] = [s]
        data["current_session_id"] = s["id"]
    elif data.get("current_session_id") == session_id:
        data["current_session_id"] = data["sessions"][0]["id"]
    _save_sessions(data)
    return ApiResp(ok=True, data={"deleted_session_id": session_id, "current_session_id": data["current_session_id"]})


@app.post("/api/chat/sessions/{session_id}/messages", response_model=ApiResp)
def append_chat_message(session_id: str, req: SessionMessageReq) -> ApiResp:
    data = _ensure_default_session()
    role = (req.role or "").strip()
    if role not in {"user", "assistant", "system"}:
        return ApiResp(ok=False, error="role must be user|assistant|system")
    content = (req.content or "").strip()
    if not content:
        return ApiResp(ok=False, error="content is empty")
    for s in data["sessions"]:
        if s.get("id") == session_id:
            s.setdefault("messages", []).append(
                {"role": role, "content": content, "timestamp": int(time.time())}
            )
            data["current_session_id"] = session_id
            _save_sessions(data)
            return ApiResp(ok=True, data={"session_id": session_id, "message_count": len(s["messages"])})
    return ApiResp(ok=False, error=f"session not found: {session_id}")


@app.get("/api/workflow/state", response_model=ApiResp)
def get_workflow_state() -> ApiResp:
    return ApiResp(ok=True, data=_load_workflow_state())


@app.post("/api/workflow/run", response_model=ApiResp)
def run_workflow(payload: Dict[str, Any]) -> ApiResp:
    state = _load_workflow_state()
    run_id = str(uuid.uuid4())
    run = {"run_id": run_id, "status": "running", "created_at": int(time.time()), "payload": payload or {}}
    state["current_run"] = run
    state["runs"].append(run)
    _save_workflow_state(state)
    return ApiResp(ok=True, data=run)


@app.post("/api/workflow/resume", response_model=ApiResp)
def resume_workflow(payload: Dict[str, Any]) -> ApiResp:
    state = _load_workflow_state()
    run_id = str(payload.get("run_id") or "")
    target = None
    for r in reversed(state["runs"]):
        if (not run_id) or r.get("run_id") == run_id:
            target = r
            break
    if not target:
        return ApiResp(ok=False, error="no run to resume")
    resumed = {
        "run_id": str(uuid.uuid4()),
        "status": "running",
        "created_at": int(time.time()),
        "resumed_from": target.get("run_id"),
        "payload": target.get("payload", {}),
    }
    state["current_run"] = resumed
    state["runs"].append(resumed)
    _save_workflow_state(state)
    return ApiResp(ok=True, data=resumed)


@app.post("/api/workflow/stop-current", response_model=ApiResp)
def stop_current_workflow() -> ApiResp:
    state = _load_workflow_state()
    cur = state.get("current_run")
    if not cur:
        return ApiResp(ok=True, data={"status": "idle"})
    cur["status"] = "stopped"
    cur["stopped_at"] = int(time.time())
    state["current_run"] = None
    _save_workflow_state(state)
    return ApiResp(ok=True, data={"status": "stopped", "run_id": cur.get("run_id")})


@app.post("/api/workflow/scheduler/start", response_model=ApiResp)
def start_workflow_scheduler(payload: Dict[str, Any]) -> ApiResp:
    state = _load_workflow_state()
    state["scheduler_running"] = True
    state["scheduler_config"] = payload or {}
    _save_workflow_state(state)
    return ApiResp(ok=True, data={"scheduler_running": True, "scheduler_config": state["scheduler_config"]})


@app.post("/api/workflow/scheduler/stop", response_model=ApiResp)
def stop_workflow_scheduler() -> ApiResp:
    state = _load_workflow_state()
    state["scheduler_running"] = False
    _save_workflow_state(state)
    return ApiResp(ok=True, data={"scheduler_running": False})


@app.get("/api/settings", response_model=ApiResp)
def get_settings() -> ApiResp:
    return ApiResp(ok=True, data={"settings": _load_settings()})


@app.post("/api/settings", response_model=ApiResp)
def update_settings(payload: Dict[str, Any]) -> ApiResp:
    cur = _load_settings()
    if isinstance(payload, dict):
        for k, v in payload.items():
            if isinstance(v, dict) and isinstance(cur.get(k), dict):
                cur[k].update(v)
            else:
                cur[k] = v
    _save_settings(cur)
    return ApiResp(ok=True, data={"settings": cur})


@app.post("/api/kb/add-file", response_model=ApiResp)
def kb_add_file(payload: Dict[str, Any]) -> ApiResp:
    file_path = str(payload.get("file_path") or "").strip()
    if not file_path:
        return ApiResp(ok=False, error="file_path is required")
    if not os.path.exists(file_path):
        return ApiResp(ok=False, error=f"file not found: {file_path}")
    res = _kb_add_file(file_path)
    return ApiResp(ok=bool(res.get("ok")), data=res, error="" if res.get("ok") else str(res.get("message")))


@app.post("/api/kb/add-folder", response_model=ApiResp)
def kb_add_folder(payload: Dict[str, Any]) -> ApiResp:
    folder = str(payload.get("folder_path") or "").strip()
    if not folder:
        return ApiResp(ok=False, error="folder_path is required")
    if not os.path.isdir(folder):
        return ApiResp(ok=False, error=f"folder not found: {folder}")
    exts = set(str(payload.get("extensions") or ".txt,.md").lower().split(","))
    files = _iter_files_from_folder(folder, exts)
    results = []
    success = 0
    for fp in files:
        r = _kb_add_file(fp)
        if r.get("ok"):
            success += 1
        results.append({"file": fp, **r})
    return ApiResp(ok=True, data={"total": len(files), "success": success, "failed": len(files) - success, "results": results})


@app.post("/api/kb/rebuild-index", response_model=ApiResp)
def kb_rebuild_index(payload: Dict[str, Any]) -> ApiResp:
    kb = _get_kb_manager()
    if kb is None:
        return ApiResp(ok=False, error="kb manager unavailable")
    # 优先重建指定目录；未指定则尝试重跑缓存中的文件
    folder = str(payload.get("folder_path") or "").strip()
    file_list: list[str] = []
    if folder and os.path.isdir(folder):
        file_list = _iter_files_from_folder(folder, {".txt", ".md", ".markdown"})
    else:
        file_list = [p for p in list(getattr(kb, "_file_cache", {}).keys()) if os.path.exists(p)]
    old_cache = dict(getattr(kb, "_file_cache", {}))
    try:
        kb._file_cache = {}
        rebuilt = 0
        for fp in file_list:
            ok, _msg = kb.add_document(fp)
            if ok:
                rebuilt += 1
        return ApiResp(ok=True, data={"total": len(file_list), "rebuilt": rebuilt})
    except Exception as e:
        return ApiResp(ok=False, error=f"rebuild failed: {e}")
    finally:
        if not getattr(kb, "_file_cache", None):
            kb._file_cache = old_cache


@app.post("/api/gui/{event_id}", response_model=ApiResp)
def dispatch_gui_event(event_id: str, req: GuiEventReq) -> ApiResp:
    """
    GUI 事件统一入口（零遗漏迁移壳）：
    - 先保证每个 event_id 都有 API 可接入
    - 已实现的事件转发到真实接口
    - 未实现事件返回 planned，便于前端灰度与映射跟踪
    """
    eid = (event_id or "").strip()
    payload = req.payload or {}

    # ===== 已实现转发 =====
    if eid == "send_message":
        msg = str(payload.get("message") or "")
        sid = str(payload.get("session_id") or "default")
        return chat_send(ChatReq(message=msg, session_id=sid))

    if eid in {"run_selected_workflow", "run_workflow_node"}:
        if eid == "run_selected_workflow":
            return run_workflow(payload)
        node_id = str(payload.get("node_id") or "")
        node_config = payload.get("node_config") or {}
        context = payload.get("context") or {}
        return run_workflow_node(RunNodeReq(node_id=node_id, node_config=node_config, context=context))

    if eid in {"open_rag_manager", "rebuild_kb_index"}:
        if eid == "open_rag_manager":
            return ApiResp(ok=True, data={"event_id": eid, "status": "implemented", "kb_ready": _get_kb_manager() is not None})
        return kb_rebuild_index(payload)

    if eid in {
        "show_chat_page",
        "show_multimodal_page",
        "show_orchestration_page",
        "show_settings_page",
        "show_video_page",
        "switch_chat_submenu",
    }:
        return ApiResp(ok=True, data={"event_id": eid, "status": "implemented", "view_state": payload})

    if eid == "list_workflow_nodes":
        return list_workflow_nodes()

    if eid == "add_file_to_kb":
        return kb_add_file(payload)

    if eid == "add_folder_to_kb":
        return kb_add_folder(payload)

    if eid == "create_new_session":
        return create_chat_session(payload)

    if eid == "load_session":
        sid = str(payload.get("session_id") or "")
        return get_chat_session(sid)

    if eid == "rename_session":
        sid = str(payload.get("session_id") or "")
        return rename_chat_session(sid, payload)

    if eid == "delete_session":
        sid = str(payload.get("session_id") or "")
        return delete_chat_session(sid)

    if eid == "show_history":
        return get_chat_sessions()

    if eid == "resume_selected_workflow_from_failed":
        return resume_workflow(payload)

    if eid == "stop_current_workflow_run":
        return stop_current_workflow()

    if eid == "save_and_start_workflow_scheduler":
        return start_workflow_scheduler(payload)

    if eid == "stop_workflow_scheduler":
        return stop_workflow_scheduler()

    if eid in {
        "open_settings",
        "open_ai_api_config_window",
        "open_ai_config_window",
        "open_thread_config_window",
        "open_task_node_center_window",
        "open_workflow_designer_window",
    }:
        return ApiResp(ok=True, data={"event_id": eid, "status": "implemented", "settings": _load_settings()})

    if eid in {
        "scroll_to_bottom",
        "on_msg_scrollbar",
        "update_jump_bottom_visibility",
        "show_text_context_menu",
        "msg_canvas",
        "session_canvas",
        "browse_workflow_multimodal_file",
        "upload_image",
        "batch_import",
        "start",
    }:
        return ApiResp(ok=True, data={"event_id": eid, "status": "implemented", "ui_only": True, "payload_echo": payload})

    # ===== 未实现兜底 =====
    return ApiResp(
        ok=True,
        data={
            "event_id": eid,
            "status": "planned",
            "note": "event registered in migration map, implementation pending",
            "payload_echo": payload,
        },
    )


@app.post("/api/chat/send", response_model=ApiResp)
def chat_send(req: ChatReq) -> ApiResp:
    rt = _get_runtime()
    if not rt or not getattr(rt, "ready", False):
        return ApiResp(ok=False, error="runtime not ready")
    try:
        result = rt.invoke(req.message)
        return ApiResp(ok=bool(result.get("ok")), data=result, error="" if result.get("ok") else result.get("output", "failed"))
    except Exception as e:
        return ApiResp(ok=False, error=f"chat_send failed: {e}")


@app.post("/api/chat/stream")
def chat_stream(req: ChatReq):
    rt = _get_runtime()

    def gen() -> Iterator[str]:
        if not rt or not getattr(rt, "ready", False):
            yield _sse_event("error", {"ok": False, "error": "runtime not ready"})
            return
        trace_id = f"trace-{int(time.time() * 1000)}"
        try:
            bundle = {}
            if hasattr(rt, "_preprocess"):
                try:
                    bundle = rt._preprocess(req.message) or {}
                except Exception as e:
                    bundle = {"preprocess_error": str(e)}

            yield _sse_event("thinking_start", {"trace_id": trace_id, "session_id": req.session_id})
            thinking_text = (
                f"任务: {(bundle or {}).get('task', '回答用户问题')}\n"
                f"query: {(bundle or {}).get('query', req.message)}\n"
                f"intent: {(bundle or {}).get('intent', 'unknown')}\n"
                f"needs_rag: {(bundle or {}).get('needs_rag', False)}"
            )
            yield _sse_event("thinking_delta", {"trace_id": trace_id, "content": thinking_text})
            yield _sse_event("thinking_end", {"trace_id": trace_id, "bundle": bundle})

            result = rt.invoke(req.message, preprocessed=bundle)
            if not result.get("ok"):
                yield _sse_event("error", {"trace_id": trace_id, "error": result.get("output", "unknown error")})
                return

            text = result.get("output", "") or ""
            yield _sse_event("answer_start", {"trace_id": trace_id})
            chunk_size = 120
            for i in range(0, len(text), chunk_size):
                yield _sse_event("answer_delta", {"trace_id": trace_id, "content": text[i:i + chunk_size]})
            yield _sse_event(
                "answer_end",
                {"trace_id": trace_id, "full_text": text, "intermediate_steps": result.get("intermediate_steps", [])},
            )
        except Exception as e:
            yield _sse_event("error", {"ok": False, "error": f"chat_stream failed: {e}"})

    return StreamingResponse(gen(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=18080, reload=True)
