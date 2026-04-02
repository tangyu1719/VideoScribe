-- ============== 分级日志系统数据库表结构 ==============

-- 1. 完整原型日志表 - 记录所有请求的完整流水
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='完整原型日志表';

-- 2. 接口粒度统计表 - 记录每次 API 调用的统计信息
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接口粒度日志表';

-- 3. 操作粒度日志表 - 记录具体业务操作的详情
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作粒度日志表';

-- ============== 初始化说明 ==============
-- 运行以下 SQL 命令创建所有表：
-- mysql -u root -p superbizagent < graded_logging_schema.sql

-- 查看表是否创建成功：
-- SHOW TABLES LIKE '%logs%';

-- 查看表结构：
-- DESCRIBE raw_logs;
-- DESCRIBE api_stats_log;
-- DESCRIBE operation_logs;
