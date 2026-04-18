#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主题配置 - 模仿豆包/DeskClaw 现代风格
浅色/深色主题 Token
"""

class Theme:
    """设计 Token"""
    
    # 浅色主题
    LIGHT = {
        # 主色
        "primary": "#0066cc",
        "primary_hover": "#0055aa",
        "primary_pressed": "#004488",
        
        # 背景
        "bg_main": "#f5f6f7",
        "bg_card": "#ffffff",
        "bg_sidebar": "#f0f1f3",
        "bg_hover": "#e8e9eb",
        
        # 文字
        "text_primary": "#1d1d1f",
        "text_secondary": "#6e6e73",
        "text_muted": "#8e8e93",
        
        # 边框
        "border": "#d1d1d6",
        "border_light": "#e5e5ea",
        
        # 状态
        "success": "#34c759",
        "warning": "#ff9500",
        "error": "#ff3b30",
        
        # 圆角
        "radius_small": 6,
        "radius_normal": 8,
        "radius_large": 12,
        
        # 间距
        "spacing_xs": 4,
        "spacing_sm": 8,
        "spacing_md": 12,
        "spacing_lg": 16,
        "spacing_xl": 20,
        
        # 字体
        "font_family": "PingFang SC, Microsoft YaHei, sans-serif",
        "font_size_xs": 11,
        "font_size_sm": 12,
        "font_size_md": 13,
        "font_size_lg": 14,
        "font_size_xl": 16,
    }
    
    # 深色主题
    DARK = {
        # 主色
        "primary": "#0a84ff",
        "primary_hover": "#0070e0",
        "primary_pressed": "#0060c0",
        
        # 背景
        "bg_main": "#1a1a1e",
        "bg_card": "#252529",
        "bg_sidebar": "#1e1e22",
        "bg_hover": "#2a2a2f",
        
        # 文字
        "text_primary": "#f5f5f7",
        "text_secondary": "#98989d",
        "text_muted": "#6e6e73",
        
        # 边框
        "border": "#3f3f46",
        "border_light": "#2c2c30",
        
        # 状态
        "success": "#30d158",
        "warning": "#ff9f0a",
        "error": "#ff453a",
        
        # 圆角和间距同浅色
        "radius_small": 6,
        "radius_normal": 8,
        "radius_large": 12,
        "spacing_xs": 4,
        "spacing_sm": 8,
        "spacing_md": 12,
        "spacing_lg": 16,
        "spacing_xl": 20,
        
        # 字体
        "font_family": "PingFang SC, Microsoft YaHei, sans-serif",
        "font_size_xs": 11,
        "font_size_sm": 12,
        "font_size_md": 13,
        "font_size_lg": 14,
        "font_size_xl": 16,
    }
    
    # 当前主题（默认浅色）
    current = LIGHT.copy()
    
    @classmethod
    def use_dark_theme(cls):
        """切换到深色主题"""
        cls.current = cls.DARK.copy()
    
    @classmethod
    def use_light_theme(cls):
        """切换到浅色主题"""
        cls.current = cls.LIGHT.copy()


# QSS 样式表模板
QSS_TEMPLATE = """
/* 全局样式 */
* {{
    font-family: "{font_family}";
    font-size: {font_size_md}px;
    color: {text_primary};
    background-color: {bg_main};
}}

/* 主窗口 */
QMainWindow {{
    background-color: {bg_main};
}}

/* 侧边栏 */
QWidget#sidebar {{
    background-color: {bg_sidebar};
    border-right: 1px solid {border_light};
}}

/* 导航列表 */
QListWidget#nav_list {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget#nav_list::item {{
    height: 44px;
    border-radius: {radius_normal}px;
    margin: 2px 8px;
    padding-left: 12px;
}}

QListWidget#nav_list::item:hover {{
    background-color: {bg_hover};
}}

QListWidget#nav_list::item:selected {{
    background-color: {primary};
    color: white;
    font-weight: bold;
}}

/* 卡片容器 */
QFrame#card {{
    background-color: {bg_card};
    border: 1px solid {border_light};
    border-radius: {radius_large}px;
    padding: {spacing_lg}px;
}}

/* 主按钮 */
QPushButton#primaryButton {{
    background-color: {primary};
    color: white;
    border: none;
    border-radius: {radius_normal}px;
    padding: 8px 20px;
    font-weight: bold;
}}

QPushButton#primaryButton:hover {{
    background-color: {primary_hover};
}}

QPushButton#primaryButton:pressed {{
    background-color: {primary_pressed};
}}

QPushButton#primaryButton:disabled {{
    background-color: {border};
    color: {text_muted};
}}

/* 次要按钮 */
QPushButton#secondaryButton {{
    background-color: transparent;
    color: {primary};
    border: 1px solid {primary};
    border-radius: {radius_normal}px;
    padding: 7px 19px;
    font-weight: bold;
}}

QPushButton#secondaryButton:hover {{
    background-color: {primary}20;
}}

QPushButton#secondaryButton:pressed {{
    background-color: {primary}40;
}}

/* 普通按钮 */
QPushButton {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: {radius_normal}px;
    padding: 6px 16px;
}}

QPushButton:hover {{
    background-color: {bg_hover};
    border-color: {primary};
}}

/* 输入框 */
QLineEdit, QPlainTextEdit, QTextEdit {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: {radius_normal}px;
    padding: 6px 10px;
    selection-background-color: {primary};
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {primary};
}}

/* 进度条 */
QProgressBar {{
    background-color: {bg_hover};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {primary};
    border-radius: 4px;
}}

/* 滚动条 */
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {border};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {text_muted};
}}

/* 分组框 */
QGroupBox {{
    font-weight: bold;
    border: 1px solid {border};
    border-radius: {radius_large}px;
    margin-top: 12px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {text_primary};
}}

/* 标签页 */
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: {radius_large}px;
    background-color: {bg_card};
}}

QTabBar::tab {{
    background-color: {bg_hover};
    border: 1px solid {border};
    border-bottom: none;
    border-top-left-radius: {radius_normal}px;
    border-top-right-radius: {radius_normal}px;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {bg_card};
    color: {primary};
    font-weight: bold;
}}

/* 状态栏 */
QStatusBar {{
    background-color: {bg_card};
    border-top: 1px solid {border_light};
}}

/* 工具提示 */
QToolTip {{
    background-color: {bg_card};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: {radius_normal}px;
    padding: 4px 8px;
}}

/* 下拉框 */
QComboBox {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: {radius_normal}px;
    padding: 6px 10px;
}}

QComboBox:hover {{
    border-color: {primary};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: {radius_normal}px;
    selection-background-color: {primary};
    outline: none;
}}

/* 复选框 */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border};
    border-radius: 4px;
    background-color: {bg_card};
}}

QCheckBox::indicator:checked {{
    background-color: {primary};
    border-color: {primary};
}}

/* 日志区域 */
QPlainTextEdit#logArea {{
    background-color: {bg_main};
    border: 1px solid {border};
    border-radius: {radius_normal}px;
    font-family: "Consolas, Monaco, monospace";
    font-size: {font_size_sm}px;
    padding: 8px;
}}
"""


def get_stylesheet(theme_name="light"):
    """获取样式表"""
    if theme_name == "dark":
        Theme.use_dark_theme()
    else:
        Theme.use_light_theme()
    
    tokens = Theme.current
    return QSS_TEMPLATE.format(**tokens)
