@echo off
chcp 65001 >nul
echo ========================================
echo  SuperBizAgent - AI 文档处理与知识库系统
echo  工程化版本 v2.0
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请确保Python已安装并添加到环境变量
    pause
    exit /b 1
)

echo [1/3] Python环境检查通过

REM 检查依赖
echo [2/3] 检查依赖...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到tkinter，GUI功能可能无法使用
)

echo [3/3] 启动应用程序...
echo.

REM 启动应用
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 应用程序异常退出
    pause
)
