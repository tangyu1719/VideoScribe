@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo 小红书视频转文字工具 - 启动器
echo ========================================
echo.

rem 使用完整路径避免编码问题
set PYTHON_PATH=D:\python解释器\python.exe

if exist "%PYTHON_PATH%" (
    echo [OK] 找到Python解释器
    echo 启动GUI应用...
    echo.
    "%PYTHON_PATH%" video_gui_fixed.py
) else (
    echo [ERROR] 未找到Python解释器: %PYTHON_PATH%
    echo 请检查Python安装路径
)

echo.
echo 应用已关闭
pause
