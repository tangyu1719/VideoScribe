#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构审查和回归测试脚本
测试优化架构的本地Python插件
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """打印小节标题"""
    print(f"\n▶ {title}")
    print("-" * 50)


def test_module_import(module_name, class_names=None):
    """测试模块导入"""
    try:
        module = __import__(module_name)
        if class_names:
            for class_name in class_names:
                if hasattr(module, class_name):
                    print(f"  ✅ {module_name}.{class_name}")
                else:
                    print(f"  ⚠️  {module_name}.{class_name} 未找到")
        else:
            print(f"  ✅ {module_name}")
        return True, module
    except ImportError as e:
        print(f"  ❌ {module_name}: {e}")
        return False, None


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    full_path = os.path.join(BASE_DIR, filepath)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"  ✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"  ❌ {description}: {filepath} 不存在")
        return False


def review_architecture():
    """审查架构"""
    print_header("架构审查 - 优化架构的本地Python插件")
    
    results = {
        "modules": {},
        "files": {},
        "tests": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # 1. 核心模块检查
    print_section("1. 核心模块检查")
    
    modules_to_check = [
        ("agentic_rag_final", ["AgenticRAG", "DocumentChunk", "SearchResult", "DynamicSemanticSplitter"]),
        ("kb_manager_advanced", ["AdvancedKnowledgeBase", "get_advanced_knowledge_base"]),
        ("ai_chat_system", ["AIChatSystem"]),
        ("unified_link_document_processor", ["UnifiedLinkDocumentProcessor"]),
        ("multimodal_gui", ["MultimodalProcessingPage"]),
        ("rag_manager_gui_optimized", ["RAGManagerGUIOptimized"]),
        ("video_downloader", ["download_video", "speech_to_text"]),
        ("link_analyzer", ["LinkAnalyzer"]),
        ("document_processor", ["DocumentProcessor"]),
    ]
    
    for module_name, classes in modules_to_check:
        success, module = test_module_import(module_name, classes)
        results["modules"][module_name] = {
            "available": success,
            "classes": classes
        }
    
    # 2. 知识库文件检查
    print_section("2. 知识库文件检查")
    
    kb_files = [
        ("knowledge_base/file_records.json", "文件记录"),
        ("knowledge_base/vector_index.json", "向量索引"),
        ("knowledge_base/real_index.json", "真实索引"),
    ]
    
    for filepath, description in kb_files:
        exists = check_file_exists(filepath, description)
        results["files"][filepath] = exists
    
    # 3. 配置检查
    print_section("3. 配置检查")
    
    # 检查AI配置
    try:
        from ai_chat_system import AIChatSystem
        chat_system = AIChatSystem()
        print(f"  ✅ AIChatSystem 初始化成功")
        print(f"     - 主模型: {AIChatSystem.PRIMARY_MODEL}")
        print(f"     - 备用模型: {AIChatSystem.FALLBACK_MODEL}")
        print(f"     - 当前模型: {chat_system.model}")
        
        stats = chat_system.get_stats()
        print(f"     - 知识库可用: {stats.get('kb_available', False)}")
        
        results["tests"]["ai_chat_system"] = {
            "status": "success",
            "primary_model": AIChatSystem.PRIMARY_MODEL,
            "fallback_model": AIChatSystem.FALLBACK_MODEL,
            "current_model": chat_system.model
        }
    except Exception as e:
        print(f"  ❌ AIChatSystem 初始化失败: {e}")
        results["tests"]["ai_chat_system"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 4. 知识库功能测试
    print_section("4. 知识库功能测试")
    
    try:
        from kb_manager_advanced import get_advanced_knowledge_base
        kb = get_advanced_knowledge_base()
        
        if kb and kb.is_ready():
            print(f"  ✅ 知识库已就绪")
            stats = kb.get_stats()
            print(f"     - 文档块数: {stats.get('total_chunks', 0)}")
            print(f"     - 文件数: {stats.get('total_files', 0)}")
            
            # 测试搜索
            print(f"\n  测试搜索功能...")
            results_search = kb.search("RAG系统", top_k=3)
            print(f"     - 搜索结果: {len(results_search)} 条")
            
            for i, result in enumerate(results_search[:3], 1):
                source = result.get('source_file', '未知')
                score = result.get('score', 0)
                print(f"     [{i}] {source} (相关度: {score:.2f})")
            
            results["tests"]["knowledge_base"] = {
                "status": "ready",
                "stats": stats,
                "search_test": len(results_search)
            }
        else:
            print(f"  ⚠️ 知识库未就绪")
            results["tests"]["knowledge_base"] = {
                "status": "not_ready"
            }
    except Exception as e:
        print(f"  ❌ 知识库测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["tests"]["knowledge_base"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 5. Agentic RAG测试
    print_section("5. Agentic RAG 功能测试")
    
    try:
        from agentic_rag_final import AgenticRAG
        
        rag = AgenticRAG()
        print(f"  ✅ AgenticRAG 初始化成功")
        
        # 检查统计信息
        stats = rag.get_stats()
        print(f"     - 文档块数: {stats.get('total_chunks', 0)}")
        print(f"     - 索引类型: {stats.get('index_type', 'unknown')}")
        
        results["tests"]["agentic_rag"] = {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        print(f"  ❌ AgenticRAG 测试失败: {e}")
        results["tests"]["agentic_rag"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 6. 统一处理器测试
    print_section("6. 统一链接+文档处理器测试")
    
    try:
        from unified_link_document_processor import UnifiedLinkDocumentProcessor
        
        processor = UnifiedLinkDocumentProcessor()
        print(f"  ✅ UnifiedLinkDocumentProcessor 初始化成功")
        
        results["tests"]["unified_processor"] = {
            "status": "success"
        }
    except Exception as e:
        print(f"  ❌ UnifiedLinkDocumentProcessor 测试失败: {e}")
        results["tests"]["unified_processor"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # 7. 输出总结
    print_section("7. 架构审查总结")
    
    total_modules = len(results["modules"])
    available_modules = sum(1 for m in results["modules"].values() if m["available"])
    
    total_files = len(results["files"])
    existing_files = sum(1 for f in results["files"].values() if f)
    
    total_tests = len(results["tests"])
    passed_tests = sum(1 for t in results["tests"].values() if t.get("status") in ["success", "ready"])
    
    print(f"  模块检查: {available_modules}/{total_modules} 通过")
    print(f"  文件检查: {existing_files}/{total_files} 通过")
    print(f"  功能测试: {passed_tests}/{total_tests} 通过")
    
    # 保存结果
    result_file = os.path.join(BASE_DIR, "architecture_review_result.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  详细结果已保存到: {result_file}")
    
    print_header("架构审查完成")
    
    return results


def run_regression_tests():
    """运行回归测试"""
    print_header("回归测试")
    
    test_results = []
    
    # 测试1: 知识库搜索
    print_section("测试1: 知识库搜索")
    try:
        from kb_manager_advanced import get_advanced_knowledge_base
        kb = get_advanced_knowledge_base()
        
        if kb and kb.is_ready():
            # 测试不同查询
            test_queries = [
                "RAG系统",
                "Java高并发",
                "向量数据库"
            ]
            
            for query in test_queries:
                results = kb.search(query, top_k=3)
                print(f"  ✅ '{query}': {len(results)} 条结果")
            
            test_results.append(("知识库搜索", True, None))
        else:
            print(f"  ⚠️ 知识库未就绪，跳过测试")
            test_results.append(("知识库搜索", False, "知识库未就绪"))
    except Exception as e:
        print(f"  ❌ 知识库搜索测试失败: {e}")
        test_results.append(("知识库搜索", False, str(e)))
    
    # 测试2: AI对话系统
    print_section("测试2: AI对话系统")
    try:
        from ai_chat_system import AIChatSystem
        
        # 测试主模型
        chat_primary = AIChatSystem(use_fallback_model=False)
        print(f"  ✅ 主模型初始化: {chat_primary.model}")
        
        # 测试备用模型
        chat_fallback = AIChatSystem(use_fallback_model=True)
        print(f"  ✅ 备用模型初始化: {chat_fallback.model}")
        
        # 测试模型切换
        chat_primary.switch_model(use_fallback=True)
        assert chat_primary.model == AIChatSystem.FALLBACK_MODEL
        print(f"  ✅ 模型切换功能正常")
        
        test_results.append(("AI对话系统", True, None))
    except Exception as e:
        print(f"  ❌ AI对话系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("AI对话系统", False, str(e)))
    
    # 测试3: 文档处理
    print_section("测试3: 文档处理器")
    try:
        from document_processor import DocumentProcessor
        processor = DocumentProcessor()
        print(f"  ✅ DocumentProcessor 初始化成功")
        test_results.append(("文档处理器", True, None))
    except Exception as e:
        print(f"  ❌ 文档处理器测试失败: {e}")
        test_results.append(("文档处理器", False, str(e)))
    
    # 测试4: 链接分析
    print_section("测试4: 链接分析器")
    try:
        from link_analyzer import LinkAnalyzer
        analyzer = LinkAnalyzer()
        print(f"  ✅ LinkAnalyzer 初始化成功")
        test_results.append(("链接分析器", True, None))
    except Exception as e:
        print(f"  ❌ 链接分析器测试失败: {e}")
        test_results.append(("链接分析器", False, str(e)))
    
    # 输出回归测试结果
    print_section("回归测试结果")
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    for test_name, success, error in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status}: {test_name}")
        if error:
            print(f"      错误: {error}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    
    print_header("回归测试完成")
    
    return test_results


if __name__ == "__main__":
    # 运行架构审查
    review_results = review_architecture()
    
    # 运行回归测试
    test_results = run_regression_tests()
    
    # 最终总结
    print_header("最终总结")
    
    # 检查是否有失败的测试
    failed_tests = [name for name, success, _ in test_results if not success]
    
    if failed_tests:
        print(f"\n  ⚠️ 以下测试未通过，需要修复:")
        for test in failed_tests:
            print(f"    - {test}")
        sys.exit(1)
    else:
        print(f"\n  ✅ 所有测试通过！系统可以正常启动。")
        sys.exit(0)
