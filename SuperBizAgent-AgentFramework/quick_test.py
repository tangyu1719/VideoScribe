#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 URL 提取功能
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
        return matches[0]
    
    return text

# 测试
test_input = "2.89 e@O.kc 05/03 Okp:/ 面试官：skill 解决了 agent 的什么痛点？#agent # ai 大模型 # 人工智能 # 大模型应用  `https://v.douyin.com/F0hlcj9C0lE/`  复制此链接，打开 Dou 音搜索，直接观看视频！"
result = extract_clean_url(test_input)
expected = "https://v.douyin.com/F0hlcj9C0lE/"

print("=" * 80)
print("URL 提取测试")
print("=" * 80)
print(f"输入：{test_input[:80]}...")
print(f"期望：{expected}")
print(f"结果：{result}")
print(f"测试：{'✅ 通过' if result == expected else '❌ 失败'}")
print("=" * 80)
