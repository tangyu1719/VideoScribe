#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperBizAgent PyQt6 GUI - 主应用
科技蓝风格，卡片化、透明化、立体化、圆角化设计
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QStackedWidget,
    QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem, QProgressBar,
    QTextEdit, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette, QLinearGradient, QBrush, QPainter, QFontDatabase
from PyQt6.QtWebEngineWidgets import QWebEngineView
import json


# ============ 主题配置 ============
class Theme:
    """科技蓝主题配色"""
    
    # 主色调
    PRIMARY = "#0066FF"
    PRIMARY_DARK = "#0052CC"
    PRIMARY_LIGHT = "#4D94FF"
    ACCENT = "#00D4FF"
    
    # 背景色
    BG_DARK = "#0A0E1A"
    BG_DARKER = "#050810"
    BG_CARD = "#111827"
    BG_CARD_HOVER = "#1A2234"
    BG_TRANSPARENT = "rgba(17, 24, 39, 0.8)"
    BG_GLASS = "rgba(17, 24, 39, 0.5)"
    
    # 文字颜色
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"
    
    # 边框和阴影
    BORDER = "#1E293B"
    BORDER_LIGHT = "#334155"
    SHADOW = "rgba(0, 0, 0, 0.4)"
    
    # 状态色
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"


# ============ 自定义组件 ============
class Card(QFrame):
    """玻璃拟态卡片"""
    
    def __init__(self, parent=None, elevated=False):
        super().__init__(parent)
        self.elevated = elevated
        self.setup_ui()
    
    def setup_ui(self):
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.BG_GLASS};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: 20px;
                padding: 20px;
            }}
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40 if self.elevated else 20)
        shadow.setColor(QColor(0, 102, 255, 60))
        shadow.setOffset(0, 4 if self.elevated else 2)
        self.setGraphicsEffect(shadow)


class ElevatedCard(QFrame):
    """立体卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setObjectName("elevatedCard")
        self.setStyleSheet(f"""
            QFrame#elevatedCard {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 16px;
                padding: 20px;
            }}
        """)
        
        # 添加立体阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)


class GradientButton(QPushButton):
    """渐变按钮"""
    
    def __init__(self, text, parent=None, icon_text=""):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.setup_ui()
    
    def setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY_LIGHT}, stop:1 {Theme.ACCENT});
            }}
        """)
        
        # 添加发光阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 102, 255, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class NavButton(QPushButton):
    """导航按钮"""
    
    clicked_signal = pyqtSignal()
    
    def __init__(self, text, icon_text, parent=None):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.is_active = False
        self.setup_ui()
    
    def setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)
        self.update_style()
    
    def update_style(self):
        if self.is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(0, 102, 255, 0.15);
                    color: {Theme.PRIMARY};
                    border: 1px solid {Theme.PRIMARY};
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_SECONDARY};
                    border: 1px solid transparent;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.05);
                    color: {Theme.TEXT_PRIMARY};
                }}
            """)
    
    def set_active(self, active):
        self.is_active = active
        self.update_style()


class StatCard(ElevatedCard):
    """统计卡片"""
    
    def __init__(self, title, value, subtitle, color, parent=None):
        super().__init__(parent)
        self.setup_content(title, value, subtitle, color)
    
    def setup_content(self, title, value, subtitle, color):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部图标和徽章
        top_layout = QHBoxLayout()
        
        icon_container = QFrame()
        icon_container.setStyleSheet(f"""
            background-color: {color}20;
            border: 2px solid {color}40;
            border-radius: 12px;
        """)
        icon_container.setFixedSize(52, 52)
        
        top_layout.addWidget(icon_container)
        top_layout.addStretch()
        
        # 数值
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 32px;
            font-weight: bold;
        """)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            font-size: 14px;
            font-weight: 500;
        """)
        
        # 副标题
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED};
            font-size: 12px;
        """)
        
        layout.addLayout(top_layout)
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)


