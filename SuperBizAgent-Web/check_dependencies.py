#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查video_gui.py的所有依赖模块
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(BASE_DIR, 'src')
sys.path.insert(0, src_path)

# 标准库依赖（不需要检查）
stdlib_modules = [
    'warnings', 'tkinter', 'threading', 'concurrent.futures', 'requests',
    'json', 'os', 'time', 'hashlib', 'datetime', 'multiprocessing', 'asyncio'
]

# 第三方库依赖
third_party_modules = [
    ('aiohttp', 'aiohttp'),
    ('volcenginesdkarkruntime', 'volcenginesdkarkruntime'),
    ('bs4', 'beautifulsoup4'),
    ('openpyxl', 'openpyxl'),
]

# 项目内部模块依赖（这些必须在src/agent/目录下）
internal_modules = [
    ('kb_manager', '知识库管理器'),
    ('rag_knowledge_base', 'RAG知识库'),
    ('chat_gui', 'AI问答GUI'),
    ('ai_chat_page', 'AI问答页面'),
    ('ai_api_config_gui', 'AI API配置GUI'),
    ('multimodal_gui', '多模态文档处理'),
    ('rag_manager_gui', 'RAG管理器GUI'),
    ('link_analyzer', '链接分析器'),
    ('feishu_integration', '飞书集成'),
    ('wechat_article_processor', '微信文章处理器'),
]

print("=" * 70)
print("检查 video_gui.py 依赖模块")
print("=" * 70)

# 检查第三方库
print("\n【第三方库依赖】")
for module, package in third_party_modules:
    try:
        __import__(module)
        print(f"  ✅ {module} ({package})")
    except ImportError:
        print(f"  ❌ {module} ({package}) - 未安装")

# 检查内部模块
print("\n【项目内部模块依赖】")
missing_modules = []
for module, description in internal_modules:
    try:
        __import__(module)
        print(f"  ✅ {module} - {description}")
    except ImportError as e:
        print(f"  ❌ {module} - {description} - 未找到")
        missing_modules.append((module, description))

print("\n" + "=" * 70)
if missing_modules:
    print(f"发现 {len(missing_modules)} 个缺失模块：")
    for module, description in missing_modules:
        print(f"  - {module}: {description}")
else:
    print("所有内部模块已就绪！")
print("=" * 70)
