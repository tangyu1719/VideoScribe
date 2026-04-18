# -*- coding: utf-8 -*-
"""测试 video_gui.py 处理小红书视频链接"""
import sys
sys.path.insert(0, 'f:/java/AIOPS/SuperBizAgent-release-2026-01-02/demo_wendanghua')

from video_gui import App
import tkinter as tk

# 创建应用
root = tk.Tk()
app = App(root)

# 测试链接
test_url = 'https://www.xiaohongshu.com/explore/69b292500000000028009849?xsec_token=ABooHNtmLa1lywHSX_GfvOvOK5_vdc3sq0jATYVEa0qMo=&xsec_source=pc_collect'

# 检测平台类型
platform = app._detect_platform(test_url)
print(f"平台检测结果：{platform}")

# 测试 link_analyzer
from link_analyzer import LinkAnalyzer
analyzer = LinkAnalyzer()
result = analyzer.analyze_link(test_url)
print(f"link_analyzer 检测结果：{result.get('type')}")
print(f"标题：{result.get('title')}")

if result.get('type') == 'video':
    print("✓ 成功识别为视频链接！")
else:
    print(f"✗ 识别失败：{result}")

root.destroy()
