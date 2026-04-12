import json
import os

# 国内高级玩家配置方案
print("=== 应用 Claude Code 国内高级配置 ===\n")

# 1. 更新 .claude.json - 添加更多优化配置
claude_json_path = os.path.expanduser('~/.claude.json')
with open(claude_json_path, 'r', encoding='utf-8') as f:
    claude_config = json.load(f)

# 添加国内玩家常用配置
claude_config.update({
    "hasCompletedOnboarding": True,
    "autoUpdates": False,  # 关闭自动更新，避免网络问题
    "installMethod": "unknown",
    "cachedStatsigGates": {
        "tengu_disable_bypass_permissions_mode": False,
        "tengu_prompt_suggestion": True
    },
    "cachedGrowthBookFeatures": {
        "tengu_mcp_tool_search": True,
        "tengu_disable_bypass_permissions_mode": False,
        "tengu_penguins_enabled": True,
        "tengu_chomp_inflection": True
    }
})

with open(claude_json_path, 'w', encoding='utf-8') as f:
    json.dump(claude_config, f, indent=2, ensure_ascii=False)

print(f"✓ 已更新: {claude_json_path}")

# 2. 更新 settings.json - 国内高级配置
settings_path = os.path.expanduser('~/.claude/settings.json')

# 国内高级玩家推荐配置
advanced_config = {
    "env": {
        # 核心 API 配置
        "ANTHROPIC_API_KEY": "sk-c884301dd9bc4e40abfa34d87778c7bf",
        "ANTHROPIC_AUTH_TOKEN": "sk-c884301dd9bc4e40abfa34d87778c7bf",
        "ANTHROPIC_BASE_URL": "https://dashscope.aliyuncs.com/apps/anthropic",
        
        # 默认模型 - 国内玩家推荐 qwen3.6-plus（性价比最高）
        "ANTHROPIC_MODEL": "qwen3.6-plus",
        
        # 模型映射 - 对标 Claude 模型系列
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "qwen-turbo",  # 快速轻量任务
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "qwen3-coder-next",  # 代码生成主力
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "qwen3-max",  # 复杂推理
        "ANTHROPIC_REASONING_MODEL": "qwen3-max-2026-01-23",  # 深度思考
        
        # 超时设置 - 国内网络优化
        "API_TIMEOUT_MS": "300000",  # 5分钟超时
        "CLAUDE_CODE_TIMEOUT": "300000",
        
        # 禁用非必要流量 - 减少 anthropic.com 连接
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        
        # 语言设置 - 强制中文回答
        "CLAUDE_CODE_LANGUAGE": "zh-CN",
        
        # 性能优化
        "CLAUDE_CODE_ENABLE_STREAMING": "true",
        "CLAUDE_CODE_MAX_TOKENS": "8192",
        
        # 国内镜像优化（如有）
        "HTTP_PROXY": "",  # 如有代理可填写
        "HTTPS_PROXY": ""
    },
    
    # 权限配置 - 国内玩家推荐开启自动权限
    "permissions": {
        "allow": ["*"],  # 允许所有操作（谨慎使用）
        "deny": []
    },
    
    # 功能开关
    "alwaysThinkingEnabled": True,  # 开启思考模式
    "includeCoAuthoredBy": False,  # 不添加模型署名，保持代码洁净
    
    # 项目级默认配置
    "defaultProjectConfig": {
        "permissions": {
            "allow": [
                "Bash(git*)",
                "Read(**/*.py)",
                "Read(**/*.js)",
                "Read(**/*.java)",
                "Write(**/*.py)",
                "Write(**/*.js)",
                "Write(**/*.java)"
            ],
            "deny": [
                "Bash(rm -rf /)",
                "Write(.env*)",
                "Write(*secret*)",
                "Write(*password*)"
            ]
        }
    }
}

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(advanced_config, f, indent=2, ensure_ascii=False)

print(f"✓ 已更新: {settings_path}")

# 3. 创建 CLAUDE.md - 项目级中文提示词
claude_md_content = """# CLAUDE.md - 项目级配置

## 语言设置
- **所有回答必须使用中文**
- 代码注释使用中文
- 技术文档使用中文

## 代码风格
- 遵循阿里巴巴 Java 开发手册（如适用）
- 遵循 PEP8 Python 编码规范（如适用）
- 变量命名使用英文，注释使用中文

## 模型选择策略
- 日常编码：qwen3.6-plus（默认）
- 快速生成：qwen-turbo
- 复杂架构：qwen3-max
- 代码专项：qwen3-coder-next

## 响应偏好
- 简洁明了，避免冗长
- 提供可执行的代码示例
- 解释关键设计决策
"""

claude_md_path = os.path.join(os.getcwd(), "CLAUDE.md")
with open(claude_md_path, 'w', encoding='utf-8') as f:
    f.write(claude_md_content)

print(f"✓ 已创建: {claude_md_path}")

print("\n=== 配置完成 ===")
print("\n国内高级玩家配置要点：")
print("1. ✅ 强制中文回答")
print("2. ✅ 模型映射优化（对标 Claude 系列）")
print("3. ✅ 超时时间优化（5分钟）")
print("4. ✅ 禁用非必要流量")
print("5. ✅ 权限自动允许（开发效率）")
print("6. ✅ 项目级 CLAUDE.md 中文提示词")
print("\n现在运行: claude")
