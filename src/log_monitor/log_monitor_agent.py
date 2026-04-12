"""
日志监控 Agent 核心实现
异步执行，独立 LLM 配置
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from .models import ErrorRecord, ErrorAnalysisResult, SuccessRule, FixHistory
from .config import get_llm_config, get_agent_config, AgentConfig
from .prompts import format_error_analysis_prompt, INITIAL_SUCCESS_RULES

# 导入日志和数据库模块
import sys
sys.path.insert(0, 'f:\\java\\AIOPS\\SuperBizAgent-release-2026-01-02\\demo_wendanghua\\src')
from db import get_db_connection
from logging_system import Logger

logger = Logger("LogMonitorAgent")

class LogMonitorAgent:
    """日志监控 Agent 主类"""
    
    def __init__(self):
        """初始化 Agent"""
        self.config = get_agent_config()
        self.llm_config = get_llm_config(use_backup=True)
        
        # 异步执行配置
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.thread_pool_size,
            thread_name_prefix="LogMonitorAgent"
        )
        
        # 内存缓存
        self.error_cache: Dict[str, ErrorRecord] = {}
        self.rules_cache: Dict[str, SuccessRule] = {}
        
        # 加载规则
        self._load_rules()
        
        logger.info("日志监控 Agent 初始化完成")
        logger.info(f"使用 LLM 配置：{self.llm_config.model}")
        logger.info(f"使用备用 API: {self.llm_config.base_url}")
    
    def _load_rules(self):
        """从数据库加载规则"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT * FROM success_rules WHERE is_active = TRUE")
            rows = cursor.fetchall()
            
            for row in rows:
                rule = SuccessRule.from_dict(row)
                self.rules_cache[rule.rule_id] = rule
            
            logger.info(f"加载了 {len(self.rules_cache)} 条成功规则")
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"加载规则失败：{e}")
            # 使用默认规则
            logger.info("使用默认规则")
    
    async def analyze_error(
        self,
        error_log: str,
        timestamp: datetime = None,
        module: str = "",
        context: Dict = None,
        trigger_type: str = 'task_check'
    ) -> Optional[ErrorAnalysisResult]:
        """
        分析错误
        
        Args:
            error_log: 错误日志
            timestamp: 错误发生时间
            module: 模块名称
            context: 上下文信息
            trigger_type: 触发类型 (task_check/log_alert)
        
        Returns:
            错误分析结果
        """
        if not self.config.enabled:
            logger.warning("Agent 未启用，跳过分析")
            return None
        
        logger.info(f"开始分析错误 [{trigger_type}]: {error_log[:100]}...")
        
        try:
            # 创建错误记录
            error_record = ErrorRecord(
                error_log=error_log,
                timestamp=timestamp or datetime.now(),
                module=module,
                context=context or {}
            )
            
            # 保存到缓存和数据库
            self.error_cache[error_record.id] = error_record
            await self._save_error_record(error_record)
            
            # 调用 LLM 分析
            loop = asyncio.get_event_loop()
            analysis_result = await loop.run_in_executor(
                self.executor,
                self._call_llm_analysis,
                error_record
            )
            
            if analysis_result:
                # 更新错误记录
                error_record.error_type = analysis_result.error_type
                error_record.severity = analysis_result.severity
                error_record.analysis_result = analysis_result.to_dict()
                error_record.fix_suggestions = analysis_result.fix_suggestions
                
                # 保存到数据库
                await self._update_error_record(error_record)
                
                logger.info(f"错误分析完成：{analysis_result.error_type} - {analysis_result.severity}")
                
                # 如果需要自动修复
                if analysis_result.auto_fixable and self.config.auto_fix_enabled:
                    logger.info("执行自动修复...")
                    # 这里会调用 auto_fix_executor
                    # 由于模块还未创建，先记录日志
                    logger.warning("自动修复功能待实现")
                
                return analysis_result
            else:
                logger.error("LLM 分析返回空结果")
                return None
                
        except Exception as e:
            logger.error(f"分析错误失败：{e}", exc_info=True)
            return None
    
    def _call_llm_analysis(self, error_record: ErrorRecord) -> Optional[ErrorAnalysisResult]:
        """
        调用 LLM 进行错误分析（同步方法，在线程池执行）
        
        Args:
            error_record: 错误记录
        
        Returns:
            错误分析结果
        """
        try:
            # 构建 Prompt
            prompt = format_error_analysis_prompt(
                error_log=error_record.error_log,
                timestamp=error_record.timestamp.isoformat(),
                module=error_record.module,
                context=error_record.context,
                similar_errors=[],
                success_rules=INITIAL_SUCCESS_RULES,
                error_id=error_record.id
            )
            
            logger.debug(f"调用 LLM，模型：{self.llm_config.model}")
            
            # 调用 LLM API
            import requests
            
            response = requests.post(
                f"{self.llm_config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.llm_config.model,
                    "messages": [
                        {"role": "system", "content": "你是一位资深的系统运维专家"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.llm_config.temperature,
                    "max_tokens": self.llm_config.max_tokens
                },
                timeout=self.llm_config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 解析 LLM 响应
            content = result['choices'][0]['message']['content']
            
            # 提取 JSON
            json_start = content.find('```json')
            json_end = content.find('```', json_start + 7)
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start + 7:json_end].strip()
            else:
                # 尝试直接解析
                json_str = content.strip()
            
            analysis_data = json.loads(json_str)
            
            # 构建分析结果
            analysis_result = ErrorAnalysisResult(
                error_id=analysis_data.get('error_id', error_record.id),
                error_type=analysis_data.get('error_type', '其他'),
                severity=analysis_data.get('severity', 'medium'),
                root_cause=analysis_data.get('root_cause', ''),
                analysis=analysis_data.get('analysis', ''),
                auto_fixable=analysis_data.get('auto_fixable', False),
                fix_suggestions=analysis_data.get('fix_suggestions', []),
                retry_recommended=analysis_data.get('retry_recommended', False),
                retry_config=analysis_data.get('retry_config', {}),
                confidence_score=float(analysis_data.get('confidence_score', 0.5))
            )
            
            logger.info(f"LLM 分析成功，错误类型：{analysis_result.error_type}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"LLM 调用失败：{e}", exc_info=True)
            return None
    
    async def _save_error_record(self, error_record: ErrorRecord):
        """保存错误记录到数据库"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO error_records 
            (id, error_type, severity, error_log, module, timestamp, context, fix_status, max_retries)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                error_record.id,
                error_record.error_type,
                error_record.severity,
                error_record.error_log,
                error_record.module,
                error_record.timestamp,
                json.dumps(error_record.context),
                error_record.fix_status,
                error_record.max_retries
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"错误记录已保存：{error_record.id}")
            
        except Exception as e:
            logger.error(f"保存错误记录失败：{e}")
    
    async def _update_error_record(self, error_record: ErrorRecord):
        """更新错误记录"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = """
            UPDATE error_records 
            SET error_type = %s, severity = %s, analysis_result = %s, 
                fix_suggestions = %s, updated_at = NOW()
            WHERE id = %s
            """
            
            cursor.execute(sql, (
                error_record.error_type,
                error_record.severity,
                json.dumps(error_record.analysis_result),
                json.dumps(error_record.fix_suggestions),
                error_record.id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"错误记录已更新：{error_record.id}")
            
        except Exception as e:
            logger.error(f"更新错误记录失败：{e}")
    
    async def check_and_alert(self, log_entry: Dict):
        """
        检查日志条目，如果检测到错误则触发分析
        
        Args:
            log_entry: 日志条目
        """
        level = log_entry.get('level', '')
        message = log_entry.get('message', '')
        
        # 检查是否需要处理
        if level in self.config.error_levels:
            logger.info(f"检测到错误日志，触发 Agent 分析")
            await self.analyze_error(
                error_log=message,
                timestamp=datetime.fromisoformat(log_entry.get('timestamp', datetime.now().isoformat())),
                module=log_entry.get('module', ''),
                trigger_type='log_alert'
            )
        elif level == 'WARNING':
            # 检查是否匹配警告模式
            for pattern in self.config.warning_patterns:
                if pattern.lower() in message.lower():
                    logger.info(f"检测到警告模式：{pattern}")
                    await self.analyze_error(
                        error_log=message,
                        timestamp=datetime.fromisoformat(log_entry.get('timestamp', datetime.now().isoformat())),
                        module=log_entry.get('module', ''),
                        trigger_type='log_alert'
                    )
                    break
    
    def shutdown(self):
        """关闭 Agent"""
        logger.info("关闭日志监控 Agent...")
        self.executor.shutdown(wait=True)
        logger.info("日志监控 Agent 已关闭")


# 单例
_agent_instance: Optional[LogMonitorAgent] = None

def get_log_monitor_agent() -> LogMonitorAgent:
    """获取 Agent 单例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LogMonitorAgent()
    return _agent_instance
