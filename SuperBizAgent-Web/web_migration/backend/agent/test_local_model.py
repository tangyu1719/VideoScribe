#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地模型加载
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 60)
print("测试本地嵌入模型加载")
print("=" * 60)

from rag_knowledge_base_v2 import RAGKnowledgeBase

print("\n初始化知识库...")
kb = RAGKnowledgeBase()

print(f"\n嵌入模型状态：{kb.embedding_model is not None}")
print(f"嵌入维度：{kb.embedding_dim}")

if kb.embedding_model is not None:
    print("\n✓ 成功加载本地模型！")
    
    # 测试嵌入
    test_text = "这是一个测试文本"
    embedding = kb._generate_embedding(test_text)
    print(f"\n测试嵌入:")
    print(f"  输入：{test_text}")
    print(f"  向量维度：{embedding.shape}")
    print(f"  向量前 5 个值：{embedding[:5]}")
else:
    print("\n✗ 使用词袋模型作为备用方案")
    
    # 测试词袋嵌入
    test_text = "这是一个测试文本"
    embedding = kb._simple_embedding(test_text)
    print(f"\n测试词袋嵌入:")
    print(f"  输入：{test_text}")
    print(f"  向量维度：{embedding.shape}")
    print(f"  向量前 5 个值：{embedding[:5]}")

print("\n" + "=" * 60)
