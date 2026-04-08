#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试模型加载
"""

import os
import sys

# 设置离线模式
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

print("测试 1: 检查模型缓存路径...")
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
model_name = "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
model_path = os.path.join(cache_dir, model_name)
print(f"模型路径：{model_path}")
print(f"路径存在：{os.path.exists(model_path)}")

if os.path.exists(model_path):
    print("\n模型文件列表:")
    for root, dirs, files in os.walk(model_path):
        level = root.replace(model_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 只显示前 5 个文件
            print(f'{subindent}{file}')
        if len(files) > 5:
            print(f'{subindent}... 共 {len(files)} 个文件')

print("\n" + "=" * 60)
print("测试 2: 尝试加载模型...")
try:
    from sentence_transformers import SentenceTransformer
    print("✓ sentence-transformers 导入成功")
    
    print("\n正在加载模型（离线模式）...")
    model = SentenceTransformer(
        model_path,
        local_files_only=True
    )
    print("✓ 模型加载成功！")
    
    embedding_dim = model.get_sentence_embedding_dimension()
    print(f"嵌入维度：{embedding_dim}")
    
    # 测试嵌入
    test_text = "这是一个测试"
    embedding = model.encode(test_text, convert_to_numpy=True)
    print(f"\n测试嵌入成功:")
    print(f"  文本：{test_text}")
    print(f"  向量形状：{embedding.shape}")
    print(f"  向量前 5 个值：{embedding[:5]}")
    
except Exception as e:
    print(f"✗ 加载失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
