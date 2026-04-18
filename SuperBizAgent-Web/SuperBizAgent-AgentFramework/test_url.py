#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 URL 提取功能
"""

import re

def extract_clean_url(text: str) -> str:
    """从包含额外文本的字符串中提取纯净的 URL"""
    # 清理反引号
    text = text.strip('`')
    
    # 使用正则表达式提取 HTTP/HTTPS URL
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(url_pattern, text)
    
    if matches:
        # 返回第一个匹配的 URL
        return matches[0]
    
    # 如果没有找到 URL，返回原文本（已清理反引号）
    return text

# 测试用例
test_cases = [
    # (输入，期望输出)
    (
        "2.89 e@O.kc 05/03 Okp:/ 面试官：skill 解决了 agent 的什么痛点？#agent # ai 大模型 # 人工智能 # 大模型应用  `https://v.douyin.com/F0hlcj9C0lE/`  复制此链接，打开 Dou 音搜索，直接观看视频！",
        "https://v.douyin.com/F0hlcj9C0lE/"
    ),
    (
        "`https://v.douyin.com/F0hlcj9C0lE/`",
        "https://v.douyin.com/F0hlcj9C0lE/"
    ),
    (
        "https://www.douyin.com/video/123456789",
        "https://www.douyin.com/video/123456789"
    ),
    (
        "来看这个视频 https://v.douyin.com/abc123/ 很好看",
        "https://v.douyin.com/abc123/"
    ),
]

print("=" * 80)
print("URL 提取功能测试")
print("=" * 80)

all_passed = True
for i, (input_text, expected) in enumerate(test_cases, 1):
    result = extract_clean_url(input_text)
    passed = result == expected
    all_passed = all_passed and passed
    
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"\n测试 {i}: {status}")
    print(f"输入：{input_text[:80]}...")
    print(f"期望：{expected}")
    print(f"结果：{result}")

print("\n" + "=" * 80)
if all_passed:
    print("所有测试通过！✅")
else:
    print("部分测试失败！❌")
print("=" * 80)
