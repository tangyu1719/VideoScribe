import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def simple_embedding(text, dim=100):
    """简单的词袋嵌入"""
    import hashlib
    words = text.lower().split()
    embedding = [0.0] * dim
    
    for i, word in enumerate(words[:dim]):
        hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
        embedding[i % dim] = (hash_val % 1000) / 1000.0
    
    # 归一化
    norm = sum(x**2 for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding

def cosine_similarity(a, b):
    """计算余弦相似度"""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x**2 for x in a) ** 0.5
    norm_b = sum(x**2 for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

def split_text(text, chunk_size=500, overlap=100):
    """将文本分割成块"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # 尝试在句子边界处分割
        if end < text_len:
            # 在overlap范围内找句子边界
            search_start = max(start + chunk_size - overlap, start)
            for i in range(end - 1, search_start - 1, -1):
                if i < text_len and text[i] in '。！？.!?':
                    end = i + 1
                    break
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, start, end))
        
        # 移动start位置
        start = end
        if start < text_len and start > overlap:
            start = start - overlap // 2
    
    return chunks

print("="*60)
print("开始构建知识库索引 (简化版)")
print("="*60)

# 扫描文件
print("\n1. 扫描OUTPUT目录...")
if not os.path.exists(OUTPUT_DIR):
    print(f"   错误: OUTPUT目录不存在 {OUTPUT_DIR}")
    sys.exit(1)

documents = []
for file in os.listdir(OUTPUT_DIR):
    if file.endswith('.txt'):
        file_path = os.path.join(OUTPUT_DIR, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            documents.append({
                'file': file,
                'content': content,
                'path': file_path
            })
            print(f"   加载: {file} ({len(content)} 字符)")
        except Exception as e:
            print(f"   错误加载 {file}: {e}")

print(f"\n   共加载 {len(documents)} 个文件")

# 构建索引
print("\n2. 构建索引...")
index = []
for doc in documents:
    chunks = split_text(doc['content'])
    print(f"   处理 {doc['file']}: {len(chunks)} 个片段")
    
    for chunk_text, start, end in chunks:
        embedding = simple_embedding(chunk_text)
        index.append({
            'content': chunk_text,
            'file': doc['file'],
            'embedding': embedding,
            'start': start,
            'end': end
        })

print(f"\n   索引构建完成: {len(index)} 个片段")

# 保存索引
print("\n3. 保存索引...")
index_file = os.path.join(BASE_DIR, "knowledge_base", "simple_index.json")
os.makedirs(os.path.dirname(index_file), exist_ok=True)

import json
with open(index_file, 'w', encoding='utf-8') as f:
    json.dump({
        'chunks': [{k: v for k, v in item.items() if k != 'embedding'} for item in index],
        'count': len(index)
    }, f, ensure_ascii=False, indent=2)

print(f"   索引已保存: {index_file}")

# 测试搜索
print("\n4. 测试搜索...")
test_queries = [
    "JSON处理",
    "泛型",
    "飞书云文档"
]

for query in test_queries:
    print(f"\n   查询: '{query}'")
    query_embedding = simple_embedding(query)
    
    # 计算相似度
    results = []
    for item in index:
        sim = cosine_similarity(query_embedding, item['embedding'])
        results.append((item, sim))
    
    # 排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    # 显示前3个
    for i, (item, sim) in enumerate(results[:3], 1):
        print(f"   {i}. [{item['file']}] 相似度: {sim:.4f}")
        print(f"      {item['content'][:100]}...")

print("\n" + "="*60)
print("知识库索引构建完成!")
print("="*60)
