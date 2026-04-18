#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统回归测试
- 测试意图识别
- 测试RAG工具调用
- 测试元数据管理
- 测试召回片段显示
"""

import sys
import os

# 添加路径
sys.path.insert(0, 'src/agent')

def test_intent_recognition():
    """测试意图识别"""
    print("=" * 60)
    print("测试1: 意图识别")
    print("=" * 60)
    
    try:
        from rag_tools import IntentRecognizer, IntentType
        
        recognizer = IntentRecognizer(llm_client=None)
        
        # 测试简单问候（规则匹配）
        test_cases = [
            ("你好", IntentType.GREETING, False),
            ("再见", IntentType.GOODBYE, False),
            ("谢谢", IntentType.THANKS, False),
            ("哈哈", IntentType.CHAT, False),
            ("什么是Python？", IntentType.NEED_RAG, True),
        ]
        
        for query, expected_intent, needs_rag in test_cases:
            result = recognizer.recognize(query, use_llm=False)
            print(f"  查询: '{query}'")
            print(f"    意图: {result.intent.value}, 需要RAG: {result.needs_rag}")
            assert result.needs_rag == needs_rag, f"期望needs_rag={needs_rag}, 实际={result.needs_rag}"
        
        print("\n✓ 意图识别测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 意图识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_management():
    """测试元数据管理"""
    print("\n" + "=" * 60)
    print("测试2: 元数据管理")
    print("=" * 60)
    
    try:
        from rag_tools import DocumentMetadata, MetadataManager
        
        manager = MetadataManager()
        
        # 测试元数据验证
        print("\n测试元数据验证...")
        valid_metadata = DocumentMetadata(
            domain="技术",
            module="后端",
            doc_type="文档",
            keyword1="Python",
            keyword2="API"
        )
        is_valid, msg = manager.validate_metadata(valid_metadata)
        print(f"  ✓ 有效元数据: {is_valid}, {msg}")
        assert is_valid, "有效元数据应该通过验证"
        
        invalid_metadata = DocumentMetadata(
            domain="",
            module="后端",
            doc_type="文档"
        )
        is_valid, msg = manager.validate_metadata(invalid_metadata)
        print(f"  ✓ 无效元数据: {is_valid}, {msg}")
        assert not is_valid, "无效元数据应该不通过验证"
        
        # 测试自动提取
        print("\n测试自动提取...")
        content = """
        这是一个Python后端API开发文档。
        使用Flask框架开发RESTful API接口。
        包含用户认证、数据验证等功能。
        """
        extracted = manager.auto_extract_metadata(content, "api_doc.md")
        print(f"  ✓ 自动提取: domain={extracted.domain}, module={extracted.module}, doc_type={extracted.doc_type}")
        print(f"  ✓ 关键词: {extracted.keyword1}, {extracted.keyword2}")
        
        print("\n✓ 元数据管理测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 元数据管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_tool():
    """测试RAG工具"""
    print("\n" + "=" * 60)
    print("测试3: RAG工具")
    print("=" * 60)
    
    try:
        from rag_tools import RAGTool, IntentRecognizer, DocumentMetadata
        
        # 创建模拟的kb_manager
        class MockKBManager:
            def search(self, query, top_k=5, doc_ids=None, metadata_filter=None):
                # 模拟返回结果
                return [
                    {
                        'content': f'这是关于{query}的内容',
                        'source_file': 'test.txt',
                        'chunk_id': 0,
                        'score': 0.95,
                        'metadata': {'domain': '技术', 'module': '后端', 'doc_type': '文档'},
                        'doc_id': 'doc1'
                    }
                ]
        
        kb_manager = MockKBManager()
        intent_recognizer = IntentRecognizer(llm_client=None)
        rag_tool = RAGTool(kb_manager, intent_recognizer)
        
        # 测试搜索
        print("\n测试RAG搜索...")
        intent_result, chunks = rag_tool.search("Python是什么？", top_k=3)
        print(f"  ✓ 意图: {intent_result.intent.value}, 需要RAG: {intent_result.needs_rag}")
        print(f"  ✓ 召回片段: {len(chunks)}个")
        
        if chunks:
            chunk = chunks[0]
            print(f"  ✓ 片段内容: {chunk.content[:30]}...")
            print(f"  ✓ 元数据: {chunk.metadata.to_dict()}")
        
        # 测试元数据过滤
        print("\n测试元数据过滤...")
        filter_metadata = DocumentMetadata(
            domain="技术",
            module="",
            doc_type=""
        )
        intent_result, chunks = rag_tool.search(
            "Python", 
            metadata_filter=filter_metadata,
            top_k=3
        )
        print(f"  ✓ 带过滤的搜索完成")
        
        print("\n✓ RAG工具测试通过")
        return True
    except Exception as e:
        print(f"\n✗ RAG工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_dialog():
    """测试元数据对话框（非GUI测试）"""
    print("\n" + "=" * 60)
    print("测试4: 元数据对话框组件")
    print("=" * 60)
    
    try:
        from metadata_dialog import MetadataDialog
        from rag_tools import DocumentMetadata
        
        # 测试元数据创建
        print("\n测试元数据创建...")
        metadata = DocumentMetadata(
            domain="技术",
            module="后端",
            doc_type="代码",
            keyword1="Python",
            keyword2="Flask"
        )
        print(f"  ✓ 元数据创建: {metadata.to_dict()}")
        
        # 验证必填字段
        assert metadata.is_valid(), "完整元数据应该有效"
        print(f"  ✓ 元数据验证通过")
        
        print("\n✓ 元数据对话框组件测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 元数据对话框组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retrieved_chunks_view():
    """测试召回片段显示组件（非GUI测试）"""
    print("\n" + "=" * 60)
    print("测试5: 召回片段显示组件")
    print("=" * 60)
    
    try:
        from retrieved_chunks_view import RetrievedChunksView
        
        # 测试数据
        test_chunks = [
            {
                'content': '这是第一个测试片段的内容',
                'source_file': 'test1.txt',
                'score': 0.95,
                'metadata': {
                    'domain': '技术',
                    'module': '后端',
                    'doc_type': '文档',
                    'keyword1': 'Python',
                    'keyword2': 'API'
                }
            },
            {
                'content': '这是第二个测试片段的内容',
                'source_file': 'test2.txt',
                'score': 0.87,
                'metadata': {
                    'domain': '产品',
                    'module': '设计',
                    'doc_type': '规范',
                    'keyword1': 'UI',
                    'keyword2': 'UX'
                }
            }
        ]
        
        print("\n测试召回片段数据结构...")
        print(f"  ✓ 测试数据: {len(test_chunks)}个片段")
        
        for i, chunk in enumerate(test_chunks, 1):
            print(f"  ✓ 片段{i}: {chunk['content'][:20]}...")
            print(f"    来源: {chunk['source_file']}")
            print(f"    相似度: {chunk['score']}")
            print(f"    元数据: {chunk['metadata']}")
        
        print("\n✓ 召回片段显示组件测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 召回片段显示组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("RAG系统回归测试开始")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("意图识别", test_intent_recognition()))
    results.append(("元数据管理", test_metadata_management()))
    results.append(("RAG工具", test_rag_tool()))
    results.append(("元数据对话框组件", test_metadata_dialog()))
    results.append(("召回片段显示组件", test_retrieved_chunks_view()))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("RAG系统回归测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
