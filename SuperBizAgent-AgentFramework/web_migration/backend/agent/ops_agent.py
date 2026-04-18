#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运维Agent模块
- 监控链接解析结果
- 分析错误日志
- 生成修复建议MD文件
- 支持业务和代码级别的维护建议
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: str  # 错误类型
    error_message: str  # 错误信息
    root_cause: str  # 根本原因
    business_impact: str  # 业务影响
    code_level_fix: str  # 代码级别修复建议
    business_level_fix: str  # 业务级别修复建议
    priority: str  # 优先级：high/medium/low
    estimated_fix_time: str  # 预计修复时间
    requires_downtime: bool  # 是否需要停机
    api_failure_suspected: bool = False
    api_config_recommendation: str = ""


@dataclass
class MaintenanceRecord:
    """维护记录"""
    timestamp: str
    link: str
    task_id: str
    status: str
    error_analysis: Optional[ErrorAnalysis]
    log_summary: str
    md_file_path: str


class OpsAgent:
    """
    运维Agent
    
    角色定位：
    - 系统健康监控员
    - 故障诊断专家
    - 维护建议生成器
    
    动作框架：
    1. 监控：监听链接解析结果
    2. 分析：识别错误并分析根因
    3. 建议：生成业务和代码级别的修复建议
    4. 记录：保存维护建议到MD文件
    """
    
    # 系统提示词 - 定义角色和动作框架
    SYSTEM_PROMPT = """你是一位专业的系统运维Agent，负责监控系统健康状态、诊断故障并生成维护建议。

## 角色定位
- **系统健康监控员**：持续监控系统运行状态
- **故障诊断专家**：深入分析错误根因
- **维护建议生成器**：提供可执行的修复方案

## 动作框架
1. **监控**：监听链接解析任务的执行结果
2. **分析**：识别错误类型，分析根本原因
3. **建议**：生成业务和代码级别的修复建议
4. **记录**：保存维护建议到结构化MD文件

## 分析维度
### 业务级别
- 用户影响范围
- 功能可用性
- 数据完整性
- 业务流程中断点

### 代码级别
- 异常类型和堆栈
- 资源依赖（网络、文件、外部服务）
- 代码逻辑缺陷
- 配置问题

## 输出格式要求
请按以下JSON格式输出分析结果：
{
    "error_type": "错误类型分类",
    "error_message": "关键错误信息摘要",
    "root_cause": "根本原因分析（技术+业务）",
    "business_impact": "业务影响描述",
    "code_level_fix": "代码级别修复建议（具体可执行）",
    "business_level_fix": "业务级别修复建议（流程/配置层面）",
    "priority": "high/medium/low",
    "estimated_fix_time": "预计修复时间（如：30分钟、2小时）",
    "requires_downtime": true/false,
    "api_failure_suspected": true/false,
    "api_config_recommendation": "若与火山/Ark 相关：是否应更换 endpoint_id、核对 base_url、检查 API Key、控制台关闭 Safe Experience/提额；否则填无。须写明是否建议将 config.json 的 ai_chat_model 与 ai_chat_model_backup 对调以优先使用稳定 endpoint。"
}

## 优先级定义
- **high**：系统不可用、数据丢失、安全风险
- **medium**：功能受限、性能下降、用户体验差
- **low**：轻微问题、可延后处理、有workaround

## 注意事项
1. 分析要具体，避免泛泛而谈
2. 修复建议要可执行，包含具体步骤
3. 区分紧急修复和长期优化
4. 评估是否需要停机维护"""
    
    def __init__(self, api_key: Optional[str] = None, api_model: Optional[str] = None):
        """
        初始化运维Agent
        
        Args:
            api_key: 备用API密钥（可选，使用配置中的默认值）
            api_model: 备用API模型（可选，使用配置中的默认值）
        """
        self.api_key = api_key or os.getenv("OPS_AGENT_API_KEY", "")
        self.api_model = api_model or os.getenv("OPS_AGENT_API_MODEL", "ep-20260320202115-9jqfp")
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3"
        
        # 维护记录目录
        self.maintenance_dir = Path("maintenance_records")
        self.maintenance_dir.mkdir(exist_ok=True)
        
        # 维护记录索引
        self.records_index_file = self.maintenance_dir / "records_index.json"
        self.records = self._load_records_index()
        
        logger.info("运维Agent初始化完成")
    
    def _load_records_index(self) -> List[Dict]:
        """加载维护记录索引"""
        if self.records_index_file.exists():
            try:
                with open(self.records_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载维护记录索引失败: {e}")
        return []
    
    def _save_records_index(self):
        """保存维护记录索引"""
        try:
            with open(self.records_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存维护记录索引失败: {e}")
    
    def monitor_task_completion(self, link: str, task_id: str, 
                                status: str, logs: List[str],
                                error_info: Optional[Dict] = None) -> Optional[str]:
        """
        监控任务完成状态
        
        Args:
            link: 任务链接
            task_id: 任务ID
            status: 任务状态（completed/failed/cancelled）
            logs: 任务执行日志列表
            error_info: 错误信息（如果有）
        
        Returns:
            生成的MD文件路径，如果没有错误返回None
        """
        # 失败与「已降级恢复」类警告均上报运维 Agent（由调用方区分 severity）
        if status not in ("failed", "warning") or not error_info:
            logger.info(f"任务 {task_id} 状态正常，无需分析")
            return None

        logger.info(f"检测到运维事件 status={status} task={task_id}，开始分析")

        # 分析错误
        error_analysis = self._analyze_error(error_info, logs, incident_status=status)
        
        # 生成维护记录
        record = MaintenanceRecord(
            timestamp=datetime.now().isoformat(),
            link=link,
            task_id=task_id,
            status=status,
            error_analysis=error_analysis,
            log_summary="\n".join(logs[-20:]) if logs else "无日志",  # 最后20行日志
            md_file_path=""  # 稍后填充
        )
        
        # 生成MD文件
        md_path = self._generate_maintenance_md(record)
        record.md_file_path = str(md_path)
        
        # 保存记录
        self.records.append(asdict(record))
        self._save_records_index()
        
        logger.info(f"维护建议已生成: {md_path}")
        return str(md_path)
    
    def _analyze_error(self, error_info: Dict, logs: List[str], incident_status: str = "failed") -> ErrorAnalysis:
        """
        使用LLM分析错误
        
        Args:
            error_info: 错误信息字典
            logs: 日志列表
        
        Returns:
            ErrorAnalysis对象
        """
        # 构建分析提示词
        error_type = error_info.get("type", "Unknown")
        error_message = error_info.get("message", "")
        error_traceback = error_info.get("traceback", "")
        
        # 提取关键日志（错误附近的日志）
        key_logs = self._extract_key_logs(logs, error_message)
        
        sev_note = ""
        if incident_status == "warning":
            sev_note = (
                "## 事件级别\n**警告（warning）**：业务可能已通过备用链路恢复或部分功能仍可用。\n"
                "请侧重：根因、预防复发、是否应调整 config（如主备 endpoint）、是否在控制台关闭限额/安全体验模式等。\n\n"
            )

        prompt = f"""{sev_note}请分析以下系统错误，并提供详细的维护建议。

## 错误信息
- **错误类型**: {error_type}
- **错误消息**: {error_message}
- **堆栈跟踪**:
```
{error_traceback}
```

## 相关日志
```
{key_logs}
```

## 分析要求
1. 确定错误的根本原因（技术层面+业务层面）
2. 评估业务影响范围
3. 提供具体的代码级别修复步骤
4. 提供业务级别的修复建议（流程、配置等）
5. 评估优先级和修复时间
6. 判断是否需要停机维护
7. 若错误与火山引擎/Ark/HTTP 状态码/OpenAPI 有关，填写 api_failure_suspected 与 api_config_recommendation
8. 在 business_level_fix 中写明：是否建议立即重试、是否建议改配置后再重试、控制台操作优先级

请严格按照JSON格式输出分析结果。"""

        try:
            # 调用LLM进行分析
            response = self._call_llm(prompt)
            analysis_dict = self._parse_json_response(response)
            
            return ErrorAnalysis(
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
            )
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            # 返回默认分析
            return ErrorAnalysis(
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
            )
    
    def _extract_key_logs(self, logs: List[str], error_keyword: str, 
                          context_lines: int = 10) -> str:
        """提取错误附近的关键日志"""
        if not logs:
            return "无日志"
        
        key_logs = []
        for i, log in enumerate(logs):
            if error_keyword.lower() in log.lower():
                # 提取前后context_lines行
                start = max(0, i - context_lines)
                end = min(len(logs), i + context_lines + 1)
                key_logs.extend(logs[start:end])
                key_logs.append("---")
        
        return "\n".join(key_logs[-50:]) if key_logs else "\n".join(logs[-30:])
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        try:
            from volcenginesdkarkruntime import Ark
            
            client = Ark(base_url=self.api_url, api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.api_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析LLM返回的JSON"""
        import json
        import re
        
        # 尝试直接解析
        try:
            return json.loads(response)
        except:
            pass
        
        # 尝试提取JSON代码块
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        
        # 解析失败，返回空字典
        logger.warning("无法解析LLM响应为JSON")
        return {}
    
    def _generate_maintenance_md(self, record: MaintenanceRecord) -> Path:
        """生成维护建议MD文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maintenance_{record.task_id}_{timestamp}.md"
        filepath = self.maintenance_dir / filename
        
        analysis = record.error_analysis
        
        st_zh = {"failed": "失败", "warning": "警告（可能已降级恢复）", "cancelled": "已取消"}.get(
            record.status, record.status
        )

        md_content = f"""# 维护建议报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 任务ID | {record.task_id} |
| 链接 | {record.link} |
| 状态 | {st_zh} (`{record.status}`) |
| 检测时间 | {record.timestamp} |

---

## 错误分析

### 错误类型
**{analysis.error_type}**

### 错误信息
```
{analysis.error_message}
```

### 根本原因
{analysis.root_cause}

---

## 业务影响评估

{analysis.business_impact}

---

## 修复建议

### 代码级别修复

{analysis.code_level_fix}

### 业务级别修复

{analysis.business_level_fix}

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
| **优先级** | {analysis.priority.upper()} |
| **预计修复时间** | {analysis.estimated_fix_time} |
| **是否需要停机** | {'是 ⚠️' if analysis.requires_downtime else '否 ✅'} |

---

## 相关日志

<details>
<summary>点击查看详细日志</summary>

```
{record.log_summary}
```

</details>

---

## 维护记录

- 创建时间: {record.timestamp}
- 维护文件: {record.md_file_path}

---

*此报告由运维Agent自动生成*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return filepath
    
    def get_maintenance_summary(self, days: int = 7) -> Dict:
        """
        获取维护摘要
        
        Args:
            days: 最近多少天的记录
        
        Returns:
            维护摘要字典
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_records = [
            r for r in self.records
            if datetime.fromisoformat(r["timestamp"]) > cutoff_date
        ]
        
        # 统计
        total_issues = len(recent_records)
        high_priority = sum(1 for r in recent_records 
                          if r.get("error_analysis", {}).get("priority") == "high")
        requires_downtime = sum(1 for r in recent_records 
                               if r.get("error_analysis", {}).get("requires_downtime", False))
        
        # 错误类型分布
        error_types = {}
        for r in recent_records:
            error_type = r.get("error_analysis", {}).get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "period_days": days,
            "total_issues": total_issues,
            "high_priority": high_priority,
            "requires_downtime": requires_downtime,
            "error_types": error_types,
            "records": recent_records
        }


# 便捷函数
def create_ops_agent(api_key: Optional[str] = None, 
                     api_model: Optional[str] = None) -> OpsAgent:
    """创建运维Agent实例"""
    return OpsAgent(api_key, api_model)


# 测试代码
if __name__ == "__main__":
    # 创建运维Agent
    agent = create_ops_agent()
    
    # 模拟错误分析
    test_error = {
        "type": "FileNotFoundError",
        "message": "[WinError 2] 系统找不到指定的文件。",
        "traceback": "FileNotFoundError: [WinError 2] 系统找不到指定的文件。\n  at video_downloader.py:123"
    }
    
    test_logs = [
        "[INFO] 开始下载视频...",
        "[INFO] 使用yt-dlp下载",
        "[ERROR] FileNotFoundError: [WinError 2] 系统找不到指定的文件。",
        "[ERROR] 视频下载失败"
    ]
    
    # 监控任务（模拟失败场景）
    md_path = agent.monitor_task_completion(
        link="https://example.com/video",
        task_id="test_001",
        status="failed",
        logs=test_logs,
        error_info=test_error
    )
    
    if md_path:
        print(f"维护建议已生成: {md_path}")
    else:
        print("任务正常，无需生成维护建议")
