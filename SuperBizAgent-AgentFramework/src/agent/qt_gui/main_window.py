#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主窗口 - 模仿豆包/DeskClaw 风格
侧边栏导航 + 内容区域
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget, 
    QLabel, QPushButton, QFrame, QStatusBar,
    QSplitter, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from qt_gui.theme import Theme, get_stylesheet
from qt_gui.video_page import VideoProcessingPage
from qt_gui.chat_page import ChatPage
from qt_gui.document_page import DocumentPage


class NavigationBar(QFrame):
    """侧边导航栏"""
    
    page_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(8)
        
        # Logo/标题
        logo_label = QLabel("多模态文档化助手")
        logo_label.setFont(QFont(Theme.current["font_family"], 18, QFont.Bold))
        logo_label.setStyleSheet(f"color: {Theme.current['primary']}; padding: 12px 8px;")
        layout.addWidget(logo_label)
        
        subtitle = QLabel("Multimodal Doc Assistant")
        subtitle.setFont(QFont(Theme.current["font_family"], 10))
        subtitle.setStyleSheet(f"color: {Theme.current['text_secondary']}; padding: 0 8px 12px;")
        layout.addWidget(subtitle)
        
        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFrameShape(QListWidget.NoFrame)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 添加导航项
        nav_items = [
            ("视频处理", 0),
            ("AI 问答", 1),
            ("文档处理", 2),
        ]
        
        for text, index in nav_items:
            item = QListWidgetItem(text)
            item.setFont(QFont(Theme.current["font_family"], 13))
            item.setSizeHint(QSize(200, 44))
            self.nav_list.addItem(item)
        
        self.nav_list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.nav_list)
        
        layout.addStretch()
        
        # 底部按钮
        self.settings_btn = QPushButton("设置")
        self.settings_btn.setObjectName("secondaryButton")
        self.settings_btn.setFixedHeight(36)
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        layout.addWidget(self.settings_btn)
        
        self.about_btn = QPushButton("关于")
        self.about_btn.setObjectName("secondaryButton")
        self.about_btn.setFixedHeight(36)
        layout.addWidget(self.about_btn)
    
    def _on_selection_changed(self, index):
        self.page_changed.emit(index)
    
    def _on_settings_clicked(self):
        # TODO: 打开设置对话框
        pass
    
    def set_current_page(self, index):
        self.nav_list.setCurrentRow(index)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态文档化助手")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 设置样式
        self.setStyleSheet(get_stylesheet("light"))
        
        self.setup_ui()
    
    def setup_ui(self):
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        self.nav_bar = NavigationBar()
        self.nav_bar.page_changed.connect(self._on_page_changed)
        main_layout.addWidget(self.nav_bar)
        
        # 内容区域
        content_frame = QFrame()
        content_frame.setObjectName("card")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        # 页面栈
        self.stack = QStackedWidget()
        
        # 添加实际页面
        self.video_page = VideoProcessingPage()
        self.chat_page = ChatPage()
        self.document_page = DocumentPage()
        
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.chat_page)
        self.stack.addWidget(self.document_page)
        
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_frame, 1)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {Theme.current['text_secondary']};")
        self.status_bar.addWidget(self.status_label)
        
        # 默认选中第一项
        self.nav_bar.set_current_page(0)
    
    def _on_page_changed(self, index):
        self.stack.setCurrentIndex(index)
        self.status_label.setText(f"切换到页面 {index + 1}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont(Theme.current["font_family"], Theme.current["font_size_md"])
    app.setFont(font)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
