#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态文档处理回归测试脚本
"""

import os
import sys

print("="*60)
print("多模态文档处理回归测试")
print("="*60)

# 测试1: 导入模块
print("\n[测试1] 导入文档处理器模块...")
try:
    from document_processor import DocumentProcessor, DocumentType, ProcessingResult
    print("✅ 文档处理器模块导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 初始化处理器
print("\n[测试2] 初始化文档处理器...")
try:
    processor = DocumentProcessor()
    print("✅ 处理器初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    sys.exit(1)

# 测试3: 检查支持的文件类型
print("\n[测试3] 支持的文件类型:")
for doc_type in DocumentType:
    print(f"  - {doc_type.value}")

# 测试4: 文件类型检测
print("\n[测试4] 文件类型检测测试:")
test_files = [
    ("test.jpg", DocumentType.IMAGE),
    ("test.pdf", DocumentType.PDF),
    ("test.docx", DocumentType.DOCX),
    ("test.md", DocumentType.MD),
    ("test.csv", DocumentType.CSV),
    ("test.mp3", DocumentType.AUDIO),
    ("test.mp4", DocumentType.VIDEO),
    ("test.unknown", DocumentType.UNKNOWN),
]

for filename, expected_type in test_files:
    detected = processor.detect_type(filename)
    status = "✅" if detected == expected_type else "❌"
    print(f"  {status} {filename} -> {detected.value} (期望: {expected_type.value})")

# 测试5: 导入多模态GUI模块
print("\n[测试5] 导入多模态GUI模块...")
try:
    from multimodal_gui import MultimodalProcessingPage, FILE_TYPE_CONFIG
    print("✅ 多模态GUI模块导入成功")
    print(f"  支持的文件类型配置: {list(FILE_TYPE_CONFIG.keys())}")
except Exception as e:
    print(f"❌ 导入失败: {e}")

# 测试6: 导入video_gui更新
print("\n[测试6] 检查video_gui多模态支持...")
try:
    import video_gui
    if hasattr(video_gui, 'MULTIMODAL_AVAILABLE'):
        print(f"✅ video_gui多模态支持已添加 (可用: {video_gui.MULTIMODAL_AVAILABLE})")
    else:
        print("❌ video_gui缺少多模态支持")
except Exception as e:
    print(f"❌ 检查失败: {e}")

print("\n" + "="*60)
print("回归测试完成!")
print("="*60)
