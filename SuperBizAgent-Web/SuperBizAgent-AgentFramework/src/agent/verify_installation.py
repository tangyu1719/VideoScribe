#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证所有依赖安装是否成功
"""

print("="*60)
print("验证RAG知识库依赖安装")
print("="*60)

# 检查各个依赖
dependencies = [
    ("sentence-transformers", "文本向量嵌入"),
    ("faiss", "FAISS向量检索"),
    ("PyPDF2", "PDF文件解析"),
    ("docx", "Word文档解析"),
    ("sklearn", "机器学习工具包"),
]

all_success = True

for package, desc in dependencies:
    try:
        if package == "faiss":
            import faiss
            print(f"✅ {package:25s} - {desc}")
        elif package == "docx":
            import docx
            print(f"✅ {package:25s} - {desc}")
        elif package == "sklearn":
            import sklearn
            print(f"✅ {package:25s} - {desc}")
        else:
            __import__(package.replace("-", "_"))
            print(f"✅ {package:25s} - {desc}")
    except ImportError as e:
        print(f"❌ {package:25s} - {desc} - 错误: {e}")
        all_success = False

print("\n" + "="*60)

if all_success:
    print("🎉 所有依赖安装成功！")
    print("\n现在您可以：")
    print("1. 运行 python test_rag.py 测试RAG功能")
    print("2. 运行 python chat_gui.py 启动AI问答系统")
    print("3. 在主程序中点击 '🤖 AI问答' 按钮使用知识库功能")
    
    # 测试RAG知识库初始化
    print("\n" + "="*60)
    print("测试RAG知识库初始化...")
    print("="*60)
    
    try:
        from rag_knowledge_base_v2 import RAGKnowledgeBaseV2
        kb = RAGKnowledgeBaseV2()
        stats = kb.get_stats()
        
        print(f"✅ RAG知识库初始化成功！")
        print(f"   向量库类型: {stats['index_type']}")
        print(f"   嵌入模型: {stats['embedding_model']}")
        print(f"   嵌入维度: {stats['embedding_dim']}")
        print(f"   文档块数: {stats['total_chunks']}")
        
    except Exception as e:
        print(f"❌ RAG知识库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("⚠️ 部分依赖未安装成功")
    print("请运行: pip install -r requirements.txt")

print("\n" + "="*60)
input("\n按回车键退出...")
