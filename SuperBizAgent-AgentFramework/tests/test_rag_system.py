#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统回归测试
测试内容：
1. 数据库模型和连接
2. 标签管理（创建、查询）
3. 文档管理（添加、查询）
4. 向量管理
5. 元数据初筛查询
6. GUI组件导入
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'agent'))

import unittest
from unittest.mock import Mock, patch, MagicMock
import json


class TestDatabaseModels(unittest.TestCase):
    """测试数据库模型"""
    
    def test_tag_model(self):
        """测试Tag模型"""
        from db_models import Tag
        
        tag = Tag(
            tag_id=1,
            domain="技术",
            module="后端",
            doc_type="API文档",
            keyword1="Python",
            keyword2="FastAPI"
        )
        
        self.assertEqual(tag.tag_id, 1)
        self.assertEqual(tag.domain, "技术")
        self.assertEqual(tag.module, "后端")
        self.assertEqual(tag.doc_type, "API文档")
        self.assertEqual(tag.keyword1, "Python")
        self.assertEqual(tag.keyword2, "FastAPI")
        print("✓ Tag模型测试通过")
    
    def test_document_model(self):
        """测试Document模型"""
        from db_models import Document
        
        doc = Document(
            doc_id=1,
            file_name="test.txt",
            file_path="/path/to/test.txt",
            file_hash="abc123",
            tag_id=1,
            file_size=1024,
            chunk_count=5
        )
        
        self.assertEqual(doc.doc_id, 1)
        self.assertEqual(doc.file_name, "test.txt")
        self.assertEqual(doc.tag_id, 1)
        print("✓ Document模型测试通过")
    
    def test_vector_chunk_model(self):
        """测试VectorChunk模型"""
        from db_models import VectorChunk
        
        vector = VectorChunk(
            vector_id=1,
            doc_id=1,
            tag_id=1,
            chunk_index=0,
            content="测试内容",
            embedding=[0.1, 0.2, 0.3]
        )
        
        self.assertEqual(vector.vector_id, 1)
        self.assertEqual(vector.doc_id, 1)
        self.assertEqual(vector.content, "测试内容")
        print("✓ VectorChunk模型测试通过")


class TestMetadataManager(unittest.TestCase):
    """测试元数据管理器"""
    
    def test_metadata_creation(self):
        """测试元数据创建"""
        from rag_tools import DocumentMetadata
        
        metadata = DocumentMetadata(
            domain="技术",
            module="后端",
            doc_type="API文档",
            keyword1="Python",
            keyword2="FastAPI"
        )
        
        self.assertEqual(metadata.domain, "技术")
        self.assertEqual(metadata.module, "后端")
        self.assertEqual(metadata.doc_type, "API文档")
        print("✓ DocumentMetadata创建测试通过")
    
    def test_metadata_validation(self):
        """测试元数据验证"""
        from rag_tools import DocumentMetadata, MetadataManager
        
        manager = MetadataManager()
        
        # 有效元数据
        valid_metadata = DocumentMetadata(
            domain="技术",
            module="后端",
            doc_type="API文档"
        )
        is_valid, msg = manager.validate_metadata(valid_metadata)
        self.assertTrue(is_valid)
        
        # 无效元数据（空domain）
        invalid_metadata = DocumentMetadata(
            domain="",
            module="后端",
            doc_type="API文档"
        )
        is_valid, msg = manager.validate_metadata(invalid_metadata)
        self.assertFalse(is_valid)
        print("✓ 元数据验证测试通过")
    
    def test_auto_extract_metadata(self):
        """测试自动提取元数据"""
        from rag_tools import MetadataManager
        
        manager = MetadataManager()
        
        # 测试API相关内容
        content = "这是一个Python FastAPI的接口文档，描述了如何使用后端API"
        metadata = manager.auto_extract_metadata(content, "api_doc.md")
        
        self.assertIsNotNone(metadata.domain)
        self.assertIsNotNone(metadata.module)
        self.assertIsNotNone(metadata.doc_type)
        print("✓ 自动提取元数据测试通过")


class TestIntentRecognizer(unittest.TestCase):
    """测试意图识别器"""
    
    def test_intent_classification(self):
        """测试意图分类"""
        from rag_tools import IntentRecognizer
        
        recognizer = IntentRecognizer()
        
        # 测试知识查询意图
        query1 = "什么是Python的GIL？"
        intent1 = recognizer.recognize(query1)
        self.assertIsNotNone(intent1)
        print(f"  查询'{query1}'的意图: {intent1.intent.value}")
        
        # 测试聊天意图
        query2 = "你好"
        intent2 = recognizer.recognize(query2)
        self.assertIsNotNone(intent2)
        print(f"  查询'{query2}'的意图: {intent2.intent.value}")
        
        print("✓ 意图分类测试通过")


