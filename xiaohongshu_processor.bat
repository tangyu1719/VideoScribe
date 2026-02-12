@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo 欢迎使用小红书视频转文字工具
echo ========================================
set /p xhs_link="请输入小红书链接: "

if "%xhs_link%"=="" (
    echo ERROR: 链接不能为空
    pause
    exit /b 1
)

echo 开始处理链接: %xhs_link%
python xiaohongshu_direct_api.py "%xhs_link%"

if %errorlevel% neq 0 (
    echo.
    echo WARNING: 如果API调用失败，可以尝试:
    echo    1. 检查网络连接
    echo    2. 确认API端点是否正确
    echo    3. 使用网站界面手动处理
    echo    4. 确保链接是有效的完整小红书链接
    pause
)