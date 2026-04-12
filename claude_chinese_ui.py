import json
import os

print("=== 优化 Claude Code 中文界面 ===\n")

# 1. 更新 settings.json - 添加更多中文相关配置
settings_path = os.path.expanduser('~/.claude/settings.json')
with open(settings_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 添加中文界面优化配置
config.update({
    # 语言设置
    "language": "Chinese",
    "locale": "zh-CN",
    
    # 系统提示词 - 强制中文界面
    "systemPrompt": """你是一个专业的编程助手。请遵守以下规则：

【语言要求】
- 所有界面提示、菜单、按钮必须使用中文
- 所有回复必须使用简体中文
- 代码注释使用中文
- 错误信息使用中文

【界面元素中文对照】
- Allow / 允许
- Deny / 拒绝
- Always allow / 始终允许
- Thinking... / 思考中...
- Running... / 运行中...
- Compacting... / 压缩中...
- Plan Mode / 规划模式
- Auto-accept edits / 自动接受编辑
- Bypass permissions / 绕过权限检查
- Esc to cancel / 按 Esc 取消
- Enter to confirm / 按 Enter 确认

【响应风格】
- 简洁明了
- 技术术语保留英文（如 API、JSON、HTTP）
- 提供可执行的代码示例
""",
    
    # 提示词模板
    "promptTemplates": {
        "permissionRequest": "请求权限：{action}\n是否允许？",
        "thinking": "思考中...",
        "running": "运行中：{command}",
        "error": "错误：{message}",
        "success": "完成：{action}"
    }
})

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✓ 已更新: {settings_path}")

# 2. 更新 CLAUDE.md - 添加界面汉化指令
claude_md_path = os.path.join(os.getcwd(), "CLAUDE.md")
with open(claude_md_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 添加界面汉化部分
chinese_ui_section = """

## 界面汉化规范

### 提示词中文对照
当显示以下英文提示时，使用对应的中文：

| 英文 | 中文 |
|------|------|
| Allow | 允许 |
| Deny | 拒绝 |
| Always allow | 始终允许 |
| Thinking... | 思考中... |
| Running... | 运行中... |
| Loading... | 加载中... |
| Compacting... | 压缩中... |
| Plan Mode | 规划模式 |
| Act Mode | 执行模式 |
| Auto-accept edits | 自动接受编辑 |
| Bypass permissions | 绕过权限检查 |
| Esc to cancel | 按 Esc 取消 |
| Enter to confirm | 按 Enter 确认 |
| Yes, I trust this folder | 是，我信任此文件夹 |
| No, exit | 否，退出 |
| Security guide | 安全指南 |

### 命令中文说明
当使用以下命令时，提供中文说明：
- `/help` - 显示帮助信息
- `/config` - 打开配置设置
- `/status` - 查看当前状态
- `/model` - 切换模型
- `/clear` - 清除对话历史
- `/plan` - 进入规划模式
- `/compact` - 压缩对话上下文

### 错误信息中文
所有错误信息使用中文显示：
- "Connection error" → "连接错误"
- "Invalid API key" → "API 密钥无效"
- "Model not found" → "模型未找到"
- "Timeout" → "请求超时"
"""

content += chinese_ui_section

with open(claude_md_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ 已更新: {claude_md_path}")

# 3. 创建中文快捷命令脚本
shortcut_script = '''@echo off
chcp 65001 >nul
echo ==========================================
echo    Claude Code 中文快捷命令
echo ==========================================
echo.
echo 可用命令：
echo   ccc        - 启动 Claude Code
echo   ccc-zh     - 强制中文模式启动
echo   ccc-status - 查看配置状态
echo   ccc-clear  - 清除对话历史
echo   ccc-plan   - 规划模式
echo.
echo 模型切换：
echo   ccc-turbo  - 切换到 qwen-turbo（快速）
echo   ccc-plus   - 切换到 qwen3.6-plus（平衡）
echo   ccc-max    - 切换到 qwen3-max（最强）
echo   ccc-coder  - 切换到 qwen3-coder-next（代码）
echo.
echo ==========================================
'''

shortcut_path = os.path.join(os.getcwd(), "claude-zh-help.bat")
with open(shortcut_path, 'w', encoding='utf-8') as f:
    f.write(shortcut_script)

print(f"✓ 已创建: {shortcut_path}")

print("\n=== 中文界面优化完成 ===")
print("\n优化内容：")
print("1. ✅ 添加 language: Chinese 配置")
print("2. ✅ 添加 locale: zh-CN 配置")
print("3. ✅ 添加系统提示词强制中文")
print("4. ✅ 更新 CLAUDE.md 界面汉化规范")
print("5. ✅ 创建中文快捷命令帮助")
print("\n注意：Claude Code 官方界面是硬编码英文，")
print("      以上配置可优化模型回复和提示词为中文，")
print("      但部分系统界面（如权限确认）仍显示英文。")