# ============ ECharts图表 ============
class EChartsWidget(QWebEngineView):
    """ECharts图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Theme.BG_CARD}; border-radius: 12px;")
    
    def load_chart(self, option):
        """加载ECharts配置"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: {Theme.BG_CARD};
                }}
                #chart {{
                    width: 100%;
                    height: 100vh;
                }}
            </style>
        </head>
        <body>
            <div id="chart"></div>
            <script>
                var chart = echarts.init(document.getElementById('chart'));
                var option = {json.dumps(option)};
                chart.setOption(option);
                window.addEventListener('resize', function() {{
                    chart.resize();
                }});
            </script>
        </body>
        </html>
        """
        self.setHtml(html)


# ============ 主窗口 ============
class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperBizAgent - AI智能助手")
        self.setMinimumSize(1400, 900)
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.create_video_page())
        self.content_stack.addWidget(self.create_chat_page())
        self.content_stack.addWidget(self.create_knowledge_page())
        self.content_stack.addWidget(self.create_link_page())
        self.content_stack.addWidget(self.create_ops_page())
        self.content_stack.addWidget(self.create_settings_page())
        
        main_layout.addWidget(self.content_stack, 1)
    
    def create_sidebar(self):
        """创建侧边栏"""
        sidebar = QFrame()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(17, 24, 39, 0.5);
                border-right: 1px solid {Theme.BORDER_LIGHT};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Logo
        logo_layout = QHBoxLayout()
        logo_icon = QLabel("🤖")
        logo_icon.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
            border-radius: 12px;
            padding: 10px;
            font-size: 24px;
        """)
        logo_icon.setFixedSize(48, 48)
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_text = QLabel("SuperBizAgent\nAI智能助手")
        logo_text.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
            line-height: 1.4;
        """)
        
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        
        layout.addLayout(logo_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {Theme.BORDER}; max-height: 1px;")
        layout.addWidget(line)
        
        # 导航菜单
        self.nav_buttons = []
        nav_items = [
            ("视频处理", "🎬", 0),
            ("AI对话", "💬", 1),
            ("知识库", "📚", 2),
            ("链接分析", "🔗", 3),
            ("运维监控", "📊", 4),
            ("系统设置", "⚙️", 5),
        ]
        
        for text, icon, index in nav_items:
            btn = NavButton(f"{icon}  {text}", icon)
            btn.clicked.connect(lambda checked, i=index, b=btn: self.switch_page(i, b))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        # 设置第一个为激活状态
        self.nav_buttons[0].set_active(True)
        
        layout.addStretch()
        
        # 状态卡片
        status_card = Card()
        status_layout = QVBoxLayout(status_card)
        
        status_label = QLabel("🟢 系统正常运行")
        status_label.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 12px;")
        
        version_label = QLabel("v2.0.0")
        version_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(version_label)
        
        layout.addWidget(status_card)
        
        return sidebar
    
    def switch_page(self, index, button):
        """切换页面"""
        self.content_stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.set_active(False)
        button.set_active(True)
    
    def create_video_page(self):
        """创建视频处理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("视频处理")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
        """)
        
        subtitle = QLabel("管理和处理视频下载任务")
        subtitle.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        
        new_task_btn = GradientButton("+ 新建任务")
        header.addWidget(new_task_btn)
        
        layout.addLayout(header)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        stats_layout.addWidget(StatCard("待处理", "12", "个任务等待", Theme.WARNING))
        stats_layout.addWidget(StatCard("处理中", "3", "正在下载", Theme.INFO))
        stats_layout.addWidget(StatCard("已完成", "156", "本月累计", Theme.SUCCESS))
        stats_layout.addWidget(StatCard("失败", "2", "需要重试", Theme.ERROR))
        
        layout.addLayout(stats_layout)
        
        # 任务列表卡片
        task_card = Card(elevated=True)
        task_layout = QVBoxLayout(task_card)
        
        task_header = QLabel("📋 任务列表")
        task_header.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        """)
        task_layout.addWidget(task_header)
        
        # 任务表格
        task_table = self.create_task_table()
        task_layout.addWidget(task_table)
        
        layout.addWidget(task_card, 1)
        
        return page
    
    def create_task_table(self):
        """创建任务表格"""
        table = QFrame()
        table.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(table)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 表头
        header = QFrame()
        header.setStyleSheet(f"""
            background-color: rgba(30, 41, 59, 0.5);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        header_layout = QHBoxLayout(header)
        
        headers = ["任务ID", "链接", "状态", "进度", "操作"]
        widths = [120, 0, 100, 150, 120]
        
        for text, width in zip(headers, widths):
            label = QLabel(text)
            label.setStyleSheet(f"""
                color: {Theme.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
                padding: 12px 16px;
            """)
            if width > 0:
                label.setFixedWidth(width)
            else:
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header_layout.addWidget(label)
        
        layout.addWidget(header)
        
        # 任务数据
        tasks = [
            ("TASK-001", "https://douyin.com/xxx", "处理中", 65, Theme.INFO),
            ("TASK-002", "https://bilibili.com/xxx", "待处理", 0, Theme.WARNING),
            ("TASK-003", "https://xiaohongshu.com/xxx", "已完成", 100, Theme.SUCCESS),
            ("TASK-004", "https://youtube.com/xxx", "失败", 30, Theme.ERROR),
        ]
        
        for i, (task_id, link, status, progress, color) in enumerate(tasks):
            row = QFrame()
            row.setStyleSheet(f"""
                background-color: {'rgba(30, 41, 59, 0.3)' if i % 2 == 0 else 'transparent'};
                border-bottom: 1px solid {Theme.BORDER};
            """)
            
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            # 任务ID
            id_label = QLabel(task_id)
            id_label.setFixedWidth(120)
            id_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; padding: 12px 16px;")
            row_layout.addWidget(id_label)
            
            # 链接
            link_label = QLabel(link)
            link_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; padding: 12px 16px;")
            link_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row_layout.addWidget(link_label)
            
            # 状态
            status_layout = QHBoxLayout()
            status_layout.setSpacing(6)
            status_dot = QLabel("●")
            status_dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            status_text = QLabel(status)
            status_text.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")
            status_layout.addWidget(status_dot)
            status_layout.addWidget(status_text)
            status_layout.addStretch()
            
            status_widget = QWidget()
            status_widget.setFixedWidth(100)
            status_widget.setLayout(status_layout)
            row_layout.addWidget(status_widget)
            
            # 进度
            progress_widget = QWidget()
            progress_widget.setFixedWidth(150)
            progress_layout = QVBoxLayout(progress_widget)
            progress_layout.setSpacing(4)
            progress_layout.setContentsMargins(16, 12, 16, 12)
            
            progress_bar = QProgressBar()
            progress_bar.setValue(progress)
            progress_bar.setTextVisible(False)
            progress_bar.setFixedHeight(6)
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {Theme.BORDER};
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            
            progress_text = QLabel(f"{progress}%")
            progress_text.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
            
            progress_layout.addWidget(progress_bar)
            progress_layout.addWidget(progress_text)
            row_layout.addWidget(progress_widget)
            
            # 操作按钮
            ops_widget = QWidget()
            ops_widget.setFixedWidth(120)
            ops_layout = QHBoxLayout(ops_widget)
            ops_layout.setSpacing(4)
            ops_layout.setContentsMargins(16, 12, 16, 12)
            
            for op_icon, op_color in [("▶", Theme.SUCCESS), ("⏹", Theme.ERROR), ("🗑", Theme.TEXT_MUTED)]:
                op_btn = QPushButton(op_icon)
                op_btn.setFixedSize(28, 28)
                op_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {op_color};
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{
                        background-color: {op_color}20;
                    }}
                """)
                ops_layout.addWidget(op_btn)
            
            row_layout.addWidget(ops_widget)
            layout.addWidget(row)
        
        layout.addStretch()
        return table
    
    def create_chat_page(self):
        """创建AI对话页面"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 左侧会话列表
        session_card = Card()
        session_card.setFixedWidth(320)
        session_layout = QVBoxLayout(session_card)
        
        session_header = QLabel("💬 会话列表")
        session_header.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        session_layout.addWidget(session_header)
        
        # 会话项
        sessions = [
            ("会话 1", "今天 10:30", "帮我分析视频内容...", True),
            ("会话 2", "昨天 15:20", "如何配置知识库？", False),
            ("会话 3", "前天 09:15", "运维监控报警处理", False),
        ]
        
        for title, time, preview, is_active in sessions:
            session_item = self.create_session_item(title, time, preview, is_active)
            session_layout.addWidget(session_item)
        
        session_layout.addStretch()
        layout.addWidget(session_card)
        
        # 右侧聊天区域
        chat_card = Card(elevated=True)
        chat_layout = QVBoxLayout(chat_card)
        
        # 聊天头部
        chat_header = QHBoxLayout()
        chat_title = QLabel("💬 会话 1")
        chat_title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        """)
        chat_header.addWidget(chat_title)
        chat_header.addStretch()
        
        online_status = QLabel("🟢 AI助手在线")
        online_status.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 12px;")
        chat_header.addWidget(online_status)
        
        chat_layout.addLayout(chat_header)
        
        # 消息区域
        messages = QFrame()
        messages.setStyleSheet(f"background-color: {Theme.BG_CARD}; border-radius: 16px;")
        messages_layout = QVBoxLayout(messages)
        
        # 示例消息
        msg1 = self.create_message("你好，我是SuperBizAgent AI助手，有什么可以帮助你的吗？", False)
        msg2 = self.create_message("帮我分析一下这个视频的内容", True)
        msg3 = self.create_message("好的，我来为您分析视频内容。请提供视频的链接或上传视频文件。", False)
        
        messages_layout.addWidget(msg1)
        messages_layout.addWidget(msg2)
        messages_layout.addWidget(msg3)
        messages_layout.addStretch()
        
        chat_layout.addWidget(messages, 1)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            background-color: rgba(30, 41, 59, 0.6);
            border-radius: 24px;
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(36, 36)
        attach_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 18px;
            }}
        """)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText("输入消息...")
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 20px;
                padding: 12px 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.PRIMARY};
            }}
        """)
        
        send_btn = QPushButton("➤")
        send_btn.setFixedSize(36, 36)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: none;
                font-size: 18px;
            }}
        """)
        
        input_layout.addWidget(attach_btn)
        input_layout.addWidget(input_field, 1)
        input_layout.addWidget(send_btn)
        
        chat_layout.addWidget(input_frame)
        layout.addWidget(chat_card, 1)
        
        return page
    
    def create_session_item(self, title, time, preview, is_active):
        """创建会话项"""
        item = QFrame()
        bg_color = f"rgba(0, 102, 255, 0.15)" if is_active else "transparent"
        border_color = Theme.PRIMARY if is_active else "transparent"
        
        item.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        layout = QHBoxLayout(item)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)
        
        # 头像
        avatar = QLabel("💬")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet(f"""
            background-color: {Theme.PRIMARY if is_active else Theme.BORDER};
            border-radius: 10px;
            font-size: 16px;
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 内容
        content = QVBoxLayout()
        content.setSpacing(4)
        
        top_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: {'600' if is_active else '500'};
        """)
        
        time_label = QLabel(time)
        time_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        
        top_row.addWidget(title_label)
        top_row.addStretch()
        top_row.addWidget(time_label)
        
        preview_label = QLabel(preview)
        preview_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY if is_active else Theme.TEXT_MUTED};
            font-size: 12px;
        """)
        
        content.addLayout(top_row)
        content.addWidget(preview_label)
        
        layout.addWidget(avatar)
        layout.addLayout(content, 1)
        
        return item
    
    def create_message(self, text, is_user):
        """创建消息气泡"""
        msg = QFrame()
        
        if is_user:
            msg.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
                    border-radius: 18px;
                    border-bottom-right-radius: 4px;
                }}
            """)
        else:
            msg.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_CARD};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                }}
            """)
        
        layout = QHBoxLayout(msg)
        layout.setContentsMargins(16, 12, 16, 12)
        
        if not is_user:
            avatar = QLabel("🤖")
            avatar.setFixedSize(32, 32)
            avatar.setStyleSheet(f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.ACCENT}, stop:1 {Theme.PRIMARY});
                border-radius: 8px;
                font-size: 14px;
            """)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(avatar)
        
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 14px;
            line-height: 1.5;
        """)
        text_label.setMaximumWidth(500)
        
        layout.addWidget(text_label)
        
        if is_user:
            layout.addStretch()
        
        # 包装在水平布局中
        wrapper = QHBoxLayout()
        if is_user:
            wrapper.addStretch()
            wrapper.addWidget(msg)
        else:
            wrapper.addWidget(msg)
            wrapper.addStretch()
        
        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper)
        return wrapper_widget
    
    def create_knowledge_page(self):
        """创建知识库页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📚 知识库")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        card = Card(elevated=True)
        card_layout = QVBoxLayout(card)
        
        content = QLabel("知识库功能开发中...")
        content.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        card_layout.addWidget(content)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return page
    
    def create_link_page(self):
        """创建链接分析页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🔗 链接分析")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        card = Card(elevated=True)
        card_layout = QVBoxLayout(card)
        
        content = QLabel("链接分析功能开发中...")
        content.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        card_layout.addWidget(content)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return page
    
    def create_ops_page(self):
        """创建运维监控页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📊 运维监控")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        card = Card(elevated=True)
        card_layout = QVBoxLayout(card)
        
        content = QLabel("运维监控功能开发中...")
        content.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        card_layout.addWidget(content)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return page
    
    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("⚙️ 系统设置")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        card = Card(elevated=True)
        card_layout = QVBoxLayout(card)
        
        content = QLabel("系统设置功能开发中...")
        content.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        card_layout.addWidget(content)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return page
    
    def apply_theme(self):
        """应用主题"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Theme.BG_DARK};
            }}
            QWidget {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
