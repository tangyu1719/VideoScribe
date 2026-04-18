"""
MariaDB 数据库连接模块
"""
import pymysql
from typing import Optional, Dict, Any, List

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_connection(database: str = 'superbizagent'):
    """获取数据库连接"""
    config = DB_CONFIG.copy()
    config['database'] = database
    return pymysql.connect(**config)

def execute_query(sql: str, params: tuple = None, database: str = 'superbizagent'):
    """执行查询，返回结果列表"""
    conn = get_connection(database)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()

def execute_update(sql: str, params: tuple = None, database: str = 'superbizagent'):
    """执行更新，返回受影响的行数"""
    conn = get_connection(database)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_insert(sql: str, params: tuple = None, database: str = 'superbizagent'):
    """执行插入，返回最后插入的 ID"""
    conn = get_connection(database)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 测试连接
if __name__ == '__main__':
    try:
        conn = get_connection()
        print('✓ MariaDB 连接成功')
        conn.close()
    except Exception as e:
        print(f'✗ MariaDB 连接失败：{e}')
