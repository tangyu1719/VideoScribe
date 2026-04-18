#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi.testclient import TestClient
import main


def run():
    c = TestClient(main.app)

    # 映射表与覆盖率
    p = c.get("/api/mapping/progress")
    assert p.status_code == 200
    pj = p.json()
    assert pj.get("ok") is True
    total = pj["data"]["total"]
    assert total >= 30
    assert c.get("/").status_code == 200

    # GUI 统一事件入口（已实现）
    r1 = c.post("/api/gui/show_chat_page", json={"payload": {"tab": "assistant"}})
    assert r1.status_code == 200
    assert r1.json()["data"]["status"] == "implemented"

    # 会话管理：创建 -> 重命名 -> 加载 -> 删除
    create = c.post("/api/gui/create_new_session", json={"payload": {"title": "web迁移测试会话"}})
    assert create.status_code == 200 and create.json().get("ok") is True
    sid = create.json()["data"]["session"]["id"]

    r2 = c.post("/api/gui/rename_session", json={"payload": {"session_id": sid, "title": "new"}})
    assert r2.status_code == 200
    assert r2.json().get("ok") is True

    load = c.post("/api/gui/load_session", json={"payload": {"session_id": sid}})
    assert load.status_code == 200 and load.json().get("ok") is True

    delete = c.post("/api/gui/delete_session", json={"payload": {"session_id": sid}})
    assert delete.status_code == 200 and delete.json().get("ok") is True

    # 工作流控制：启动调度 -> 运行 -> 停止当前 -> 停止调度
    s1 = c.post("/api/gui/save_and_start_workflow_scheduler", json={"payload": {"mode": "manual"}})
    assert s1.status_code == 200 and s1.json().get("ok") is True

    run_wf = c.post("/api/gui/run_selected_workflow", json={"payload": {"workflow_id": "wf1"}})
    assert run_wf.status_code == 200 and run_wf.json().get("ok") is True

    stop_cur = c.post("/api/gui/stop_current_workflow_run", json={"payload": {}})
    assert stop_cur.status_code == 200 and stop_cur.json().get("ok") is True

    s2 = c.post("/api/gui/stop_workflow_scheduler", json={"payload": {}})
    assert s2.status_code == 200 and s2.json().get("ok") is True

    # 聊天 SSE
    s = c.post("/api/chat/stream", json={"message": "你能调用哪些工具", "session_id": "s1"})
    assert s.status_code == 200
    text = s.text
    assert "thinking_start" in text
    assert "answer_end" in text

    print("ALL_OK")


if __name__ == "__main__":
    run()
