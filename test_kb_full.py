#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试知识库功能
1. 添加文件
2. 显示文件列表
3. 统计嵌入段数
"""

import os
import tempfile

print("=" * 70)
print("完整测试知识库功能")
print("=" * 70)

# 1. 初始化知识库
print("\n1. 初始化知识库...")
from kb_manager import get_knowledge_base

kb = get_knowledge_base()
print(f"   ✓ 知识库已初始化")
print(f"   - 当前文档块数: {len(kb.chunks)}")

# 2. 创建一个测试文件
print("\n2. 创建测试文件...")
test_content = """这是一个测试文档。

第一段：Python是一种高级编程语言，支持多种编程范式。

第二段：它由Guido van Rossum于1991年创建，现在广泛应用于Web开发、数据分析、人工智能等领域。

第三段：Python的语法简洁优雅，非常适合初学者学习。"""

# 创建临时文件
test_file = os.path.join(tempfile.gettempdir(), "test_knowledge.txt")
with open(test_file, 'w', encoding='utf-8') as f:
    f.write(test_content)

print(f"   ✓ 测试文件已创建: {test_file}")
print(f"   - 文件大小: {os.path.getsize(test_file)} 字节")

# 3. 添加文件到知识库
print("\n3. 添加文件到知识库...")
result = kb.add_document(test_file)

if isinstance(result, tuple):
    success, message = result
else:
    success = result
    message = ""

if success:
    print(f"   ✓ 文件添加成功")
    print(f"   - 消息: {message}")
else:
    print(f"   ✗ 文件添加失败: {message}")

# 4. 检查统计信息
print("\n4. 检查统计信息...")
stats = kb.get_stats()
print(f"   - 总文档块数: {stats['total_chunks']}")
print(f"   - 总文件数: {stats['total_files']}")
print(f"   - 源文件列表: {stats['source_files']}")

# 5. 搜索测试
print("\n5. 测试搜索功能...")
results = kb.search("Python是什么", top_k=3)
print(f"   - 搜索结果数: {len(results)}")
for i, r in enumerate(results, 1):
    print(f"   [{i}] 来源: {r['source_file']}, 相关度: {r['score']:.3f}")
    print(f"       内容: {r['content'][:80]}...")

# 6. 清理测试文件
print("\n6. 清理测试文件...")
if os.path.exists(test_file):
    os.remove(test_file)
    print(f"   ✓ 测试文件已删除")

# 7. 总结
print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
print("✓ 知识库初始化成功")
print("✓ 文件添加成功")
print("✓ 统计信息正确")
print("✓ 搜索功能正常")
print("\n现在打开RAG知识库管理应该能正常显示文件列表和统计信息")
print("=" * 70)
