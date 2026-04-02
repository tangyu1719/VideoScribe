# -*- coding: utf-8 -*-
"""
直接测试百度 OCR API
"""
from aip import AipOcr
import os

# 百度 OCR API 配置
APP_ID = '122094788'
API_KEY = 'KZOpVw7PGLRiBdsqRnuLFVY7'
SECRET_KEY = 'L1pdbtb4IZZv67ofXnsxDNAhELGN2UXs'

# 初始化客户端
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 读取测试图片
img_path = 'Pictures/1.png'
if not os.path.exists(img_path):
    print(f"图片不存在：{img_path}")
    exit(1)

print(f"读取图片：{img_path}")
with open(img_path, 'rb') as f:
    image_data = f.read()

print(f"图片大小：{len(image_data)} bytes")
print("\n调用百度 OCR API...")

# 调用高精度 OCR
result = client.basicAccurate(image_data)

print(f"\nAPI 返回结果：{result}")

if 'words_result' in result:
    print(f"\n✓ OCR 识别成功！共识别 {len(result['words_result'])} 行文本\n")
    for item in result['words_result']:
        if 'words' in item:
            print(f"  - {item['words']}")
else:
    print("\n✗ OCR 识别失败")
    if 'error_code' in result:
        print(f"错误码：{result['error_code']}")
        print(f"错误信息：{result['error_msg']}")
