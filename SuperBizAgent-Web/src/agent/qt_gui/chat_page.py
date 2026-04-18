#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 问答页面 - PySide6 版本
模仿豆包风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QFrame, QScrollArea, QListWidget,
    QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from qt_gui.theme import Theme


class ChatPage(QWidget):
    """AI 问答页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("AI 问答")
        title_label.setFont(QFont(Theme.current["font_family"], 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.current['text_primary']};")
        layout.addWidget(title_label)
        
        # 主内容区（左右分栏）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：会话列表
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        
        # 会话列表标题
        session_header = QHBoxLayout()
        session_title = QLabel("会话列表")
        session_title.setFont(QFont(Theme.current["font_family"], 13, QFont.Bold))
        session_header.addWidget(session_title)
        session_header.addStretch()
        
        # 新建会话按钮
        self.btn_new_session = QPushButton("新建")
        self.btn_new_session.setObjectName("secondaryButton")
        self.btn_new_session.setFixedHeight(32)
        session_header.addWidget(self.btn_new_session)
        
        left_layout.addLayout(session_header)
        
        # 会话列表
        self.session_list = QListWidget()
        self.session_list.setFrameShape(QListWidget.NoFrame)
        left_layout.addWidget(self.session_list)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        self.btn_rename = QPushButton("重命名")
        self.btn_rename.setObjectName("secondaryButton")
        self.btn_rename.setFixedHeight(32)
        btn_layout.addWidget(self.btn_rename)
        
        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("secondaryButton")
        self.btn_delete.setFixedHeight(32)
        btn_layout.addWidget(self.btn_delete)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # 右侧：聊天区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # 聊天内容区
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setFrameShape(QScrollArea.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        self.chat_scroll.setWidgetResizable(True)
        right_layout.addWidget(self.chat_scroll)
        
        # 输入区域
        input_card = QFrame()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setSpacing(8)
        
        # 输入框
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入问题，按 Enter 发送，Shift+Enter 换行...")
        self.input_box.setMaximumHeight(120)
        self.input_box.setFixedHeight(80)
        input_layout.addWidget(self.input_box)
        
        # 按钮区域
        btn_row = QHBoxLayout()
        
        self.btn_upload = QPushButton("上传文件")
        self.btn_upload.setObjectName("secondaryButton")
        self.btn_upload.setFixedHeight(36)
        btn_row.addWidget(self.btn_upload)
        
        btn_row.addStretch()
        
        self.btn_send = QPushButton("发送")
        self.btn_send.setObjectName("primaryButton")
        self.btn_send.setFixedHeight(36)
        self.btn_send.setFixedWidth(100)
        btn_row.addWidget(self.btn_send)
        
        input_layout.addLayout(btn_row)
        right_layout.addWidget(input_card)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([250, 750])
        
        layout.addWidget(splitter, 1)
    
    def add_message(self, text: str, is_user: bool):
        """添加消息气泡"""
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if is_user:
            bubble.setStyleSheet(f"""
                QLabel {{
                    background-color: {Theme.current['primary']};
                    color: white;
                    border-radius: 12px;
                    padding: 10px 14px;
                    margin: 4px;
                }}
            """)
            bubble.setAlignment(Qt.AlignRight)
        else:
            bubble.setStyleSheet(f"""
                QLabel {{
                    background-color: {Theme.current['bg_hover']};
                    color: {Theme.current['text_primary']};
                    border-radius: 12px;
                    padding: 10px 14px;
                    margin: 4px;
                }}
            """)
            bubble.setAlignment(Qt.AlignLeft)
        
        self.chat_layout.addWidget(bubble)
        self.chat_layout.addStretch()
