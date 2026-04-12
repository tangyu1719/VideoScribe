#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链接分析功能回归测试
测试 AgentFramework 的 link_analyzer 是否能正常工作
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    try:
        from link_analyzer import LinkAnalyzer
        print("✓ link_analyzer 模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_initialization():
    """测试初始化"""
    print("\n" + "=" * 60)
    print("测试2: LinkAnalyzer 初始化")
    print("=" * 60)
    try:
        from link_analyzer import LinkAnalyzer
        analyzer = LinkAnalyzer()
        print("✓ LinkAnalyzer 初始化成功")
        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False

def test_analyze_link():
    """测试链接分析功能"""
    print("\n" + "=" * 60)
    print("测试3: 链接分析功能")
    print("=" * 60)
    try:
        from link_analyzer import LinkAnalyzer
        analyzer = LinkAnalyzer()
        
        # 测试小红书链接
        test_url = "https://www.xiaohongshu.com/explore/123456"
        print(f"测试链接: {test_url}")
        
        result = analyzer.analyze_link(test_url)
        print(f"分析结果: {result}")
        
        if result and 'type' in result:
            print(f"✓ 链接分析成功，类型: {result['type']}")
            return True
        else:
            print("✗ 链接分析返回结果异常")
            return False
    except Exception as e:
        print(f"✗ 链接分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_detection():
    """测试视频检测功能"""
    print("\n" + "=" * 60)
    print("测试4: 视频检测功能")
    print("=" * 60)
    try:
        from link_analyzer import LinkAnalyzer
        analyzer = LinkAnalyzer()
        
        # 测试视频链接
        video_url = "https://www.xiaohongshu.com/explore/video123"
        print(f"测试视频链接: {video_url}")
        
        result = analyzer.analyze_link(video_url)
        print(f"检测结果: {result}")
        
        print("✓ 视频检测功能正常")
        return True
    except Exception as e:
        print(f"✗ 视频检测失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("链接分析功能回归测试")
    print("=" * 60)
    print(f"测试目录: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Python版本: {sys.version}")
    print()
    
    results = []
    
    # 运行所有测试
    results.append(("模块导入", test_import()))
    results.append(("初始化", test_initialization()))
    results.append(("链接分析", test_analyze_link()))
    results.append(("视频检测", test_video_detection()))
    
    # 打印测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print("\n✓ 所有测试通过！链接分析功能正常。")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败，需要修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
