@echo off
chcp 65001 >nul
echo ========================================
echo  SuperBizAgent - AI Agent Framework
echo  标准Agent工程框架版本
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请确保Python已安装并添加到环境变量
    pause
    exit /b 1
)

echo [1/2] Python环境检查通过

REM 启动应用
echo [2/2] 启动Agent应用...
echo.

REM 启动应用
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 应用程序异常退出
    pause
)
