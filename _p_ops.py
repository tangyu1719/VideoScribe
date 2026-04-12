from pathlib import Path
oa = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\ops_agent.py")
s = oa.read_text(encoding="utf-8")

old_dc = """    requires_downtime: bool  # 是否需要停机


@dataclass
class MaintenanceRecord:"""
new_dc = """    requires_downtime: bool  # 是否需要停机
    api_failure_suspected: bool = False
    api_config_recommendation: str = ""


@dataclass
class MaintenanceRecord:"""
if old_dc not in s:
    raise SystemExit("dataclass not found")
s = s.replace(old_dc, new_dc, 1)

needle = """    \"requires_downtime\": true/false
}

## 优先级定义"""
repl = """    \"requires_downtime\": true/false,
    \"api_failure_suspected\": true/false,
    \"api_config_recommendation\": \"若与火山/Ark 相关：是否应更换 endpoint_id、核对 base_url、检查 API Key；否则填无。\"
}

## 优先级定义"""
if needle not in s:
    raise SystemExit("system json not found")
s = s.replace(needle, repl, 1)

old_p = """5. 评估优先级和修复时间
6. 判断是否需要停机维护

请严格按照JSON格式输出分析结果。\"\"\""""
new_p = """5. 评估优先级和修复时间
6. 判断是否需要停机维护
7. 若错误与火山引擎/Ark/HTTP 状态码/OpenAPI 有关，填写 api_failure_suspected 与 api_config_recommendation

请严格按照JSON格式输出分析结果。\"\"\""""
if old_p not in s:
    raise SystemExit("user prompt not found")
s = s.replace(old_p, new_p, 1)

old_ret = """                requires_downtime=analysis_dict.get("requires_downtime", False)
            )"""
new_ret = """                requires_downtime=analysis_dict.get("requires_downtime", False),
                api_failure_suspected=analysis_dict.get("api_failure_suspected", False),
                api_config_recommendation=analysis_dict.get("api_config_recommendation", ""),
            )"""
if old_ret not in s:
    raise SystemExit("return not found")
s = s.replace(old_ret, new_ret, 1)

old_def = """                requires_downtime=False
            )"""
new_def = """                requires_downtime=False,
                api_failure_suspected=False,
                api_config_recommendation="",
            )"""
# might match multiple - only the one in except block has specific context
ctx = """            return ErrorAnalysis(
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
ctx_new = """            return ErrorAnalysis(
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
if ctx not in s:
    raise SystemExit("except return not found")
s = s.replace(ctx, ctx_new, 1)

old_md = """{analysis.business_level_fix}

---

## 维护计划

| 项目 | 内容 |
|------|------|
| **优先级** | {analysis.priority.upper()} |"""
new_md = """{analysis.business_level_fix}

---

## API 配置研判

| 项目 | 内容 |
|------|------|
| **疑似 API 故障** | {'是' if analysis.api_failure_suspected else '否'} |
| **配置调整建议** | {analysis.api_config_recommendation or '（未识别为 API 配置类问题）'} |

---

## 维护计划

| 项目 | 内容 |
|------|------|
| **优先级** | {analysis.priority.upper()} |"""
if old_md not in s:
    raise SystemExit("md not found")
s = s.replace(old_md, new_md, 1)

oa.write_text(s, encoding="utf-8")
print("ops ok")
