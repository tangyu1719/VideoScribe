# -*- coding: utf-8 -*-
"""
测试修复后的 OCR 功能
"""
from link_analyzer import LinkAnalyzer
import os

def test_ocr():
    analyzer = LinkAnalyzer()
    
    # 测试图片
    img_path = 'Pictures/1.png'
    if not os.path.exists(img_path):
        print(f"图片不存在：{img_path}")
        return
    
    print(f"读取图片：{img_path}")
    with open(img_path, 'rb') as f:
        image_data = f.read()
    
    print(f"图片大小：{len(image_data)} bytes")
    print("\n开始 OCR 识别...")
    
    text = analyzer.ocr_image(image_data)
    
    if text:
        print("\n✓ OCR 识别成功！")
        print(f"识别到的文本:\n{text}")
    else:
        print("\n✗ OCR 识别失败，无文本返回")

if __name__ == '__main__':
    test_ocr()
