#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperBizAgent - 视频转文字处理工具 (GUI)
工程化版本入口

基于 video_gui.py 重构
功能：视频下载、语音转文字、AI分析、知识库问答
"""

import os
import sys

# 添加src目录到Python路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(BASE_DIR, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 添加各模块路径
for module_dir in ['core', 'video', 'chat', 'gui', 'utils']:
    module_path = os.path.join(src_path, module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)


def main():
    """主函数 - 启动视频转文字处理工具"""
    import tkinter as tk
    from gui.video_gui import App
    
    print("=" * 60)
    print("启动 SuperBizAgent - 视频转文字处理工具")
    print("=" * 60)
    
    # 创建主窗口
    root = tk.Tk()
    
    # 初始化应用
    app = App(root)
    
    print("✅ 应用程序已启动")
    print("=" * 60)
    
    # 运行主循环
    root.mainloop()
    
    print("\n应用程序已关闭")


if __name__ == "__main__":
    main()
