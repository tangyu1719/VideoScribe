# PowerShell启动脚本
# 设置工作目录
Set-Location -Path $PSScriptRoot

Write-Host "========================================" -ForegroundColor Green
Write-Host "小红书视频转文字工具 - 启动器" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Python解释器路径
$PythonPaths = @(
    "D:\python解释器\python.exe",
    "C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe", 
    "C:\Users\PC\AppData\Local\Programs\Python\Python312\python.exe",
    "python"
)

$PythonExe = $null
foreach ($path in $PythonPaths) {
    if (Test-Path $path -ErrorAction SilentlyContinue) {
        $PythonExe = $path
        Write-Host "[✓] 找到Python: $PythonExe" -ForegroundColor Green
        break
    }
    elseif (Get-Command $path -ErrorAction SilentlyContinue) {
        $PythonExe = $path
        Write-Host "[✓] 找到Python: $PythonExe" -ForegroundColor Green
        break
    }
}

if (-not $PythonExe) {
    Write-Host "[✗] 未找到Python解释器" -ForegroundColor Red
    Write-Host "请确保Python已安装并添加到PATH" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host ""
Write-Host "启动GUI应用..." -ForegroundColor Cyan
Write-Host ""

# 启动Python GUI
& $PythonExe "video_gui_fixed.py"

Write-Host ""
Write-Host "应用已关闭" -ForegroundColor Yellow
Read-Host "按Enter键退出"
