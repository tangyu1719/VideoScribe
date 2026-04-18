#!/usr/bin/env python3
"""
Agentic RAG 回归测试
测试完整的知识库流水线
"""

import os
import sys
import json
from pathlib import Path

# 测试Agentic RAG模块
from agentic_rag_final import AgenticRAG, DynamicSemanticSplitter

def test_semantic_splitter():
    """测试动态语义分割器"""
    print("\n" + "=" * 70)
    print("测试1: 动态语义分割器")
    print("=" * 70)
    
    splitter = DynamicSemanticSplitter(
        target_chunk_size=200,
        min_chunk_size=100,
        max_chunk_size=300,
        overlap_ratio=0.1
    )
    
    # 测试文本 - 包含多个句子
    text = """
    人工智能是计算机科学的一个重要分支。
    机器学习是AI的核心技术之一，它使计算机能够从数据中学习。
    深度学习是机器学习的一个子集，使用神经网络处理复杂数据。
    自然语言处理让计算机能够理解和生成人类语言。
    计算机视觉使机器能够看懂图像和视频。
    强化学习通过与环境交互来学习最优策略。
    """
    
    chunks = splitter.split(text, "test.txt", 1)
    
    print(f"原文本长度: {len(text)} 字符")
    print(f"分割后块数: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\n块 {i}:")
        print(f"  内容长度: {len(chunk.content)} 字符")
        print(f"  内容预览: {chunk.content[:50]}...")
        print(f"  位置: {chunk.start_pos}-{chunk.end_pos}")
        print(f"  页号: {chunk.page_number}")
    
    # 验证重合
    if len(chunks) >= 2:
        for i in range(len(chunks) - 1):
            current_end = chunks[i].end_pos
            next_start = chunks[i + 1].start_pos
            overlap = current_end - next_start
            print(f"\n块{i}和块{i+1}的重合: {overlap} 字符")
    
    print("\n✓ 动态语义分割器测试通过")
    return len(chunks) > 0

def test_document_ingestion():
    """测试文档导入"""
    print("\n" + "=" * 70)
    print("测试2: 文档导入")
    print("=" * 70)
    
    rag = AgenticRAG()
    
    # 创建测试文档
    test_files = [
        ("regression_doc_page_1.txt", """
人工智能（AI）是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。
AI的研究领域包括机器学习、自然语言处理、计算机视觉、知识图谱等。
机器学习是AI的核心技术，使计算机能够从数据中学习而无需明确编程。
深度学习是机器学习的子集，使用神经网络处理复杂数据模式。
"""),
        ("regression_doc_page_2.txt", """
自然语言处理（NLP）是AI的重要领域，使计算机能够理解、解释和生成人类语言。
NLP应用包括机器翻译、情感分析、问答系统和聊天机器人。
计算机视觉让机器能够"看"和理解图像视频，应用包括人脸识别和自动驾驶。
强化学习通过与环境交互学习，在游戏和机器人控制领域有广泛应用。
""")
    ]
    
    # 写入测试文件
    for filename, content in test_files:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"创建测试文件: {filename}")
    
    # 导入文档
    success_count = 0
    for filename, _ in test_files:
        success = rag.add_document(filename)
        if success:
            success_count += 1
            print(f"✓ 成功导入: {filename}")
        else:
            print(f"✗ 导入失败: {filename}")
    
    # 验证
    total_chunks = len(rag.local_chunks)
    print(f"\n总块数: {total_chunks}")
    
    # 清理
    for filename, _ in test_files:
        if os.path.exists(filename):
            os.remove(filename)
    
    assert success_count == len(test_files), "文档导入失败"
    assert total_chunks > 0, "没有生成文档块"
    
    print("\n✓ 文档导入测试通过")
    return rag

