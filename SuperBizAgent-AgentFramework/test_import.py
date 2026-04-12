#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

print("测试导入开始...")

# 添加路径
sys.path.insert(0, 'src/agent')

try:
    print("导入 tkinter...")
    import tkinter as tk
    print("✓ tkinter 导入成功")
    
    print("导入 kb_manager_fast...")
    from kb_manager_fast import get_fast_knowledge_base
    print("✓ kb_manager_fast 导入成功")
    
    print("导入 video_gui...")
    from video_gui import App
    print("✓ video_gui 导入成功")
    
    print("\n所有导入成功，尝试创建窗口...")
    root = tk.Tk()
    print("✓ Tk 窗口创建成功")
    
    app = App(root)
    print("✓ App 实例创建成功")
    
    print("\n启动主循环...")
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"\n✗ 错误: {e}")
    print(traceback.format_exc())
