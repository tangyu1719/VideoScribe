#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链接分析页面 - 核心功能页面
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QProgressBar, QFrame, QGridLayout,
    QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QRunnable, QThreadPool

from tlinker_gui.theme import Theme, StyleSheet, ShadowEffect, PlatformBadge, LogColors


class AnalysisWorker(QRunnable):
    """分析任务工作线程"""
    
    def __init__(self, url, callback):
        super().__init__()
        self.url = url
        self.callback = callback
    
    def run(self):
        """执行分析"""
        try:
            from link_analyzer import LinkAnalyzer
            analyzer = LinkAnalyzer()
            result = analyzer.analyze_link(self.url)
            self.callback(result, None)
        except Exception as e:
            self.callback(None, str(e))


class LinkAnalysisPage(QWidget):
    """链接分析页面"""
    
    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 标题
        title = QLabel("🔗 链接分析")
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
        
        # 输入卡片
        input_card = self.create_input_card()
        content_layout.addWidget(input_card)
        
        # 进度卡片
        self.progress_card = self.create_progress_card()
        self.progress_card.hide()
        content_layout.addWidget(self.progress_card)
        
        # 结果卡片
        self.result_card = self.create_result_card()
        self.result_card.hide()
        content_layout.addWidget(self.result_card)
        
        # 日志卡片
        log_card = self.create_log_card()
        content_layout.addWidget(log_card)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def create_input_card(self):
        """创建输入卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 输入标签
        input_label = QLabel("输入链接")
        input_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        layout.addWidget(input_label)
        
        # 输入框行
        input_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴小红书、抖音或其他链接...")
        self.url_input.textChanged.connect(self.on_url_changed)
        input_row.addWidget(self.url_input, 1)
        
        self.platform_label = QLabel("")
        input_row.addWidget(self.platform_label)
        layout.addLayout(input_row)
        
        # 按钮行
        button_row = QHBoxLayout()
        self.analyze_btn = QPushButton("🔍 开始分析")
        self.analyze_btn.setObjectName("primaryButton")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.clicked.connect(self.start_analysis)
        button_row.addWidget(self.analyze_btn)
        
        self.batch_btn = QPushButton("📁 批量导入")
        self.batch_btn.setObjectName("secondaryButton")
        self.batch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_btn.clicked.connect(self.batch_import)
        button_row.addWidget(self.batch_btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        
        return card
    
    def create_progress_card(self):
        """创建进度卡片"""
        card = QFrame()
        card.setObjectName("glassCard")
        card.setStyleSheet(StyleSheet.get_glass_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.status_label = QLabel("正在分析...")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 500;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
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
        
        result_title = QLabel("📊 分析结果")
        result_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        layout.addWidget(result_title)
        
        # 元信息
        meta_grid = QGridLayout()
        meta_grid.setSpacing(12)
        
        labels = ["标题:", "平台:", "类型:", "内容:"]
        self.meta_values = []
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            meta_grid.addWidget(label, i, 0)
            value = QLabel("-")
            value.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
            if i == 0 or i == 3:
                value.setWordWrap(True)
            meta_grid.addWidget(value, i, 1)
            self.meta_values.append(value)
        
        layout.addLayout(meta_grid)
        return card
    
    def create_log_card(self):
        """创建日志卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        log_title = QLabel("📝 处理日志")
        log_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        layout.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logArea")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        return card
    
    def on_url_changed(self, text):
        """URL变化时识别平台"""
        platform = self.detect_platform(text)
        if platform:
            self.platform_label.setText(platform)
            self.platform_label.setStyleSheet(PlatformBadge.get_style(platform))
        else:
            self.platform_label.setText("")
    
    def detect_platform(self, url):
        """检测平台类型"""
        if "xiaohongshu.com" in url or "xhslink.com" in url:
            return "xiaohongshu"
        elif "douyin.com" in url or "iesdouyin.com" in url:
            return "douyin"
        elif "bilibili.com" in url or "b23.tv" in url:
            return "bilibili"
        elif "weibo.com" in url or "weibo.cn" in url:
            return "weibo"
        return None
    
    def start_analysis(self):
        """开始分析"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入链接")
            return
        
        self.log_text.clear()
        self.log("info", f"开始分析链接: {url}")
        
        self.progress_card.show()
        self.result_card.hide()
        self.progress_bar.setValue(30)
        
        # 启动工作线程
        worker = AnalysisWorker(url, self.on_analysis_complete)
        self.thread_pool.start(worker)
    
    def on_analysis_complete(self, result, error):
        """分析完成回调"""
        self.progress_bar.setValue(100)
        
        if error:
            self.log("error", f"分析失败: {error}")
            QMessageBox.critical(self, "错误", f"分析失败: {error}")
            self.progress_card.hide()
            return
        
        self.log("success", "分析完成")
        self.display_result(result)
        self.progress_card.hide()
        self.result_card.show()
    
    def display_result(self, result):
        """显示结果"""
        if not result:
            return
        
        # 更新元信息
        if isinstance(result, dict):
            self.meta_values[0].setText(result.get('title', '-')[:100])
            self.meta_values[1].setText(result.get('platform', '-'))
            self.meta_values[2].setText(result.get('type', '-'))
            content = result.get('text_content', result.get('content', '-'))
            self.meta_values[3].setText(content[:500] + "..." if len(content) > 500 else content)
    
    def batch_import(self):
        """批量导入"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            self.log("info", f"批量导入文件: {file_path}")
            # TODO: 实现批量处理逻辑
    
    def log(self, level, message):
        """添加日志"""
        color = LogColors.get_color_html(level)
        html = f'<span style="color: {color};">[{level.upper()}]</span> {message}'
        self.log_text.append(html)
