#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import traceback

# 设置日志文件
log_file = open('debug.log', 'w', encoding='utf-8')

def log(msg):
    print(msg, file=log_file, flush=True)
    print(msg)

log("=" * 60)
log("调试启动开始...")
log(f"Python路径: {sys.executable}")
log(f"当前目录: {os.getcwd()}")
log(f"sys.path: {sys.path}")

# 添加路径
sys.path.insert(0, 'src/agent')
log("已添加 src/agent 到路径")

try:
    log("\n1. 导入 tkinter...")
    import tkinter as tk
    log("✓ tkinter 导入成功")
    
    log("\n2. 导入 kb_manager_fast...")
    from kb_manager_fast import get_fast_knowledge_base
    log("✓ kb_manager_fast 导入成功")
    
    log("\n3. 导入 video_gui...")
    from video_gui import App
    log("✓ video_gui 导入成功")
    
    log("\n4. 创建 Tk 窗口...")
    root = tk.Tk()
    log("✓ Tk 窗口创建成功")
    
    log("\n5. 创建 App 实例...")
    app = App(root)
    log("✓ App 实例创建成功")
    
    log("\n6. 启动主循环...")
    log("=" * 60)
    root.mainloop()
    
except Exception as e:
    log(f"\n✗ 错误: {e}")
    log(traceback.format_exc())
finally:
    log_file.close()
