# Patch ops_agent.py — warning status + incident prompt tweak
from pathlib import Path
p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\ops_agent.py")
t = p.read_text(encoding="utf-8")

old_m = """        # 只处理失败的任务
        if status != \"failed\" or not error_info:
            logger.info(f\"任务 {task_id} 状态正常，无需分析\")
            return None
        
        logger.info(f\"检测到任务失败，开始分析: {task_id}\")
        
        # 分析错误
        error_analysis = self._analyze_error(error_info, logs)"""
new_m = """        # 失败与「已降级恢复」类警告均上报运维 Agent（由调用方区分 severity）
        if status not in (\"failed\", \"warning\") or not error_info:
            logger.info(f\"任务 {task_id} 状态正常，无需分析\")
            return None

        logger.info(f\"检测到运维事件 status={status} task={task_id}，开始分析\")

        # 分析错误
        error_analysis = self._analyze_error(error_info, logs, incident_status=status)"""
if old_m not in t:
    raise SystemExit("monitor block missing")
t = t.replace(old_m, new_m, 1)

old_an = """    def _analyze_error(self, error_info: Dict, logs: List[str]) -> ErrorAnalysis:"""
new_an = """    def _analyze_error(self, error_info: Dict, logs: List[str], incident_status: str = \"failed\") -> ErrorAnalysis:"""
if old_an not in t:
    raise SystemExit("_analyze_error sig missing")
t = t.replace(old_an, new_an, 1)

old_p_intro = """        prompt = f\"\"\"请分析以下系统错误，并提供详细的维护建议。

## 错误信息"""
new_p_intro = """        sev_note = \"\"
        if incident_status == \"warning\":
            sev_note = (
                \"## 事件级别\\\\n**警告（warning）**：业务可能已通过备用链路恢复或部分功能仍可用。\\\\n\"
                \"请侧重：根因、预防复发、是否应调整 config（如主备 endpoint）、是否在控制台关闭限额/安全体验模式等。\\\\n\\\\n\"
            )

        prompt = f\"\"\"{sev_note}请分析以下系统错误，并提供详细的维护建议。

## 错误信息"""
if old_p_intro not in t:
    raise SystemExit("prompt intro missing")
t = t.replace(old_p_intro, new_p_intro, 1)

# JSON hint for retry/config
old_json = """    \"api_config_recommendation\": \"若与火山/Ark 相关：是否应更换 endpoint_id、核对 base_url、检查 API Key；否则填无。\"
}"""
new_json = """    \"api_config_recommendation\": \"若与火山/Ark 相关：是否应更换 endpoint_id、核对 base_url、检查 API Key、控制台关闭 Safe Experience/提额；否则填无。须写明是否建议将 config.json 的 ai_chat_model 与 ai_chat_model_backup 对调以优先使用稳定 endpoint。\"
}"""
if old_json not in t:
    raise SystemExit("json block missing")
t = t.replace(old_json, new_json, 1)

p.write_text(t, encoding="utf-8")
print("ops_agent ok")
