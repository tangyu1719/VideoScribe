# -*- coding: utf-8 -*-
from pathlib import Path

vg = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py")
t = vg.read_text(encoding="utf-8")

old_ops = """                self.ops_agent = create_ops_agent(
                    api_key="ebc08852-e7ae-4e64-b71c-79cfcce9d251",
                    api_model="ep-20260411182220-jv5qt"
                )"""
new_ops = """                self.ops_agent = create_ops_agent(
                    api_key=CONFIG.get("volcengine_api_key") or AI_CHAT_API_KEY,
                    api_model=CONFIG.get("ai_chat_model") or AI_CHAT_MODEL,
                )"""
if old_ops not in t:
    raise SystemExit("ops create not found")
t = t.replace(old_ops, new_ops, 1)

old_open = """    def open_ai_api_config_window(self):
        \"\"\"打开AI API配置窗口（API Key、Model等）\"\"\"
        if AI_API_CONFIG_AVAILABLE:
            open_ai_api_config_window(self.root)"""
new_open = """    def _apply_ai_api_runtime_config(self, main_config, backup_configs):
        \"\"\"将 API 窗口中的主/备配置写回 config.json，与 summarize/chat 使用同一数据源。\"\"\"
        global CONFIG
        CONFIG = {**CONFIG}
        if main_config.get("api_key"):
            CONFIG["volcengine_api_key"] = main_config["api_key"]
        if main_config.get("endpoint_id"):
            CONFIG["ai_chat_model"] = main_config["endpoint_id"]
        if main_config.get("base_url"):
            CONFIG["volcengine_base_url"] = main_config["base_url"]
        if main_config.get("model"):
            CONFIG["ai_chat_model_display_name"] = main_config["model"]
        if backup_configs:
            ep = (backup_configs[0] or {}).get("endpoint_id") or ""
            if ep:
                CONFIG["ai_chat_model_backup"] = ep
        save_config(CONFIG)
        self.append_log("已同步 AI API 到 config.json（主/备接入点与密钥）", "INFO")

    def open_ai_api_config_window(self):
        \"\"\"打开AI API配置窗口（API Key、Model等）\"\"\"
        if AI_API_CONFIG_AVAILABLE:
            open_ai_api_config_window(
                self.root,
                get_runtime_config=lambda: CONFIG.copy(),
                on_save_runtime=self._apply_ai_api_runtime_config,
            )"""
if old_open not in t:
    raise SystemExit("open_ai_api not found")
t = t.replace(old_open, new_open, 1)

vg.write_text(t, encoding="utf-8")
print("video_gui patched")

oa = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\ops_agent.py")
s = oa.read_text(encoding="utf-8")

old_dc = """    requires_downtime: bool  # 是否需要停机


@dataclass
class MaintenanceRecord:"""
new_dc = """    requires_downtime: bool  # 是否需要停机
    api_failure_suspected: bool = False  # 是否与 LLM/API 调用相关
    api_config_recommendation: str = ""  # 是否应调整 endpoint/base_url/key 等


@dataclass
class MaintenanceRecord:"""
if old_dc not in s:
    raise SystemExit("dataclass not found")
s = s.replace(old_dc, new_dc, 1)

# Extend SYSTEM_PROMPT output JSON - find the closing brace before 优先级定义
needle = """    \"requires_downtime\": true/false
}

## 优先级定义"""
if needle not in s:
    raise SystemExit("system prompt needle not found")
repl = """    \"requires_downtime\": true/false,
    \"api_failure_suspected\": true/false,
    \"api_config_recommendation\": \"若日志含 401/403/429、InvalidEndpoint、model not found、Ark API 等，说明是否应更换火山 endpoint_id、核对 base_url（chat 多为 /api/v3）、轮换 API Key；否则填无。\"
}

## 优先级定义"""
s = s.replace(needle, repl, 1)

# Add API section to user prompt in _analyze_error
old_p = """6. 判断是否需要停机维护

请严格按照JSON格式输出分析结果。\"\"\""""
new_p = """6. 判断是否需要停机维护
7. 若错误与火山引擎/Ark/HTTP 状态码/OpenAPI 有关，必须填写 api_failure_suspected 与 api_config_recommendation

请严格按照JSON格式输出分析结果。\"\"\""""
if old_p not in s:
    raise SystemExit("analyze prompt not found")
