#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理页面 - 核心功能页面
包含所有原GUI的功能和后端接口
"""

import sys
import os
import re
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QProgressBar, QFrame, QGridLayout,
    QScrollArea, QFileDialog, QMessageBox, QComboBox, QDialog,
    QDialogButtonBox, QSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QObject

from video_tool_gui.theme import Theme, StyleSheet, ShadowEffect


# 全局配置
CONFIG = {
    "max_workers": 4,
    "user_prompt": "",
    "api_key": "",
    "model": "ep-20260411182220-jv5qt",
    "model_backup": "ep-20260320202115-9jqfp",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3"
}

# 历史记录
HISTORY_FILE = os.path.expanduser("~/.video_tool_history.json")


class VideoProcessingPage(QWidget):
    """视频处理页面"""
    
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=CONFIG["max_workers"])
        self.history = self.load_history()
        self.task_queue = []
        self.active_futures = {}  # 跟踪正在执行的任务
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. 链接输入区域
        link_card = self.create_link_card()
        content_layout.addWidget(link_card)
        
        # 2. 按钮区域
        button_card = self.create_button_card()
        content_layout.addWidget(button_card)
        
        # 3. 任务状态区域
        status_card = self.create_status_card()
        content_layout.addWidget(status_card)
        
        # 4. User Prompt输入区域
        prompt_card = self.create_prompt_card()
        content_layout.addWidget(prompt_card)
        
        # 5. 日志区域
        log_card = self.create_log_card()
        content_layout.addWidget(log_card)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def create_link_card(self):
        """创建链接输入卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标签
        link_label = QLabel("视频链接：")
        link_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_MEDIUM}px; font-weight: bold;")
        layout.addWidget(link_label)
        
        # 输入框
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("请输入视频链接（支持小红书、抖音、B站等平台）...")
        layout.addWidget(self.link_input)
        
        return card
    
    def create_button_card(self):
        """创建按钮卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QHBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 开始处理按钮 - 蓝色主按钮
        self.start_btn = QPushButton("▶ 开始处理")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 8px 20px;
                font-family: "{Theme.FONT_FAMILY}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Theme.PRIMARY_DARK};
            }}
        """)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setMinimumHeight(36)
        self.start_btn.setMinimumWidth(100)
        self.start_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_btn)
        
        # AI配置按钮
        self.ai_config_btn = QPushButton("⚙️ AI配置")
        self.ai_config_btn.setObjectName("secondaryButton")
        self.ai_config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_config_btn.clicked.connect(self.open_ai_config)
        layout.addWidget(self.ai_config_btn)
        
        # API设置按钮
        self.api_config_btn = QPushButton("🔑 API设置")
        self.api_config_btn.setObjectName("secondaryButton")
        self.api_config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.api_config_btn.clicked.connect(self.open_api_config)
        layout.addWidget(self.api_config_btn)
        
        # 批量导入按钮
        self.batch_btn = QPushButton("📁 批量导入")
        self.batch_btn.setObjectName("secondaryButton")
        self.batch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_btn.clicked.connect(self.batch_import)
        layout.addWidget(self.batch_btn)
        
        # 历史查询按钮
        self.history_btn = QPushButton("📋 历史查询")
        self.history_btn.setObjectName("secondaryButton")
        self.history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_btn.clicked.connect(self.show_history)
        layout.addWidget(self.history_btn)
        
        # 线程配置按钮
        self.thread_btn = QPushButton("🔧 线程配置")
        self.thread_btn.setObjectName("secondaryButton")
        self.thread_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.thread_btn.clicked.connect(self.open_thread_config)
        layout.addWidget(self.thread_btn)
        
        layout.addStretch()
        return card
    
    def create_status_card(self):
        """创建状态卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QHBoxLayout(card)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 任务状态
        self.status_info = QLabel("任务状态：就绪")
        self.status_info.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_NORMAL}px;")
        layout.addWidget(self.status_info)
        
        # 队列状态
        self.queue_status = QLabel("队列：0 个任务")
        self.queue_status.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SIZE_NORMAL}px;")
        layout.addWidget(self.queue_status)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, 1)
        
        return card
    
    def create_prompt_card(self):
        """创建Prompt输入卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标签
        prompt_label = QLabel("User Prompt（可选）：")
        prompt_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_MEDIUM}px;")
        layout.addWidget(prompt_label)
        
        # 输入框
        prompt_row = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("输入自定义提示词（最多500字符）...")
        self.prompt_input.setMaxLength(500)
        self.prompt_input.setText(CONFIG.get("user_prompt", ""))
        prompt_row.addWidget(self.prompt_input, 1)
        
        # 展开按钮
        expand_btn = QPushButton("⛶")
        expand_btn.setFixedWidth(40)
        expand_btn.setToolTip("展开编辑")
        expand_btn.clicked.connect(self.expand_prompt)
        prompt_row.addWidget(expand_btn)
        
        layout.addLayout(prompt_row)
        return card
    
    def create_log_card(self):
        """创建日志卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(StyleSheet.get_card_style())
        ShadowEffect.apply_card_shadow(card)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        log_title = QLabel("📝 处理日志")
        log_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_MEDIUM}px; font-weight: bold;")
        layout.addWidget(log_title)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logArea")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        return card
    
    def start_processing(self):
        """开始处理 - 使用ThreadPoolExecutor多线程"""
        link = self.link_input.text().strip()
        if not link:
            QMessageBox.warning(self, "警告", "请输入视频链接")
            return
        
        # 添加到历史
        self.add_to_history(link)
        
        # 更新UI
        self.status_info.setText("任务状态：处理中...")
        self.status_info.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: {Theme.FONT_SIZE_NORMAL}px;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        self.log("INFO", f"开始处理链接: {link}")
        self.log("INFO", f"使用线程池并行处理，最大线程数: {CONFIG['max_workers']}")
        
        # 使用ThreadPoolExecutor提交任务
        future = self.executor.submit(self._process_link_task, link)
        self.active_futures[link] = future
    
    def _process_link_task(self, link):
        """处理链接任务 - 在线程池中执行"""
        try:
            self.on_analysis_progress(10, "开始下载视频...")
            
            # 1. 下载视频
            from video_downloader import VideoDownloader
            downloader = VideoDownloader()
            video_path = downloader.download(link)
            
            self.on_analysis_progress(30, "视频下载完成，开始转写...")
            
            # 2. 语音转文字
            from multimodal_tool import WhisperModel
            whisper = WhisperModel()
            transcription = whisper.transcribe(video_path)
            
            self.on_analysis_progress(60, "转写完成，开始分析内容...")
            
            # 3. 内容分析
            from link_analyzer import LinkAnalyzer
            analyzer = LinkAnalyzer()
            analysis = analyzer.analyze_content(transcription)
            
            self.on_analysis_progress(90, "分析完成，保存结果...")
            
            # 4. 保存结果
            result = {
                "link": link,
                "video_path": video_path,
                "transcription": transcription,
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }
            
            self.on_analysis_progress(100, "处理完成！")
            self.on_analysis_finished(result)
            
        except Exception as e:
            self.on_analysis_error(str(e))
        finally:
            # 从活动任务中移除
            if link in self.active_futures:
                del self.active_futures[link]
    
    def on_analysis_progress(self, progress, message):
        """分析进度更新"""
        self.progress_bar.setValue(progress)
        self.log("INFO", message)
    
    def on_analysis_finished(self, result):
        """分析完成"""
        self.status_info.setText("任务状态：完成")
        self.status_info.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: {Theme.FONT_SIZE_NORMAL}px;")
        self.progress_bar.setVisible(False)
        
        self.log("SUCCESS", "处理完成！")
        self.log("INFO", f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 更新历史状态
        self.update_history_status(result["link"], "completed")
    
    def on_analysis_error(self, error):
        """分析错误"""
        self.status_info.setText("任务状态：失败")
        self.status_info.setStyleSheet(f"color: {Theme.ERROR}; font-size: {Theme.FONT_SIZE_NORMAL}px;")
        self.progress_bar.setVisible(False)
        
        self.log("ERROR", f"处理失败: {error}")
        QMessageBox.critical(self, "错误", f"处理失败: {error}")
    
    def open_ai_config(self):
        """打开AI配置窗口"""
        dialog = AIConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            CONFIG["user_prompt"] = dialog.get_prompt()
            self.prompt_input.setText(CONFIG["user_prompt"])
    
    def open_api_config(self):
        """打开API配置窗口"""
        dialog = APIConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            CONFIG.update(config)
    
    def open_thread_config(self):
        """打开线程配置窗口"""
        dialog = ThreadConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            CONFIG["max_workers"] = dialog.get_workers()
            self.executor = ThreadPoolExecutor(max_workers=CONFIG["max_workers"])
    
    def batch_import(self):
        """批量导入"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    links = [line.strip() for line in f if line.strip()]
                
                self.task_queue.extend(links)
                self.queue_status.setText(f"队列：{len(self.task_queue)} 个任务")
                self.log("INFO", f"批量导入 {len(links)} 个链接")
                
                QMessageBox.information(self, "成功", f"已导入 {len(links)} 个链接")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")
    
    def show_history(self):
        """显示历史记录"""
        dialog = HistoryDialog(self.history, self)
        dialog.exec()
    
    def expand_prompt(self):
        """展开Prompt编辑"""
        dialog = PromptEditDialog(self.prompt_input.text(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.prompt_input.setText(dialog.get_text())
    
    def log(self, level, message):
        """添加日志"""
        colors = {
            "INFO": Theme.INFO,
            "SUCCESS": Theme.SUCCESS,
            "WARNING": Theme.WARNING,
            "ERROR": Theme.ERROR
        }
        color = colors.get(level, Theme.TEXT_PRIMARY)
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: {Theme.TEXT_MUTED};">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">[{level}]</span> {message}'
        self.log_text.append(html)
    
    def load_history(self):
        """加载历史记录"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"tasks": []}
        return {"tasks": []}
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log("ERROR", f"保存历史记录失败: {e}")
    
    def add_to_history(self, link):
        """添加到历史"""
        task = {
            "id": len(self.history["tasks"]) + 1,
            "link": link,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.history["tasks"].append(task)
        self.save_history()
    
    def update_history_status(self, link, status):
        """更新历史状态"""
        for task in self.history["tasks"]:
            if task["link"] == link:
                task["status"] = status
                task["completed_at"] = datetime.now().isoformat()
                break
        self.save_history()


# 配置对话框类
class AIConfigDialog(QDialog):
    """AI配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI配置")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setText(CONFIG.get("user_prompt", ""))
        self.prompt_edit.setMaximumHeight(150)
        form_layout.addRow("System Prompt:", self.prompt_edit)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_prompt(self):
        return self.prompt_edit.toPlainText()


class APIConfigDialog(QDialog):
    """API配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API设置")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(CONFIG.get("api_key", ""))
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API Key:", self.api_key_edit)
        
        self.model_edit = QLineEdit()
        self.model_edit.setText(CONFIG.get("model", ""))
        form_layout.addRow("Model:", self.model_edit)
        
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setText(CONFIG.get("base_url", ""))
        form_layout.addRow("Base URL:", self.base_url_edit)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_config(self):
        return {
            "api_key": self.api_key_edit.text(),
            "model": self.model_edit.text(),
            "base_url": self.base_url_edit.text()
        }


class ThreadConfigDialog(QDialog):
    """线程配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("线程配置")
        self.setMinimumWidth(300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(CONFIG.get("max_workers", 4))
        form_layout.addRow("最大工作线程数:", self.workers_spin)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_workers(self):
        return self.workers_spin.value()


class HistoryDialog(QDialog):
    """历史记录对话框"""
    
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录")
        self.setMinimumSize(600, 400)
        self.history = history
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        
        # 格式化显示历史
        text = "历史任务列表:\n\n"
        for task in self.history.get("tasks", []):
            text += f"ID: {task.get('id', '-')}\n"
            text += f"链接: {task.get('link', '-')}\n"
            text += f"状态: {task.get('status', '-')}\n"
            text += f"创建时间: {task.get('created_at', '-')}\n"
            if task.get('completed_at'):
                text += f"完成时间: {task['completed_at']}\n"
            text += "-" * 50 + "\n\n"
        
        self.history_text.setText(text)
        layout.addWidget(self.history_text)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class PromptEditDialog(QDialog):
    """Prompt编辑对话框"""
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑提示词")
        self.setMinimumSize(800, 500)
        self.initial_text = text
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setText(self.initial_text)
        layout.addWidget(self.text_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_text(self):
        return self.text_edit.toPlainText()
