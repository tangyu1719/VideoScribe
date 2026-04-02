@echo off
chcp 65001 >nul
echo ==========================================
echo SuperBizAgent Web端启动脚本
echo ==========================================
echo.

REM 检查Python环境
echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)
echo [OK] Python环境正常

REM 检查Node.js环境
echo.
echo [2/3] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请确保Node.js已安装并添加到PATH
    pause
    exit /b 1
)
echo [OK] Node.js环境正常

REM 安装Python依赖
echo.
echo [3/3] 检查Python依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 正在安装FastAPI...
    pip install fastapi uvicorn python-multipart pydantic -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo [OK] Python依赖已安装

echo.
echo ==========================================
echo 启动服务...
echo ==========================================
echo.

REM 获取当前目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 启动后端API服务（在新窗口）
echo 启动后端API服务...
start "SuperBizAgent API" cmd /k "python web_api.py"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 进入web目录并启动前端
cd web

REM 检查node_modules
echo.
echo 检查前端依赖...
if not exist "node_modules" (
    echo 正在安装前端依赖，请稍候...
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
)
echo [OK] 前端依赖已安装

echo.
echo 启动前端开发服务器...
echo.
echo ==========================================
echo 服务启动完成！
echo ==========================================
echo 前端地址: http://localhost:3000
echo API文档: http://localhost:8000/docs
echo ==========================================
echo.

npm run dev

pause
