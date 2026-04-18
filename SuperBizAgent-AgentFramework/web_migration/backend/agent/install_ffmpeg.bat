@echo off
chcp 65001 >nul
echo ============================================
echo FFmpeg 自动安装脚本
echo ============================================
echo.

set "INSTALL_DIR=%~dp0tools\ffmpeg"
set "TEMP_ZIP=%~dp0ffmpeg_temp.zip"
set "TEMP_EXTRACT=%~dp0ffmpeg_temp"

:: 检查是否已安装
if exist "%INSTALL_DIR%\bin\ffmpeg.exe" (
    echo [OK] FFmpeg 已安装
    echo 路径: %INSTALL_DIR%
    goto :verify
)

:: 创建安装目录
echo [INFO] 创建安装目录...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: 下载ffmpeg
echo.
echo [INFO] 步骤1: 下载 FFmpeg
echo ----------------------------------------
echo 正在从 https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip 下载...
echo 这可能需要几分钟...

powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile '%TEMP_ZIP%' -UseBasicParsing"

if not exist "%TEMP_ZIP%" (
    echo [ERROR] 下载失败
    echo 请手动下载: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    pause
    exit /b 1
)

echo [OK] 下载完成

:: 解压ffmpeg
echo.
echo [INFO] 步骤2: 解压 FFmpeg
echo ----------------------------------------
echo 正在解压...

if exist "%TEMP_EXTRACT%" rmdir /s /q "%TEMP_EXTRACT%"
powershell -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_EXTRACT%' -Force"

if not exist "%TEMP_EXTRACT%" (
    echo [ERROR] 解压失败
    pause
    exit /b 1
)

echo [OK] 解压完成

:: 查找ffmpeg目录
echo.
echo [INFO] 步骤3: 查找 FFmpeg 可执行文件
echo ----------------------------------------

for /f "delims=" %%i in ('dir /s /b "%TEMP_EXTRACT%\ffmpeg.exe"') do (
    set "FFMPEG_BIN_DIR=%%~dpi"
    goto :found
)

:found
if not defined FFMPEG_BIN_DIR (
    echo [ERROR] 未找到 ffmpeg.exe
    pause
    exit /b 1
)

echo [OK] 找到 FFmpeg: %FFMPEG_BIN_DIR%

:: 移动到安装目录
echo.
echo [INFO] 步骤4: 安装到目标目录
echo ----------------------------------------

if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

:: 移动bin目录的上级目录（即ffmpeg根目录）
for %%i in ("%FFMPEG_BIN_DIR%..") do set "FFMPEG_ROOT=%%~fi"
xcopy /s /e /i /q "%FFMPEG_ROOT%\*" "%INSTALL_DIR%\"

if not exist "%INSTALL_DIR%\bin\ffmpeg.exe" (
    echo [ERROR] 安装失败
    pause
    exit /b 1
)

echo [OK] 安装完成: %INSTALL_DIR%

:: 清理临时文件
echo.
echo [INFO] 步骤5: 清理临时文件
echo ----------------------------------------

if exist "%TEMP_ZIP%" del /f /q "%TEMP_ZIP%"
if exist "%TEMP_EXTRACT%" rmdir /s /q "%TEMP_EXTRACT%"

echo [OK] 清理完成

:verify
:: 验证安装
echo.
echo [INFO] 步骤6: 验证安装
echo ----------------------------------------

if exist "%INSTALL_DIR%\bin\ffmpeg.exe" (
    echo [OK] FFmpeg 安装成功!
    echo 路径: %INSTALL_DIR%\bin\ffmpeg.exe
    
    :: 添加到PATH
    setx PATH "%INSTALL_DIR%\bin;%PATH%" /M >nul 2>&1
    echo [OK] 已添加到系统 PATH
) else (
    echo [ERROR] 安装验证失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo FFmpeg 安装完成!
echo ============================================
echo.
echo 现在可以正常使用视频转文字功能了。
echo 请重新启动程序。
echo.
pause
