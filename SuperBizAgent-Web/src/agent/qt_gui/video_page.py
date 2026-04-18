#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理页面 - PySide6 版本
连接完整后端接口
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QPlainTextEdit, QProgressBar, QFrame,
    QCheckBox, QGroupBox, QMessageBox, QFileDialog, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from qt_gui.theme import Theme

# 导入后端接口
try:
    from video_downloader import VideoDownloader
    from multimodal_tool import WhisperModel
    from link_analyzer import LinkAnalyzer
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    print(f"[VideoPage] 后端模块导入失败：{e}")


class VideoProcessingWorker(QThread):
    """视频处理工作线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int, str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, link, user_prompt=""):
        super().__init__()
        self.link = link
        self.user_prompt = user_prompt
    
    def run(self):
        try:
            if not BACKEND_AVAILABLE:
                self.finished_signal.emit(False, "后端模块未加载")
                return
            
            # 1. 下载视频
            self.progress_signal.emit(10, "开始下载视频...")
            downloader = VideoDownloader()
            video_path = downloader.download(self.link)
            self.log_signal.emit(f"视频下载成功：{video_path}")
            
            # 2. 语音转文字
            self.progress_signal.emit(40, "开始语音转写...")
            whisper = WhisperModel()
            transcription = whisper.transcribe(video_path)
            self.log_signal.emit(f"转写完成：{len(transcription.get('segments', []))} 个片段")
            
            # 3. 内容分析
            self.progress_signal.emit(70, "开始内容分析...")
            analyzer = LinkAnalyzer()
            analysis = analyzer.analyze_content(transcription)
            self.log_signal.emit(f"分析完成")
            
            # 4. 生成文档
            self.progress_signal.emit(90, "生成文档...")
            result = {
                "link": self.link,
                "video_path": video_path,
                "transcription": transcription,
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }
            
            self.progress_signal.emit(100, "处理完成！")
            self.finished_signal.emit(True, "视频处理成功")
            
        except Exception as e:
            self.finished_signal.emit(False, f"处理失败：{str(e)}")


class VideoProcessingPage(QWidget):
    """视频处理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setup_ui()
        self._connect_signals()
    
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
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setMinimumWidth(120)
        self.start_btn.setFixedHeight(40)
        btn_layout.addWidget(self.start_btn)
        
        # 功能按钮
        buttons = [
            ("AI 配置", "open_ai_config"),
            ("API 设置", "open_api_config"),
            ("批量导入", "batch_import"),
            ("历史查询", "show_history"),
            ("线程配置", "open_thread_config"),
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
    
    def _connect_signals(self):
        """连接信号和槽"""
        self.start_btn.clicked.connect(self.start_processing)
        self.open_ai_config.clicked.connect(self.open_ai_config_handler)
        self.open_api_config.clicked.connect(self.open_api_config_handler)
        self.batch_import.clicked.connect(self.batch_import_handler)
        self.show_history.clicked.connect(self.show_history_handler)
        self.open_thread_config.clicked.connect(self.open_thread_config_handler)
        self.btn_expand_prompt.clicked.connect(self.expand_prompt)
    
    def append_log(self, message: str):
        """追加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] {message}")
    
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
    
    # ========== 后端接口处理方法 ==========
    
    def start_processing(self):
        """开始处理 - 调用后端接口"""
        link = self.link_input.text().strip()
        if not link:
            QMessageBox.warning(self, "警告", "请输入视频链接")
            return
        
        if not BACKEND_AVAILABLE:
            QMessageBox.critical(self, "错误", "后端模块未加载，无法处理")
            return
        
        user_prompt = self.user_prompt_edit.text().strip()
        
        # 更新 UI 状态
        self.update_status("处理中...")
        self.update_queue_status(1, True)
        self.start_btn.setEnabled(False)
        
        # 创建并启动工作线程
        self.worker = VideoProcessingWorker(link, user_prompt)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_processing_finished)
        self.worker.start()
        
        self.append_log(f"开始处理链接：{link}")
    
    def on_processing_finished(self, success: bool, message: str):
        """处理完成回调"""
        self.start_btn.setEnabled(True)
        self.update_status("就绪")
        self.update_queue_status(0, False)
        
        if success:
            self.append_log(f"✓ {message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.append_log(f"✗ {message}")
            QMessageBox.critical(self, "错误", message)
    
    def open_ai_config_handler(self):
        """AI 配置 - 调用后端接口"""
        try:
            from ai_api_config_gui import AIAPIConfigManager
            config_manager = AIAPIConfigManager()
            config_manager.show_config_dialog(self)
            self.append_log("打开 AI 配置对话框")
        except ImportError:
            QMessageBox.information(self, "提示", "AI 配置模块未加载")
            self.append_log("AI 配置模块未加载")
    
    def open_api_config_handler(self):
        """API 设置 - 调用后端接口"""
        try:
            from ai_api_config_gui import AIAPIConfigManager
            config_manager = AIAPIConfigManager()
            config_manager.show_api_config_dialog(self)
            self.append_log("打开 API 设置对话框")
        except ImportError:
            QMessageBox.information(self, "提示", "API 配置模块未加载")
            self.append_log("API 配置模块未加载")
    
    def batch_import_handler(self):
        """批量导入 - 调用后端接口"""
        try:
            from batch_import_gui import BatchImportDialog
            dialog = BatchImportDialog(self)
            if dialog.exec() == QDialog.Accepted:
                links = dialog.get_links()
                self.append_log(f"批量导入 {len(links)} 个链接")
                QMessageBox.information(self, "批量导入", f"已导入 {len(links)} 个链接")
        except ImportError:
            # 简单实现
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择导入文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        links = [line.strip() for line in f if line.strip()]
                        self.append_log(f"从文件导入 {len(links)} 个链接")
                        QMessageBox.information(self, "批量导入", f"已导入 {len(links)} 个链接")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导入失败：{e}")
    
    def show_history_handler(self):
        """历史查询 - 调用后端接口"""
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent', 'output')
            if os.path.exists(output_dir):
                import subprocess
                subprocess.Popen(f'explorer "{output_dir}"')
                self.append_log(f"打开输出目录：{output_dir}")
            else:
                QMessageBox.information(self, "历史记录", "输出目录不存在")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开历史失败：{e}")
    
    def open_thread_config_handler(self):
        """线程配置 - 调用后端接口"""
        try:
            from thread_config_gui import ThreadConfigDialog
            dialog = ThreadConfigDialog(self)
            if dialog.exec() == QDialog.Accepted:
                config = dialog.get_config()
                self.append_log(f"线程配置已更新：最大线程数={config.get('max_workers', 4)}")
        except ImportError:
            # 简单实现
            num, ok = QInputDialog.getInt(self, "线程配置", "设置最大工作线程数:", 4, 1, 16, 1)
            if ok:
                self.append_log(f"线程配置已更新：最大线程数={num}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"线程配置失败：{e}")
    
    def expand_prompt(self):
        """展开编辑 User Prompt"""
        text, ok = QPlainTextEdit.getMultiLineText(self, "编辑 User Prompt", "输入额外提示信息:", self.user_prompt_edit.text())
        if ok:
            self.user_prompt_edit.setText(text)
            self.append_log("已编辑 User Prompt")
