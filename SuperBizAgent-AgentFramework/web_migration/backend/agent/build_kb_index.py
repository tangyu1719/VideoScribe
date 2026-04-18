import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

print("="*60)
print("开始构建知识库索引")
print("="*60)

# 导入RAG模块
sys.path.insert(0, BASE_DIR)
from rag_knowledge_base import RAGKnowledgeBase

# 初始化知识库
print("\n1. 初始化知识库...")
kb = RAGKnowledgeBase()
print(f"   知识库目录: {kb.kb_dir}")
print(f"   索引文件: {kb.index_file}")

# 扫描文件
print("\n2. 扫描OUTPUT目录...")
if not os.path.exists(OUTPUT_DIR):
    print(f"   错误: OUTPUT目录不存在 {OUTPUT_DIR}")
    sys.exit(1)

txt_files = []
for file in os.listdir(OUTPUT_DIR):
    if file.endswith('.txt'):
        file_path = os.path.join(OUTPUT_DIR, file)
        txt_files.append(file_path)
        print(f"   找到: {file}")

print(f"\n   共找到 {len(txt_files)} 个文件")

# 添加文件
print("\n3. 添加文件到知识库...")
success_count = 0
for file_path in txt_files:
    file_name = os.path.basename(file_path)
    print(f"   处理: {file_name}...", end=" ")
    try:
        if kb.add_document(file_path):
            success_count += 1
            print("成功")
        else:
            print("失败")
    except Exception as e:
        print(f"错误: {e}")

print(f"\n   成功添加 {success_count}/{len(txt_files)} 个文件")

# 保存索引
print("\n4. 保存索引...")
kb.save_index()
print("   索引已保存")

# 统计
print("\n5. 知识库统计:")
stats = kb.get_stats()
print(f"   文档片段数: {stats['total_chunks']}")
print(f"   嵌入维度: {stats['embedding_dim']}")
print(f"   源文件: {stats['source_files']}")

# 测试搜索
print("\n6. 测试搜索...")
test_queries = [
    "JSON处理",
    "泛型",
    "飞书云文档"
]

for query in test_queries:
    print(f"\n   查询: '{query}'")
    results = kb.search(query, top_k=2)
    if results:
        print(f"   找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. [{result['source_file']}] {result['content'][:80]}...")
    else:
        print("   未找到结果")

print("\n" + "="*60)
print("知识库索引构建完成!")
print("="*60)
