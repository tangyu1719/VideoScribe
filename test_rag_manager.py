#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 RAG 知识库管理功能
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 60)
print("RAG 知识库管理系统 - 功能测试")
print("=" * 60)

# 测试 1: 导入 RAG 知识库 v2
print("\n[测试 1] 导入 RAG 知识库 v2...")
try:
    from rag_knowledge_base_v2 import RAGKnowledgeBase
    print("✓ RAG 知识库 v2 导入成功")
except Exception as e:
    print(f"✗ RAG 知识库 v2 导入失败：{e}")
    sys.exit(1)

# 测试 2: 初始化知识库
print("\n[测试 2] 初始化知识库...")
try:
    kb = RAGKnowledgeBase()
    print(f"✓ 知识库初始化成功")
    print(f"  - 知识库目录：{kb.kb_dir}")
    print(f"  - 嵌入维度：{kb.embedding_dim}")
except Exception as e:
    print(f"✗ 知识库初始化失败：{e}")
    sys.exit(1)

# 测试 3: 测试添加 TXT 文件
print("\n[测试 3] 测试添加 TXT 文件...")
test_txt = os.path.join(current_dir, "test.txt")
try:
    # 创建测试文件
    with open(test_txt, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文本文件。\n")
        f.write("用于测试 RAG 知识库的 TXT 文件添加功能。\n")
        f.write("第三行内容。\n")
    
    success = kb.add_document(test_txt)
    if success:
        print(f"✓ TXT 文件添加成功")
        stats = kb.get_stats()
        print(f"  - 总文件数：{stats['total_files']}")
        print(f"  - 总块数：{stats['total_chunks']}")
    else:
        print(f"✗ TXT 文件添加失败")
except Exception as e:
    print(f"✗ 测试失败：{e}")

# 测试 4: 测试添加 MD 文件
print("\n[测试 4] 测试添加 MD 文件...")
test_md = os.path.join(current_dir, "test.md")
try:
    # 创建测试文件
    with open(test_md, 'w', encoding='utf-8') as f:
        f.write("# 测试 Markdown 文件\n\n")
        f.write("这是一个测试 Markdown 文件。\n\n")
        f.write("## 第二节\n\n")
        f.write("用于测试 RAG 知识库的 MD 文件添加功能。\n")
    
    success = kb.add_document(test_md)
    if success:
        print(f"✓ MD 文件添加成功")
        stats = kb.get_stats()
        print(f"  - 总文件数：{stats['total_files']}")
        print(f"  - 总块数：{stats['total_chunks']}")
    else:
        print(f"✗ MD 文件添加失败")
except Exception as e:
    print(f"✗ 测试失败：{e}")

# 测试 5: 测试搜索功能
print("\n[测试 5] 测试搜索功能...")
try:
    results = kb.search("测试", top_k=3)
    if results:
        print(f"✓ 搜索成功，找到 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            print(f"  [{i}] 相似度：{result['score']:.4f}, 来源：{result['source_file']}")
    else:
        print(f"✗ 搜索未找到结果")
except Exception as e:
    print(f"✗ 搜索失败：{e}")

# 测试 6: 测试文件记录管理 GUI
print("\n[测试 6] 测试文件记录管理 GUI...")
try:
    from rag_manager_gui import RAGManagerGUI
    print("✓ RAG 管理器 GUI 导入成功")
    print("  提示：运行 'python launch_rag_manager.py' 启动管理界面")
except Exception as e:
    print(f"✗ RAG 管理器 GUI 导入失败：{e}")

# 清理测试文件
print("\n[清理] 清理测试文件...")
try:
    if os.path.exists(test_txt):
        os.remove(test_txt)
        print(f"✓ 已删除：{test_txt}")
    if os.path.exists(test_md):
        os.remove(test_md)
        print(f"✓ 已删除：{test_md}")
except Exception as e:
    print(f"✗ 清理失败：{e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n使用说明：")
print("1. 运行 'python launch_rag_manager.py' 启动独立的管理界面")
print("2. 或者在主界面点击左上角的 📚 图标打开管理窗口")
print("3. 支持添加 .txt 和 .md 格式的文件")
print("4. 可以添加单个文件或整个文件夹")
print("5. 支持删除文件和查看文件详情")
print("=" * 60)
