#!/usr/bin/env python3
"""
创建项目入口文件和启动脚本
"""
from pathlib import Path

PROJECT_ROOT = Path(r"f:\java\AIOPS\SuperBizAgent_v2")

# 创建 main.py
main_py = """#!/usr/bin/env python3
\"\"\"
SuperBizAgent 主入口
启动 Web API 服务
\"\"\"
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def main():
    \"\"\"启动 FastAPI 服务\"\"\"
    print("="*60)
    print("SuperBizAgent v2.0 - AI 驱动的智能业务助手")
    print("="*60)
    
    # 启动服务
    uvicorn.run(
        "api.web_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
"""

(PROJECT_ROOT / 'main.py').write_text(main_py, encoding='utf-8')
print("✓ 创建 main.py")

# 创建 start.bat
start_bat = """@echo off
chcp 65001 >nul
echo ============================================================
echo SuperBizAgent v2.0 - 启动脚本
echo ============================================================
echo.

echo [1/2] 启动后端服务...
start "SuperBizAgent Backend" cmd /k "cd /d %~dp0 && python main.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
cd web
start "SuperBizAgent Frontend" cmd /k "npm run dev"

echo.
echo ============================================================
echo 服务已启动！
echo - 后端：http://localhost:8000
echo - 前端：http://localhost:5173
echo ============================================================
pause
"""

(PROJECT_ROOT / 'start.bat').write_text(start_bat, encoding='gbk')
print("✓ 创建 start.bat")

# 创建 stop.bat
stop_bat = """@echo off
chcp 65001 >nul
echo ============================================================
echo 停止 SuperBizAgent 服务
echo ============================================================

echo 正在停止服务...
taskkill /F /FI "WindowTitle eq SuperBizAgent*" 2>nul

echo.
echo 服务已停止
pause
"""

(PROJECT_ROOT / 'stop.bat').write_text(stop_bat, encoding='gbk')
print("✓ 创建 stop.bat")

# 创建 configs/config.py
config_py = """#!/usr/bin/env python3
\"\"\"
项目配置文件
\"\"\"
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'superbizagent'
}

# API 配置
API_CONFIG = {
    'volcengine_api_key': 'your_api_key',
    'ai_chat_model': 'ep-20260320202517-w6ncg'
}

# 路径配置
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
KNOWLEDGE_BASE_DIR = DATA_DIR / 'knowledge_base'
SESSIONS_DIR = DATA_DIR / 'sessions'
UPLOADS_DIR = DATA_DIR / 'uploads'

# 确保目录存在
for dir_path in [DATA_DIR, LOGS_DIR, KNOWLEDGE_BASE_DIR, SESSIONS_DIR, UPLOADS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
"""

(PROJECT_ROOT / 'configs' / 'config.py').write_text(config_py, encoding='utf-8')
print("✓ 创建 configs/config.py")

# 创建 .env.example
env_example = """# SuperBizAgent 环境变量配置

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=superbizagent

# API 密钥
VOLCENGINE_API_KEY=your_api_key
AI_CHAT_MODEL=ep-20260320202517-w6ncg

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
"""

(PROJECT_ROOT / '.env.example').write_text(env_example, encoding='utf-8')
print("✓ 创建 .env.example")

print("\n✅ 所有配置文件创建完成！")
