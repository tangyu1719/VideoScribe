#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 URL 提取功能
"""

import sys
sys.path.insert(0, r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent')

from video_downloader import extract_clean_url

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
