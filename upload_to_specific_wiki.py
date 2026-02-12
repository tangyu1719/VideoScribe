#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传文档到指定的飞书文档库
"""

import os
import json
from feishu_integration import FeishuKnowledgeBase

# 文档路径
doc_path = r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\output\015-02-11-#_百万级Excel数据导出优化（面试导_视频分析.md'

# 读取文档内容
with open(doc_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取文档标题
title = os.path.basename(doc_path).replace('.md', '')

print(f"=== 上传到指定文档库 ===")
print(f"文档标题: {title}")
print(f"文档大小: {len(content)} 字符")
print(f"目标文档库链接: https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b")
print(f"文档库ID: YhzqwByshiRNWKk0T1GcxFHmn6b")

# 初始化飞书客户端
feishu = FeishuKnowledgeBase('cli_a9b7cc9aba389bc4', 'q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6')

# 智能分类：根据内容自动判断文件夹
folder_path = feishu.auto_classify_content(content)
print(f"智能分类结果: {folder_path}")

# 清除去重记录，确保这次能上传
print("\n=== 清除去重记录 ===")
dedup_file = 'feishu_dedup.json'
if os.path.exists(dedup_file):
    os.remove(dedup_file)
    print("✓ 已清除去重记录")
else:
    print("⚠ 去重记录文件不存在")

# 重新加载去重数据
feishu.dedup_data = {}
feishu.save_dedup_data()
print("✓ 已重置去重数据")

# 上传文档
print("\n=== 开始上传文档 ===")
print(f"正在上传到: {folder_path}")
print(f"目标文档库: YhzqwByshiRNWKk0T1GcxFHmn6b")

# 使用明确的文件夹路径
target_folder = "就业技术文档集/八股"
print(f"明确上传目标: {target_folder}")

doc_token = feishu.upload_document(title, content, feishu_folder_path=target_folder)

if doc_token:
    print('\n🎉 文档上传成功！')
    print(f'文档Token: {doc_token}')
    print(f'文档标题: {title}')
    print(f'上传到文件夹: {target_folder}')
    print(f'目标文档库: YhzqwByshiRNWKk0T1GcxFHmn6b')
    print('\n=== 直接访问链接 ===')
    print(f'文档库链接: https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b')
    print('\n=== 验证步骤 ===')
    print('1. 复制上面的链接到浏览器打开')
    print('2. 在左侧导航栏找到 "就业技术文档集"')
    print('3. 展开后点击 "八股" 文件夹')
    print('4. 在右侧内容区查找文档标题')
else:
    print('\n❌ 文档上传失败')
    print('请检查网络连接和飞书应用权限')

print('\n上传完成！')
