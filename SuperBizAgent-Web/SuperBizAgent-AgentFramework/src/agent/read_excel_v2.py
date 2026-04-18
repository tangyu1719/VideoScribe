#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取招聘会企业 Excel 文件，筛选出互联网 JAVA 或 AI 应用开发相关的公司
"""

import subprocess
import json
import sys

# 使用 Python 直接执行读取操作
python_code = """
import openpyxl
import sys

try:
    # 尝试读取 Excel
    wb = openpyxl.load_workbook(r'F:\\java\\AIOPS\\SuperBizAgent-release-2026-01-02\\demo_wendanghua\\4 月 8 日专场招聘会参会企业.xlsx')
    ws = wb.active
    
    # 获取所有行
    data = []
    headers = []
    
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(h) if h else f'Column_{j}' for j, h in enumerate(row)]
        else:
            data.append(dict(zip(headers, row)))
    
    # 输出为 JSON
    result = {
        'headers': headers,
        'data': data,
        'total': len(data)
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"""

# 执行 Python 代码
result = subprocess.run(
    ['py', '-c', python_code],
    capture_output=True,
    text=True,
    cwd=r'F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua'
)

if result.returncode == 0:
    print(result.stdout)
else:
    print(f"错误：{result.stderr}")
    sys.exit(1)
