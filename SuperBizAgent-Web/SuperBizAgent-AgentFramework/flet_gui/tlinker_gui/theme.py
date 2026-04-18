#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLink GUI 主题配置 - 科技浅色透明蓝风格
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QLinearGradient, QBrush, QFont, QFontDatabase
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


class Theme:
    """科技浅色透明蓝配色方案"""
    
    # 主色调
    PRIMARY = "#1890FF"           # 主蓝色
    PRIMARY_LIGHT = "#36CFC9"     # 浅青蓝
    PRIMARY_DARK = "#096DD9"      # 深蓝
    
    # 背景色
    BG_MAIN_START = "#F5F9FF"     # 渐变起始
    BG_MAIN_END = "#E8F0FE"       # 渐变结束
    BG_CARD = "#FFFFFFE0"         # 卡片白底半透明
    BG_GLASS = "#F0F5FFC0"        # 玻璃效果
    BG_INPUT = "#FAFBFF"          # 输入框背景
    
    # 边框色
    BORDER_LIGHT = "#D6E4FF"      # 浅蓝边框
    BORDER_FOCUS = "#1890FF"      # 聚焦边框
    BORDER_CARD = "#E8E8E8"       # 卡片边框
    
    # 文字色
    TEXT_PRIMARY = "#262626"      # 主文字
    TEXT_SECONDARY = "#595959"    # 次要文字
    TEXT_MUTED = "#8C8C8C"        # 淡化文字
    TEXT_WHITE = "#FFFFFF"        # 白色文字
    
    # 功能色
    SUCCESS = "#52C41A"
    WARNING = "#FAAD14"
    ERROR = "#F5222D"
    INFO = "#1890FF"
    
    # 平台标签色
    XIAOHONGSHU = "#FF2442"       # 小红书红
    DOUYIN = "#000000"            # 抖音黑
    BILIBILI = "#00A1D6"          # B站蓝
    WEIBO = "#E6162D"             # 微博红
    
    # 圆角
    RADIUS_SMALL = 6
    RADIUS_MEDIUM = 8
    RADIUS_LARGE = 12
    RADIUS_XLARGE = 16
    
    # 阴影
    SHADOW_COLOR = QColor(0, 0, 0, 25)
    SHADOW_BLUR = 20
    SHADOW_OFFSET = (0, 4)


