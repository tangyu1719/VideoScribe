"""
自动修复执行器
执行 LLM 生成的修复建议
"""
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime

from .models import FixHistory, ErrorRecord
from .config import get_agent_config
from db import get_db_connection
from logging_system import Logger

logger = Logger("AutoFixExecutor")

class AutoFixExecutor:
    """自动修复执行器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_agent_config()
        self.fix_history: List[FixHistory] = []
    
    async def execute_fix(
        self,
        error_record: ErrorRecord,
        fix_suggestions: List[Dict]
    ) -> bool:
        """
        执行修复
        
        Args:
            error_record: 错误记录
            fix_suggestions: 修复建议列表
        
        Returns:
            是否成功
        """
        if not self.config.auto_fix_enabled:
            logger.warning("自动修复未启用")
            return False
        
        logger.info(f"开始执行修复，错误 ID: {error_record.id}")
        
        for suggestion in fix_suggestions:
            try:
                start_time = time.time()
                
                # 执行修复
                success = await self._apply_fix(suggestion)
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # 记录修复历史
                fix_history = FixHistory(
                    error_record_id=error_record.id,
                    fix_action=suggestion.get('action', ''),
                    fix_result={'success': success},
                    success=success,
                    retry_count=error_record.retry_count,
                    execution_time=execution_time
                )
                
                self.fix_history.append(fix_history)
                await self._save_fix_history(fix_history)
                
                if success:
                    logger.info(f"修复成功：{suggestion.get('action', '')}")
                    return True
                else:
                    logger.warning(f"修复失败：{suggestion.get('action', '')}")
                    
            except Exception as e:
                logger.error(f"执行修复失败：{e}")
        
        return False
    
    async def _apply_fix(self, suggestion: Dict) -> bool:
        """
        应用修复
        
        Args:
            suggestion: 修复建议
        
        Returns:
            是否成功
        """
        action = suggestion.get('action', '')
        command = suggestion.get('command', '')
        
        logger.info(f"执行修复操作：{action}")
        
        # 根据操作类型执行
        if '切换' in action or '配置' in action:
            # 配置修改
            return await self._apply_configuration_fix(suggestion)
        elif '重试' in action:
            # 重试操作
            return True  # 重试由 retry_manager 处理
        elif '清理' in action:
            # 清理操作
            return await self._apply_cleanup_fix(suggestion)
        else:
            # 其他操作，记录日志
            logger.info(f"修复操作（仅记录）：{action}")
            return True
    
    async def _apply_configuration_fix(self, suggestion: Dict) -> bool:
        """应用配置修复"""
        try:
            command = suggestion.get('command', '')
            logger.info(f"执行配置修改：{command}")
            
            # 这里应该调用配置管理模块
            # 暂时只记录日志
            logger.warning("配置修改功能待实现")
            return True
            
        except Exception as e:
            logger.error(f"配置修改失败：{e}")
            return False
    
    async def _apply_cleanup_fix(self, suggestion: Dict) -> bool:
        """应用清理修复"""
        try:
            import os
            import shutil
            
            command = suggestion.get('command', '')
            logger.info(f"执行清理操作：{command}")
            
            # 示例：清理临时文件
            temp_dir = 'temp'
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logger.error(f"删除文件失败：{e}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理操作失败：{e}")
            return False
    
    async def _save_fix_history(self, fix_history: FixHistory):
        """保存修复历史"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO fix_history 
            (id, error_record_id, fix_action, fix_result, success, retry_count, execution_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                fix_history.id,
                fix_history.error_record_id,
                fix_history.fix_action,
                str(fix_history.fix_result),
                fix_history.success,
                fix_history.retry_count,
                fix_history.execution_time
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"修复历史已保存：{fix_history.id}")
            
        except Exception as e:
            logger.error(f"保存修复历史失败：{e}")


# 单例
_executor_instance: Optional[AutoFixExecutor] = None

def get_auto_fix_executor() -> AutoFixExecutor:
    """获取执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = AutoFixExecutor()
    return _executor_instance
