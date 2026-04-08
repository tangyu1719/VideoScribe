#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG知识库测试脚本
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_knowledge_base import RAGKnowledgeBase

def test_rag():
    print("=" * 60)
    print("RAG知识库功能测试")
    print("=" * 60)
    
    # 初始化知识库
    kb = RAGKnowledgeBase()
    
    # 显示统计信息
    print("\n【知识库统计】")
    stats = kb.get_stats()
    print(f"- 总块数: {stats['total_chunks']}")
    print(f"- 嵌入维度: {stats['embedding_dim']}")
    print(f"- 源文件: {stats['source_files']}")
    
    # 自动索引output目录
    output_dir = kb.output_dir
    if os.path.exists(output_dir):
        print(f"\n【索引文档】")
        print(f"扫描目录: {output_dir}")
        
        indexed_count = 0
        for filename in os.listdir(output_dir):
            if filename.endswith('.txt') or filename.endswith('.md'):
                file_path = os.path.join(output_dir, filename)
                print(f"\n正在索引: {filename}")
                if kb.add_document(file_path):
                    indexed_count += 1
        
        print(f"\n成功索引 {indexed_count} 个文档")
    else:
        print(f"\n输出目录不存在: {output_dir}")
    
    # 显示更新后的统计
    print("\n【更新后的统计】")
    stats = kb.get_stats()
    print(f"- 总块数: {stats['total_chunks']}")
    print(f"- 源文件: {stats['source_files']}")
    
    # 测试搜索功能
    if stats['total_chunks'] > 0:
        print("\n【搜索测试】")
        test_queries = [
            "视频转文字",
            "AI分析",
            "文档生成"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            results = kb.search(query, top_k=2)
            
            if results:
                print(f"找到 {len(results)} 个相关结果:")
                for i, result in enumerate(results, 1):
                    print(f"  [{i}] 相似度: {result['score']:.4f}")
                    print(f"      来源: {result['source_file']}")
                    print(f"      内容: {result['content'][:100]}...")
            else:
                print("  未找到相关结果")
    else:
        print("\n知识库为空，跳过搜索测试")
        print("提示：请在output目录中添加一些文档后再测试")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_rag()
