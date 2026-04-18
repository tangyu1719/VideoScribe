#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理页面
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from tlinker_gui.theme import Theme, StyleSheet, ShadowEffect


class DocumentPage(QWidget):
    """文档处理页面"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 标题
        title = QLabel("📄 文档处理")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 上传卡片
        upload_card = self.create_upload_card()
        content_layout.addWidget(upload_card)
        
        # 处理卡片
        process_card = self.create_process_card()
        content_layout.addWidget(process_card)
        
        # 结果卡片
        self.result_card = self.create_result_card()
        self.result_card.hide()
        content_layout.addWidget(self.result_card)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def create_upload_card(self):
        """创建上传卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        upload_label = QLabel("上传文档")
        upload_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        layout.addWidget(upload_label)
        
        # 上传区域
        upload_area = QFrame()
        upload_area.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_INPUT};
                border: 2px dashed {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_MEDIUM}px;
            }}
        """)
        upload_area.setMinimumHeight(150)
        
        upload_layout = QVBoxLayout(upload_area)
        upload_icon = QLabel("📁")
        upload_icon.setStyleSheet("font-size: 48px;")
        upload_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(upload_icon)
        
        upload_text = QLabel("拖拽文件到此处或点击上传")
        upload_text.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        upload_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(upload_text)
        
        layout.addWidget(upload_area)
        
        # 按钮
        button_row = QHBoxLayout()
        self.upload_btn = QPushButton("📂 选择文件")
        self.upload_btn.setObjectName("primaryButton")
        self.upload_btn.clicked.connect(self.select_file)
        button_row.addWidget(self.upload_btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        
        self.file_path_label = QLabel("")
        self.file_path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.file_path_label)
        
        return card
    
    def create_process_card(self):
        """创建处理卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        options_label = QLabel("处理选项")
        options_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        layout.addWidget(options_label)
        
        button_row = QHBoxLayout()
        
        self.extract_btn = QPushButton("📄 提取文本")
        self.extract_btn.setObjectName("secondaryButton")
        self.extract_btn.clicked.connect(self.extract_text)
        button_row.addWidget(self.extract_btn)
        
        self.summarize_btn = QPushButton("📝 生成摘要")
        self.summarize_btn.setObjectName("secondaryButton")
        button_row.addWidget(self.summarize_btn)
        
        self.analyze_btn = QPushButton("🔍 智能分析")
        self.analyze_btn.setObjectName("primaryButton")
        button_row.addWidget(self.analyze_btn)
        
        button_row.addStretch()
        layout.addLayout(button_row)
        
        return card
    
    def create_result_card(self):
        """创建结果卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        result_title = QLabel("📊 处理结果")
        result_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        layout.addWidget(result_title)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        button_row = QHBoxLayout()
        self.save_btn = QPushButton("💾 保存结果")
        self.save_btn.setObjectName("secondaryButton")
        button_row.addWidget(self.save_btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        
        return card
    
    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "",
            "文档文件 (*.pdf *.docx *.txt *.md);;所有文件 (*.*)"
        )
        if file_path:
            self.file_path_label.setText(f"已选择: {file_path}")
            self.current_file = file_path
    
    def extract_text(self):
        """提取文本"""
        if not hasattr(self, 'current_file') or not self.current_file:
            QMessageBox.warning(self, "警告", "请先选择文件")
            return
        
        try:
            from unified_link_document_processor import UnifiedLinkDocumentProcessor
            processor = UnifiedLinkDocumentProcessor()
            result = processor.process_document(self.current_file)
            
            self.result_text.setText(result.get('text', '无文本内容'))
            self.result_card.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"提取失败: {e}")
