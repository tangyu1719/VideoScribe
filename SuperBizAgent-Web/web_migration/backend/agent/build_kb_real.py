#!/usr/bin/env python3
"""使用真正的Embedding模型构建知识库索引 - 离线模式"""
import os
import sys
import json
import math

# 设置离线模式，禁止连接HuggingFace
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def split_text(text, chunk_size=500, overlap=100):
    """将文本分割成块"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        if end < text_len:
            search_start = max(start + chunk_size - overlap, start)
            for i in range(end - 1, search_start - 1, -1):
                if i < text_len and text[i] in '。！？.!?':
                    end = i + 1
                    break
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, start, end))
        
        start = end
        if start < text_len and start > overlap:
            start = start - overlap // 2
    
    return chunks

def cosine_similarity(a, b):
    """计算余弦相似度"""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x**2 for x in a))
    norm_b = math.sqrt(sum(x**2 for x in b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

print("="*60)
print("使用真正的Embedding模型构建知识库索引 (离线模式)")
print("="*60)

# 导入sentence-transformers
print("\n1. 加载Embedding模型...")
try:
    from sentence_transformers import SentenceTransformer
    
    # 直接使用本地缓存的模型路径
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    model_path = os.path.join(
        cache_dir,
        "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
        "snapshots"
    )
    
    # 找到snapshot目录
    if os.path.exists(model_path):
        snapshots = os.listdir(model_path)
        if snapshots:
            model_full_path = os.path.join(model_path, snapshots[0])
            print(f"   找到本地模型: {model_full_path}")
        else:
            raise Exception("本地模型snapshot不存在")
    else:
        raise Exception(f"本地模型路径不存在: {model_path}")
    
    # 从本地路径加载模型
    model = SentenceTransformer(model_full_path)
    embedding_dim = model.get_sentence_embedding_dimension()
    print(f"   ✓ 模型加载成功: paraphrase-multilingual-MiniLM-L12-v2")
    print(f"   ✓ 嵌入维度: {embedding_dim}")
except Exception as e:
    print(f"   ✗ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 扫描文件
print("\n2. 扫描OUTPUT目录...")
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
print("\n3. 构建索引 (使用Embedding模型)...")
index = []
all_chunks_text = []
chunk_metadata = []

for doc in documents:
    chunks = split_text(doc['content'])
    print(f"   处理 {doc['file']}: {len(chunks)} 个片段")
    
    for chunk_text, start, end in chunks:
        all_chunks_text.append(chunk_text)
        chunk_metadata.append({
            'file': doc['file'],
            'start': start,
            'end': end
        })

print(f"\n   总共 {len(all_chunks_text)} 个片段，开始生成Embedding...")

# 批量生成Embedding
batch_size = 32
embeddings = []
for i in range(0, len(all_chunks_text), batch_size):
    batch = all_chunks_text[i:i+batch_size]
    print(f"   处理批次 {i//batch_size + 1}/{(len(all_chunks_text)-1)//batch_size + 1}...")
    batch_embeddings = model.encode(batch, show_progress_bar=False)
    embeddings.extend(batch_embeddings.tolist())

# 构建索引结构
for i, (chunk_text, metadata) in enumerate(zip(all_chunks_text, chunk_metadata)):
    index.append({
        'content': chunk_text,
        'file': metadata['file'],
        'start': metadata['start'],
        'end': metadata['end'],
        'embedding': embeddings[i]
    })

print(f"\n   ✓ 索引构建完成: {len(index)} 个片段")

# 保存索引
print("\n4. 保存索引...")
kb_dir = os.path.join(BASE_DIR, "knowledge_base")
os.makedirs(kb_dir, exist_ok=True)

index_file = os.path.join(kb_dir, "real_index.json")
with open(index_file, 'w', encoding='utf-8') as f:
    json.dump({
        'chunks': index,
        'count': len(index),
        'embedding_dim': embedding_dim,
        'model': 'paraphrase-multilingual-MiniLM-L12-v2'
    }, f, ensure_ascii=False, indent=2)

print(f"   ✓ 索引已保存: {index_file}")

# 测试搜索
print("\n5. 测试搜索 (使用Embedding相似度)...")
test_queries = [
    "JSON处理",
    "泛型",
    "飞书云文档"
]

for query in test_queries:
    print(f"\n   查询: '{query}'")
    query_embedding = model.encode([query])[0].tolist()
    
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