class TestTextSplitterStrategies(unittest.TestCase):
    """测试文本分割策略"""
    
    def test_fixed_window_splitter(self):
        """测试固定窗口分割"""
        from text_splitter_strategies import FixedWindowSplitter
        
        splitter = FixedWindowSplitter(chunk_size=100, overlap=20)
        text = "这是一个测试文本。" * 50
        
        chunks = splitter.split(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        print(f"✓ 固定窗口分割测试通过，生成{len(chunks)}个块")
    
    def test_sentence_boundary_splitter(self):
        """测试句子边界分割"""
        from text_splitter_strategies import SentenceBoundarySplitter
        
        splitter = SentenceBoundarySplitter()
        text = "这是第一句。这是第二句。这是第三句。这是第四句。" * 10
        
        chunks = splitter.split(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        print(f"✓ 句子边界分割测试通过，生成{len(chunks)}个块")
    
    def test_dynamic_semantic_splitter(self):
        """测试动态语义分割"""
        from text_splitter_strategies import DynamicSemanticSplitter
        
        splitter = DynamicSemanticSplitter()
        text = "这是关于Python编程的内容。Python是一种强大的编程语言。" * 20
        
        chunks = splitter.split(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        print(f"✓ 动态语义分割测试通过，生成{len(chunks)}个块")


class TestRAGTool(unittest.TestCase):
    """测试RAG工具"""
    
    def test_rag_tool_creation(self):
        """测试RAG工具创建"""
        from rag_tools import RAGTool, IntentRecognizer
        
        # 模拟知识库管理器
        mock_kb_manager = Mock()
        mock_kb_manager.search = Mock(return_value=[
            {"content": "测试内容1", "score": 0.9},
            {"content": "测试内容2", "score": 0.8}
        ])
        
        # 创建意图识别器
        intent_recognizer = IntentRecognizer()
        
        rag_tool = RAGTool(kb_manager=mock_kb_manager, intent_recognizer=intent_recognizer)
        
        self.assertIsNotNone(rag_tool)
        self.assertEqual(rag_tool.kb_manager, mock_kb_manager)
        print("✓ RAG工具创建测试通过")
    
    def test_rag_tool_search(self):
        """测试RAG工具搜索"""
        from rag_tools import RAGTool, IntentRecognizer
        
        mock_kb_manager = Mock()
        mock_kb_manager.search = Mock(return_value=[
            {"content": "Python是一种编程语言", "score": 0.95, "source": "doc1.txt", "metadata": {}},
            {"content": "Python支持多种编程范式", "score": 0.85, "source": "doc2.txt", "metadata": {}}
        ])
        
        intent_recognizer = IntentRecognizer()
        rag_tool = RAGTool(kb_manager=mock_kb_manager, intent_recognizer=intent_recognizer)
        
        # 测试搜索
        intent_result, chunks = rag_tool.search(query="什么是Python？", top_k=2, skip_intent=True)
        
        self.assertIsNotNone(intent_result)
        self.assertIsInstance(chunks, list)
        print("✓ RAG工具搜索测试通过")


class TestGUIComponents(unittest.TestCase):
    """测试GUI组件"""
    
    def test_metadata_dialog_import(self):
        """测试元数据对话框导入"""
        try:
            from metadata_dialog import MetadataDialog, show_metadata_dialog
            print("✓ 元数据对话框导入成功")
        except ImportError as e:
            self.fail(f"元数据对话框导入失败: {e}")
    
    def test_retrieved_chunks_view_import(self):
        """测试召回片段视图导入"""
        try:
            from retrieved_chunks_view import RetrievedChunksView, create_retrieved_chunks_view
            print("✓ 召回片段视图导入成功")
        except ImportError as e:
            self.fail(f"召回片段视图导入失败: {e}")
    
    def test_rag_manager_gui_import(self):
        """测试RAG管理器GUI导入"""
        try:
            from rag_manager_gui import RAGManagerGUI
            print("✓ RAG管理器GUI导入成功")
        except ImportError as e:
            self.fail(f"RAG管理器GUI导入失败: {e}")


class TestDatabaseManager(unittest.TestCase):
    """测试数据库管理器（使用Mock）"""
    
    def test_db_manager_creation(self):
        """测试数据库管理器创建"""
        from db_manager import DatabaseManager
        
        # 由于pymysql是延迟导入的，我们直接测试初始化
        db = DatabaseManager(
            host='localhost',
            port=3306,
            user='root',
            password='test',
            database='rag_kb'
        )
        
        self.assertIsNotNone(db)
        self.assertEqual(db.host, 'localhost')
        print("✓ 数据库管理器创建测试通过")


def run_regression_tests():
    """运行回归测试"""
    print("\n" + "="*60)
    print("开始RAG系统回归测试")
    print("="*60 + "\n")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseModels))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadataManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntentRecognizer))
    suite.addTests(loader.loadTestsFromTestCase(TestTextSplitterStrategies))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGTool))
    suite.addTests(loader.loadTestsFromTestCase(TestGUIComponents))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n❌ 测试未通过，请检查失败项")
        return 1


if __name__ == "__main__":
    exit_code = run_regression_tests()
    sys.exit(exit_code)
