#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理页面 - PySide6 版本
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QPlainTextEdit,
    QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from qt_gui.theme import Theme


class DocumentPage(QWidget):
    """文档处理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("文档处理")
        title_label.setFont(QFont(Theme.current["font_family"], 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.current['text_primary']};")
        layout.addWidget(title_label)
        
        # 文件选择区域
        file_card = QFrame()
        file_card.setObjectName("card")
        file_layout = QVBoxLayout(file_card)
        file_layout.setSpacing(12)
        
        # 文件列表标题
        file_header = QHBoxLayout()
        file_title = QLabel("待处理文件")
        file_title.setFont(QFont(Theme.current["font_family"], 13, QFont.Bold))
        file_header.addWidget(file_title)
        file_header.addStretch()
        
        # 文件类型筛选
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "全部类型",
            "图片",
            "PDF",
            "Word",
            "Markdown",
            "CSV",
            "音频",
            "视频"
        ])
        self.type_filter.setFixedWidth(120)
        file_header.addWidget(self.type_filter)
        
        file_layout.addLayout(file_header)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setFrameShape(QListWidget.NoFrame)
        self.file_list.setMinimumHeight(120)
        file_layout.addWidget(self.file_list)
        
        # 添加文件按钮
        btn_row = QHBoxLayout()
        self.btn_add_files = QPushButton("📁 添加文件")
        self.btn_add_files.setObjectName("primaryButton")
        self.btn_add_files.setFixedHeight(36)
        btn_row.addWidget(self.btn_add_files)
        
        self.btn_remove = QPushButton("移除")
        self.btn_remove.setObjectName("secondaryButton")
        self.btn_remove.setFixedHeight(36)
        btn_row.addWidget(self.btn_remove)
        
        btn_row.addStretch()
        file_layout.addLayout(btn_row)
        
        layout.addWidget(file_card)
        
        # 处理选项
        options_card = QFrame()
        options_card.setObjectName("card")
        options_layout = QVBoxLayout(options_card)
        options_layout.setSpacing(8)
        
        options_title = QLabel("处理选项")
        options_title.setFont(QFont(Theme.current["font_family"], 13, QFont.Bold))
        options_layout.addWidget(options_title)
        
        # TODO: 添加具体选项
        
        layout.addWidget(options_card)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ 开始处理")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setMinimumWidth(120)
        self.btn_start.setFixedHeight(40)
        btn_layout.addWidget(self.btn_start)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logArea")
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(150)
        log_layout.addWidget(self.log_view)
        
        layout.addWidget(log_group, 1)
