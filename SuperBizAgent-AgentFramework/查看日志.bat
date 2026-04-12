@echo off
chcp 65001 >nul
echo ========================================
echo  查看知识库导入日志
echo ========================================
echo.

if exist "logs\kb_import.log" (
    echo 正在打开日志文件...
    type "logs\kb_import.log"
    echo.
    echo 日志文件位置: logs\kb_import.log
) else (
    echo 日志文件不存在，请先运行知识库导入
    echo 日志将保存在: logs\kb_import.log
)

echo.
pause
