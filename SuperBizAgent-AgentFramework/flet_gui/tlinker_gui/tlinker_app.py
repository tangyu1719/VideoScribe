#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLink GUI 主应用
科技浅色透明蓝风格，卡片化、圆角化、立体化设计
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QLinearGradient, QBrush, QPalette, QFont

from tlinker_gui.theme import Theme, StyleSheet, ShadowEffect, get_global_stylesheet


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TLink - 链接分析工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 当前页面索引
        self.current_page = 0
        self.nav_buttons = []
        
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """设置UI"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航栏
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # 右侧内容区
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        
        # 添加各个页面
        from tlinker_gui.link_analysis_page import LinkAnalysisPage
        from tlinker_gui.document_page import DocumentPage
        
        self.link_page = LinkAnalysisPage()
        self.doc_page = DocumentPage()
        self.history_page = self.create_history_page()
        self.ai_config_page = self.create_ai_config_page()
        
        self.content_stack.addWidget(self.link_page)
        self.content_stack.addWidget(self.doc_page)
        self.content_stack.addWidget(self.history_page)
        self.content_stack.addWidget(self.ai_config_page)
        
        main_layout.addWidget(self.content_stack, 1)
    
    def create_sidebar(self):
        """创建侧边导航栏"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {Theme.BG_GLASS};
                border-right: 1px solid {Theme.BORDER_LIGHT};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(8)
        
        # Logo区域
        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(20, 0, 20, 20)
        
        logo_icon = QLabel("🔗")
        logo_icon.setStyleSheet(f"""
            font-size: 28px;
            padding: 8px;
        """)
        
        logo_text = QLabel("TLink")
        logo_text.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: 24px;
            font-weight: bold;
        """)
        
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        
        layout.addWidget(logo_widget)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {Theme.BORDER_LIGHT}; max-height: 1px;")
        layout.addWidget(line)
        
        # 导航项
        nav_items = [
            ("链接分析", "🔗", 0),
            ("文档处理", "📄", 1),
            ("历史记录", "📋", 2),
            ("AI 配置", "⚙️", 3),
        ]
        
        for text, icon, index in nav_items:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("navButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(index == 0)
            btn.setStyleSheet(StyleSheet.get_nav_button_style(active=(index == 0)))
            btn.clicked.connect(lambda checked, i=index: self.switch_page(i))
            self.nav_buttons.append((btn, index))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 底部版本信息
        version_label = QLabel("v2.0.0")
        version_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        return sidebar
    
    def switch_page(self, index):
        """切换页面"""
        self.content_stack.setCurrentIndex(index)
        
        # 更新导航按钮状态
        for btn, btn_index in self.nav_buttons:
            is_active = btn_index == index
            btn.setChecked(is_active)
            btn.setStyleSheet(StyleSheet.get_nav_button_style(active=is_active))
    
    def create_history_page(self):
        """创建历史记录页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📋 历史记录")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        # 占位内容
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        card_layout = QVBoxLayout(card)
        placeholder = QLabel("历史记录功能开发中...")
        placeholder.setStyleSheet(f"color: {Theme.TEXT_MUTED}; padding: 40px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(placeholder)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return page
    
    def create_ai_config_page(self):
        """创建AI配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("⚙️ AI 配置")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        # 占位内容
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        card_layout = QVBoxLayout(card)
        placeholder = QLabel("AI配置功能开发中...")
        placeholder.setStyleSheet(f"color: {Theme.TEXT_MUTED}; padding: 40px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(placeholder)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return page
    
    def apply_theme(self):
        """应用主题"""
        # 设置窗口背景渐变
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Theme.BG_MAIN_START}, stop:1 {Theme.BG_MAIN_END});
            }}
        """)
        
        # 应用全局样式
        self.setStyleSheet(self.styleSheet() + get_global_stylesheet())


def main():
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 创建窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
