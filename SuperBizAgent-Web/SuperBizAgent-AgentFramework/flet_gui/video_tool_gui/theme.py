#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理工具GUI主题配置
科技浅蓝风格 - 与原GUI保持一致
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


class Theme:
    """科技浅蓝配色方案 - 与原video_gui.py保持一致"""
    
    # 主色调
    PRIMARY = "#0066cc"           # 主蓝色
    PRIMARY_LIGHT = "#4d94ff"     # 浅蓝
    PRIMARY_DARK = "#004c99"      # 深蓝
    
    # 背景色
    BG_MAIN = "#f0f4f8"           # 主背景
    BG_WHITE = "#ffffff"          # 白色背景
    BG_INPUT = "#f9f9f9"          # 输入框背景
    BG_CARD = "#ffffff"           # 卡片背景
    BG_SIDEBAR = "#ffffff"        # 侧边栏背景
    
    # 边框色
    BORDER = "#e0e0e0"            # 普通边框
    BORDER_FOCUS = "#0066cc"      # 聚焦边框
    BORDER_LIGHT = "#e8e8e8"      # 浅色边框
    
    # 文字色
    TEXT_PRIMARY = "#333333"      # 主文字
    TEXT_SECONDARY = "#666666"    # 次要文字
    TEXT_MUTED = "#999999"        # 淡化文字
    TEXT_WHITE = "#ffffff"        # 白色文字
    
    # 状态色
    SUCCESS = "#00cc66"           # 成功绿
    WARNING = "#ff9900"           # 警告橙
    ERROR = "#ff3333"             # 错误红
    INFO = "#0066cc"              # 信息蓝
    
    # 导航按钮颜色
    NAV_ACTIVE_BG = "#0066cc"     # 选中背景
    NAV_ACTIVE_FG = "#ffffff"     # 选中文字
    NAV_INACTIVE_BG = "#f0f4f8"   # 未选中背景
    NAV_INACTIVE_FG = "#333333"   # 未选中文字
    
    # 字体
    FONT_FAMILY = "Microsoft YaHei"
    FONT_FAMILY_EN = "Consolas"
    
    # 字体大小
    FONT_SIZE_SMALL = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_MEDIUM = 11
    FONT_SIZE_LARGE = 14
    FONT_SIZE_TITLE = 18
    
    # 间距
    PADDING_SMALL = 5
    PADDING_NORMAL = 10
    PADDING_LARGE = 15
    PADDING_XLARGE = 20
    
    # 圆角
    RADIUS_SMALL = 4
    RADIUS_NORMAL = 6
    RADIUS_LARGE = 8


class StyleSheet:
    """QSS样式片段"""
    
    @staticmethod
    def get_main_window_style():
        """主窗口样式"""
        return f"""
            QMainWindow {{
                background-color: {Theme.BG_MAIN};
            }}
        """
    
    @staticmethod
    def get_card_style():
        """卡片样式"""
        return f"""
            QFrame#card {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_NORMAL}px;
            }}
        """
    
    @staticmethod
    def get_input_style():
        """输入框样式"""
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_WHITE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 8px 12px;
                font-family: "{Theme.FONT_FAMILY}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {Theme.TEXT_MUTED};
            }}
        """
    
    @staticmethod
    def get_text_edit_style():
        """文本编辑框样式"""
        return f"""
            QTextEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 10px;
                font-family: "{Theme.FONT_FAMILY}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
        """
    
    @staticmethod
    def get_primary_button_style():
        """主按钮样式"""
        return f"""
            QPushButton#primaryButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 8px 20px;
                font-family: "{Theme.FONT_FAMILY}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
            }}
            QPushButton#primaryButton:hover {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
            QPushButton#primaryButton:pressed {{
                background-color: {Theme.PRIMARY_DARK};
            }}
        """
    
    @staticmethod
    def get_secondary_button_style():
        """次要按钮样式"""
        return f"""
            QPushButton#secondaryButton {{
                background-color: {Theme.BG_WHITE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 8px 20px;
                font-family: "{Theme.FONT_FAMILY}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QPushButton#secondaryButton:hover {{
                border-color: {Theme.PRIMARY};
                color: {Theme.PRIMARY};
            }}
        """
    
    @staticmethod
    def get_nav_button_style(active=False):
        """导航按钮样式"""
        if active:
            return f"""
                QPushButton#navButton {{
                    background-color: {Theme.NAV_ACTIVE_BG};
                    color: {Theme.NAV_ACTIVE_FG};
                    border: none;
                    border-radius: {Theme.RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-family: "{Theme.FONT_FAMILY}";
                    font-size: {Theme.FONT_SIZE_MEDIUM}px;
                    font-weight: bold;
                }}
            """
        else:
            return f"""
                QPushButton#navButton {{
                    background-color: {Theme.NAV_INACTIVE_BG};
                    color: {Theme.NAV_INACTIVE_FG};
                    border: none;
                    border-radius: {Theme.RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-family: "{Theme.FONT_FAMILY}";
                    font-size: {Theme.FONT_SIZE_MEDIUM}px;
                }}
                QPushButton#navButton:hover {{
                    background-color: {Theme.PRIMARY_LIGHT}20;
                }}
            """
    
    @staticmethod
    def get_log_text_edit_style():
        """日志区域样式"""
        return f"""
            QTextEdit#logArea {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 10px;
                font-family: "{Theme.FONT_FAMILY_EN}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
                line-height: 1.5;
            }}
        """
    
    @staticmethod
    def get_scrollbar_style():
        """滚动条样式"""
        return f"""
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {Theme.BORDER};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {Theme.PRIMARY}80;
            }}
        """
    
    @staticmethod
    def get_combo_box_style():
        """下拉框样式"""
        return f"""
            QComboBox {{
                background-color: {Theme.BG_WHITE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 6px 10px;
                font-family: "{Theme.FONT_FAMILY}";
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QComboBox:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """
    
    @staticmethod
    def get_progress_bar_style():
        """进度条样式"""
        return f"""
            QProgressBar {{
                background-color: {Theme.BORDER};
                border: none;
                border-radius: 3px;
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.PRIMARY};
                border-radius: 3px;
            }}
        """
    
    @staticmethod
    def get_tab_widget_style():
        """标签页样式"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_NORMAL}px;
                background-color: {Theme.BG_WHITE};
            }}
            QTabBar::tab {{
                background-color: {Theme.BG_MAIN};
                color: {Theme.TEXT_SECONDARY};
                padding: 8px 16px;
                border-top-left-radius: {Theme.RADIUS_SMALL}px;
                border-top-right-radius: {Theme.RADIUS_SMALL}px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_WHITE};
            }}
        """


class ShadowEffect:
    """阴影效果工具"""
    
    @staticmethod
    def apply_card_shadow(widget: QWidget, blur_radius: int = 15):
        """应用卡片阴影"""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        widget.setGraphicsEffect(shadow)
        return shadow


def get_global_stylesheet() -> str:
    """获取全局样式表"""
    styles = [
        StyleSheet.get_main_window_style(),
        StyleSheet.get_card_style(),
        StyleSheet.get_input_style(),
        StyleSheet.get_text_edit_style(),
        StyleSheet.get_primary_button_style(),
        StyleSheet.get_secondary_button_style(),
        StyleSheet.get_log_text_edit_style(),
        StyleSheet.get_scrollbar_style(),
        StyleSheet.get_combo_box_style(),
        StyleSheet.get_progress_bar_style(),
        StyleSheet.get_tab_widget_style(),
    ]
    return "\n".join(styles)
