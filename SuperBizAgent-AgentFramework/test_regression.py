#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试脚本 - 测试策略模式和配置功能
"""

import sys
import os
import time

# 添加路径
sys.path.insert(0, 'src/agent')

def test_text_splitter_strategies():
    """测试文本分割策略"""
    print("=" * 60)
    print("测试1: 文本分割策略")
    print("=" * 60)
    
    try:
        from text_splitter_strategies import TextSplitterFactory
        
        # 测试获取所有策略
        strategies = TextSplitterFactory.list_strategies()
        print(f"✓ 可用策略: {list(strategies.keys())}")
        
        # 测试每种策略
        test_text = "这是一段测试文本。这是第二句话！这是第三句话？这是第四句话。这是第五句话。"
        
        for strategy_name in strategies.keys():
            print(f"\n测试策略: {strategy_name}")
            strategy = TextSplitterFactory.get_strategy(strategy_name)
            chunks = strategy.split(test_text, chunk_size=50, overlap=10)
            print(f"  ✓ 生成 {len(chunks)} 个块")
            for i, (text, start, end) in enumerate(chunks[:3]):  # 只显示前3个
                print(f"    块{i+1}: 长度{len(text)}, 位置{start}-{end}")
        
        print("\n✓ 文本分割策略测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 文本分割策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_kb_manager_with_strategy():
    """测试知识库管理器使用策略模式"""
    print("\n" + "=" * 60)
    print("测试2: 知识库管理器策略模式")
    print("=" * 60)
    
    try:
        from kb_manager_fast import FastKnowledgeBaseManager
        
        # 测试使用不同策略初始化
        print("\n测试使用句子边界策略...")
        kb1 = FastKnowledgeBaseManager(text_splitter_strategy='sentence_boundary')
        strategies = kb1.get_available_strategies()
        print(f"  ✓ 可用策略: {list(strategies.keys())}")
        print(f"  ✓ 当前策略: {kb1._text_splitter_strategy_name}")
        
        # 测试切换策略
        print("\n测试切换策略...")
        kb1.set_text_splitter_strategy('fixed_window')
        print(f"  ✓ 切换后策略: {kb1._text_splitter_strategy_name}")
        
        # 测试文本分割
        print("\n测试文本分割...")
        test_text = "这是第一句话。这是第二句话！这是第三句话？这是第四句话。这是第五句话。"
        chunks = kb1._split_text(test_text, chunk_size=50, overlap=10)
        print(f"  ✓ 分割成 {len(chunks)} 个块")
        
        print("\n✓ 知识库管理器策略模式测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 知识库管理器策略模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dynamic_semantic_splitter():
    """测试动态语义分割策略"""
    print("\n" + "=" * 60)
    print("测试3: 动态语义分割策略")
    print("=" * 60)
    
    try:
        from text_splitter_strategies import DynamicSemanticSplitter
        
        # 没有embedding模型时的回退测试
        print("\n测试无模型时的回退...")
        splitter = DynamicSemanticSplitter(embedding_model=None)
        test_text = "这是第一段内容。这是第二段内容！这是第三段内容？"
        chunks = splitter.split(test_text, chunk_size=50, overlap=10)
        print(f"  ✓ 回退分割成 {len(chunks)} 个块")
        
        print("\n✓ 动态语义分割策略测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 动态语义分割策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_import():
    """测试文件导入功能"""
    print("\n" + "=" * 60)
    print("测试4: 文件导入功能")
    print("=" * 60)
    
    try:
        from kb_manager_fast import get_fast_knowledge_base
        
        kb = get_fast_knowledge_base()
        
        # 创建测试文件
        test_file = 'test_regression_import.txt'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是回归测试文件。\n")
            f.write("包含多行内容。\n")
            f.write("用于测试导入功能。\n")
        
        print(f"\n测试导入文件: {test_file}")
        start_time = time.time()
        success, message = kb.add_document(test_file)
        elapsed = time.time() - start_time
        
        if success:
            print(f"  ✓ 导入成功: {message}")
            print(f"  ✓ 耗时: {elapsed:.2f}秒")
        else:
            print(f"  ✗ 导入失败: {message}")
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        
        print("\n✓ 文件导入功能测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 文件导入功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("回归测试开始")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("文本分割策略", test_text_splitter_strategies()))
    results.append(("知识库管理器策略模式", test_kb_manager_with_strategy()))
    results.append(("动态语义分割策略", test_dynamic_semantic_splitter()))
    results.append(("文件导入功能", test_file_import()))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("回归测试结果汇总")
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
