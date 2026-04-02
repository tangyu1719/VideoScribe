#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化分级日志数据库表
"""

import db

def init_tables():
    """创建分级日志系统的所有表"""
    
    # 1. 创建完整原型日志表
    db.execute_update("""
        CREATE TABLE IF NOT EXISTS raw_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id VARCHAR(100) NOT NULL COMMENT '请求唯一标识',
            method VARCHAR(10) NOT NULL COMMENT 'HTTP 方法',
            path VARCHAR(500) NOT NULL COMMENT '请求路径',
            headers TEXT COMMENT '请求头 (JSON)',
            body TEXT COMMENT '请求体 (JSON)',
            start_time DATETIME NOT NULL COMMENT '请求开始时间',
            end_time DATETIME COMMENT '请求结束时间',
            duration_ms DECIMAL(10,2) COMMENT '耗时 (毫秒)',
            status_code INT COMMENT 'HTTP 状态码',
            response_body TEXT COMMENT '响应体 (JSON)',
            client_ip VARCHAR(50) COMMENT '客户端 IP',
            complete TINYINT(1) DEFAULT 0 COMMENT '是否完成',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
            
            INDEX idx_request_id (request_id),
            INDEX idx_path (path(255)),
            INDEX idx_start_time (start_time),
            INDEX idx_complete (complete)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='完整原型日志表'
    """, database='superbizagent')
    print("✓ 创建 raw_logs 表成功")
    
    # 2. 创建接口粒度统计表
    db.execute_update("""
        CREATE TABLE IF NOT EXISTS api_stats_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            api_path VARCHAR(500) NOT NULL COMMENT 'API 路径',
            method VARCHAR(10) NOT NULL COMMENT 'HTTP 方法',
            status_code INT NOT NULL COMMENT 'HTTP 状态码',
            duration_ms DECIMAL(10,2) NOT NULL COMMENT '耗时 (毫秒)',
            called_at DATETIME NOT NULL COMMENT '调用时间',
            extra_info TEXT COMMENT '额外信息 (JSON)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
            
            INDEX idx_api_path (api_path(255)),
            INDEX idx_method (method),
            INDEX idx_status_code (status_code),
            INDEX idx_called_at (called_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接口粒度日志表'
    """, database='superbizagent')
    print("✓ 创建 api_stats_log 表成功")
    
    # 3. 创建操作粒度日志表
    db.execute_update("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            operation_type VARCHAR(100) NOT NULL COMMENT '操作类型',
            operation_id VARCHAR(100) NOT NULL COMMENT '操作唯一标识',
            inputs TEXT COMMENT '输入参数 (JSON)',
            outputs TEXT COMMENT '输出结果 (JSON)',
            start_time DATETIME NOT NULL COMMENT '开始时间',
            end_time DATETIME NOT NULL COMMENT '结束时间',
            duration_ms DECIMAL(10,2) NOT NULL COMMENT '耗时 (毫秒)',
            status VARCHAR(20) NOT NULL COMMENT '状态 (success/failed)',
            error_message TEXT COMMENT '错误消息',
            extra_details TEXT COMMENT '额外详情 (JSON)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
            
            INDEX idx_operation_type (operation_type),
            INDEX idx_operation_id (operation_id),
            INDEX idx_status (status),
            INDEX idx_start_time (start_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作粒度日志表'
    """, database='superbizagent')
    print("✓ 创建 operation_logs 表成功")
    
    print("\n✅ 所有表创建成功！")


if __name__ == "__main__":
    try:
        init_tables()
    except Exception as e:
        print(f"\n✗ 创建表失败：{e}")
        raise
