"""
重试管理器
管理错误修复的重试逻辑
"""
import asyncio
import time
from typing import Dict, Optional, Callable
from datetime import datetime

from .models import ErrorRecord
from .config import get_agent_config
from logging_system import Logger

logger = Logger("RetryManager")

class RetryManager:
    """重试管理器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_agent_config()
        self.retry_tasks: Dict[str, Dict] = {}
    
    async def schedule_retry(
        self,
        error_record: ErrorRecord,
        retry_callback: Callable
    ) -> bool:
        """
        调度重试
        
        Args:
            error_record: 错误记录
            retry_callback: 重试回调函数
        
        Returns:
            是否成功
        """
        if error_record.retry_count >= self.config.max_retries:
            logger.warning(f"达到最大重试次数：{error_record.id}")
            return False
        
        # 计算延迟时间（指数退避）
        delay = self._calculate_delay(error_record.retry_count)
        
        logger.info(f"调度重试：{error_record.id}, 延迟：{delay}秒, 次数：{error_record.retry_count + 1}")
        
        # 创建重试任务
        retry_task = {
            'error_id': error_record.id,
            'retry_count': error_record.retry_count + 1,
            'scheduled_time': datetime.now(),
            'delay': delay,
            'callback': retry_callback
        }
        
        self.retry_tasks[error_record.id] = retry_task
        
        # 异步执行重试
        asyncio.create_task(self._execute_retry(retry_task))
        
        return True
    
    def _calculate_delay(self, retry_count: int) -> int:
        """
        计算延迟时间（指数退避）
        
        Args:
            retry_count: 重试次数
        
        Returns:
            延迟秒数
        """
        initial_delay = 10
        backoff_multiplier = 2
        max_delay = 300
        
        delay = initial_delay * (backoff_multiplier ** retry_count)
        return min(int(delay), max_delay)
    
    async def _execute_retry(self, retry_task: Dict):
        """执行重试"""
        try:
            # 等待延迟
            await asyncio.sleep(retry_task['delay'])
            
            # 执行重试
            callback = retry_task['callback']
            success = await callback()
            
            if success:
                logger.info(f"重试成功：{retry_task['error_id']}")
            else:
                logger.warning(f"重试失败：{retry_task['error_id']}")
                
                # 如果还有重试次数，继续调度
                if retry_task['retry_count'] < self.config.max_retries:
                    # 更新错误记录的重试次数
                    error_record = ErrorRecord(
                        id=retry_task['error_id'],
                        retry_count=retry_task['retry_count']
                    )
                    await self.schedule_retry(error_record, callback)
            
        except Exception as e:
            logger.error(f"执行重试失败：{e}")
    
    def can_retry(self, error_type: str) -> bool:
        """
        判断是否可以重试
        
        Args:
            error_type: 错误类型
        
        Returns:
            是否可以重试
        """
        # 可重试的错误类型
        retryable_types = ['网络', '配置', '资源']
        
        # 不可重试的错误类型
        non_retryable_types = ['代码']
        
        if error_type in non_retryable_types:
            return False
        
        if error_type in retryable_types:
            return True
        
        # 默认可以重试
        return True


# 单例
_retry_manager_instance: Optional[RetryManager] = None

def get_retry_manager() -> RetryManager:
    """获取重试管理器单例"""
    global _retry_manager_instance
    if _retry_manager_instance is None:
        _retry_manager_instance = RetryManager()
    return _retry_manager_instance
