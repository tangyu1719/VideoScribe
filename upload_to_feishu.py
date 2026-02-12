#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传文档到飞书脚本
"""

from feishu_integration import FeishuKnowledgeBase
import os

# 文档路径
doc_path = r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\output\015-02-11-#_百万级Excel数据导出优化（面试导_视频分析.md'

# 读取文档内容
with open(doc_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取文档标题
title = os.path.basename(doc_path).replace('.md', '')

print(f"准备上传文档: {title}")
print(f"文档大小: {len(content)} 字符")

# 初始化飞书客户端
feishu = FeishuKnowledgeBase('cli_a9b7cc9aba389bc4', 'q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6')

# 上传文档到JAVA八股文件夹
doc_token = feishu.upload_document(title, content, 'JAVA八股')

if doc_token:
    print('\n文档上传成功！')
    print(f'Token: {doc_token}')
    print(f'标题: {title}')
    
    # 添加到稍后阅读
    print('\n添加到稍后阅读...')
    success = feishu.add_to_read_later(doc_token)
    if success:
        print('✓ 添加到稍后阅读成功')
    else:
        print('✗ 添加到稍后阅读失败')
else:
    print('\n文档上传失败')

print('\n上传完成！')
