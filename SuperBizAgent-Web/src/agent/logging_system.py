#!/usr/bin/env python3
"""
分级日志系统 - 三级日志架构
1. 原始日志 (Raw Logs) - 记录所有请求的完整流水
2. 接口粒度日志 (API Summary) - 按接口聚合统计
3. 操作粒度日志 (Operation Details) - 记录每个具体操作详情
"""

import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import db

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class RawLog:
    """原始日志 - 记录每个请求的完整信息"""
    id: str
    timestamp: str
    level: str
    module: str
    api_path: str
    method: str
    request_id: str
    message: str
    request_data: Optional[Dict] = None
    response_data: Optional[Dict] = None
    duration_ms: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level,
            "module": self.module,
            "api_path": self.api_path,
            "method": self.method,
            "request_id": self.request_id,
            "message": self.message,
            "request_data": json.dumps(self.request_data) if self.request_data else None,
            "response_data": json.dumps(self.response_data) if self.response_data else None,
            "duration_ms": self.duration_ms,
            "error": self.error
        }

@dataclass
class APISummary:
    """接口粒度日志 - 按接口聚合统计"""
    id: str
    api_path: str
    method: str
    total_calls: int = 0
    success_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    last_called: Optional[str] = None
    last_status: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "api_path": self.api_path,
            "method": self.method,
            "total_calls": self.total_calls,
            "success_calls": self.success_calls,
            "failed_calls": self.failed_calls,
            "total_duration_ms": self.total_duration_ms,
            "avg_duration_ms": self.avg_duration_ms,
            "max_duration_ms": self.max_duration_ms,
            "min_duration_ms": self.min_duration_ms,
            "last_called": self.last_called,
            "last_status": self.last_status
        }

@dataclass
class OperationStep:
    """操作步骤 - 记录每个步骤的详情"""
    step_name: str
    step_order: int
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    inputs: Optional[Dict] = None
    outputs: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "step_name": self.step_name,
            "step_order": self.step_order,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "inputs": json.dumps(self.inputs) if self.inputs else None,
            "outputs": json.dumps(self.outputs) if self.outputs else None,
            "error": self.error
        }

@dataclass
class OperationLog:
    """操作粒度日志 - 记录每个具体操作的完整流程"""
    id: str
    operation_type: str
    operation_name: str
    request_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    inputs: Optional[Dict] = None
    outputs: Optional[Dict] = None
    error_message: Optional[str] = None
    steps: List[OperationStep] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "operation_type": self.operation_type,
            "operation_name": self.operation_name,
            "request_id": self.request_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "inputs": json.dumps(self.inputs) if self.inputs else None,
            "outputs": json.dumps(self.outputs) if self.outputs else None,
            "error_message": self.error_message,
            "steps": json.dumps([s.to_dict() for s in self.steps]) if self.steps else None
        }

