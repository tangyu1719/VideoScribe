#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查video_gui.py的所有依赖模块 - 修正版
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加src目录到Python路径
src_path = os.path.join(BASE_DIR, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 添加各模块路径
for module_dir in ['agent', 'services', 'models', 'utils', 'graph']:
    module_path = os.path.join(src_path, module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

# 项目内部模块依赖
internal_modules = [
    ('kb_manager', '知识库管理器'),
    ('rag_knowledge_base', 'RAG知识库'),
    ('chat_gui', 'AI问答GUI'),
    ('ai_chat_page', 'AI问答页面'),
    ('ai_api_config_gui', 'AI API配置GUI'),
    ('multimodal_gui', '多模态文档处理'),
    ('rag_manager_gui', 'RAG管理器GUI'),
    ('link_analyzer', '链接分析器'),
    ('wechat_article_processor', '微信文章处理器'),
]

print("=" * 70)
print("检查 video_gui.py 依赖模块")
print("=" * 70)

# 检查内部模块
print("\n【项目内部模块依赖】")
missing_modules = []
for module, description in internal_modules:
    try:
        __import__(module)
        print(f"  ✅ {module} - {description}")
    except ImportError as e:
        print(f"  ❌ {module} - {description}")
        print(f"     错误: {e}")
        missing_modules.append((module, description))

print("\n" + "=" * 70)
if missing_modules:
    print(f"发现 {len(missing_modules)} 个缺失模块：")
    for module, description in missing_modules:
        print(f"  - {module}: {description}")
else:
    print("所有内部模块已就绪！")
print("=" * 70)
