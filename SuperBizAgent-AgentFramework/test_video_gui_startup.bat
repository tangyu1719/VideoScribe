@echo off
chcp 65001 >nul
echo 启动 video_gui.py 并记录日志...
echo 开始时间：%date% %time%
echo.

cd /d "%~dp0src\agent"

REM 运行 video_gui.py 并记录所有输出
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe video_gui.py 2>&1 | tee ..\..\logs\video_gui_startup.log

echo.
echo 结束时间：%date% %time%
echo 日志已保存到：..\..\logs\video_gui_startup.log
pause
