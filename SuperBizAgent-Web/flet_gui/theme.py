#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flet GUI 主题配置 - 科技蓝风格
特点：卡片化、透明化、立体化、圆角化
"""

import flet as ft


class TechBlueTheme:
    """科技蓝主题配色"""
    
    # 主色调
    PRIMARY = "#0066FF"           # 科技蓝
    PRIMARY_DARK = "#0052CC"      # 深蓝
    PRIMARY_LIGHT = "#4D94FF"     # 浅蓝
    ACCENT = "#00D4FF"            # 青色强调
    
    # 背景色
    BG_DARK = "#0A0E1A"           # 深色背景
    BG_DARKER = "#050810"         # 更深背景
    BG_CARD = "#111827"           # 卡片背景
    BG_CARD_HOVER = "#1A2234"     # 卡片悬停
    BG_TRANSPARENT = "#111827CC"  # 半透明背景 (80%透明度)
    BG_GLASS = "#11182780"        # 玻璃效果背景 (50%透明度)
    BG_GLASS_LIGHT = "#1A223460"  # 轻玻璃效果
    
    # 文字颜色
    TEXT_PRIMARY = "#FFFFFF"      # 主文字
    TEXT_SECONDARY = "#94A3B8"    # 次要文字
    TEXT_MUTED = "#64748B"        # 淡化文字
    
    # 边框和阴影
    BORDER = "#1E293B"            # 边框色
    BORDER_LIGHT = "#334155"      # 浅色边框
    BORDER_ACTIVE = "#0066FF"     # 激活边框
    SHADOW = "#00000060"          # 阴影色
    SHADOW_LIGHT = "#00000030"    # 浅色阴影
    GLOW = "#0066FF40"            # 发光效果
    GLOW_ACCENT = "#00D4FF40"     # 青色发光
    
    # 状态色
    SUCCESS = "#10B981"           # 成功绿
    WARNING = "#F59E0B"           # 警告黄
    ERROR = "#EF4444"             # 错误红
    INFO = "#3B82F6"              # 信息蓝
    
    # 渐变
    GRADIENT_PRIMARY = ["#0066FF", "#00D4FF"]
    GRADIENT_DARK = ["#0A0E1A", "#111827"]
    GRADIENT_CARD = ["#111827", "#1A2234"]
    GRADIENT_GLASS = ["#11182780", "#1A223480"]


class CardStyles:
    """卡片样式"""
    
    @staticmethod
    def get_card_style():
        """获取标准卡片样式"""
        return {
            "bgcolor": TechBlueTheme.BG_CARD,
            "border_radius": 20,
            "border": ft.border.all(1, TechBlueTheme.BORDER),
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=TechBlueTheme.SHADOW,
                offset=ft.Offset(0, 4)
            ),
            "padding": 24,
        }
    
    @staticmethod
    def get_glass_card_style():
        """获取玻璃拟态卡片样式"""
        return {
            "bgcolor": TechBlueTheme.BG_GLASS,
            "border_radius": 24,
            "border": ft.border.all(1, TechBlueTheme.BORDER_LIGHT),
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=40,
                color=TechBlueTheme.GLOW,
                offset=ft.Offset(0, 0)
            ),
            "padding": 28,
        }
    
    @staticmethod
    def get_elevated_card_style():
        """获取立体卡片样式"""
        return {
            "bgcolor": TechBlueTheme.BG_CARD,
            "border_radius": 20,
            "border": ft.border.all(1, TechBlueTheme.BORDER),
            "shadow": ft.BoxShadow(
                spread_radius=2,
                blur_radius=30,
                color=TechBlueTheme.SHADOW,
                offset=ft.Offset(0, 10)
            ),
            "padding": 24,
        }
    
    @staticmethod
    def get_hover_card_style():
        """获取悬停效果卡片样式"""
        return {
            "bgcolor": TechBlueTheme.BG_CARD,
            "border_radius": 16,
            "border": ft.border.all(1, TechBlueTheme.BORDER),
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=TechBlueTheme.SHADOW_LIGHT,
                offset=ft.Offset(0, 4)
            ),
            "padding": 20,
            "animate": ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        }


class ButtonStyles:
    """按钮样式"""
    
    @staticmethod
    def get_primary_button():
        """主按钮样式"""
        return ft.ButtonStyle(
            color=TechBlueTheme.TEXT_PRIMARY,
            bgcolor={
                ft.ControlState.DEFAULT: TechBlueTheme.PRIMARY,
                ft.ControlState.HOVERED: TechBlueTheme.PRIMARY_LIGHT,
            },
            shadow_color=TechBlueTheme.GLOW,
            elevation={
                ft.ControlState.DEFAULT: 6,
                ft.ControlState.HOVERED: 12,
            },
            padding=ft.padding.symmetric(horizontal=28, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=14),
        )
    
    @staticmethod
    def get_secondary_button():
        """次要按钮样式"""
        return ft.ButtonStyle(
            color=TechBlueTheme.PRIMARY,
            bgcolor={
                ft.ControlState.DEFAULT: "transparent",
                ft.ControlState.HOVERED: TechBlueTheme.BG_CARD_HOVER,
            },
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1, TechBlueTheme.PRIMARY),
                ft.ControlState.HOVERED: ft.BorderSide(1, TechBlueTheme.PRIMARY_LIGHT),
            },
            padding=ft.padding.symmetric(horizontal=28, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=14),
        )
    
    @staticmethod
    def get_icon_button():
        """图标按钮样式"""
        return ft.ButtonStyle(
            color=TechBlueTheme.TEXT_SECONDARY,
            bgcolor={
                ft.ControlState.DEFAULT: "transparent",
                ft.ControlState.HOVERED: TechBlueTheme.BG_CARD_HOVER,
            },
            padding=12,
            shape=ft.CircleBorder(),
        )
    
    @staticmethod
    def get_gradient_button():
        """渐变按钮样式"""
        return ft.ButtonStyle(
            color=TechBlueTheme.TEXT_PRIMARY,
            padding=ft.padding.symmetric(horizontal=32, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=16),
            shadow_color=TechBlueTheme.GLOW,
            elevation={
                ft.ControlState.DEFAULT: 8,
                ft.ControlState.HOVERED: 16,
            },
        )


class InputStyles:
    """输入框样式"""
    
    @staticmethod
    def get_text_field_style():
        """文本输入框样式"""
        return ft.TextStyle(
            color=TechBlueTheme.TEXT_PRIMARY,
            size=14,
        )
    
    @staticmethod
    def get_text_field_border():
        """输入框边框样式"""
        return ft.InputBorder.OUTLINE
    
    @staticmethod
    def get_text_field_theme():
        """输入框主题"""
        return ft.TextTheme(
            body_large=ft.TextStyle(color=TechBlueTheme.TEXT_PRIMARY),
            body_medium=ft.TextStyle(color=TechBlueTheme.TEXT_SECONDARY),
        )


class Typography:
    """排版样式"""
    
    # 标题
    H1 = ft.TextStyle(
        size=36,
        weight=ft.FontWeight.BOLD,
        color=TechBlueTheme.TEXT_PRIMARY,
    )
    
    H2 = ft.TextStyle(
        size=28,
        weight=ft.FontWeight.BOLD,
        color=TechBlueTheme.TEXT_PRIMARY,
    )
    
    H3 = ft.TextStyle(
        size=22,
        weight=ft.FontWeight.W_600,
        color=TechBlueTheme.TEXT_PRIMARY,
    )
    
    H4 = ft.TextStyle(
        size=18,
        weight=ft.FontWeight.W_600,
        color=TechBlueTheme.TEXT_PRIMARY,
    )
    
    # 正文
    BODY_LARGE = ft.TextStyle(
        size=16,
        weight=ft.FontWeight.NORMAL,
        color=TechBlueTheme.TEXT_PRIMARY,
    )
    
    BODY = ft.TextStyle(
        size=14,
        weight=ft.FontWeight.NORMAL,
        color=TechBlueTheme.TEXT_SECONDARY,
    )
    
    CAPTION = ft.TextStyle(
        size=12,
        weight=ft.FontWeight.NORMAL,
        color=TechBlueTheme.TEXT_MUTED,
    )


def create_gradient_container(
    content,
    colors,
    begin=None,
    end=None,
    border_radius=20,
    padding=24
):
    """创建渐变容器"""
    return ft.Container(
        content=content,
        border_radius=border_radius,
        padding=padding,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left if begin is None else begin,
            end=ft.alignment.bottom_right if end is None else end,
            colors=colors,
        ),
    )


def create_glass_card(
    content,
    width=None,
    height=None,
    expand=False
):
    """创建玻璃拟态卡片"""
    style = CardStyles.get_glass_card_style()
    return ft.Container(
        content=content,
        width=width,
        height=height,
        expand=expand,
        **style
    )


def create_elevated_card(
    content,
    width=None,
    height=None,
    expand=False
):
    """创建立体卡片"""
    style = CardStyles.get_elevated_card_style()
    return ft.Container(
        content=content,
        width=width,
        height=height,
        expand=expand,
        **style
    )


def create_hover_card(
    content,
    width=None,
    height=None,
    expand=False,
    on_hover=None
):
    """创建悬停效果卡片"""
    style = CardStyles.get_hover_card_style()
    return ft.Container(
        content=content,
        width=width,
        height=height,
        expand=expand,
        on_hover=on_hover,
        **style
    )


def create_status_indicator(status: str, text: str):
    """创建状态指示器"""
    color_map = {
        "success": TechBlueTheme.SUCCESS,
        "warning": TechBlueTheme.WARNING,
        "error": TechBlueTheme.ERROR,
        "info": TechBlueTheme.INFO,
        "pending": TechBlueTheme.TEXT_MUTED,
    }
    color = color_map.get(status, TechBlueTheme.TEXT_MUTED)
    
    return ft.Row(
        [
            ft.Container(
                width=10,
                height=10,
                border_radius=5,
                bgcolor=color,
                shadow=ft.BoxShadow(
                    spread_radius=3,
                    blur_radius=10,
                    color=color + "50",
                ),
            ),
            ft.Text(
                text,
                size=12,
                color=color,
                weight=ft.FontWeight.W_500,
            ),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.START,
    )


def create_divider():
    """创建分隔线"""
    return ft.Divider(
        color=TechBlueTheme.BORDER,
        thickness=1,
        height=32,
    )


def create_section_title(title: str, icon=None, action=None):
    """创建区块标题"""
    return ft.Row(
        [
            ft.Row(
                [
                    ft.Container(
                        content=icon if icon else ft.Container(),
                        padding=8,
                        border_radius=10,
                        bgcolor=TechBlueTheme.PRIMARY + "15",
                    ) if icon else ft.Container(),
                    ft.Text(
                        title,
                        style=Typography.H3,
                    ),
                ],
                spacing=12,
            ),
            ft.Container(expand=True),
            action if action else ft.Container(),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


def create_gradient_button(text: str, icon=None, on_click=None):
    """创建渐变按钮"""
    return ft.Container(
        content=ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            style=ButtonStyles.get_gradient_button(),
        ),
        border_radius=16,
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=TechBlueTheme.GRADIENT_PRIMARY,
        ),
    )


def create_badge(text: str, color: str):
    """创建徽章"""
    return ft.Container(
        content=ft.Text(
            text,
            size=11,
            color=TechBlueTheme.TEXT_PRIMARY,
            weight=ft.FontWeight.W_600,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=20,
        bgcolor=color + "30",
        border=ft.border.all(1, color + "50"),
    )


def create_icon_badge(icon, color: str, size: int = 40):
    """创建图标徽章"""
    return ft.Container(
        content=ft.Icon(icon, color=color, size=size//2),
        width=size,
        height=size,
        border_radius=size//2,
        bgcolor=color + "20",
        border=ft.border.all(2, color + "40"),
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=color + "30",
        ),
    )
