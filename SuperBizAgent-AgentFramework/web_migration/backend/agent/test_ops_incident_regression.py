# -*- coding: utf-8 -*-
"""运维 Agent 事件上报回归：mock LLM，不发起真实 Ark 请求。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ops_agent import OpsAgent  # noqa: E402


MOCK_JSON = json.dumps(
    {
        "error_type": "API限额",
        "error_message": "429 SetLimitExceeded",
        "root_cause": "安全体验模式限额",
        "business_impact": "主 endpoint 不可用，已降级",
        "code_level_fix": "对调主备或换 endpoint",
        "business_level_fix": "控制台关闭 Safe Experience",
        "priority": "medium",
        "estimated_fix_time": "10分钟",
        "requires_downtime": False,
        "api_failure_suspected": True,
        "api_config_recommendation": "将 ai_chat_model 改为当前备用 ep；或控制台提额",
    },
    ensure_ascii=False,
)


class TestOpsIncident(unittest.TestCase):
    def test_volcengine_primary_fail_report_as_failed_generates_md(self):
        """GUI 侧主备降级等事件以 failed 上报，与 ERROR/EXCEPTION 日志策略一致。"""
        with tempfile.TemporaryDirectory() as tmp:
            agent = OpsAgent(api_key="dummy", api_model="dummy")
            agent.maintenance_dir = Path(tmp)

            with patch.object(OpsAgent, "_call_llm", return_value=MOCK_JSON):
                md = agent.monitor_task_completion(
                    link="https://example.com/x",
                    task_id="t_volc_1",
                    status="failed",
                    logs=["line1", "429 SetLimitExceeded"],
                    error_info={
                        "type": "VolcenginePrimaryFailedBackupOk",
                        "message": "主接入点 429，备用已成功",
                        "traceback": "",
                    },
                )
            self.assertIsNotNone(md)
            self.assertTrue(Path(md).is_file())
            content = Path(md).read_text(encoding="utf-8")
            self.assertIn("失败", content)
            self.assertIn("API", content)

    def test_failed_status_generates_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = OpsAgent(api_key="dummy", api_model="dummy")
            agent.maintenance_dir = Path(tmp)

            with patch.object(OpsAgent, "_call_llm", return_value=MOCK_JSON):
                md = agent.monitor_task_completion(
                    link="https://example.com/y",
                    task_id="t_fail_1",
                    status="failed",
                    logs=["boom"],
                    error_info={"type": "RuntimeError", "message": "x", "traceback": "tb"},
                )
            self.assertIsNotNone(md)


if __name__ == "__main__":
    unittest.main()
