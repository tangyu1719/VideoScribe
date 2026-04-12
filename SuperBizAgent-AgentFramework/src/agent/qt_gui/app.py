#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 GUI 启动脚本
模仿豆包/DeskClaw 现代风格
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from qt_gui.theme import Theme, get_stylesheet
from qt_gui.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("SuperBizAgent")
    app.setApplicationVersion("2.0.0")
    
    # 设置全局字体
    font = QFont(Theme.current["font_family"], Theme.current["font_size_md"])
    app.setFont(font)
    
    # 应用样式
    app.setStyleSheet(get_stylesheet("light"))
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
