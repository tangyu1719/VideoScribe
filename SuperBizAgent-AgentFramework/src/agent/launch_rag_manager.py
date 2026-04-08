#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 知识库管理启动脚本
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from rag_manager_gui import RAGManagerGUI

if __name__ == "__main__":
    print("启动 RAG 知识库管理界面...")
    app = RAGManagerGUI()
    app.window.mainloop()
    print("RAG 知识库管理界面已关闭")
