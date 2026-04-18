import unittest

from fastapi.testclient import TestClient

from app.main import app


class SettingsModulesApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_settings_modules(self):
        r = self.client.get("/api/settings/modules")
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertTrue(payload["ok"])
        data = payload["data"]
        self.assertIn("ai_gateway", data)
        self.assertIn("agent_models", data)
        self.assertIn("prompt_center", data)
        self.assertIn("runtime_pools", data)
        pc = data["prompt_center"]
        self.assertIn("chat_agent", pc)
        self.assertIn("doc_standardize_agent", pc)
        self.assertIn("doc_summarize_agent", pc)
        self.assertIn("ops_agent", pc)

    def test_menu_tree_api(self):
        r = self.client.get("/api/menu/tree")
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertTrue(payload["ok"])
        items = payload["data"].get("items", [])
        self.assertTrue(any((x or {}).get("key") == "ops" for x in items))

        save_body = {
            "tree": {
                "version": 2,
                "items": [
                    {"key": "video", "title": "链接文档化", "children": []},
                    {"key": "ops", "title": "OPS运维", "children": [{"key": "ops_agent", "title": "运维AGENT"}]},
                ],
            }
        }
        r2 = self.client.post("/api/menu/tree", json=save_body)
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json()["ok"])

    def test_save_single_module(self):
        body = {"data": {"system_workers": 16, "queue_max_size": 88}}
        r = self.client.post("/api/settings/modules/runtime_pools", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

        r2 = self.client.get("/api/settings/modules")
        data = r2.json()["data"]["runtime_pools"]
        self.assertEqual(data.get("system_workers"), 16)
        self.assertEqual(data.get("queue_max_size"), 88)

    def test_prompt_center_version_fields(self):
        body = {
            "data": {
                "chat_agent": {
                    "layer1_role_flow": "role-flow",
                    "layer2_rules": "rules",
                    "layer2_constraints": "constraints",
                    "layer2_reply_format": "format",
                    "layer3_eval_strategy": "eval",
                    "version": 2,
                    "changelog": "v2 change",
                }
            }
        }
        r = self.client.post("/api/settings/modules/prompt_center", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])
        got = self.client.get("/api/settings/modules").json()["data"]["prompt_center"]["chat_agent"]
        self.assertEqual(int(got.get("version", 0)), 2)
        self.assertTrue(int(got.get("updated_at", 0)) > 0)
        self.assertIn("changelog", got)

    def test_ops_route_endpoints(self):
        r1 = self.client.post(
            "/api/ops/route/mark-failed",
            json={"model_id": "ep-test", "error_type": "timeout", "context": {"src": "ut"}},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(r1.json()["ok"])

        r2 = self.client.post(
            "/api/ops/route/reconfigure",
            json={"model_id": "ep-test", "action": "degrade_weight"},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json()["ok"])
        self.assertTrue(r2.json()["data"]["applied"])

        # 验证路由池被真实更新
        modules = self.client.get("/api/settings/modules").json()["data"]
        pool = modules["ai_gateway"]["routing"].get("model_pool", [])
        row = next((x for x in pool if x.get("model_id") == "ep-test"), None)
        self.assertIsNotNone(row)
        self.assertIn("weight", row)
        self.assertIn("status", row)

        # 再执行 disable，确认状态变化
        r2b = self.client.post(
            "/api/ops/route/reconfigure",
            json={"model_id": "ep-test", "action": "disable"},
        )
        self.assertEqual(r2b.status_code, 200)
        modules2 = self.client.get("/api/settings/modules").json()["data"]
        pool2 = modules2["ai_gateway"]["routing"].get("model_pool", [])
        row2 = next((x for x in pool2 if x.get("model_id") == "ep-test"), None)
        self.assertIsNotNone(row2)
        self.assertEqual(row2.get("status"), "disabled")
        self.assertEqual(int(row2.get("weight", -1)), 0)

        # 验证回滚接口可用
        rb = self.client.post("/api/ops/route/rollback-last", json={"history_index": -1})
        self.assertEqual(rb.status_code, 200)
        self.assertTrue(rb.json()["ok"])
        self.assertTrue(rb.json()["data"]["rolled_back"])

        # 按指定历史索引回滚也可执行
        rb2 = self.client.post("/api/ops/route/rollback-last", json={"history_index": 0})
        self.assertEqual(rb2.status_code, 200)
        self.assertTrue(rb2.json()["ok"])

    def test_observability_overview_and_events(self):
        # 先制造几条调用事件
        self.client.get("/api/health")
        self.client.get("/api/settings/modules")
        self.client.post("/api/workflow/run", json={"payload": {"x": 1}})

        r1 = self.client.get("/api/ops/observability/overview")
        self.assertEqual(r1.status_code, 200)
        p1 = r1.json()
        self.assertTrue(p1["ok"])
        self.assertIn("total_calls", p1["data"])
        self.assertIn("avg_cost_ms", p1["data"])
        self.assertIn("top_paths", p1["data"])

        r2 = self.client.get("/api/ops/observability/events?limit=20")
        self.assertEqual(r2.status_code, 200)
        p2 = r2.json()
        self.assertTrue(p2["ok"])
        self.assertIn("events", p2["data"])

        r3 = self.client.get("/api/ops/route/suggestions")
        self.assertEqual(r3.status_code, 200)
        self.assertTrue(r3.json()["ok"])
        self.assertIn("suggestions", r3.json()["data"])


if __name__ == "__main__":
    unittest.main()

