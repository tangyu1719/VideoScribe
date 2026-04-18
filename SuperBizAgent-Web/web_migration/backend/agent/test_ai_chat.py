#!/usr/bin/env python3
"""测试AI对话功能 - 使用知识库"""
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载知识库索引
print("="*60)
print("测试AI对话 - 使用知识库")
print("="*60)

# 加载简单索引
index_file = os.path.join(BASE_DIR, "knowledge_base", "simple_index.json")
if os.path.exists(index_file):
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    print(f"\n✓ 加载知识库索引: {index_data.get('count', 0)} 个片段")
else:
    print(f"\n✗ 索引文件不存在: {index_file}")
    sys.exit(1)

# 模拟RAG搜索
def simple_search(query, top_k=3):
    """简单的关键词匹配搜索"""
    query_words = set(query.lower().split())
    results = []
    
    for chunk in index_data.get('chunks', []):
        content = chunk.get('content', '').lower()
        # 计算匹配度
        match_count = sum(1 for word in query_words if word in content)
        if match_count > 0:
            results.append({
                'content': chunk.get('content', ''),
                'file': chunk.get('file', ''),
                'score': match_count / len(query_words) if query_words else 0
            })
    
    # 排序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

# 测试5个问题
test_questions = [
    "JSON处理方案优化版这篇博客提到了什么技术？",
    "泛型理解这篇文章讲了什么？",
    "飞书云文档MCP工具调用教程的主要内容是什么？",
    "如何处理JSON数据？",
    "MCP工具是什么？"
]

print("\n" + "="*60)
print("开始测试5个问题")
print("="*60)

for i, question in enumerate(test_questions, 1):
    print(f"\n【问题 {i}】{question}")
    print("-"*60)
    
    # 搜索知识库
    results = simple_search(question, top_k=3)
    
    if results:
        print(f"✓ 从知识库检索到 {len(results)} 条相关信息:")
        for j, result in enumerate(results, 1):
            print(f"\n  [{j}] 来源: {result['file']} (相关度: {result['score']:.2f})")
            print(f"      内容: {result['content'][:150]}...")
    else:
        print("✗ 未从知识库检索到相关信息")
    
    print()

print("="*60)
print("测试完成!")
print("="*60)
