# -*- coding: utf-8 -*-
"""命令行测试小红书视频链接处理"""
import sys
sys.path.insert(0, 'f:/java/AIOPS/SuperBizAgent-release-2026-01-02/demo_wendanghua')

from link_analyzer import LinkAnalyzer
import os
from datetime import datetime

# 测试链接
test_url = 'https://www.xiaohongshu.com/explore/69b292500000000028009849?xsec_token=ABooHNtmLa1lywHSX_GfvOvOK5_vdc3sq0jATYVEa0qMo=&xsec_source=pc_collect'

print("=" * 80)
print("开始测试小红书视频链接处理")
print("=" * 80)

# 1. 检测平台类型
print("\n【步骤 1】检测平台类型...")
from video_gui import App
import tkinter as tk
root = tk.Tk()
app = App(root)
platform = app._detect_platform(test_url)
print(f"平台检测结果：{platform}")

# 2. 分析链接
print("\n【步骤 2】分析链接内容...")
analyzer = LinkAnalyzer()
result = analyzer.analyze_link(test_url)

print(f"分析结果类型：{result.get('type')}")
print(f"标题：{result.get('title')}")
print(f"消息：{result.get('message', '无')}")

# 3. 生成输出文件
print("\n【步骤 3】生成输出文件...")
output_dir = 'f:/java/AIOPS/SuperBizAgent-release-2026-01-02/demo_wendanghua/OUTPUT'
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime('%H%M-%m%d')
filename = f"{timestamp}-小红书视频测试_内容分析.md"
filepath = os.path.join(output_dir, filename)

content = f"""# {result.get('title', '未知标题')}

## 分析结果
- **链接类型**: {result.get('type')}
- **原始链接**: {test_url}
- **检测平台**: {platform}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试结果
"""

if result.get('type') == 'video':
    content += """
✓ **成功识别为视频链接！**

- 平台检测：小红书视频
- 内容检测：video
- 状态：成功
"""
else:
    content += f"""
✗ **识别失败**

- 平台检测：{platform}
- 内容检测：{result.get('type')}
- 状态：失败
"""

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"输出文件已生成：{filepath}")
print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)

root.destroy()
