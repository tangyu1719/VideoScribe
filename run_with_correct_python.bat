@echo off
chcp 65001>nul
cd /d "%~dp0"

echo 使用正确的Python解释器运行脚本
echo.

if exist "D:\python解释器\python.exe" (
    echo 找到Python解释器: D:\python解释器\python.exe
    echo.
    
    REM 运行命令行版本
    echo 启动小红书视频转文字工具...
    "D:\python解释器\python.exe" simple_cli.py
    
) else (
    echo 错误: 未找到Python解释器
    echo 请确保 D:\python解释器\python.exe 存在
    pause
)
