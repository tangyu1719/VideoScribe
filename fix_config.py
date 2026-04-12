import json
import os

# 修复 .claude.json
claude_json_path = os.path.expanduser('~/.claude.json')
if os.path.exists(claude_json_path):
    with open(claude_json_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
else:
    content = {}

content['hasCompletedOnboarding'] = True

with open(claude_json_path, 'w', encoding='utf-8') as f:
    json.dump(content, f, indent=2, ensure_ascii=False)

print(f'Fixed: {claude_json_path}')

# 修复 settings.json
settings_path = os.path.expanduser('~/.claude/settings.json')
os.makedirs(os.path.dirname(settings_path), exist_ok=True)

settings = {
    'env': {
        'ANTHROPIC_API_KEY': 'sk-c884301dd9bc4e40abfa34d87778c7bf',
        'ANTHROPIC_BASE_URL': 'https://dashscope.aliyuncs.com/apps/anthropic',
        'ANTHROPIC_MODEL': 'qwen3.6-plus',
        'API_TIMEOUT_MS': '300000',
        'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1'
    },
    'alwaysThinkingEnabled': True
}

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print(f'Fixed: {settings_path}')
print('Done!')
