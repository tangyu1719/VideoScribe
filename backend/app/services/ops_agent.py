#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运维Agent服务 - 从本地工具移植
包含错误监控、维护建议生成、报告管理等功能
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: str
    error_message: str
    root_cause: str
    business_impact: str
    code_level_fix: str
    business_level_fix: str
    priority: str  # high, medium, low
    estimated_fix_time: str
    requires_downtime: bool


@dataclass
class MaintenanceRecord:
    """维护记录"""
    timestamp: str
    link: str
    task_id: str
    status: str
    error_analysis: ErrorAnalysis
    log_summary: str
    md_file_path: str


class OpsAgentService:
    """运维Agent服务"""
    
    def __init__(self, api_key: str = "", api_model: str = "gpt-4o-mini",
                 maintenance_dir: str = "./storage/maintenance"):
        """
        初始化运维Agent
        
        Args:
            api_key: LLM API密钥
            api_model: LLM模型
            maintenance_dir: 维护记录存储目录
        """
        self.api_key = api_key
        self.api_model = api_model
        self.maintenance_dir = Path(maintenance_dir)
        self.maintenance_dir.mkdir(parents=True, exist_ok=True)
        
        self.records_index_file = self.maintenance_dir / "records_index.json"
        self.records: List[MaintenanceRecord] = []
        self._lock = threading.Lock()
        
        # 加载历史记录
        self._load_records_index()
    
    def _load_records_index(self):
        """加载维护记录索引"""
        try:
            if self.records_index_file.exists():
                with open(self.records_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [MaintenanceRecord(**record) for record in data]
                print(f"[OpsAgent] 加载了 {len(self.records)} 条维护记录")
        except Exception as e:
            print(f"[OpsAgent] 加载维护记录失败: {e}")
            self.records = []
    
    def _save_records_index(self):
        """保存维护记录索引"""
        try:
            with self._lock:
                data = [asdict(record) for record in self.records]
                with open(self.records_index_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[OpsAgent] 保存维护记录失败: {e}")
    
    def monitor_task_completion(self, link: str, task_id: str, 
                               status: str, logs: List[str],
                               error_info: Optional[str] = None) -> Optional[str]:
        """
        监控任务完成状态，生成维护建议
        
        Args:
            link: 视频链接
            task_id: 任务ID
            status: 任务状态 (success/failed)
            logs: 任务日志
            error_info: 错误信息
        
        Returns:
            Optional[str]: 维护建议MD文件路径，成功时返回None
        """
        if status == "success":
            return None
        
        if not error_info:
            error_info = "任务执行失败"
        
        print(f"[OpsAgent] 检测到任务失败，开始分析错误...")
        
        # 分析错误
        error_analysis = self._analyze_error(error_info, logs)
        
        # 提取关键日志
        log_summary = self._extract_key_logs(logs, error_info[:100])
        
        # 创建维护记录
        record = MaintenanceRecord(
            timestamp=datetime.now().isoformat(),
            link=link,
            task_id=task_id,
            status=status,
            error_analysis=error_analysis,
            log_summary=log_summary,
            md_file_path=""
        )
        
        # 生成维护建议MD文件
        md_file_path = self._generate_maintenance_md(record)
        record.md_file_path = str(md_file_path)
        
        # 保存记录
        with self._lock:
            self.records.append(record)
        self._save_records_index()
        
        print(f"[OpsAgent] 维护建议已生成: {md_file_path}")
        return str(md_file_path)
    
    def _analyze_error(self, error_info: str, logs: List[str]) -> ErrorAnalysis:
        """
        使用LLM分析错误
        
        Args:
            error_info: 错误信息
            logs: 日志列表
        
        Returns:
            ErrorAnalysis: 错误分析结果
        """
        # 构建提示词
        logs_text = "\n".join(logs[-50:])  # 最近50条日志
        
        prompt = f"""请分析以下错误信息，提供详细的错误分析和修复建议。

错误信息:
{error_info}

相关日志:
{logs_text}

请按以下JSON格式输出分析结果:
{{
    "error_type": "错误类型",
    "error_message": "错误消息摘要",
    "root_cause": "根本原因分析",
    "business_impact": "业务影响",
    "code_level_fix": "代码层面的修复建议",
    "business_level_fix": "业务层面的修复建议",
    "priority": "high|medium|low",
    "estimated_fix_time": "预计修复时间",
    "requires_downtime": true|false
}}

要求:
1. error_type: 分类错误类型（如网络错误、配置错误、资源不足等）
2. root_cause: 深入分析根本原因
3. business_impact: 说明对业务的影响
4. code_level_fix: 提供具体的代码修复建议
5. business_level_fix: 提供业务流程或配置层面的建议
6. priority: 根据严重程度判断优先级
7. estimated_fix_time: 给出合理的修复时间估计
8. requires_downtime: 是否需要停机修复"""

        try:
            response = self._call_llm(prompt)
            result_json = self._extract_json(response)
            
            if result_json:
                return ErrorAnalysis(
                    error_type=result_json.get("error_type", "未知错误"),
                    error_message=result_json.get("error_message", error_info[:200]),
                    root_cause=result_json.get("root_cause", "未知"),
                    business_impact=result_json.get("business_impact", "未知"),
                    code_level_fix=result_json.get("code_level_fix", "无建议"),
                    business_level_fix=result_json.get("business_level_fix", "无建议"),
                    priority=result_json.get("priority", "medium"),
                    estimated_fix_time=result_json.get("estimated_fix_time", "未知"),
                    requires_downtime=result_json.get("requires_downtime", False)
                )
            else:
                return self._get_default_error_analysis(error_info)
                
        except Exception as e:
            print(f"[OpsAgent] 错误分析失败: {e}")
            return self._get_default_error_analysis(error_info)
    
    def _get_default_error_analysis(self, error_info: str) -> ErrorAnalysis:
        """获取默认错误分析"""
        return ErrorAnalysis(
            error_type="未知错误",
            error_message=error_info[:200],
            root_cause="需要进一步分析",
            business_impact="可能影响业务正常运行",
            code_level_fix="请检查错误日志并修复相关问题",
            business_level_fix="请评估业务影响并制定应急预案",
            priority="medium",
            estimated_fix_time="未知",
            requires_downtime=False
        )
    
    def _extract_key_logs(self, logs: List[str], error_keyword: str, 
                         context_lines: int = 5) -> str:
        """
        提取错误附近的关键日志
        
        Args:
            logs: 日志列表
            error_keyword: 错误关键词
            context_lines: 上下文行数
        
        Returns:
            str: 关键日志摘要
        """
        if not logs:
            return "无日志"
        
        # 找到包含错误关键词的日志行
        error_indices = []
        for i, log in enumerate(logs):
            if error_keyword.lower() in log.lower():
                error_indices.append(i)
        
        if not error_indices:
            # 如果没有找到，返回最后几条日志
            return "\n".join(logs[-10:])
        
        # 提取错误附近的日志
        key_logs = []
        for idx in error_indices[:3]:  # 最多处理前3个错误位置
            start = max(0, idx - context_lines)
            end = min(len(logs), idx + context_lines + 1)
            key_logs.extend(logs[start:end])
            key_logs.append("---")
        
        return "\n".join(key_logs)
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM API
        
        Args:
            prompt: 提示词
        
        Returns:
            str: LLM响应
        """
        if not self.api_key:
            return ""
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.api_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"[OpsAgent] LLM API调用失败: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"[OpsAgent] LLM API调用异常: {e}")
            return ""
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON"""
        import re
        
        try:
            return json.loads(text)
        except:
            # 尝试提取JSON代码块
            pattern = r'```json\s*(.*?)\s*```'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            
            # 尝试提取花括号内容
            pattern = r'\{.*\}'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        
        return None
    
    def _generate_maintenance_md(self, record: MaintenanceRecord) -> Path:
        """
        生成维护建议MD文件
        
        Args:
            record: 维护记录
        
        Returns:
            Path: MD文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_hash = hashlib.md5(record.task_id.encode()).hexdigest()[:8]
        filename = f"maintenance_{timestamp}_{task_hash}.md"
        file_path = self.maintenance_dir / filename
        
        # 生成MD内容
        md_content = f"""# 维护建议报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 任务ID | {record.task_id} |
| 链接 | {record.link} |
| 状态 | ❌ 失败 |
| 时间 | {record.timestamp} |

## 错误分析

### 错误类型
{record.error_analysis.error_type}

### 错误消息
```
{record.error_analysis.error_message}
```

### 根本原因
{record.error_analysis.root_cause}

### 业务影响
{record.error_analysis.business_impact}

## 修复建议

### 代码层面
{record.error_analysis.code_level_fix}

### 业务层面
{record.error_analysis.business_level_fix}

## 修复计划

| 项目 | 内容 |
|------|------|
| 优先级 | {'🔴 高' if record.error_analysis.priority == 'high' else '🟡 中' if record.error_analysis.priority == 'medium' else '🟢 低'} |
| 预计修复时间 | {record.error_analysis.estimated_fix_time} |
| 需要停机 | {'是' if record.error_analysis.requires_downtime else '否'} |

## 关键日志

```
{record.log_summary}
```

## 后续行动

1. 根据修复建议进行代码修改
2. 在测试环境验证修复效果
3. 部署到生产环境（如需要）
4. 监控任务执行情况

---

*此报告由OpsAgent自动生成*
"""
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return file_path
    
    def get_maintenance_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        获取维护摘要
        
        Args:
            days: 天数
        
        Returns:
            Dict: 统计摘要
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_records = [
            r for r in self.records
            if datetime.fromisoformat(r.timestamp) > cutoff_date
        ]
        
        # 统计错误类型
        error_types = {}
        for record in recent_records:
            error_type = record.error_analysis.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # 统计优先级
        priorities = {"high": 0, "medium": 0, "low": 0}
        for record in recent_records:
            priority = record.error_analysis.priority
            if priority in priorities:
                priorities[priority] += 1
        
        return {
            "total_records": len(recent_records),
            "period_days": days,
            "error_types": error_types,
            "priorities": priorities,
            "records": [asdict(r) for r in recent_records[-10:]]  # 最近10条
        }
    
    def get_all_records(self) -> List[MaintenanceRecord]:
        """获取所有维护记录"""
        return self.records.copy()
    
    def get_record_by_id(self, task_id: str) -> Optional[MaintenanceRecord]:
        """根据任务ID获取维护记录"""
        for record in self.records:
            if record.task_id == task_id:
                return record
        return None


# 便捷函数
def create_ops_agent_service(api_key: str = "", api_model: str = "gpt-4o-mini",
                             maintenance_dir: str = "./storage/maintenance") -> OpsAgentService:
    """创建运维Agent服务实例"""
    return OpsAgentService(api_key, api_model, maintenance_dir)
