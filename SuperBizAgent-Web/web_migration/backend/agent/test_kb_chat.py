#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试知识库问答功能
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_kb_chat():
    """测试知识库问答功能"""
    print("=" * 60)
    print("测试知识库问答功能")
    print("=" * 60)
    
    # 测试1: 检查模型配置
    print("\n[测试1] 检查模型配置...")
    try:
        from ai_chat_system import AIChatSystem
        chat_system = AIChatSystem()
        
        stats = chat_system.get_stats()
        print(f"✅ AIChatSystem 初始化成功")
        print(f"   - 模型: {stats['model']}")
        print(f"   - 知识库可用: {stats['kb_available']}")
        
        if stats['kb_available']:
            kb_stats = stats.get('kb_stats', {})
            print(f"   - 文档块数: {kb_stats.get('total_chunks', 0)}")
            print(f"   - 文件数: {kb_stats.get('total_files', 0)}")
        
        # 验证模型配置
        expected_model = "ep-20260320202115-9jqfp"
        if stats['model'] == expected_model:
            print(f"✅ 模型配置正确: {expected_model} (Doubao-Seed-2.0-mini)")
        else:
            print(f"⚠️ 模型配置不匹配")
            print(f"   期望: {expected_model}")
            print(f"   实际: {stats['model']}")
            
    except Exception as e:
        print(f"❌ AIChatSystem 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2: 检查知识库管理器
    print("\n[测试2] 检查知识库管理器...")
    try:
        from kb_manager_advanced import get_advanced_knowledge_base
        kb = get_advanced_knowledge_base()
        
        if kb and kb.is_ready():
            print("✅ 高级知识库管理器可用")
            stats = kb.get_stats()
            print(f"   - 文档块数: {stats.get('total_chunks', 0)}")
            print(f"   - 文件数: {stats.get('total_files', 0)}")
            
            # 测试搜索功能
            print("\n[测试3] 测试知识库搜索...")
            results = kb.search("RAG系统", top_k=3)
            print(f"✅ 搜索完成，找到 {len(results)} 条结果")
            
            for i, result in enumerate(results, 1):
                source = result.get('source_file', '未知')
                score = result.get('score', 0)
                content = result.get('content', '')[:100]
                print(f"   [{i}] {source} (相关度: {score:.2f})")
                print(f"       {content}...")
        else:
            print("⚠️ 知识库未就绪")
            
    except Exception as e:
        print(f"❌ 知识库管理器检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试4: 检查API配置
    print("\n[测试4] 检查API配置...")
    try:
        api_key = chat_system.api_key
        api_url = chat_system.api_url
        model = chat_system.model
        
        print(f"✅ API配置:")
        print(f"   - API URL: {api_url}")
        print(f"   - 模型: {model}")
        print(f"   - API Key: {'*' * 10}{api_key[-4:] if len(api_key) > 4 else ''}")
        
    except Exception as e:
        print(f"❌ API配置检查失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_kb_chat()
