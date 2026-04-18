#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# 写入文件
with open('env_check_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"Python版本: {sys.version}\n")
    f.write(f"Python路径: {sys.executable}\n")
    f.write(f"当前目录: {os.getcwd()}\n")
    f.write(f"命令行参数: {sys.argv}\n")
    f.write("\n检查tkinter...\n")
    try:
        import tkinter as tk
        f.write(f"tkinter版本: {tk.Tcl().eval('info patchlevel')}\n")
        f.write("tkinter导入成功\n")
    except Exception as e:
        f.write(f"tkinter导入失败: {e}\n")
    
    f.write("\n检查kb_manager_fast...\n")
    sys.path.insert(0, 'src/agent')
    try:
        from kb_manager_fast import get_fast_knowledge_base
        f.write("kb_manager_fast导入成功\n")
    except Exception as e:
        f.write(f"kb_manager_fast导入失败: {e}\n")
    
    f.write("\n检查video_gui...\n")
    try:
        from video_gui import App
        f.write("video_gui导入成功\n")
    except Exception as e:
        f.write(f"video_gui导入失败: {e}\n")

print("检查完成，结果写入 env_check_result.txt")