def test_search_functionality(rag):
    """测试搜索功能"""
    print("\n" + "=" * 70)
    print("测试3: 搜索功能")
    print("=" * 70)
    
    test_queries = [
        "机器学习",
        "自然语言处理",
        "深度学习",
        "计算机视觉"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        result = rag.search(query, threshold=0.3)
        
        print(f"  返回结果数: {result['top_k']}")
        print(f"  总块数: {result['total_chunks']}")
        
        assert 'results' in result, "结果中缺少results字段"
        assert 'top_k' in result, "结果中缺少top_k字段"
        
        for i, item in enumerate(result['results']):
            print(f"\n  结果 {i+1}:")
            print(f"    内容: {item['content'][:60]}...")
            print(f"    来源: {item['source']['file_name']}")
            print(f"    页号: {item['source']['page_number']}")
            print(f"    块索引: {item['source']['chunk_index']}")
            print(f"    位置: {item['source']['position']}")
            print(f"    分数: 语义={item['scores']['semantic']:.4f}, BM25={item['scores']['bm25']:.4f}, RRF={item['scores']['rrf']:.4f}")
            
            # 验证必需字段
            assert 'content' in item, "结果缺少content字段"
            assert 'source' in item, "结果缺少source字段"
            assert 'scores' in item, "结果缺少scores字段"
            assert 'file_name' in item['source'], "source缺少file_name"
            assert 'page_number' in item['source'], "source缺少page_number"
    
    print("\n✓ 搜索功能测试通过")
    return True

def test_dynamic_topk(rag):
    """测试动态TopK选择"""
    print("\n" + "=" * 70)
    print("测试4: 动态TopK选择")
    print("=" * 70)
    
    # 测试不同查询的TopK选择
    queries = [
        "机器学习",
        "强化学习应用",
        "AI伦理问题"
    ]
    
    topk_values = []
    for query in queries:
        result = rag.search(query)
        topk_values.append(result['top_k'])
        print(f"查询 '{query}' -> TopK: {result['top_k']}")
    
    # 验证TopK在合理范围内
    for k in topk_values:
        assert 3 <= k <= 10, f"TopK值 {k} 不在合理范围[3, 10]内"
    
    print("\n✓ 动态TopK选择测试通过")
    return True

def test_source_information(rag):
    """测试来源信息完整性"""
    print("\n" + "=" * 70)
    print("测试5: 来源信息完整性")
    print("=" * 70)
    
    result = rag.search("机器学习")
    
    for item in result['results']:
        source = item['source']
        
        # 验证所有必需字段
        assert 'file_name' in source, "缺少file_name"
        assert 'page_number' in source, "缺少page_number"
        assert 'chunk_index' in source, "缺少chunk_index"
        assert 'position' in source, "缺少position"
        
        print(f"\n来源信息:")
        print(f"  文件名: {source['file_name']}")
        print(f"  页号: {source['page_number']}")
        print(f"  块索引: {source['chunk_index']}")
        print(f"  位置: {source['position']}")
        
        # 验证页号提取
        if 'page' in source['file_name'].lower():
            assert source['page_number'] > 0, "页号应该大于0"
    
    print("\n✓ 来源信息完整性测试通过")
    return True

def test_hybrid_retrieval(rag):
    """测试混合检索（语义+BM25+RRF）"""
    print("\n" + "=" * 70)
    print("测试6: 混合检索")
    print("=" * 70)
    
    result = rag.search("深度学习")
    
    print(f"检索到 {len(result['results'])} 个结果")
    
    for item in result['results']:
        scores = item['scores']
        
        # 验证分数字段
        assert 'semantic' in scores, "缺少semantic分数"
        assert 'bm25' in scores, "缺少bm25分数"
        assert 'rrf' in scores, "缺少rrf分数"
        assert 'final' in scores, "缺少final分数"
        
        print(f"\n内容: {item['content'][:50]}...")
        print(f"  语义相似度: {scores['semantic']:.4f}")
        print(f"  BM25分数: {scores['bm25']:.4f}")
        print(f"  RRF分数: {scores['rrf']:.4f}")
        print(f"  最终分数: {scores['final']:.4f}")
    
    print("\n✓ 混合检索测试通过")
    return True

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 70)
    print("测试7: 边界情况")
    print("=" * 70)
    
    rag = AgenticRAG()
    
    # 测试空知识库搜索
    print("\n测试空知识库搜索...")
    result = rag.search("测试查询")
    assert result['top_k'] == 0, "空知识库应该返回0个结果"
    assert len(result['results']) == 0, "空知识库结果列表应该为空"
    print("✓ 空知识库搜索正常")
    
    # 测试空文档
    print("\n测试空文档...")
    with open("empty_doc.txt", 'w', encoding='utf-8') as f:
        f.write("")
    
    success = rag.add_document("empty_doc.txt")
    assert not success, "空文档应该导入失败"
    print("✓ 空文档处理正常")
    
    # 测试短文档
    print("\n测试短文档...")
    with open("short_doc.txt", 'w', encoding='utf-8') as f:
        f.write("这是一个短文档。")
    
    success = rag.add_document("short_doc.txt")
    # 短文档可能成功也可能失败，取决于min_chunk_size
    print(f"短文档导入结果: {'成功' if success else '失败'}")
    
    # 清理
    for f in ["empty_doc.txt", "short_doc.txt"]:
        if os.path.exists(f):
            os.remove(f)
    
    print("\n✓ 边界情况测试通过")
    return True

def run_all_tests():
    """运行所有回归测试"""
    print("\n" + "=" * 70)
    print("Agentic RAG 回归测试套件")
    print("=" * 70)
    
    tests = []
    
    try:
        # 测试1: 动态语义分割
        tests.append(("动态语义分割", test_semantic_splitter()))
        
        # 测试2: 文档导入
        rag = test_document_ingestion()
        tests.append(("文档导入", rag is not None))
        
        # 测试3: 搜索功能
        tests.append(("搜索功能", test_search_functionality(rag)))
        
        # 测试4: 动态TopK
        tests.append(("动态TopK", test_dynamic_topk(rag)))
        
        # 测试5: 来源信息
        tests.append(("来源信息", test_source_information(rag)))
        
        # 测试6: 混合检索
        tests.append(("混合检索", test_hybrid_retrieval(rag)))
        
        # 测试7: 边界情况
        tests.append(("边界情况", test_edge_cases()))
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        tests.append(("异常", False))
    
    # 打印测试报告
    print("\n" + "=" * 70)
    print("测试报告")
    print("=" * 70)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
