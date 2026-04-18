#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文档导入并监控日志
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(BASE_DIR, 'src')
sys.path.insert(0, src_path)

for module_dir in ['agent', 'services', 'models', 'utils']:
    module_path = os.path.join(src_path, module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

from kb_manager_fast import get_fast_knowledge_base

print("=" * 70)
print("测试文档导入")
print("=" * 70)

# 获取知识库
kb = get_fast_knowledge_base()

# 测试文件路径
test_file = os.path.join(BASE_DIR, "test_import.txt")

print(f"\n导入文件: {test_file}")
print(f"文件大小: {os.path.getsize(test_file)} 字节")
print()

# 开始导入
start_time = time.time()

def progress_callback(current, total):
    percent = (current / total) * 100 if total > 0 else 0
    print(f"\r进度: {current}/{total} ({percent:.1f}%)", end="", flush=True)

success, message = kb.add_document(test_file, progress_callback)

elapsed_time = time.time() - start_time

print()  # 换行
print()
print("=" * 70)
print("导入结果")
print("=" * 70)
print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
print(f"消息: {message}")
print(f"总耗时: {elapsed_time:.2f} 秒")
print()

# 显示统计
stats = kb.get_stats()
print("知识库统计:")
print(f"  - 文档块数: {stats['total_chunks']}")
print(f"  - 文件数: {stats['total_files']}")
print(f"  - 嵌入维度: {stats['embedding_dim']}")
print("=" * 70)
