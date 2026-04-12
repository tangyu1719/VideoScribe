#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取招聘会企业 Excel 文件，筛选出互联网 JAVA 或 AI 应用开发相关的公司
"""

import pandas as pd
import sys
import os

# 读取 Excel 文件 - 使用当前目录
excel_path = r'4 月 8 日专场招聘会参会企业.xlsx'

print("=" * 80)
print("正在读取 Excel 文件...")
print("=" * 80)
print(f"当前目录：{os.getcwd()}")
print(f"查找文件：{excel_path}")
print(f"文件存在：{os.path.exists(excel_path)}")
print()

try:
    # 读取 Excel
    df = pd.read_excel(excel_path)
    
    print(f"✓ 成功读取 Excel 文件")
    print(f"✓ 共有 {len(df)} 家企业")
    print(f"✓ 列名：{list(df.columns)}")
    print()
    
    # 显示前几行数据结构
    print("数据预览（前 5 行）：")
    print("-" * 80)
    print(df.head())
    print()
    
    # 显示所有列名和数据类型
    print("列信息：")
    print("-" * 80)
    for col in df.columns:
        print(f"{col}: {df[col].dtype}")
    print()
    
except Exception as e:
    print(f"❌ 读取失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
