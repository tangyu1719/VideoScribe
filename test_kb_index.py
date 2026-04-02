#!/usr/bin/env python3
"""测试知识库索引构建"""
import os
import sys
import traceback

# 添加当前目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def main():
    print("="*60)
    print("开始构建知识库索引")
    print("="*60)
    
    try:
        print("\n1. 导入RAG知识库模块...")
        from rag_knowledge_base import RAGKnowledgeBase
        print("   ✓ 导入成功")
    except Exception as e:
        print(f"   ✗ 导入失败: {e}")
        traceback.print_exc()
        return
    
    try:
        # 初始化知识库
        print("\n2. 初始化RAG知识库...")
        kb = RAGKnowledgeBase()
        print(f"   ✓ 知识库初始化成功")
        print(f"   知识库目录: {kb.kb_dir}")
        print(f"   索引文件: {kb.index_file}")
    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")
        traceback.print_exc()
        return
    
    # 获取output目录中的所有txt文件
    print("\n3. 扫描OUTPUT目录...")
    if not os.path.exists(OUTPUT_DIR):
        print(f"   ✗ OUTPUT目录不存在: {OUTPUT_DIR}")
        return
    
    txt_files = []
    for file in os.listdir(OUTPUT_DIR):
        if file.endswith('.txt'):
            file_path = os.path.join(OUTPUT_DIR, file)
            txt_files.append(file_path)
            print(f"   找到文件: {file}")
    
    if not txt_files:
        print("   ✗ 未找到任何txt文件")
        return
    
    print(f"\n   共找到 {len(txt_files)} 个文件")
    
    # 添加文件到知识库
    print("\n4. 添加文件到知识库...")
    success_count = 0
    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        print(f"\n   正在处理: {file_name}")
        try:
            if kb.add_document(file_path):
                success_count += 1
                print(f"   ✓ 成功添加: {file_name}")
            else:
                print(f"   ✗ 添加失败: {file_name}")
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            traceback.print_exc()
    
    print(f"\n   成功添加 {success_count}/{len(txt_files)} 个文件")
    
    # 保存索引
    print("\n5. 保存索引...")
    try:
        kb.save_index()
        print("   ✓ 索引已保存")
    except Exception as e:
        print(f"   ✗ 保存失败: {e}")
        traceback.print_exc()
    
    # 显示统计信息
    print("\n6. 知识库统计:")
    print(f"   文档片段数: {len(kb.chunks)}")
    print(f"   嵌入维度: {kb.embedding_dim}")
    
    # 测试搜索
    print("\n7. 测试搜索功能...")
    test_queries = [
        "JSON处理",
        "泛型",
        "飞书云文档"
    ]
    
    for query in test_queries:
        print(f"\n   查询: '{query}'")
        try:
            results = kb.search(query, top_k=2)
            if results:
                print(f"   找到 {len(results)} 个结果:")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['content'][:100]}...")
            else:
                print("   未找到结果")
        except Exception as e:
            print(f"   ✗ 搜索错误: {e}")
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("知识库索引构建完成!")
    print("="*60)

if __name__ == "__main__":
    main()
