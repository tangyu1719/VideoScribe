#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理页面 - PySide6版本
与原GUI unified_link_document_gui.py 保持一致的功能
支持链接分析和多模态文档处理
"""

import os
import json
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QProgressBar, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QSplitter,
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QTabWidget, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

from video_tool_gui.theme import Theme, StyleSheet, ShadowEffect, get_global_stylesheet

# 导入统一处理器
try:
    import sys
    sys.path.insert(0, r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent')
    from unified_link_document_processor import (
        UnifiedLinkDocumentProcessor, InputType, ContentType,
        UnifiedProcessingResult
    )
    UNIFIED_PROCESSOR_AVAILABLE = True
except ImportError as e:
    UNIFIED_PROCESSOR_AVAILABLE = False
    print(f"[DocumentPage] 统一处理器未安装: {e}")

# 文件类型配置
FILE_TYPE_CONFIG = {
    'image': {
        'label': '图片',
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
        'max_size': 10 * 1024 * 1024,
        'color': '#9333ea'
    },
    'pdf': {
        'label': 'PDF',
        'extensions': ['.pdf'],
        'max_size': 50 * 1024 * 1024,
        'color': '#dc2626'
    },
    'docx': {
        'label': 'Word',
        'extensions': ['.docx', '.doc'],
        'max_size': 20 * 1024 * 1024,
        'color': '#2563eb'
    },
    'markdown': {
        'label': 'Markdown',
        'extensions': ['.md', '.markdown'],
        'max_size': 5 * 1024 * 1024,
        'color': '#6b7280'
    },
    'csv': {
        'label': 'CSV',
        'extensions': ['.csv'],
        'max_size': 10 * 1024 * 1024,
        'color': '#16a34a'
    },
    'audio': {
        'label': '音频',
        'extensions': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
        'max_size': 100 * 1024 * 1024,
        'color': '#ea580c'
    },
    'video': {
        'label': '视频',
        'extensions': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
        'max_size': 500 * 1024 * 1024,
        'color': '#db2777'
    }
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "OUTPUT")


def get_file_type(file_path: str) -> tuple:
    """获取文件类型信息"""
    ext = Path(file_path).suffix.lower()
    for file_type, config in FILE_TYPE_CONFIG.items():
        if ext in config['extensions']:
            return file_type, config
    return None, None


class ProcessingThread(QThread):
    """处理线程"""
    log_signal = Signal(str)
    progress_signal = Signal(str, int, str)
    complete_signal = Signal(bool, str)
    
    def __init__(self, processor, task_queue, config):
        super().__init__()
        self.processor = processor
        self.task_queue = task_queue
        self.config = config
        self._is_running = True
    
    def run(self):
        try:
            total_tasks = len(self.task_queue)
            
            for i, task in enumerate(self.task_queue, 1):
                if not self._is_running:
                    break
                    
                self.log_signal.emit(f"\n{'='*50}")
                self.log_signal.emit(f"处理任务 {i}/{total_tasks}")
                
                # 设置回调
                self.processor.set_callbacks(
                    progress_callback=lambda s, p, m: self.progress_signal.emit(
                        s, int((i-1)*100/total_tasks + p/total_tasks), m
                    ),
                    log_callback=lambda m, l: self.log_signal.emit(m)
                )
                
                # 处理
                result = self.processor.process(
                    task['source'],
                    is_url=(task['type'] == 'url'),
                    llm_config=self.config.get('llm_config', {}),
                    output_dir=self.config.get('output_dir', OUTPUT_DIR),
                    user_prompt=self.config.get('user_prompt', '')
                )
                
                if result.success:
                    self.log_signal.emit(f"任务完成: {result.output_file}")
                else:
                    self.log_signal.emit(f"任务失败: {result.error}")
            
            if self._is_running:
                self.complete_signal.emit(True, "所有任务处理完成！")
            
        except Exception as e:
            self.complete_signal.emit(False, str(e))
    
    def stop(self):
        self._is_running = False


class AIConfigDialog(QDialog):
    """AI配置对话框"""
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.setWindowTitle("AI配置")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 表单
        form_layout = QFormLayout()
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.config.get('api_key', ''))
        self.api_key_input.setPlaceholderText("请输入API Key")
        form_layout.addRow("API Key:", self.api_key_input)
        
        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "ep-20260320202517-w6ncg",
            "doubao-pro-32k",
            "doubao-lite-32k"
        ])
        self.model_combo.setCurrentText(self.config.get('model', 'ep-20260320202517-w6ncg'))
        form_layout.addRow("模型:", self.model_combo)
        
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(self.config.get('temperature', 0.7))
        form_layout.addRow("Temperature:", self.temp_spin)
        
        # Max Tokens
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(100, 8000)
        self.tokens_spin.setSingleStep(100)
        self.tokens_spin.setValue(self.config.get('max_tokens', 4096))
        form_layout.addRow("Max Tokens:", self.tokens_spin)
        
        # Top P
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(self.config.get('top_p', 0.9))
        form_layout.addRow("Top P:", self.top_p_spin)
        
        layout.addLayout(form_layout)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_config(self):
        return {
            'api_key': self.api_key_input.text(),
            'model': self.model_combo.currentText(),
            'temperature': self.temp_spin.value(),
            'max_tokens': self.tokens_spin.value(),
            'top_p': self.top_p_spin.value()
        }


class BatchImportDialog(QDialog):
    """批量导入对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量导入")
        self.setMinimumSize(600, 400)
        self.links = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel("每行输入一个链接，支持批量导入多个链接进行处理")
        info_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(info_label)
        
        # 文本输入区
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("输入链接URL（每行一个）...")
        layout.addWidget(self.text_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.import_file_btn = QPushButton("从文件导入")
        self.import_file_btn.clicked.connect(self.import_from_file)
        btn_layout.addWidget(self.import_file_btn)
        
        btn_layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        
        layout.addLayout(btn_layout)
    
    def import_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_edit.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"读取文件失败: {e}")
    
    def get_links(self):
        text = self.text_edit.toPlainText()
        return [line.strip() for line in text.split('\n') if line.strip()]


