#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理工具GUI启动脚本
PySide6版本 - 与原GUI功能完全一致
"""

import sys
import os

# 添加src/agent到路径
sys.path.insert(0, r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from video_tool_gui.main_app import MainApp
from video_tool_gui.theme import get_global_stylesheet


def main():
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("视频转文字处理工具")
    app.setApplicationVersion("2.0.0")
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 应用全局样式
    app.setStyleSheet(get_global_stylesheet())
    
    # 创建主窗口
    window = MainApp()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
