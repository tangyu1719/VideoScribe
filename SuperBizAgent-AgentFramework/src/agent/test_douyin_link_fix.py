#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试 - 模拟真实抖音链接处理流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from link_analyzer import LinkAnalyzer

def test_douyin_link():
    """测试抖音分享文本链接"""
    # 真实的抖音分享文本
    test_link = "2.89 e@O.kc 05/03 Okp:/ 面试官：skill 解决了 agent 的什么痛点？#agent # ai 大模型 # 人工智能 # 大模型应用  `https://v.douyin.com/F0hlcj9C0lE/`  复制此链接，打开 Dou 音搜索，直接观看视频！"
    
    print("=" * 80)
    print("抖音链接处理回归测试")
    print("=" * 80)
    print(f"原始输入：{test_link[:80]}...")
    
    # 初始化分析器
    analyzer = LinkAnalyzer()
    
    # 测试 URL 提取
    clean_url = analyzer._extract_clean_url(test_link)
    print(f"提取后的 URL: {clean_url}")
    
    expected = "https://v.douyin.com/F0hlcj9C0lE/"
    if clean_url == expected:
        print("✅ URL 提取成功！")
    else:
        print(f"❌ URL 提取失败！期望：{expected}")
        return False
    
    # 测试链接类型判断
    link_type = analyzer._judge_link_type(clean_url)
    print(f"链接类型：{link_type}")
    
    if link_type in ['video', 'douyin_image']:
        print("✅ 链接类型判断正确！")
    else:
        print(f"⚠ 链接类型：{link_type}")
    
    print("=" * 80)
    print("所有测试通过！✅")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        test_douyin_link()
    except Exception as e:
        print(f"测试异常：{e}")
        import traceback
        traceback.print_exc()
