#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试脚本 - 测试快速知识库管理器
验证BGE-Large 1024维是否生效
"""

import os
import sys

# 添加路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(BASE_DIR, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

for module_dir in ['agent', 'services', 'models', 'utils']:
    module_path = os.path.join(src_path, module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

print("=" * 70)
print("回归测试 - 快速知识库管理器")
print("=" * 70)

# 测试1: 导入模块
print("\n【测试1】导入kb_manager_fast模块...")
try:
    from kb_manager_fast import get_fast_knowledge_base, FastKnowledgeBaseManager
    print("✅ 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 初始化知识库
print("\n【测试2】初始化知识库...")
try:
    kb = get_fast_knowledge_base()
    print("✅ 初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    sys.exit(1)

# 测试3: 检查维度
print("\n【测试3】检查嵌入维度...")
stats = kb.get_stats()
embedding_dim = stats.get('embedding_dim', 0)
print(f"  - 当前维度: {embedding_dim}")

if embedding_dim == 1024:
    print("✅ 维度正确 (1024 - BGE-Large)")
else:
    print(f"⚠️ 维度不匹配 (期望1024，实际{embedding_dim})")

# 测试4: 检查模型
print("\n【测试4】检查模型状态...")
model_loaded = stats.get('model_loaded', False)
if model_loaded:
    print("✅ 模型已加载")
else:
    print("⚠️ 模型未加载")

# 测试5: 测试文档添加（模拟）
print("\n【测试5】测试文档处理...")
test_content = """
这是一个测试文档。
用于验证知识库功能是否正常。
包含多行文本内容。
"""

# 测试文本分割
chunks = kb._split_text(test_content)
print(f"  - 文本分割: {len(chunks)} 个块")

# 测试嵌入生成
if kb._model_loaded:
    print("  - 测试嵌入生成...")
    test_texts = [chunk[0] for chunk in chunks]
    embeddings = kb._generate_embeddings_batch(test_texts)
    print(f"  - 生成嵌入: {len(embeddings)} 个")
    if embeddings and embeddings[0] is not None:
        print(f"  - 嵌入维度: {len(embeddings[0])}")
        if len(embeddings[0]) == 1024:
            print("✅ 嵌入维度正确")
        else:
            print(f"⚠️ 嵌入维度错误 (期望1024，实际{len(embeddings[0])})")

# 测试6: 检查video_gui.py修改
print("\n【测试6】检查video_gui.py导入...")
with open(os.path.join(src_path, 'agent', 'video_gui.py'), 'r', encoding='utf-8') as f:
    content = f.read()
    if 'kb_manager_fast' in content:
        print("✅ video_gui.py已修改为使用kb_manager_fast")
    else:
        print("⚠️ video_gui.py未使用kb_manager_fast")

# 总结
print("\n" + "=" * 70)
print("回归测试完成")
print("=" * 70)
print(f"\n统计信息:")
print(f"  - 嵌入维度: {embedding_dim}")
print(f"  - 模型状态: {'已加载' if model_loaded else '未加载'}")
print(f"  - 文档块数: {stats.get('total_chunks', 0)}")

if embedding_dim == 1024 and model_loaded:
    print("\n✅ 所有测试通过！BGE-Large 1024维已生效")
    sys.exit(0)
else:
    print("\n⚠️ 部分测试未通过")
    sys.exit(1)
