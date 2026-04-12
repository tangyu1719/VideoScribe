# Claude Code 配置修复脚本
# 以管理员身份运行 PowerShell，然后执行此脚本

Write-Host "=== Claude Code 配置修复工具 ===" -ForegroundColor Green
Write-Host ""

# 1. 修复 .claude.json
$claudeJsonPath = "$env:USERPROFILE\.claude.json"
Write-Host "正在修复: $claudeJsonPath" -ForegroundColor Yellow

if (Test-Path $claudeJsonPath) {
    $content = Get-Content $claudeJsonPath -Raw | ConvertFrom-Json
    
    # 添加 hasCompletedOnboarding
    if (-not $content.PSObject.Properties.Name.Contains("hasCompletedOnboarding")) {
        $content | Add-Member -Name "hasCompletedOnboarding" -Value $true -MemberType NoteProperty
        Write-Host "✓ 已添加 hasCompletedOnboarding: true" -ForegroundColor Green
    } else {
        $content.hasCompletedOnboarding = $true
        Write-Host "✓ 已更新 hasCompletedOnboarding: true" -ForegroundColor Green
    }
    
    # 保存文件
    $content | ConvertTo-Json -Depth 10 | Set-Content $claudeJsonPath -Encoding UTF8
    Write-Host "✓ 文件已保存" -ForegroundColor Green
} else {
    # 创建新文件
    @{hasCompletedOnboarding = $true} | ConvertTo-Json | Set-Content $claudeJsonPath -Encoding UTF8
    Write-Host "✓ 已创建新文件" -ForegroundColor Green
}

# 2. 修复 settings.json
$settingsPath = "$env:USERPROFILE\.claude\settings.json"
Write-Host ""
Write-Host "正在修复: $settingsPath" -ForegroundColor Yellow

$settings = @{
    env = @{
        ANTHROPIC_API_KEY = "sk-c884301dd9bc4e40abfa34d87778c7bf"
        ANTHROPIC_BASE_URL = "https://dashscope.aliyuncs.com/apps/anthropic"
        ANTHROPIC_MODEL = "qwen3.6-plus"
        API_TIMEOUT_MS = "300000"
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = "1"
    }
    alwaysThinkingEnabled = $true
}

# 确保目录存在
$claudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    Write-Host "✓ 创建目录: $claudeDir" -ForegroundColor Green
}

$settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
Write-Host "✓ settings.json 已更新" -ForegroundColor Green

# 3. 验证配置
Write-Host ""
Write-Host "=== 配置验证 ===" -ForegroundColor Cyan
Write-Host ""

Write-Host ".claude.json 内容:" -ForegroundColor Yellow
Get-Content $claudeJsonPath | Select-Object -First 3

Write-Host ""
Write-Host "settings.json 内容:" -ForegroundColor Yellow
Get-Content $settingsPath

Write-Host ""
Write-Host "=== 配置完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以运行: claude" -ForegroundColor Cyan
Write-Host ""
Read-Host "按 Enter 键退出"
