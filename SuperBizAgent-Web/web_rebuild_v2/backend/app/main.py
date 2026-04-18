from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


app = FastAPI(title="Web Rebuild V2")

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/web", StaticFiles(directory=str(FRONTEND_DIR)), name="web")


class ApiResp(BaseModel):
    ok: bool
    data: Any = None
    error: str = ""


class GuiEventReq(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)


class SettingsReq(BaseModel):
    settings: Dict[str, Any] = Field(default_factory=dict)


class ChatSendReq(BaseModel):
    message: str
    session_id: str = "default"


class ModuleSaveReq(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


class OpsRouteReq(BaseModel):
    model_id: str = ""
    error_type: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    action: str = ""
    history_index: int = -1


class MenuSaveReq(BaseModel):
    tree: Dict[str, Any] = Field(default_factory=dict)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ops_unified_log_path() -> Path:
    return DATA_DIR / "ops_unified_log.json"


def _append_unified_log(entry: Dict[str, Any]) -> None:
    path = _ops_unified_log_path()
    rows = _load_json(path, default=[])
    if not isinstance(rows, list):
        rows = []
    rows.append(entry)
    _save_json(path, rows[-1000:])


def _safe_json_excerpt(payload: Any, max_len: int = 600) -> str:
    try:
        raw = json.dumps(payload, ensure_ascii=False)
    except Exception:
        raw = str(payload)
    if len(raw) > max_len:
        return raw[:max_len] + "...(truncated)"
    return raw


def _default_menu_tree() -> Dict[str, Any]:
    return {
        "version": 1,
        "items": [
            {"key": "video", "title": "链接文档化", "children": []},
            {"key": "workflow", "title": "任务编排", "children": []},
            {"key": "chat", "title": "AI问答", "children": []},
            {"key": "doc", "title": "文档处理", "children": []},
            {"key": "settings", "title": "设置", "children": []},
            {
                "key": "ops",
                "title": "OPS运维",
                "children": [
                    {"key": "ops_agent", "title": "运维AGENT"},
                    {"key": "ops_dashboard", "title": "OPS数据可视化"},
                ],
            },
        ],
    }


def _load_menu_from_mysql() -> Dict[str, Any] | None:
    host = os.getenv("MENU_DB_HOST", "").strip()
    user = os.getenv("MENU_DB_USER", "").strip()
    pwd = os.getenv("MENU_DB_PASSWORD", "").strip()
    db = os.getenv("MENU_DB_NAME", "").strip()
    if not (host and user and db):
        return None
    port = int(os.getenv("MENU_DB_PORT", "3306") or 3306)
    try:
        import pymysql  # type: ignore

        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=pwd,
            database=db,
            charset="utf8mb4",
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ui_menu_tree (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        tree_json LONGTEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cur.execute("SELECT tree_json FROM ui_menu_tree ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                if not row:
                    return None
                raw = row[0]
                obj = json.loads(raw) if isinstance(raw, str) else None
                if isinstance(obj, dict) and isinstance(obj.get("items"), list):
                    return obj
                return None
        finally:
            conn.close()
    except Exception:
        return None


def _save_menu_to_mysql(tree: Dict[str, Any]) -> bool:
    host = os.getenv("MENU_DB_HOST", "").strip()
    user = os.getenv("MENU_DB_USER", "").strip()
    pwd = os.getenv("MENU_DB_PASSWORD", "").strip()
    db = os.getenv("MENU_DB_NAME", "").strip()
    if not (host and user and db):
        return False
    port = int(os.getenv("MENU_DB_PORT", "3306") or 3306)
    try:
        import pymysql  # type: ignore

        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=pwd,
            database=db,
            charset="utf8mb4",
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ui_menu_tree (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        tree_json LONGTEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cur.execute("INSERT INTO ui_menu_tree(tree_json) VALUES (%s)", (json.dumps(tree, ensure_ascii=False),))
            return True
        finally:
            conn.close()
    except Exception:
        return False


@app.middleware("http")
async def unified_observability_middleware(request: Request, call_next):
    # 统一日志平面：记录 API 调用耗时、状态、入参摘要
    if request.url.path.startswith("/web"):
        return await call_next(request)
    ts = int(time.time())
    start = time.perf_counter()
    req_excerpt = ""
    try:
        if request.method in ("POST", "PUT", "PATCH"):
            raw = await request.body()
            req_excerpt = _safe_json_excerpt(raw.decode("utf-8", errors="ignore"))
    except Exception:
        req_excerpt = ""
    status_code = 500
    err_text = ""
    try:
        response = await call_next(request)
        status_code = int(getattr(response, "status_code", 200))
        return response
    except Exception as e:
        err_text = f"{type(e).__name__}: {e}"
        raise
    finally:
        cost_ms = int((time.perf_counter() - start) * 1000)
        _append_unified_log(
            {
                "ts": ts,
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "cost_ms": cost_ms,
                "req_excerpt": req_excerpt,
                "error": err_text,
            }
        )


def _default_settings_modules() -> Dict[str, Any]:
    prompt_block = {
        "layer1_role_flow": "",
        "layer2_rules": "",
        "layer2_constraints": "",
        "layer2_reply_format": "",
        "layer3_eval_strategy": "",
        "version": 1,
        "updated_at": 0,
        "changelog": "",
    }
    return {
        "ai_gateway": {
            "provider": "ark",
            "providers": {
                "ark": {"base_url": "", "api_key": "", "endpoint_id": "", "timeout_sec": 90},
                "openai": {"base_url": "", "api_key": "", "model": "", "timeout_sec": 90},
                "anthropic": {"base_url": "", "api_key": "", "model": "", "timeout_sec": 90},
            },
            "routing": {
                "mode": "priority",
                "task_routes": {"qa": [], "summary": [], "ops": []},
                "model_pool": [
                    {"model_id": "ep-primary", "weight": 100, "status": "active"},
                    {"model_id": "ep-backup", "weight": 50, "status": "active"},
                ],
                "ops_history": [],
            },
        },
        "agent_models": {
            "doc_standardize": {"strategy": "route", "forced_model": "", "temperature": 0.2, "top_p": 0.9},
            "doc_summarize": {"strategy": "route", "forced_model": "", "temperature": 0.4, "top_p": 0.9},
            "qa_orchestrator": {"strategy": "route", "forced_model": "", "temperature": 0.5, "top_p": 0.9},
            "ops_agent": {"strategy": "priority", "forced_model": "", "temperature": 0.2, "top_p": 0.8},
        },
        "prompt_center": {
            "chat_agent": dict(prompt_block),
            "doc_standardize_agent": dict(prompt_block),
            "doc_summarize_agent": dict(prompt_block),
            "ops_agent": dict(prompt_block),
        },
        "runtime_pools": {
            "system_workers": 8,
            "rag_workers": 4,
            "whisper_pool_size": 4,
            "mineru_workers": 2,
            "queue_max_size": 64,
        },
    }


def _settings_modules_path() -> Path:
    return DATA_DIR / "settings_modules.json"


def _load_settings_modules() -> Dict[str, Any]:
    path = _settings_modules_path()
    data = _load_json(path, default={})
    merged = _default_settings_modules()
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k].update(v)
            else:
                merged[k] = v
    return merged


def _save_settings_modules(data: Dict[str, Any]) -> None:
    _save_json(_settings_modules_path(), data)


@app.get("/api/health")
def health():
    return ApiResp(ok=True, data={"service": "web-rebuild-v2"})


@app.get("/api/menu/tree", response_model=ApiResp)
def get_menu_tree() -> ApiResp:
    tree = _load_menu_from_mysql()
    if not tree:
        tree = _load_json(DATA_DIR / "menu_tree_fallback.json", default={}) or _default_menu_tree()
    return ApiResp(ok=True, data=tree)


@app.post("/api/menu/tree", response_model=ApiResp)
def save_menu_tree(req: MenuSaveReq) -> ApiResp:
    tree = req.tree or {}
    if not isinstance(tree, dict) or not isinstance(tree.get("items"), list):
        return ApiResp(ok=False, error="invalid menu tree")
    saved_mysql = _save_menu_to_mysql(tree)
    if not saved_mysql:
        _save_json(DATA_DIR / "menu_tree_fallback.json", tree)
    return ApiResp(ok=True, data={"saved": True, "mysql": bool(saved_mysql)})


@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.post("/api/gui/{event_id}", response_model=ApiResp)
def gui_dispatch(event_id: str, req: GuiEventReq) -> ApiResp:
    """
    统一 GUI 事件入口：前端按钮/操作都映射到这里。
    后续再逐个把 event_id 路由到真实业务实现。
    """
    return ApiResp(ok=True, data={"event_id": event_id, "payload_echo": req.payload, "status": "planned"})


@app.get("/api/settings", response_model=ApiResp)
def get_settings() -> ApiResp:
    path = DATA_DIR / "settings.json"
    data = _load_json(path, default={})
    return ApiResp(ok=True, data=data)


@app.post("/api/settings", response_model=ApiResp)
def save_settings(req: SettingsReq) -> ApiResp:
    path = DATA_DIR / "settings.json"
    _save_json(path, req.settings)
    return ApiResp(ok=True, data={"saved": True})


@app.get("/api/settings/modules", response_model=ApiResp)
def get_settings_modules() -> ApiResp:
    return ApiResp(ok=True, data=_load_settings_modules())


@app.post("/api/settings/modules/{module_name}", response_model=ApiResp)
def save_settings_module(module_name: str, req: ModuleSaveReq) -> ApiResp:
    allowed = {"ai_gateway", "agent_models", "prompt_center", "runtime_pools"}
    if module_name not in allowed:
        return ApiResp(ok=False, error=f"unsupported module: {module_name}")
    modules = _load_settings_modules()
    payload = req.data or {}
    if module_name == "prompt_center":
        now_ts = int(time.time())
        prev_prompt_center = (modules.get("prompt_center", {}) or {})
        agent_keys = ["chat_agent", "doc_standardize_agent", "doc_summarize_agent", "ops_agent"]
        if not isinstance(payload, dict):
            payload = {}
        for key in agent_keys:
            cur = payload.get(key) or {}
            prev = prev_prompt_center.get(key) or {}
            prev_ver = int(prev.get("version", 1) or 1)
            try:
                next_ver = int(cur.get("version", prev_ver))
            except Exception:
                next_ver = prev_ver
            if next_ver < prev_ver:
                next_ver = prev_ver
            cur["version"] = next_ver
            cur["updated_at"] = now_ts
            if "changelog" not in cur:
                cur["changelog"] = ""
            payload[key] = cur
    modules[module_name] = payload
    _save_settings_modules(modules)
    return ApiResp(ok=True, data={"saved": True, "module": module_name})


@app.post("/api/ops/route/mark-failed", response_model=ApiResp)
def ops_mark_model_failed(req: OpsRouteReq) -> ApiResp:
    path = DATA_DIR / "ops_route_events.json"
    events = _load_json(path, default=[])
    if not isinstance(events, list):
        events = []
    events.append(
        {
            "ts": int(time.time()),
            "type": "mark_failed",
            "model_id": req.model_id,
            "error_type": req.error_type or "unknown",
            "context": req.context or {},
        }
    )
    _save_json(path, events[-300:])
    return ApiResp(ok=True, data={"recorded": True, "event_count": len(events[-300:])})


@app.post("/api/ops/route/reconfigure", response_model=ApiResp)
def ops_reconfigure_route(req: OpsRouteReq) -> ApiResp:
    modules = _load_settings_modules()
    gateway = modules.get("ai_gateway", {})
    routing = gateway.get("routing", {})
    action = (req.action or "").strip() or "degrade_weight"
    model_id = (req.model_id or "").strip()
    suggestion = {
        "action": action,
        "model_id": model_id,
        "note": "ops agent suggested route compensation",
        "updated_at": int(time.time()),
    }
    pool = routing.get("model_pool", [])
    if not isinstance(pool, list):
        pool = []
    changed = False
    before = None
    after = None
    for row in pool:
        if str(row.get("model_id")) != model_id:
            continue
        before = dict(row)
        changed = True
        if action == "degrade_weight":
            row["weight"] = max(1, int(row.get("weight", 100)) - 30)
        elif action == "disable":
            row["status"] = "disabled"
            row["weight"] = 0
        elif action == "recover":
            row["status"] = "active"
            row["weight"] = max(10, int(row.get("weight", 50)))
        after = dict(row)
        break
    if model_id and not changed:
        created = {"model_id": model_id, "weight": 50, "status": "active"}
        pool.append(created)
        before = None
        after = dict(created)
        changed = True

    history = routing.get("ops_history", [])
    if not isinstance(history, list):
        history = []
    suggestion["before"] = before
    suggestion["after"] = after
    history.append(suggestion)
    routing["ops_history"] = history[-100:]
    routing["model_pool"] = pool
    routing["last_ops_action"] = suggestion
    gateway["routing"] = routing
    modules["ai_gateway"] = gateway
    _save_settings_modules(modules)
    return ApiResp(ok=True, data={"applied": True, "suggestion": suggestion})


@app.post("/api/ops/route/rollback-last", response_model=ApiResp)
def ops_rollback_last(req: OpsRouteReq) -> ApiResp:
    modules = _load_settings_modules()
    gateway = modules.get("ai_gateway", {})
    routing = gateway.get("routing", {})
    pool = routing.get("model_pool", [])
    history = routing.get("ops_history", [])
    if not isinstance(pool, list):
        pool = []
    if not isinstance(history, list) or not history:
        return ApiResp(ok=False, error="no history to rollback")

    idx = req.history_index if isinstance(req.history_index, int) else -1
    if idx < 0:
        idx = len(history) - 1
    if idx >= len(history):
        return ApiResp(ok=False, error="history_index out of range")

    item = history[idx] or {}
    model_id = str(item.get("model_id") or "")
    before = item.get("before")
    if not model_id:
        return ApiResp(ok=False, error="history item missing model_id")

    applied = False
    for i, row in enumerate(pool):
        if str(row.get("model_id")) != model_id:
            continue
        if isinstance(before, dict):
            pool[i] = dict(before)
        else:
            pool[i]["status"] = "active"
            pool[i]["weight"] = max(10, int(pool[i].get("weight", 50)))
        applied = True
        break
    if not applied and isinstance(before, dict):
        pool.append(dict(before))
        applied = True

    rollback_entry = {
        "action": "rollback",
        "model_id": model_id,
        "updated_at": int(time.time()),
        "target_history_index": idx,
    }
    history.append(rollback_entry)
    routing["ops_history"] = history[-100:]
    routing["model_pool"] = pool
    routing["last_ops_action"] = rollback_entry
    gateway["routing"] = routing
    modules["ai_gateway"] = gateway
    _save_settings_modules(modules)
    return ApiResp(ok=True, data={"rolled_back": True, "entry": rollback_entry})


@app.get("/api/ops/route/suggestions", response_model=ApiResp)
def ops_route_suggestions() -> ApiResp:
    path = DATA_DIR / "ops_route_events.json"
    events = _load_json(path, default=[])
    if not isinstance(events, list):
        events = []
    by_model: Dict[str, int] = {}
    for e in events[-200:]:
        model_id = str((e or {}).get("model_id") or "unknown")
        by_model[model_id] = by_model.get(model_id, 0) + 1
    ranked = sorted(by_model.items(), key=lambda x: x[1], reverse=True)
    suggestions = []
    for model_id, cnt in ranked[:5]:
        suggestions.append(
            {
                "model_id": model_id,
                "recent_failures": cnt,
                "recommended_action": "degrade_or_disable" if cnt >= 3 else "watch",
            }
        )
    return ApiResp(ok=True, data={"suggestions": suggestions, "sample_size": len(events[-200:])})


@app.get("/api/ops/observability/events", response_model=ApiResp)
def ops_observability_events(limit: int = 100) -> ApiResp:
    rows = _load_json(_ops_unified_log_path(), default=[])
    if not isinstance(rows, list):
        rows = []
    lim = max(1, min(int(limit), 500))
    return ApiResp(ok=True, data={"events": rows[-lim:]})


@app.get("/api/ops/observability/overview", response_model=ApiResp)
def ops_observability_overview() -> ApiResp:
    rows = _load_json(_ops_unified_log_path(), default=[])
    if not isinstance(rows, list):
        rows = []
    sample = rows[-300:]
    total = len(sample)
    ok_count = sum(1 for r in sample if int((r or {}).get("status_code", 500)) < 400)
    fail_count = total - ok_count
    avg_cost = int(sum(int((r or {}).get("cost_ms", 0)) for r in sample) / total) if total else 0
    top_paths: Dict[str, int] = {}
    for r in sample:
        p = str((r or {}).get("path") or "/unknown")
        top_paths[p] = top_paths.get(p, 0) + 1
    top = sorted(top_paths.items(), key=lambda x: x[1], reverse=True)[:10]
    return ApiResp(
        ok=True,
        data={
            "total_calls": total,
            "success_calls": ok_count,
            "failed_calls": fail_count,
            "avg_cost_ms": avg_cost,
            "top_paths": [{"path": p, "count": c} for p, c in top],
        },
    )


@app.get("/api/workflow/state", response_model=ApiResp)
def get_workflow_state() -> ApiResp:
    # 先给前端一个稳定的数据形态（后续接入真实执行态）
    return ApiResp(
        ok=True,
        data={
            "current": None,
            "scheduler_running": False,
            "updated_at": int(time.time()),
        },
    )


@app.post("/api/workflow/run", response_model=ApiResp)
def workflow_run(req: GuiEventReq) -> ApiResp:
    return ApiResp(ok=True, data={"started": True, "payload": req.payload})


@app.post("/api/workflow/resume", response_model=ApiResp)
def workflow_resume(req: GuiEventReq) -> ApiResp:
    return ApiResp(ok=True, data={"resumed": True, "payload": req.payload})


@app.post("/api/workflow/stop-current", response_model=ApiResp)
def workflow_stop_current(req: GuiEventReq) -> ApiResp:
    return ApiResp(ok=True, data={"stopped": True, "payload": req.payload})


@app.post("/api/workflow/scheduler/start", response_model=ApiResp)
def workflow_scheduler_start(req: GuiEventReq) -> ApiResp:
    return ApiResp(ok=True, data={"scheduler_running": True, "payload": req.payload})


@app.post("/api/workflow/scheduler/stop", response_model=ApiResp)
def workflow_scheduler_stop(req: GuiEventReq) -> ApiResp:
    return ApiResp(ok=True, data={"scheduler_running": False, "payload": req.payload})


@app.post("/api/kb/rebuild-index", response_model=ApiResp)
def kb_rebuild_index(req: GuiEventReq) -> ApiResp:
    # 注意：真实重建会耗时；这里先提供 API 形态，避免前端按钮空转
    return ApiResp(ok=True, data={"rebuild_started": True, "payload": req.payload})


@app.post("/api/chat/send", response_model=ApiResp)
def chat_send(req: ChatSendReq) -> ApiResp:
    # 先给可用的“回声式”回答，保证 UI 通路；后续接入真实 LLM/SSE
    answer = f"（Web Rebuild V2 临时回声）你说：{req.message}"
    return ApiResp(ok=True, data={"session_id": req.session_id, "answer": answer})


@app.post("/api/chat/stream")
def chat_stream(req: ChatSendReq):
    def gen():
        # SSE 最小协议，保证前端能对接流式 UI
        yield "event: thinking_start\n"
        yield "data: " + json.dumps({"content": "智能助手正在分析..."}, ensure_ascii=False) + "\n\n"
        yield "event: thinking_end\n"
        yield "data: " + json.dumps({"content": "done"}, ensure_ascii=False) + "\n\n"
        yield "event: answer_start\n"
        yield "data: " + json.dumps({"content": ""}, ensure_ascii=False) + "\n\n"
        text = f"（Web Rebuild V2 临时流式）你说：{req.message}"
        for ch in text:
            yield "event: answer_delta\n"
            yield "data: " + json.dumps({"content": ch}, ensure_ascii=False) + "\n\n"
        yield "event: answer_end\n"
        yield "data: " + json.dumps({"full_text": text}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
