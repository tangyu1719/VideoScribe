"""
错误检测器
实时监听日志，检测错误模式
"""
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import defaultdict

from .config import get_agent_config
from .models import ErrorRecord
from db import get_db_connection
from logging_system import Logger

logger = Logger("ErrorDetector")

class ErrorDetector:
    """错误检测器"""
    
    def __init__(self):
        """初始化错误检测器"""
        self.config = get_agent_config()
        
        # 错误模式匹配器
        self.error_patterns = [
            (r'error', 'ERROR'),
            (r'exception', 'ERROR'),
            (r'failed', 'ERROR'),
            (r'failure', 'ERROR'),
            (r'timeout', 'WARNING'),
            (r'connection refused', 'ERROR'),
            (r'connection reset', 'ERROR'),
            (r'401', 'ERROR'),
            (r'403', 'ERROR'),
            (r'404', 'WARNING'),
            (r'500', 'ERROR'),
            (r'502', 'ERROR'),
            (r'503', 'ERROR'),
            (r'out of memory', 'ERROR'),
            (r'disk space', 'ERROR'),
            (r'permission denied', 'ERROR'),
        ]
        
        # 去重缓存（最近 1000 条错误）
        self.seen_errors: Dict[str, datetime] = {}
        self.max_cache_size = 1000
        
        # 错误回调
        self.error_callbacks: List[Callable] = []
        
        logger.info("错误检测器初始化完成")
    
    def add_error_callback(self, callback: Callable):
        """
        添加错误回调函数
        
        Args:
            callback: 回调函数，接收 ErrorRecord 参数
        """
        self.error_callbacks.append(callback)
        logger.info(f"添加错误回调，当前回调数：{len(self.error_callbacks)}")
    
    def is_duplicate(self, error_log: str, module: str, time_window: int = 60) -> bool:
        """
        检查是否为重复错误
        
        Args:
            error_log: 错误日志
            module: 模块
            time_window: 时间窗口（秒）
        
        Returns:
            是否重复
        """
        # 生成错误指纹
        error_key = f"{module}:{error_log[:200]}"
        now = datetime.now()
        
        # 清理过期缓存
        self._cleanup_cache(now)
        
        # 检查是否重复
        if error_key in self.seen_errors:
            last_seen = self.seen_errors[error_key]
            if (now - last_seen).total_seconds() < time_window:
                logger.debug(f"检测到重复错误：{error_key[:50]}...")
                return True
        
        # 记录新错误
        self.seen_errors[error_key] = now
        return False
    
    def _cleanup_cache(self, now: datetime):
        """清理过期缓存"""
        if len(self.seen_errors) > self.max_cache_size:
            # 删除最旧的 50%
            keys_to_delete = list(self.seen_errors.keys())[:self.max_cache_size // 2]
            for key in keys_to_delete:
                del self.seen_errors[key]
    
    def detect_error(self, log_entry: Dict) -> Optional[ErrorRecord]:
        """
        检测日志条目是否为错误
        
        Args:
            log_entry: 日志条目
        
        Returns:
            ErrorRecord 或 None
        """
        level = log_entry.get('level', '')
        message = log_entry.get('message', '')
        module = log_entry.get('module', '')
        timestamp = log_entry.get('timestamp', datetime.now().isoformat())
        
        # 检查日志级别
        if level in self.config.error_levels:
            logger.debug(f"检测到 ERROR 级别日志：{message[:50]}...")
            return self._create_error_record(log_entry)
        
        # 检查警告模式
        if level == 'WARNING':
            for pattern in self.config.warning_patterns:
                if pattern.lower() in message.lower():
                    logger.debug(f"检测到警告模式：{pattern}")
                    return self._create_error_record(log_entry)
        
        # 检查错误模式
        message_lower = message.lower()
        for pattern, severity in self.error_patterns:
            if re.search(pattern, message_lower):
                # 忽略已知模式
                should_ignore = False
                for ignore_pattern in self.config.ignore_patterns:
                    if ignore_pattern.lower() in message_lower:
                        should_ignore = True
                        break
                
                if not should_ignore:
                    logger.debug(f"匹配错误模式：{pattern}")
                    return self._create_error_record(log_entry, severity)
        
        return None
    
    def _create_error_record(self, log_entry: Dict, severity: str = None) -> ErrorRecord:
        """创建错误记录"""
        from .models import ErrorRecord
        
        return ErrorRecord(
            error_log=log_entry.get('message', ''),
            module=log_entry.get('module', ''),
            timestamp=datetime.fromisoformat(log_entry.get('timestamp', datetime.now().isoformat())),
            context={
                'level': log_entry.get('level', ''),
                'file': log_entry.get('file', ''),
                'line': log_entry.get('line', ''),
                'function': log_entry.get('function', '')
            }
        )
    
    def notify_callbacks(self, error_record: ErrorRecord):
        """通知所有回调"""
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as e:
                logger.error(f"错误回调执行失败：{e}")
    
    def start_listening(self, db_poll_interval: int = 5):
        """
        开始监听日志数据库
        
        Args:
            db_poll_interval: 数据库轮询间隔（秒）
        """
        import time
        import threading
        
        logger.info(f"开始监听日志数据库，轮询间隔：{db_poll_interval}秒")
        
        def listen_loop():
            last_timestamp = datetime.now()
            
            while True:
                try:
                    # 查询新日志
                    conn = get_db_connection()
                    cursor = conn.cursor(as_dict=True)
                    
                    sql = """
                    SELECT * FROM logs 
                    WHERE timestamp > %s 
                    ORDER BY timestamp ASC
                    LIMIT 100
                    """
                    
                    cursor.execute(sql, (last_timestamp,))
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        # 检测错误
                        error_record = self.detect_error(row)
                        
                        if error_record:
                            # 检查是否重复
                            if not self.is_duplicate(
                                error_record.error_log,
                                error_record.module
                            ):
                                # 通知回调
                                self.notify_callbacks(error_record)
                                last_timestamp = error_record.timestamp
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    logger.error(f"监听日志失败：{e}")
                
                time.sleep(db_poll_interval)
        
        # 在后台线程运行
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
        logger.info("日志监听线程已启动")


# 单例
_detector_instance: Optional[ErrorDetector] = None

def get_error_detector() -> ErrorDetector:
    """获取错误检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ErrorDetector()
    return _detector_instance
