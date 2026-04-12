-- 日志监控 Agent 数据库初始化脚本
-- 创建时间：2026-04-04

-- 使用数据库
USE superbizagent;

-- 错误记录表
CREATE TABLE IF NOT EXISTS `error_records` (
  `id` VARCHAR(64) PRIMARY KEY,
  `error_type` VARCHAR(50) NOT NULL,
  `severity` VARCHAR(20) NOT NULL,
  `error_log` TEXT NOT NULL,
  `module` VARCHAR(100),
  `timestamp` DATETIME NOT NULL,
  `context` JSON,
  `analysis_result` JSON,
  `fix_suggestions` JSON,
  `auto_fixed` BOOLEAN DEFAULT FALSE,
  `fix_status` VARCHAR(20) DEFAULT 'pending',
  `retry_count` INT DEFAULT 0,
  `max_retries` INT DEFAULT 3,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_timestamp` (`timestamp`),
  INDEX `idx_severity` (`severity`),
  INDEX `idx_module` (`module`),
  INDEX `idx_status` (`fix_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 成功规则表
CREATE TABLE IF NOT EXISTS `success_rules` (
  `rule_id` VARCHAR(64) PRIMARY KEY,
  `pattern` TEXT NOT NULL,
  `diagnosis` TEXT,
  `solution` TEXT,
  `auto_fix` BOOLEAN DEFAULT FALSE,
  `confidence` DECIMAL(3,2) DEFAULT 0.50,
  `learned_from` JSON,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_active` (`is_active`),
  INDEX `idx_confidence` (`confidence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 修复历史表
CREATE TABLE IF NOT EXISTS `fix_history` (
  `id` VARCHAR(64) PRIMARY KEY,
  `error_record_id` VARCHAR(64) NOT NULL,
  `fix_action` TEXT NOT NULL,
  `fix_result` JSON,
  `success` BOOLEAN,
  `retry_count` INT,
  `execution_time` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`error_record_id`) REFERENCES `error_records`(`id`) ON DELETE CASCADE,
  INDEX `idx_error_id` (`error_record_id`),
  INDEX `idx_success` (`success`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初始化默认规则
INSERT INTO `success_rules` (`rule_id`, `pattern`, `diagnosis`, `solution`, `auto_fix`, `confidence`, `learned_from`, `created_at`) VALUES
('rule_001', '.*timeout.*', '网络超时或服务器响应慢', '增加超时时间或重试', TRUE, 0.85, '[]', NOW()),
('rule_002', '.*connection refused.*', '目标服务未启动或网络不通', '检查服务状态和网络连接', TRUE, 0.90, '[]', NOW()),
('rule_003', '.*API.*key.*expired.*', 'API 密钥过期或无效', '更新 API 密钥或切换到备用配置', TRUE, 0.95, '[]', NOW()),
('rule_004', '.*401.*unauthorized.*', '认证失败', '检查认证配置和权限', FALSE, 0.80, '[]', NOW()),
('rule_005', '.*403.*forbidden.*', '权限不足', '申请相应权限或联系管理员', FALSE, 0.85, '[]', NOW()),
('rule_006', '.*404.*not found.*', '资源不存在', '检查 URL 或资源路径', FALSE, 0.90, '[]', NOW()),
('rule_007', '.*500.*internal server error.*', '服务器内部错误', '稍后重试或联系服务提供方', TRUE, 0.75, '[]', NOW()),
('rule_008', '.*502.*bad gateway.*', '网关错误', '检查代理服务或稍后重试', TRUE, 0.80, '[]', NOW()),
('rule_009', '.*503.*service unavailable.*', '服务不可用', '服务过载或维护中，稍后重试', TRUE, 0.85, '[]', NOW()),
('rule_010', '.*out of memory.*', '内存不足', '增加内存或优化代码', FALSE, 0.90, '[]', NOW()),
('rule_011', '.*disk space.*', '磁盘空间不足', '清理磁盘空间', FALSE, 0.95, '[]', NOW()),
('rule_012', '.*file.*not found.*', '文件不存在', '检查文件路径或创建文件', FALSE, 0.90, '[]', NOW()),
('rule_013', '.*permission denied.*', '权限被拒绝', '检查文件权限或用户权限', FALSE, 0.95, '[]', NOW()),
('rule_014', '.*database.*connection.*', '数据库连接失败', '检查数据库服务和连接配置', TRUE, 0.85, '[]', NOW()),
('rule_015', '.*rate limit.*', '请求频率超限', '降低请求频率或等待', TRUE, 0.90, '[]', NOW());

-- 查看创建的表
SHOW TABLES LIKE 'error%';
SHOW TABLES LIKE 'success%';
SHOW TABLES LIKE 'fix%';

-- 查看初始化的规则
SELECT COUNT(*) as rule_count FROM success_rules WHERE is_active = TRUE;