s = s.replace(old_p, new_p, 1)

old_ret = """            return ErrorAnalysis(
                error_type=analysis_dict.get("error_type", error_type),
                error_message=analysis_dict.get("error_message", error_message),
                root_cause=analysis_dict.get("root_cause", "未分析出根因"),
                business_impact=analysis_dict.get("business_impact", "未知"),
                code_level_fix=analysis_dict.get("code_level_fix", "无建议"),
                business_level_fix=analysis_dict.get("business_level_fix", "无建议"),
                priority=analysis_dict.get("priority", "medium"),
                estimated_fix_time=analysis_dict.get("estimated_fix_time", "未知"),
                requires_downtime=analysis_dict.get("requires_downtime", False)
            )"""
new_ret = """            return ErrorAnalysis(
                error_type=analysis_dict.get("error_type", error_type),
                error_message=analysis_dict.get("error_message", error_message),
                root_cause=analysis_dict.get("root_cause", "未分析出根因"),
                business_impact=analysis_dict.get("business_impact", "未知"),
                code_level_fix=analysis_dict.get("code_level_fix", "无建议"),
                business_level_fix=analysis_dict.get("business_level_fix", "无建议"),
                priority=analysis_dict.get("priority", "medium"),
                estimated_fix_time=analysis_dict.get("estimated_fix_time", "未知"),
                requires_downtime=analysis_dict.get("requires_downtime", False),
                api_failure_suspected=analysis_dict.get("api_failure_suspected", False),
                api_config_recommendation=analysis_dict.get("api_config_recommendation", ""),
            )"""
if old_ret not in s:
    raise SystemExit("ErrorAnalysis return not found")
s = s.replace(old_ret, new_ret, 1)

old_def = """            return ErrorAnalysis(
                error_type=error_type,
                error_message=error_message,
                root_cause=f"自动分析失败: {e}",
                business_impact="需要人工评估",
                code_level_fix="请查看原始错误信息",
                business_level_fix="请评估业务影响",
                priority="medium",
                estimated_fix_time="未知",
                requires_downtime=False
            )"""
new_def = """            return ErrorAnalysis(
                error_type=error_type,
                error_message=error_message,
                root_cause=f"自动分析失败: {e}",
                business_impact="需要人工评估",
                code_level_fix="请查看原始错误信息",
                business_level_fix="请评估业务影响",
                priority="medium",
                estimated_fix_time="未知",
                requires_downtime=False,
                api_failure_suspected=False,
                api_config_recommendation="",
            )"""
if old_def not in s:
    raise SystemExit("default ErrorAnalysis not found")
s = s.replace(old_def, new_def, 1)

md_ins = """### 业务级别修复

{analysis.business_level_fix}

---

## 维护计划"""
md_new = """### 业务级别修复

{analysis.business_level_fix}

---

## API 配置研判（运维 Agent）

| 项目 | 内容 |
|------|------|
| **疑似 API 故障** | {api_sus} |
| **配置调整建议** | {api_rec} |

---

## 维护计划"""
if md_ins not in s:
    raise SystemExit("md insert not found")
s = s.replace(md_ins, md_new, 1)

# md_content uses f-string - need api_sus and api_rec variables - they're inside _generate_maintenance_md
# Replace in md_content = f"""...""" - find analysis.business_level_fix section in file

old_md = """{analysis.business_level_fix}

---

## 维护计划

| 项目 | 内容 |
|------|------|
| **优先级** | {analysis.priority.upper()} |"""
new_md = """{analysis.business_level_fix}

---

## API 配置研判（运维 Agent）

| 项目 | 内容 |
|------|------|
| **疑似 API 故障** | {'是' if analysis.api_failure_suspected else '否'} |
| **配置调整建议** | {analysis.api_config_recommendation or '（模型未给出或与本错误无关）'} |

---

## 维护计划

| 项目 | 内容 |
|------|------|
| **优先级** | {analysis.priority.upper()} |"""
if old_md not in s:
    raise SystemExit("md block not found")
s = s.replace(old_md, new_md, 1)

# Remove erroneous md_ins replacement if we did both - check duplicate

s = s.replace(md_new.replace("{api_sus}", "").replace("{api_rec}", ""), "")  # noop

oa.write_text(s, encoding="utf-8")
print("ops_agent patched")