class DocumentPage(QWidget):
    """文档处理页面 - 与原GUI unified_link_document_gui.py 功能一致"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.processor = UnifiedLinkDocumentProcessor() if UNIFIED_PROCESSOR_AVAILABLE else None
        self.selected_files = []
        self.processing = False
        self.task_queue = []
        self.config = self._load_config()
        self.processing_thread = None
        
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def _load_config(self):
        """加载配置"""
        config_file = os.path.join(BASE_DIR, "unified_processor_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
        return {
            'llm_config': {},
            'output_dir': OUTPUT_DIR,
            'user_prompt': ''
        }
    
    def _save_config(self):
        """保存配置"""
        config_file = os.path.join(BASE_DIR, "unified_processor_config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def setup_ui(self):
        """创建UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        title_label = QLabel("链接+文档统一处理")
        title_label.setFont(QFont(Theme.FONT_FAMILY, 18, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("支持链接分析、多模态文档处理、统一文字分析流程")
        subtitle_label.setFont(QFont(Theme.FONT_FAMILY, 11))
        subtitle_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 输入区域
        input_group = QGroupBox("输入内容")
        input_group.setFont(QFont(Theme.FONT_FAMILY, 12, QFont.Bold))
        input_layout = QHBoxLayout(input_group)
        
        # 左侧：链接输入
        link_layout = QVBoxLayout()
        
        link_title = QLabel("链接输入")
        link_title.setFont(QFont(Theme.FONT_FAMILY, 12, QFont.Bold))
        link_title.setStyleSheet(f"color: {Theme.PRIMARY};")
        link_layout.addWidget(link_title)
        
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("输入链接URL（小红书、抖音、网页等）...")
        self.link_input.setMinimumHeight(36)
        self.link_input.textChanged.connect(self._update_link_display)
        link_layout.addWidget(self.link_input)
        
        link_hint = QLabel("支持：小红书图文/视频、抖音图文/视频、B站、YouTube、网页等")
        link_hint.setFont(QFont(Theme.FONT_FAMILY, 9))
        link_hint.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        link_layout.addWidget(link_hint)
        
        input_layout.addLayout(link_layout, 1)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"background-color: {Theme.BORDER};")
        separator.setFixedWidth(2)
        input_layout.addWidget(separator)
        
        # 右侧：文档上传
        doc_layout = QVBoxLayout()
        
        doc_title = QLabel("多模态文档上传")
        doc_title.setFont(QFont(Theme.FONT_FAMILY, 12, QFont.Bold))
        doc_title.setStyleSheet(f"color: #9333ea;")
        doc_layout.addWidget(doc_title)
        
        # 拖放区域
        self.drop_frame = QFrame()
        self.drop_frame.setMinimumHeight(80)
        self.drop_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_INPUT};
                border: 2px dashed {Theme.BORDER};
                border-radius: {Theme.RADIUS_NORMAL}px;
            }}
            QFrame:hover {{
                border-color: {Theme.PRIMARY};
            }}
        """)
        drop_layout = QVBoxLayout(self.drop_frame)
        
        self.drop_label = QLabel("拖拽文件到此处，或点击选择文件\n支持：图片、PDF、Word、Markdown、CSV、音频、视频")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setFont(QFont(Theme.FONT_FAMILY, 10))
        self.drop_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        drop_layout.addWidget(self.drop_label)
        
        self.drop_frame.mousePressEvent = lambda e: self._select_files()
        self.drop_label.mousePressEvent = lambda e: self._select_files()
        
        doc_layout.addWidget(self.drop_frame)
        
        # 文件类型标签
        types_layout = QHBoxLayout()
        for file_type, config in FILE_TYPE_CONFIG.items():
            badge = QLabel(f" {config['label']} ")
            badge.setFont(QFont(Theme.FONT_FAMILY, 8))
            badge.setStyleSheet(f"""
                background-color: {config['color']};
                color: white;
                border-radius: 3px;
                padding: 2px 6px;
            """)
            types_layout.addWidget(badge)
        types_layout.addStretch()
        doc_layout.addLayout(types_layout)
        
        input_layout.addLayout(doc_layout, 1)
        
        main_layout.addWidget(input_group)
        
        # 已选择内容区域
        content_group = QGroupBox("已选择的内容")
        content_group.setFont(QFont(Theme.FONT_FAMILY, 12, QFont.Bold))
        content_layout = QVBoxLayout(content_group)
        
        # 链接显示
        self.link_display = QLabel("链接：未输入")
        self.link_display.setFont(QFont(Theme.FONT_FAMILY, 10))
        self.link_display.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        content_layout.addWidget(self.link_display)
        
        # 文件列表
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(80)
        content_layout.addWidget(self.files_list)
        
        main_layout.addWidget(content_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        # 左侧按钮
        left_btns = QHBoxLayout()
        
        self.process_btn = QPushButton("▶ 开始处理")
        self.process_btn.setObjectName("primaryButton")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setMinimumWidth(120)
        self.process_btn.clicked.connect(self._start_processing)
        left_btns.addWidget(self.process_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.setMinimumWidth(80)
        self.clear_btn.clicked.connect(self._clear_all)
        left_btns.addWidget(self.clear_btn)
        
        btn_layout.addLayout(left_btns)
        btn_layout.addStretch()
        
        # 右侧按钮
        right_btns = QHBoxLayout()
        
        self.ai_config_btn = QPushButton("⚙ AI配置")
        self.ai_config_btn.setMinimumHeight(36)
        self.ai_config_btn.setMinimumWidth(90)
        self.ai_config_btn.clicked.connect(self._open_ai_config)
        right_btns.addWidget(self.ai_config_btn)
        
        self.batch_btn = QPushButton("批量导入")
        self.batch_btn.setMinimumHeight(36)
        self.batch_btn.setMinimumWidth(90)
        self.batch_btn.clicked.connect(self._batch_import)
        right_btns.addWidget(self.batch_btn)
        
        self.history_btn = QPushButton("历史记录")
        self.history_btn.setMinimumHeight(36)
        self.history_btn.setMinimumWidth(90)
        self.history_btn.clicked.connect(self._show_history)
        right_btns.addWidget(self.history_btn)
        
        btn_layout.addLayout(right_btns)
        
        main_layout.addLayout(btn_layout)
        
        # 进度区域
        progress_group = QGroupBox("处理进度")
        progress_group.setFont(QFont(Theme.FONT_FAMILY, 11, QFont.Bold))
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(20)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont(Theme.FONT_FAMILY, 10))
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        progress_layout.addWidget(self.status_label)
        
        main_layout.addWidget(progress_group)
        
        # 日志区域
        log_group = QGroupBox("处理日志")
        log_group.setFont(QFont(Theme.FONT_FAMILY, 11, QFont.Bold))
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logArea")
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group, 1)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self._add_file(file_path)
    
    def _update_link_display(self):
        """更新链接显示"""
        link = self.link_input.text().strip()
        if link:
            display_link = link[:60] + "..." if len(link) > 60 else link
            self.link_display.setText(f"链接：{display_link}")
            self.link_display.setStyleSheet(f"color: {Theme.PRIMARY};")
        else:
            self.link_display.setText("链接：未输入")
            self.link_display.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
    
    def _select_files(self):
        """选择文件"""
        all_extensions = []
        for config in FILE_TYPE_CONFIG.values():
            all_extensions.extend(config['extensions'])
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要处理的文件",
            "",
            f"所有支持的文件 ({' '.join(f'*{ext}' for ext in all_extensions)});;"
            "图片文件 (*.jpg *.jpeg *.png *.gif *.webp *.bmp);;"
            "PDF文件 (*.pdf);;"
            "Word文件 (*.docx *.doc);;"
            "Markdown文件 (*.md *.markdown);;"
            "CSV文件 (*.csv);;"
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg *.aac);;"
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv);;"
            "所有文件 (*.*)"
        )
        
        for file_path in file_paths:
            self._add_file(file_path)
    
    def _add_file(self, file_path: str):
        """添加文件到列表"""
        file_type, config = get_file_type(file_path)
        
        if not file_type:
            self._log(f"不支持的文件类型: {os.path.basename(file_path)}")
            return
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > config['max_size']:
            self._log(f"文件过大: {os.path.basename(file_path)}")
            return
        
        # 添加到列表
        self.selected_files.append({
            'path': file_path,
            'type': file_type,
            'config': config,
            'size': file_size
        })
        
        # 更新列表显示
        display_text = f"[{config['label']}] {os.path.basename(file_path)}"
        item = QListWidgetItem(display_text)
        self.files_list.addItem(item)
        
        self._log(f"已添加文件: {os.path.basename(file_path)}")
    
    def _clear_all(self):
        """清空所有内容"""
        # 清空链接
        self.link_input.clear()
        self._update_link_display()
        
        # 清空文件
        self.selected_files.clear()
        self.files_list.clear()
        
        # 清空日志
        self.log_text.clear()
        
        # 重置进度
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        
        self._log("已清空所有内容")
    
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def _start_processing(self):
        """开始处理"""
        link = self.link_input.text().strip()
        has_link = bool(link)
        
        # 检查是否有内容可处理
        if not has_link and not self.selected_files:
            QMessageBox.warning(self, "警告", "请输入链接或选择要处理的文件")
            return
        
        if self.processing:
            QMessageBox.warning(self, "警告", "正在处理中，请等待")
            return
        
        if not UNIFIED_PROCESSOR_AVAILABLE:
            QMessageBox.critical(self, "错误", "统一处理器模块未安装")
            return
        
        # 构建任务队列
        self.task_queue = []
        
        if has_link:
            self.task_queue.append({
                'type': 'url',
                'source': link
            })
        
        for file_info in self.selected_files:
            self.task_queue.append({
                'type': 'file',
                'source': file_info['path'],
                'file_info': file_info
            })
        
        # 开始处理
        self.processing = True
        self.process_btn.setEnabled(False)
        self.process_btn.setText("处理中...")
        
        # 创建并启动处理线程
        self.processing_thread = ProcessingThread(
            self.processor,
            self.task_queue,
            self.config
        )
        self.processing_thread.log_signal.connect(self._log)
        self.processing_thread.progress_signal.connect(self._update_progress)
        self.processing_thread.complete_signal.connect(self._processing_complete)
        self.processing_thread.start()
    
    def _update_progress(self, stage: str, progress: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"[{stage}] {message}")
        self.status_label.setStyleSheet(f"color: {Theme.PRIMARY};")
        self._log(f"{stage}: {progress}% - {message}")
    
    def _processing_complete(self, success: bool, message: str):
        """处理完成"""
        self.processing = False
        self.process_btn.setEnabled(True)
        self.process_btn.setText("▶ 开始处理")
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("处理完成")
            self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")
            self._log(f"\n{message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.status_label.setText(f"处理失败: {message}")
            self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
            self._log(f"\n处理失败: {message}")
            QMessageBox.critical(self, "错误", f"处理失败: {message}")
    
    def _open_ai_config(self):
        """打开AI配置"""
        dialog = AIConfigDialog(self.config.get('llm_config', {}), self)
        if dialog.exec() == QDialog.Accepted:
            self.config['llm_config'] = dialog.get_config()
            self._save_config()
            self._log("AI配置已保存")
    
    def _batch_import(self):
        """批量导入"""
        dialog = BatchImportDialog(self)
        if dialog.exec() == QDialog.Accepted:
            links = dialog.get_links()
            if links:
                # 添加到任务队列
                for link in links:
                    self.task_queue.append({
                        'type': 'url',
                        'source': link
                    })
                self._log(f"已批量导入 {len(links)} 个链接")
                QMessageBox.information(self, "批量导入", f"已导入 {len(links)} 个链接")
    
    def _show_history(self):
        """显示历史记录"""
        output_dir = self.config.get('output_dir', OUTPUT_DIR)
        if os.path.exists(output_dir):
            import subprocess
            subprocess.Popen(f'explorer "{output_dir}"')
            self._log(f"打开输出目录: {output_dir}")
        else:
            QMessageBox.information(self, "历史记录", "输出目录为空")
