#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理页面 - PySide6 版本
模仿豆包/DeskClaw 现代风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QPlainTextEdit, QProgressBar, QFrame,
    QCheckBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from qt_gui.theme import Theme


class VideoProcessingPage(QWidget):
    """视频处理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("视频处理")
        title_label.setFont(QFont(Theme.current["font_family"], 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.current['text_primary']};")
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("智能视频分析与文本转换系统")
        subtitle_label.setFont(QFont(Theme.current["font_family"], 11))
        subtitle_label.setStyleSheet(f"color: {Theme.current['text_secondary']};")
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 输入区域卡片
        input_card = QFrame()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setSpacing(12)
        
        # 视频链接输入
        link_label = QLabel("视频链接：")
        link_label.setFont(QFont(Theme.current["font_family"], 12, QFont.Bold))
        input_layout.addWidget(link_label)
        
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("输入视频 URL（支持小红书、抖音、B 站、YouTube 等）...")
        self.link_input.setFixedHeight(40)
        input_layout.addWidget(self.link_input)
        
        # 飞书同步选项
        feishu_layout = QHBoxLayout()
        self.feishu_sync_check = QCheckBox("同步到飞书")
        self.feishu_sync_check.setChecked(False)
        feishu_layout.addWidget(self.feishu_sync_check)
        
        self.feishu_folder_edit = QLineEdit()
        self.feishu_folder_edit.setPlaceholderText("飞书文件夹路径（可选）")
        self.feishu_folder_edit.setFixedHeight(32)
        feishu_layout.addWidget(self.feishu_folder_edit, 1)
        
        input_layout.addLayout(feishu_layout)
        
        # User Prompt 折叠区域
        prompt_group = QGroupBox("User Prompt（可选）")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.user_prompt_edit = QLineEdit()
        self.user_prompt_edit.setPlaceholderText("每次处理视频时的额外提示信息，最多 500 字符")
        self.user_prompt_edit.setFixedHeight(36)
        prompt_layout.addWidget(self.user_prompt_edit)
        
        self.btn_expand_prompt = QPushButton("展开编辑")
        self.btn_expand_prompt.setObjectName("secondaryButton")
        self.btn_expand_prompt.setFixedHeight(32)
        prompt_layout.addWidget(self.btn_expand_prompt)
        
        input_layout.addWidget(prompt_group)
        
        layout.addWidget(input_card)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 主按钮
        self.start_btn = QPushButton("▶ 开始处理")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setMinimumWidth(120)
        self.start_btn.setFixedHeight(40)
        btn_layout.addWidget(self.start_btn)
        
        # 功能按钮
        buttons = [
            ("⚙ AI 配置", "open_ai_config"),
            ("🔑 API 设置", "open_api_config"),
            ("📥 批量导入", "batch_import"),
            ("📜 历史查询", "show_history"),
            ("⚡ 线程配置", "open_thread_config"),
        ]
        
        for text, attr in buttons:
            btn = QPushButton(text)
            btn.setObjectName("secondaryButton")
            btn.setFixedHeight(36)
            btn.setFixedWidth(100)
            setattr(self, attr, btn)
            btn_layout.addWidget(btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 状态区域
        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setSpacing(8)
        
        # 任务状态
        task_status_layout = QHBoxLayout()
        self.lbl_task_status = QLabel("任务状态：就绪")
        self.lbl_task_status.setFont(QFont(Theme.current["font_family"], 11))
        task_status_layout.addWidget(self.lbl_task_status)
        task_status_layout.addStretch()
        
        self.lbl_queue_status = QLabel("队列：0 个任务 | 状态：空闲")
        self.lbl_queue_status.setStyleSheet(f"color: {Theme.current['text_secondary']};")
        task_status_layout.addWidget(self.lbl_queue_status)
        
        status_layout.addLayout(task_status_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(8)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_card)
        
        # 日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logArea")
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(200)
        log_layout.addWidget(self.log_view)
        
        layout.addWidget(log_group, 1)
    
    def append_log(self, message: str):
        """追加日志"""
        self.log_view.appendPlainText(message)
    
    def update_progress(self, value: int):
        """更新进度"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status: str):
        """更新状态"""
        self.lbl_task_status.setText(f"任务状态：{status}")
    
    def update_queue_status(self, count: int, processing: bool):
        """更新队列状态"""
        status = "处理中" if processing else "空闲"
        self.lbl_queue_status.setText(f"队列：{count} 个任务 | 状态：{status}")
