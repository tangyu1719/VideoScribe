#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复transformers离线模式 - 在应用启动时最先导入
"""

import os
import sys

# 必须在导入transformers之前设置！！！
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

# 禁用transformers的safetensors自动转换检查
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'

# 设置本地缓存目录
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir

# 禁用自动转换线程
import transformers
# 禁用自动转换功能
transformers.utils.hub._is_offline_mode = lambda: True

print("✅ Transformers离线模式已启用")
print(f"   缓存目录: {cache_dir}")