class LoggingSystem:
    """分级日志系统主类"""
    
    def __init__(self):
        self._init_database()
        self.active_operations: Dict[str, OperationLog] = {}
    
    def _init_database(self):
        """初始化数据库表"""
        # 原始日志表
        db.execute_update("""
            CREATE TABLE IF NOT EXISTS raw_logs (
                id VARCHAR(64) PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level VARCHAR(20),
                module VARCHAR(100),
                api_path VARCHAR(500),
                method VARCHAR(10),
                request_id VARCHAR(64),
                message TEXT,
                request_data TEXT,
                response_data TEXT,
                duration_ms FLOAT,
                error TEXT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_request_id (request_id),
                INDEX idx_api_path (api_path),
                INDEX idx_level (level)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 接口统计表
        db.execute_update("""
            CREATE TABLE IF NOT EXISTS api_summary (
                id VARCHAR(128) PRIMARY KEY,
                api_path VARCHAR(500),
                method VARCHAR(10),
                total_calls INT DEFAULT 0,
                success_calls INT DEFAULT 0,
                failed_calls INT DEFAULT 0,
                total_duration_ms FLOAT DEFAULT 0,
                avg_duration_ms FLOAT DEFAULT 0,
                max_duration_ms FLOAT DEFAULT 0,
                min_duration_ms FLOAT DEFAULT 0,
                last_called DATETIME,
                last_status VARCHAR(20),
                INDEX idx_api_path (api_path)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 操作日志表
        db.execute_update("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id VARCHAR(64) PRIMARY KEY,
                operation_type VARCHAR(100),
                operation_name VARCHAR(200),
                request_id VARCHAR(64),
                status VARCHAR(20),
                start_time DATETIME,
                end_time DATETIME,
                duration_ms FLOAT,
                inputs TEXT,
                outputs TEXT,
                error_message TEXT,
                steps TEXT,
                INDEX idx_operation_type (operation_type),
                INDEX idx_request_id (request_id),
                INDEX idx_status (status),
                INDEX idx_start_time (start_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    
    def log_raw(self, 
                level: LogLevel,
                module: str,
                api_path: str,
                method: str,
                request_id: str,
                message: str,
                request_data: Dict = None,
                response_data: Dict = None,
                duration_ms: float = 0.0,
                error: str = None) -> str:
        """记录原始日志"""
        log_id = hashlib.md5(f"{request_id}_{time.time()}".encode()).hexdigest()[:16]
        
        log = RawLog(
            id=log_id,
            timestamp=datetime.now().isoformat(),
            level=level.value,
            module=module,
            api_path=api_path,
            method=method,
            request_id=request_id,
            message=message,
            request_data=request_data,
            response_data=response_data,
            duration_ms=duration_ms,
            error=error
        )
        
        # 保存到数据库
        try:
            db.execute_update("""
                INSERT INTO raw_logs 
                (id, timestamp, level, module, api_path, method, request_id, 
                 message, request_data, response_data, duration_ms, error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log.id, log.timestamp, log.level, log.module, log.api_path,
                log.method, log.request_id, log.message,
                json.dumps(log.request_data) if log.request_data else None,
                json.dumps(log.response_data) if log.response_data else None,
                log.duration_ms, log.error
            ))
        except Exception as e:
            print(f"[LoggingSystem] 保存原始日志失败: {e}")
        
        return log_id
    
    def update_api_summary(self, api_path: str, method: str, 
                          duration_ms: float, success: bool):
        """更新接口统计"""
        summary_id = hashlib.md5(f"{method}_{api_path}".encode()).hexdigest()[:32]
        
        try:
            # 检查是否已存在
            result = db.execute_query(
                "SELECT * FROM api_summary WHERE id = %s",
                (summary_id,)
            )
            
            if result:
                # 更新现有记录
                row = result[0]
                total_calls = row['total_calls'] + 1
                success_calls = row['success_calls'] + (1 if success else 0)
                failed_calls = row['failed_calls'] + (0 if success else 1)
                total_duration = row['total_duration_ms'] + duration_ms
                avg_duration = total_duration / total_calls
                max_duration = max(row['max_duration_ms'], duration_ms)
                min_duration = min(row['min_duration_ms'], duration_ms) if row['min_duration_ms'] > 0 else duration_ms
                
                db.execute_update("""
                    UPDATE api_summary SET
                        total_calls = %s,
                        success_calls = %s,
                        failed_calls = %s,
                        total_duration_ms = %s,
                        avg_duration_ms = %s,
                        max_duration_ms = %s,
                        min_duration_ms = %s,
                        last_called = %s,
                        last_status = %s
                    WHERE id = %s
                """, (
                    total_calls, success_calls, failed_calls,
                    total_duration, avg_duration, max_duration, min_duration,
                    datetime.now(), 'success' if success else 'failed',
                    summary_id
                ))
            else:
                # 插入新记录
                db.execute_update("""
                    INSERT INTO api_summary
                    (id, api_path, method, total_calls, success_calls, failed_calls,
                     total_duration_ms, avg_duration_ms, max_duration_ms, min_duration_ms,
                     last_called, last_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    summary_id, api_path, method, 1, 1 if success else 0, 0 if success else 1,
                    duration_ms, duration_ms, duration_ms, duration_ms,
                    datetime.now(), 'success' if success else 'failed'
                ))
        except Exception as e:
            print(f"[LoggingSystem] 更新接口统计失败: {e}")
    
    def start_operation(self, operation_type: str, operation_name: str,
                       request_id: str, inputs: Dict = None) -> str:
        """开始记录一个操作"""
        operation_id = hashlib.md5(f"{request_id}_{operation_type}_{time.time()}".encode()).hexdigest()[:16]
        
        operation = OperationLog(
            id=operation_id,
            operation_type=operation_type,
            operation_name=operation_name,
            request_id=request_id,
            status=OperationStatus.RUNNING.value,
            start_time=datetime.now().isoformat(),
            inputs=inputs
        )
        
        self.active_operations[operation_id] = operation
        
        # 保存到数据库
        try:
            db.execute_update("""
                INSERT INTO operation_logs
                (id, operation_type, operation_name, request_id, status, start_time, inputs)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                operation.id, operation.operation_type, operation.operation_name,
                operation.request_id, operation.status, operation.start_time,
                json.dumps(operation.inputs) if operation.inputs else None
            ))
        except Exception as e:
            print(f"[LoggingSystem] 保存操作日志失败: {e}")
        
        return operation_id
    
    def add_operation_step(self, operation_id: str, step_name: str,
                          step_order: int, inputs: Dict = None):
        """添加操作步骤"""
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        step = OperationStep(
            step_name=step_name,
            step_order=step_order,
            status=OperationStatus.RUNNING.value,
            start_time=datetime.now().isoformat(),
            inputs=inputs
        )
        operation.steps.append(step)
    
    def complete_operation_step(self, operation_id: str, step_order: int,
                               outputs: Dict = None, error: str = None):
        """完成操作步骤"""
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        for step in operation.steps:
            if step.step_order == step_order:
                step.end_time = datetime.now().isoformat()
                step.status = OperationStatus.FAILED.value if error else OperationStatus.SUCCESS.value
                step.outputs = outputs
                step.error = error
                
                # 计算耗时
                if step.start_time:
                    start = datetime.fromisoformat(step.start_time)
                    end = datetime.fromisoformat(step.end_time)
                    step.duration_ms = (end - start).total_seconds() * 1000
                break
    
    def complete_operation(self, operation_id: str, outputs: Dict = None,
                          error_message: str = None):
        """完成操作记录"""
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        operation.end_time = datetime.now().isoformat()
        operation.status = OperationStatus.FAILED.value if error_message else OperationStatus.SUCCESS.value
        operation.outputs = outputs
        operation.error_message = error_message
        
        # 计算总耗时
        if operation.start_time:
            start = datetime.fromisoformat(operation.start_time)
            end = datetime.fromisoformat(operation.end_time)
            operation.duration_ms = (end - start).total_seconds() * 1000
        
        # 更新数据库
        try:
            db.execute_update("""
                UPDATE operation_logs SET
                    status = %s,
                    end_time = %s,
                    duration_ms = %s,
                    outputs = %s,
                    error_message = %s,
                    steps = %s
                WHERE id = %s
            """, (
                operation.status, operation.end_time, operation.duration_ms,
                json.dumps(operation.outputs) if operation.outputs else None,
                operation.error_message,
                json.dumps([s.to_dict() for s in operation.steps]) if operation.steps else None,
                operation_id
            ))
        except Exception as e:
            print(f"[LoggingSystem] 更新操作日志失败: {e}")
        
        # 从内存中移除
        del self.active_operations[operation_id]
    
    def get_raw_logs(self, level: str = None, module: str = None,
                    api_path: str = None, request_id: str = None,
                    page: int = 1, page_size: int = 50) -> Dict:
        """获取原始日志"""
        try:
            where_clause = []
            params = []
            
            if level:
                where_clause.append("level = %s")
                params.append(level)
            if module:
                where_clause.append("module = %s")
                params.append(module)
            if api_path:
                where_clause.append("api_path = %s")
                params.append(api_path)
            if request_id:
                where_clause.append("request_id = %s")
                params.append(request_id)
            
            where_sql = "WHERE " + " AND ".join(where_clause) if where_clause else ""
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM raw_logs {where_sql}"
            count_result = db.execute_query(count_sql, tuple(params) if params else None)
            total = count_result[0]['total'] if count_result else 0
            
            # 获取数据
            sql = f"""
                SELECT * FROM raw_logs {where_sql}
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, (page - 1) * page_size])
            
            results = db.execute_query(sql, tuple(params))
            
            items = []
            for row in results:
                items.append({
                    "id": row['id'],
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                    "level": row['level'],
                    "module": row['module'],
                    "api_path": row['api_path'],
                    "method": row['method'],
                    "request_id": row['request_id'],
                    "message": row['message'],
                    "request_data": json.loads(row['request_data']) if row['request_data'] else None,
                    "response_data": json.loads(row['response_data']) if row['response_data'] else None,
                    "duration_ms": row['duration_ms'],
                    "error": row['error']
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            print(f"[LoggingSystem] 获取原始日志失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
    
    def get_api_summary(self, api_path: str = None) -> List[Dict]:
        """获取接口统计"""
        try:
            if api_path:
                results = db.execute_query(
                    "SELECT * FROM api_summary WHERE api_path = %s ORDER BY total_calls DESC",
                    (api_path,)
                )
            else:
                results = db.execute_query(
                    "SELECT * FROM api_summary ORDER BY total_calls DESC"
                )
            
            return [dict(row) for row in results]
        except Exception as e:
            print(f"[LoggingSystem] 获取接口统计失败: {e}")
            return []
    
    def get_operation_logs(self, operation_type: str = None,
                          status: str = None, request_id: str = None,
                          page: int = 1, page_size: int = 50) -> Dict:
        """获取操作日志"""
        try:
            where_clause = []
            params = []
            
            if operation_type:
                where_clause.append("operation_type = %s")
                params.append(operation_type)
            if status:
                where_clause.append("status = %s")
                params.append(status)
            if request_id:
                where_clause.append("request_id = %s")
                params.append(request_id)
            
            where_sql = "WHERE " + " AND ".join(where_clause) if where_clause else ""
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM operation_logs {where_sql}"
            count_result = db.execute_query(count_sql, tuple(params) if params else None)
            total = count_result[0]['total'] if count_result else 0
            
            # 获取数据
            sql = f"""
                SELECT * FROM operation_logs {where_sql}
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, (page - 1) * page_size])
            
            results = db.execute_query(sql, tuple(params))
            
            items = []
            for row in results:
                items.append({
                    "id": row['id'],
                    "operation_type": row['operation_type'],
                    "operation_name": row['operation_name'],
                    "request_id": row['request_id'],
                    "status": row['status'],
                    "start_time": row['start_time'].isoformat() if row['start_time'] else None,
                    "end_time": row['end_time'].isoformat() if row['end_time'] else None,
                    "duration_ms": row['duration_ms'],
                    "inputs": json.loads(row['inputs']) if row['inputs'] else None,
                    "outputs": json.loads(row['outputs']) if row['outputs'] else None,
                    "error_message": row['error_message'],
                    "steps": json.loads(row['steps']) if row['steps'] else []
                })
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            print(f"[LoggingSystem] 获取操作日志失败: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

# 全局日志系统实例
logging_system = LoggingSystem()
