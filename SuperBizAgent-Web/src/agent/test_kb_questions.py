#!/usr/bin/env python3
"""知识库回归测试 - 5个问题"""
import os
import sys
import json
import math

# 设置离线模式
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cosine_similarity(a, b):
    """计算余弦相似度"""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x**2 for x in a))
    norm_b = math.sqrt(sum(x**2 for x in b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

print("="*70)
print("知识库回归测试 - 5个问题")
print("="*70)

# 加载索引
print("\n1. 加载知识库索引...")
index_file = os.path.join(BASE_DIR, "knowledge_base", "real_index.json")
if not os.path.exists(index_file):
    print(f"   ✗ 索引文件不存在: {index_file}")
    sys.exit(1)

with open(index_file, 'r', encoding='utf-8') as f:
    index_data = json.load(f)

index = index_data.get('chunks', [])
print(f"   ✓ 加载成功: {len(index)} 个片段")
print(f"   ✓ 嵌入维度: {index_data.get('embedding_dim', 'N/A')}")
print(f"   ✓ 模型: {index_data.get('model', 'N/A')}")

# 加载Embedding模型
print("\n2. 加载Embedding模型...")
try:
    from sentence_transformers import SentenceTransformer
    
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    model_path = os.path.join(
        cache_dir,
        "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
        "snapshots"
    )
    
    snapshots = os.listdir(model_path)
    model_full_path = os.path.join(model_path, snapshots[0])
    
    model = SentenceTransformer(model_full_path)
    print(f"   ✓ 模型加载成功")
except Exception as e:
    print(f"   ✗ 模型加载失败: {e}")
    sys.exit(1)

# 5个测试问题
print("\n" + "="*70)
print("开始测试5个问题")
print("="*70)

test_questions = [
    "JSON处理方案优化版这篇博客提到了什么技术？",
    "泛型理解这篇文章讲了什么？",
    "飞书云文档MCP工具调用教程的主要内容是什么？",
    "如何处理JSON数据？",
    "MCP工具是什么？"
]

all_passed = True

for i, question in enumerate(test_questions, 1):
    print(f"\n【问题 {i}】{question}")
    print("-"*70)
    
    # 生成查询的embedding
    query_embedding = model.encode([question])[0].tolist()
    
    # 搜索
    results = []
    for item in index:
        sim = cosine_similarity(query_embedding, item['embedding'])
        results.append((item, sim))
    
    # 排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    # 显示前3个结果
    if results:
        print(f"✓ 检索到 {len(results)} 个结果，显示前3个:")
        for j, (item, sim) in enumerate(results[:3], 1):
            print(f"\n  [{j}] 来源: {item['file']}")
            print(f"      相似度: {sim:.4f}")
            print(f"      内容: {item['content'][:150]}...")
            
            # 检查相似度是否过低
            if sim < 0.2:
                print(f"      ⚠ 警告: 相似度过低 ({sim:.4f} < 0.2)")
                all_passed = False
    else:
        print("✗ 未检索到任何结果")
        all_passed = False

print("\n" + "="*70)
if all_passed:
    print("✓ 所有测试通过!")
else:
    print("✗ 部分测试未通过，请检查知识库内容")
print("="*70)
