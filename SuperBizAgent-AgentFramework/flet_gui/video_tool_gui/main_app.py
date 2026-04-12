#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理工具GUI - 主应用
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from video_tool_gui.theme import Theme, StyleSheet, get_global_stylesheet
from video_tool_gui.video_page import VideoProcessingPage
from video_tool_gui.chat_page import ChatPage
from video_tool_gui.document_page import DocumentPage


class MainApp(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频转文字处理工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self.current_page = 0
        self.nav_buttons = []
        
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 导航栏
        nav_bar = self.create_nav_bar()
        main_layout.addWidget(nav_bar)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        
        # 创建页面
        self.video_page = VideoProcessingPage()
        self.chat_page = ChatPage()
        self.document_page = DocumentPage()
        
        self.content_stack.addWidget(self.video_page)
        self.content_stack.addWidget(self.chat_page)
        self.content_stack.addWidget(self.document_page)
        
        main_layout.addWidget(self.content_stack, 1)
    
    def create_nav_bar(self):
        """创建导航栏"""
        nav_bar = QFrame()
        nav_bar.setObjectName("navBar")
        nav_bar.setStyleSheet(f"""
            QFrame#navBar {{
                background-color: {Theme.BG_SIDEBAR};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        nav_bar.setFixedHeight(60)
        
        layout = QHBoxLayout(nav_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("视频转文字处理工具")
        title_label.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: {Theme.FONT_SIZE_TITLE}px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("智能视频分析与文本转换系统")
        subtitle_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            font-size: {Theme.FONT_SIZE_SMALL}px;
            font-style: italic;
        """)
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        # 导航按钮
        nav_items = [
            ("📹 视频处理", 0),
            ("🤖 AI问答", 1),
            ("📁 文档处理", 2),
        ]
        
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(index == 0)
            btn.setStyleSheet(StyleSheet.get_nav_button_style(active=(index == 0)))
            btn.clicked.connect(lambda checked, i=index: self.switch_page(i))
            self.nav_buttons.append((btn, index))
            layout.addWidget(btn)
        
        return nav_bar
    
    def switch_page(self, index):
        """切换页面"""
        self.content_stack.setCurrentIndex(index)
        
        for btn, btn_index in self.nav_buttons:
            is_active = btn_index == index
            btn.setChecked(is_active)
            btn.setStyleSheet(StyleSheet.get_nav_button_style(active=is_active))
    
    def apply_theme(self):
        """应用主题"""
        self.setStyleSheet(get_global_stylesheet())


def main():
    app = QApplication(sys.argv)
    
    font = QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_NORMAL)
    app.setFont(font)
    
    window = MainApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
