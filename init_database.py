"""
初始化 MariaDB 数据库
创建 SuperBizAgent 所需的表结构
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

def create_database():
    """创建数据库"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS superbizagent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    print('✓ 数据库 superbizagent 创建成功')
    conn.close()

def create_tables():
    """创建数据表"""
    conn = pymysql.connect(**DB_CONFIG, database='superbizagent')
    cursor = conn.cursor()
    
    # 1. LLM API 配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_configs (
            id VARCHAR(100) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            api_key TEXT,
            base_url VARCHAR(500),
            model VARCHAR(200),
            endpoint_id VARCHAR(200),
            request_format VARCHAR(50) DEFAULT 'openai',
            headers JSON,
            enabled BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            backup_configs JSON,
            INDEX idx_enabled (enabled),
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 llm_configs 创建成功')
    
    # 2. AI 形象配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_personas (
            id VARCHAR(100) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            system_prompt TEXT,
            thinking_system_prompt TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_enabled (enabled),
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 ai_personas 创建成功')
    
    # 3. 文档解析器配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_parsers (
            id VARCHAR(100) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            system_prompt TEXT,
            rules TEXT,
            file_naming_rule VARCHAR(500),
            output_template TEXT,
            user_prompt TEXT,
            summary_prompt TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_enabled (enabled),
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 document_parsers 创建成功')
    
    # 4. 会话配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR(100) PRIMARY KEY,
            title VARCHAR(500),
            group_id VARCHAR(100),
            context_length INT DEFAULT 0,
            max_context_length INT DEFAULT 8192,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_group (group_id),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 chat_sessions 创建成功')
    
    # 5. 会话消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id VARCHAR(100) PRIMARY KEY,
            session_id VARCHAR(100) NOT NULL,
            role VARCHAR(50) NOT NULL,
            content LONGTEXT,
            images JSON,
            thinking TEXT,
            use_deep_thinking BOOLEAN DEFAULT FALSE,
            use_web_search BOOLEAN DEFAULT FALSE,
            timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 chat_messages 创建成功')
    
    # 6. 会话分组表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_groups (
            id VARCHAR(100) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 session_groups 创建成功')
    
    # 7. 应用配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_config (
            id INT PRIMARY KEY DEFAULT 1,
            current_llm_config_id VARCHAR(100),
            chat_llm_config_id VARCHAR(100),
            parser_llm_config_id VARCHAR(100),
            current_ai_persona_id VARCHAR(100),
            current_parser_id VARCHAR(100),
            knowledge_base_threshold FLOAT DEFAULT 0.7,
            default_deep_thinking BOOLEAN DEFAULT FALSE,
            default_web_search BOOLEAN DEFAULT FALSE,
            use_unified_api_config BOOLEAN DEFAULT TRUE,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 app_config 创建成功')
    
    # 8. 视频下载任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_tasks (
            id VARCHAR(100) PRIMARY KEY,
            url VARCHAR(1000) NOT NULL,
            platform VARCHAR(50),
            status VARCHAR(50) DEFAULT 'pending',
            progress FLOAT DEFAULT 0,
            title VARCHAR(500),
            transcript LONGTEXT,
            summary LONGTEXT,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 video_tasks 创建成功')
    
    # 9. 链接分析任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS link_tasks (
            id VARCHAR(100) PRIMARY KEY,
            url VARCHAR(1000) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            progress FLOAT DEFAULT 0,
            title VARCHAR(500),
            transcript LONGTEXT,
            summary LONGTEXT,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 link_tasks 创建成功')
    
    # 10. 系统日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            level VARCHAR(50),
            module VARCHAR(100),
            message TEXT,
            details JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_level (level),
            INDEX idx_module (module),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 system_logs 创建成功')
    
    # 11. 知识库文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kb_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(500) NOT NULL,
            file_path VARCHAR(1000),
            file_size BIGINT DEFAULT 0,
            file_type VARCHAR(50),
            status VARCHAR(50) DEFAULT 'pending',
            chunk_count INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    print('✓ 表 kb_files 创建成功')
    
    conn.commit()
    conn.close()
    print('\n✅ 所有表创建成功！')

if __name__ == '__main__':
    print('=' * 60)
    print('初始化 SuperBizAgent MariaDB 数据库')
    print('=' * 60)
    create_database()
    create_tables()
    print('\n数据库初始化完成！')
