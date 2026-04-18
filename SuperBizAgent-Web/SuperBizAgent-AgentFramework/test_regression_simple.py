#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化回归测试脚本 - 测试策略模式和配置功能（跳过模型加载）
"""

import sys
import os

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

def test_kb_manager_without_model():
    """测试知识库管理器策略模式（不加载模型）"""
    print("\n" + "=" * 60)
    print("测试2: 知识库管理器策略模式（简化版）")
    print("=" * 60)
    
    try:
        from text_splitter_strategies import TextSplitterFactory
        
        # 测试策略切换
        print("\n测试策略切换...")
        strategy1 = TextSplitterFactory.get_strategy('sentence_boundary')
        print(f"  ✓ 创建句子边界策略: {strategy1.name}")
        
        strategy2 = TextSplitterFactory.get_strategy('fixed_window')
        print(f"  ✓ 创建固定窗口策略: {strategy2.name}")
        
        strategy3 = TextSplitterFactory.get_strategy('dynamic_semantic')
        print(f"  ✓ 创建动态语义策略: {strategy3.name}")
        
        # 测试文本分割
        print("\n测试文本分割...")
        test_text = "这是第一句话。这是第二句话！这是第三句话？这是第四句话。这是第五句话。"
        
        chunks1 = strategy1.split(test_text, chunk_size=50, overlap=10)
        print(f"  ✓ 句子边界分割: {len(chunks1)} 个块")
        
        chunks2 = strategy2.split(test_text, chunk_size=50, overlap=10)
        print(f"  ✓ 固定窗口分割: {len(chunks2)} 个块")
        
        chunks3 = strategy3.split(test_text, chunk_size=50, overlap=10)
        print(f"  ✓ 动态语义分割: {len(chunks3)} 个块")
        
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
        
        # 测试句子分割功能
        print("\n测试句子分割...")
        sentences = splitter._split_into_sentences(test_text)
        print(f"  ✓ 分割成 {len(sentences)} 个句子")
        for i, (text, start, end) in enumerate(sentences):
            print(f"    句子{i+1}: {text[:20]}...")
        
        print("\n✓ 动态语义分割策略测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 动态语义分割策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_factory():
    """测试策略工厂"""
    print("\n" + "=" * 60)
    print("测试4: 策略工厂")
    print("=" * 60)
    
    try:
        from text_splitter_strategies import TextSplitterFactory
        
        # 测试列出策略
        print("\n测试列出策略...")
        strategies = TextSplitterFactory.list_strategies()
        print(f"  ✓ 可用策略: {strategies}")
        
        # 测试获取策略
        print("\n测试获取策略...")
        for name in strategies.keys():
            strategy = TextSplitterFactory.get_strategy(name)
            print(f"  ✓ {name}: {strategy.name}")
        
        # 测试未知策略回退
        print("\n测试未知策略回退...")
        strategy = TextSplitterFactory.get_strategy('unknown_strategy')
        print(f"  ✓ 未知策略回退到: {strategy.name}")
        
        print("\n✓ 策略工厂测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 策略工厂测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("简化回归测试开始")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("文本分割策略", test_text_splitter_strategies()))
    results.append(("知识库管理器策略模式", test_kb_manager_without_model()))
    results.append(("动态语义分割策略", test_dynamic_semantic_splitter()))
    results.append(("策略工厂", test_strategy_factory()))
    
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
