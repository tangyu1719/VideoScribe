#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答页面 - 豆包AI风格
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QFrame, QScrollArea, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from video_tool_gui.theme import Theme, StyleSheet, ShadowEffect


# AI配置
DEFAULT_AI_CONFIG = {
    "thinking_system_prompt": "你是一个善于分析的AI助手，请仔细思考后给出准确的回答。",
    "response_system_prompt": "你是一个专业的AI助手，请给出清晰、准确的回答。",
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 0.9,
    "api_key": "",
    "model": "ep-20260411182220-jv5qt",
    "model_backup": "ep-20260320202115-9jqfp"
}


class ChatWorker(QThread):
    """聊天工作线程"""
    
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, message, config):
        super().__init__()
        self.message = message
        self.config = config
    
    def run(self):
        """执行聊天请求"""
        try:
            # 这里调用后端LLM接口
            # from llm_client import LLMClient
            # client = LLMClient(self.config)
            # response = client.chat(self.message)
            
            # 模拟响应
            import time
            time.sleep(1)
            response = f"这是对\"{self.message}\"的模拟回复。实际使用时需要连接后端LLM接口。"
            
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatPage(QWidget):
    """AI问答页面"""
    
    def __init__(self):
        super().__init__()
        self.ai_config = DEFAULT_AI_CONFIG.copy()
        self.current_session = None
        self.sessions = []
        self.chat_history = []
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧边栏
        left_sidebar = self.create_left_sidebar()
        splitter.addWidget(left_sidebar)
        
        # 右侧聊天区域
        chat_area = self.create_chat_area()
        splitter.addWidget(chat_area)
        
        splitter.setSizes([250, 950])
        main_layout.addWidget(splitter)
    
    def create_left_sidebar(self):
        """创建左侧边栏"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {Theme.BG_SIDEBAR};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("🤖 AI助手")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 新建会话按钮
        new_chat_btn = QPushButton("＋ 新建会话")
        new_chat_btn.setObjectName("secondaryButton")
        new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat_btn.clicked.connect(self.new_session)
        layout.addWidget(new_chat_btn)
        
        # 功能按钮行
        btn_row = QHBoxLayout()
        
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("设置")
        settings_btn.clicked.connect(self.open_settings)
        btn_row.addWidget(settings_btn)
        
        kb_btn = QPushButton("📚")
        kb_btn.setToolTip("知识库")
        kb_btn.clicked.connect(self.open_knowledge_base)
        btn_row.addWidget(kb_btn)
        
        layout.addLayout(btn_row)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {Theme.BORDER}; max-height: 1px;")
        layout.addWidget(line)
        
        # 知识库管理按钮
        kb_label = QLabel("知识库管理")
        kb_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(kb_label)
        
        add_file_btn = QPushButton("📄 添加文件")
        add_file_btn.setObjectName("secondaryButton")
        add_file_btn.clicked.connect(self.add_file_to_kb)
        layout.addWidget(add_file_btn)
        
        add_folder_btn = QPushButton("📁 添加文件夹")
        add_folder_btn.setObjectName("secondaryButton")
        add_folder_btn.clicked.connect(self.add_folder_to_kb)
        layout.addWidget(add_folder_btn)
        
        rebuild_btn = QPushButton("🔄 重建索引")
        rebuild_btn.setObjectName("secondaryButton")
        rebuild_btn.clicked.connect(self.rebuild_kb_index)
        layout.addWidget(rebuild_btn)
        
        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet(f"background-color: {Theme.BORDER}; max-height: 1px;")
        layout.addWidget(line2)
        
        # 会话列表
        session_label = QLabel("会话列表")
        session_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(session_label)
        
        self.session_list = QListWidget()
        self.session_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {Theme.PRIMARY}20;
                color: {Theme.PRIMARY};
            }}
        """)
        self.session_list.itemClicked.connect(self.on_session_selected)
        layout.addWidget(self.session_list)
        
        layout.addStretch()
        return sidebar
    
    def create_chat_area(self):
        """创建聊天区域"""
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 聊天头部
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_WHITE};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        self.chat_title = QLabel("新会话")
        self.chat_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.chat_title)
        header_layout.addStretch()
        
        more_btn = QPushButton("⋮")
        more_btn.setToolTip("更多选项")
        more_btn.setStyleSheet("border: none; font-size: 16px;")
        header_layout.addWidget(more_btn)
        
        layout.addWidget(header)
        
        # 消息显示区域
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setSpacing(15)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_widget)
        layout.addWidget(self.messages_scroll, 1)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_WHITE};
                border-top: 1px solid {Theme.BORDER};
            }}
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # 输入框行
        input_row = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setMaximumHeight(80)
        input_row.addWidget(self.message_input, 1)
        
        # 发送按钮
        send_btn = QPushButton("➤")
        send_btn.setObjectName("primaryButton")
        send_btn.setFixedSize(40, 40)
        send_btn.clicked.connect(self.send_message)
        input_row.addWidget(send_btn)
        
        input_layout.addLayout(input_row)
        
        # 快捷功能按钮
        quick_row = QHBoxLayout()
        
        image_btn = QPushButton("📷")
        image_btn.setToolTip("发送图片")
        image_btn.clicked.connect(self.send_image)
        quick_row.addWidget(image_btn)
        
        clear_btn = QPushButton("🗑️")
        clear_btn.setToolTip("清空对话")
        clear_btn.clicked.connect(self.clear_chat)
        quick_row.addWidget(clear_btn)
        
        quick_row.addStretch()
        input_layout.addLayout(quick_row)
        
        layout.addWidget(input_frame)
        return chat_widget
    
    def new_session(self):
        """新建会话"""
        session_name = f"会话 {len(self.sessions) + 1}"
        self.sessions.append({"name": session_name, "messages": []})
        
        item = QListWidgetItem(session_name)
        self.session_list.addItem(item)
        self.session_list.setCurrentItem(item)
        
        self.chat_title.setText(session_name)
        self.clear_messages()
    
    def on_session_selected(self, item):
        """选择会话"""
        self.chat_title.setText(item.text())
        self.clear_messages()
    
    def send_message(self):
        """发送消息"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        
        # 添加用户消息
        self.add_message("user", message)
        self.message_input.clear()
        
        # 启动AI回复
        self.get_ai_response(message)
    
    def get_ai_response(self, message):
        """获取AI回复"""
        # 显示思考中
        thinking_label = QLabel("🤔 思考中...")
        thinking_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; padding: 10px;")
        thinking_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加到消息区域底部
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, thinking_label)
        
        # 启动工作线程
        self.worker = ChatWorker(message, self.ai_config)
        self.worker.response_ready.connect(lambda resp: self.on_response_ready(resp, thinking_label))
        self.worker.error_occurred.connect(lambda err: self.on_response_error(err, thinking_label))
        self.worker.start()
    
    def on_response_ready(self, response, thinking_label):
        """响应就绪"""
        thinking_label.deleteLater()
        self.add_message("assistant", response)
    
    def on_response_error(self, error, thinking_label):
        """响应错误"""
        thinking_label.deleteLater()
        self.add_message("assistant", f"错误: {error}")
    
    def add_message(self, role, content):
        """添加消息"""
        msg_frame = QFrame()
        msg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_WHITE if role == 'assistant' else Theme.PRIMARY};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        
        layout = QHBoxLayout(msg_frame)
        layout.setContentsMargins(10, 8, 10, 8)
        
        if role == "user":
            layout.addStretch()
            msg_label = QLabel(content)
            msg_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 13px;")
            msg_label.setWordWrap(True)
            msg_label.setMaximumWidth(500)
            layout.addWidget(msg_label)
        else:
            avatar = QLabel("🤖")
            avatar.setStyleSheet("font-size: 20px;")
            layout.addWidget(avatar)
            
            msg_label = QLabel(content)
            msg_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px;")
            msg_label.setWordWrap(True)
            msg_label.setMaximumWidth(500)
            layout.addWidget(msg_label)
            layout.addStretch()
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg_frame)
    
    def clear_messages(self):
        """清空消息"""
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def clear_chat(self):
        """清空对话"""
        self.clear_messages()
    
    def send_image(self):
        """发送图片"""
        QMessageBox.information(self, "提示", "图片功能开发中...")
    
    def open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "提示", "设置功能开发中...")
    
    def open_knowledge_base(self):
        """打开知识库"""
        QMessageBox.information(self, "提示", "知识库功能开发中...")
    
    def add_file_to_kb(self):
        """添加文件到知识库"""
        try:
            from kb_manager import get_knowledge_base
            kb = get_knowledge_base()
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", "文档 (*.pdf *.docx *.txt *.md)"
            )
            if file_path:
                kb.add_document(file_path)
                QMessageBox.information(self, "成功", "文件已添加到知识库")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {e}")
    
    def add_folder_to_kb(self):
        """添加文件夹到知识库"""
        QMessageBox.information(self, "提示", "批量添加功能开发中...")
    
    def rebuild_kb_index(self):
        """重建知识库索引"""
        try:
            from kb_manager import get_knowledge_base
            kb = get_knowledge_base()
            kb.rebuild_index()
            QMessageBox.information(self, "成功", "索引重建完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重建失败: {e}")
