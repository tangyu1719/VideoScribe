#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态文档化助手（Multimodal Doc Assistant）
基于标准Agent工程框架的项目入口

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
for module_dir in ['agent', 'services', 'models', 'utils', 'graph']:
    module_path = os.path.join(src_path, module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)


def main():
    """主函数 - 启动Agent应用"""
    import tkinter as tk
    from agent.video_gui import App
    
    print("=" * 60)
    print("多模态文档化助手（Multimodal Doc Assistant）")
    print("=" * 60)
    
    # 创建主窗口
    root = tk.Tk()
    
    # 初始化应用
    app = App(root)
    
    print("[OK] Agent应用已启动")
    print("=" * 60)
    
    # 运行主循环
    root.mainloop()
    
    print("\n应用已关闭")


if __name__ == "__main__":
    main()