class StyleSheet:
    """QSS样式片段"""
    
    @staticmethod
    def get_card_style():
        """卡片容器样式"""
        return f"""
            QWidget#card {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_CARD};
                border-radius: {Theme.RADIUS_LARGE}px;
            }}
        """
    
    @staticmethod
    def get_glass_card_style():
        """玻璃卡片样式"""
        return f"""
            QWidget#glassCard {{
                background-color: {Theme.BG_GLASS};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_LARGE}px;
            }}
        """
    
    @staticmethod
    def get_primary_button_style():
        """主按钮样式 - 渐变蓝"""
        return f"""
            QPushButton#primaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.PRIMARY_LIGHT});
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: {Theme.RADIUS_MEDIUM}px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton#primaryButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY_DARK}, stop:1 {Theme.PRIMARY});
            }}
            QPushButton#primaryButton:pressed {{
                background: {Theme.PRIMARY_DARK};
            }}
            QPushButton#primaryButton:disabled {{
                background: #BFBFBF;
                color: #FFFFFF;
            }}
        """
    
    @staticmethod
    def get_secondary_button_style():
        """次要按钮样式"""
        return f"""
            QPushButton#secondaryButton {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_MEDIUM}px;
                padding: 10px 24px;
                font-size: 14px;
            }}
            QPushButton#secondaryButton:hover {{
                border-color: {Theme.PRIMARY};
                color: {Theme.PRIMARY};
            }}
        """
    
    @staticmethod
    def get_input_style():
        """输入框样式"""
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
                background-color: #FFFFFF;
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
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_SMALL}px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.6;
            }}
            QTextEdit:focus {{
                border: 2px solid {Theme.PRIMARY};
                background-color: #FFFFFF;
            }}
        """
    
    @staticmethod
    def get_progress_bar_style():
        """进度条样式"""
        return f"""
            QProgressBar {{
                background-color: {Theme.BORDER_LIGHT};
                border: none;
                border-radius: {Theme.RADIUS_SMALL // 2}px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.PRIMARY_LIGHT});
                border-radius: {Theme.RADIUS_SMALL // 2}px;
            }}
        """
    
    @staticmethod
    def get_nav_button_style(active=False):
        """导航按钮样式"""
        if active:
            return f"""
                QPushButton#navButton {{
                    background-color: {Theme.PRIMARY}15;
                    color: {Theme.PRIMARY};
                    border: none;
                    border-left: 3px solid {Theme.PRIMARY};
                    border-radius: 0px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    text-align: left;
                }}
            """
        else:
            return f"""
                QPushButton#navButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_SECONDARY};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    padding: 12px 20px;
                    font-size: 14px;
                    text-align: left;
                }}
                QPushButton#navButton:hover {{
                    background-color: {Theme.PRIMARY}08;
                    color: {Theme.TEXT_PRIMARY};
                }}
            """
    
    @staticmethod
    def get_log_text_edit_style():
        """日志区域样式 - 深色底"""
        return f"""
            QTextEdit#logArea {{
                background-color: #1E1E2E;
                color: #E8E8E8;
                border: none;
                border-radius: {Theme.RADIUS_MEDIUM}px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
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
                background-color: {Theme.BORDER_LIGHT};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {Theme.PRIMARY}80;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """


class ShadowEffect:
    """阴影效果工具"""
    
    @staticmethod
    def apply_card_shadow(widget: QWidget, blur_radius: int = 20, 
                         offset: tuple = (0, 4)):
        """应用卡片阴影"""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(Theme.SHADOW_COLOR)
        shadow.setXOffset(offset[0])
        shadow.setYOffset(offset[1])
        widget.setGraphicsEffect(shadow)
        return shadow
    
    @staticmethod
    def apply_glow_shadow(widget: QWidget, color: str = Theme.PRIMARY):
        """应用发光阴影"""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(color))
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        widget.setGraphicsEffect(shadow)
        return shadow


class PlatformBadge:
    """平台标签样式"""
    
    STYLES = {
        'xiaohongshu': f"""
            background-color: {Theme.XIAOHONGSHU}15;
            color: {Theme.XIAOHONGSHU};
            border: 1px solid {Theme.XIAOHONGSHU}40;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: 600;
        """,
        'douyin': f"""
            background-color: #00000015;
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid #00000040;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: 600;
        """,
        'bilibili': f"""
            background-color: {Theme.BILIBILI}15;
            color: {Theme.BILIBILI};
            border: 1px solid {Theme.BILIBILI}40;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: 600;
        """,
        'weibo': f"""
            background-color: {Theme.WEIBO}15;
            color: {Theme.WEIBO};
            border: 1px solid {Theme.WEIBO}40;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: 600;
        """,
        'general': f"""
            background-color: {Theme.INFO}15;
            color: {Theme.INFO};
            border: 1px solid {Theme.INFO}40;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: 600;
        """
    }
    
    @classmethod
    def get_style(cls, platform: str) -> str:
        """获取平台标签样式"""
        return cls.STYLES.get(platform.lower(), cls.STYLES['general'])


class LogColors:
    """日志颜色配置"""
    
    DEBUG = "#8C8C8C"      # 灰色
    INFO = "#1890FF"       # 蓝色
    SUCCESS = "#52C41A"    # 绿色
    WARNING = "#FAAD14"    # 黄色
    ERROR = "#F5222D"      # 红色
    
    @classmethod
    def get_color_html(cls, level: str) -> str:
        """获取HTML颜色"""
        colors = {
            'debug': cls.DEBUG,
            'info': cls.INFO,
            'success': cls.SUCCESS,
            'warning': cls.WARNING,
            'error': cls.ERROR,
        }
        return colors.get(level.lower(), cls.INFO)


# 全局样式组合
def get_global_stylesheet() -> str:
    """获取全局样式表"""
    styles = [
        StyleSheet.get_input_style(),
        StyleSheet.get_text_edit_style(),
        StyleSheet.get_progress_bar_style(),
        StyleSheet.get_log_text_edit_style(),
        StyleSheet.get_scrollbar_style(),
        StyleSheet.get_primary_button_style(),
        StyleSheet.get_secondary_button_style(),
        StyleSheet.get_card_style(),
        StyleSheet.get_glass_card_style(),
    ]
    return "\n".join(styles)
