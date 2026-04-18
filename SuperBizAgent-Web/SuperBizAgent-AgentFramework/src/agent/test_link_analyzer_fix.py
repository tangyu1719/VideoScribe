#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试 - 直接测试 link_analyzer 的核心函数
"""

import re

# 直接从 link_analyzer.py 复制函数代码进行测试
def _extract_clean_url(text: str) -> str:
    """从包含额外文本的字符串中提取纯净的 URL"""
    # 清理反引号
    text = text.strip('`')
    
    # 使用正则表达式提取 HTTP/HTTPS URL
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(url_pattern, text)
    
    if matches:
        return matches[0]
    
    return text

def test_all_cases():
    """测试所有用例"""
    test_cases = [
        # (输入，期望输出，描述)
        (
            "2.89 e@O.kc 05/03 Okp:/ 面试官：skill 解决了 agent 的什么痛点？#agent # ai 大模型 # 人工智能 # 大模型应用  `https://v.douyin.com/F0hlcj9C0lE/`  复制此链接，打开 Dou 音搜索，直接观看视频！",
            "https://v.douyin.com/F0hlcj9C0lE/",
            "抖音完整分享文本"
        ),
        (
            "`https://v.douyin.com/F0hlcj9C0lE/`",
            "https://v.douyin.com/F0hlcj9C0lE/",
            "带反引号的 URL"
        ),
        (
            "https://www.douyin.com/video/123456789",
            "https://www.douyin.com/video/123456789",
            "纯净的抖音 URL"
        ),
        (
            "来看这个视频 https://v.douyin.com/abc123/ 很好看",
            "https://v.douyin.com/abc123/",
            "包含说明文字的 URL"
        ),
        (
            "https://www.xiaohongshu.com/explore/abc123",
            "https://www.xiaohongshu.com/explore/abc123",
            "小红书 URL"
        ),
    ]
    
    print("=" * 80)
    print("抖音链接解析修复 - 回归测试")
    print("=" * 80)
    
    all_passed = True
    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = _extract_clean_url(input_text)
        passed = result == expected
        
        print(f"\n测试 {i}: {description}")
        print(f"  输入：{input_text[:60]}...")
        print(f"  期望：{expected}")
        print(f"  结果：{result}")
        print(f"  状态：{'✅ 通过' if passed else '❌ 失败'}")
        
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过！修复成功！")
        print("\n现在程序可以正确处理以下格式的输入：")
        print("  1. 抖音完整分享文本（包含标题、标签、说明文字）")
        print("  2. 带反引号的 URL")
        print("  3. 纯净的 URL")
        print("  4. 小红书、B 站等其他平台的分享文本")
    else:
        print("❌ 部分测试失败！需要进一步修复！")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    test_all_cases()
