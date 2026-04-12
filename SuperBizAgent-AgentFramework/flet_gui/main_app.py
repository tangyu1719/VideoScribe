#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperBizAgent Flet GUI - 主应用
科技蓝风格，卡片化、透明化、立体化、圆角化设计
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from theme import (
    TechBlueTheme, CardStyles, ButtonStyles, Typography,
    create_glass_card, create_elevated_card, create_hover_card,
    create_status_indicator, create_divider, create_section_title,
    create_gradient_button, create_badge, create_icon_badge
)


class SuperBizAgentApp:
    """SuperBizAgent Flet应用"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page = "video"
        self.setup_page()
        self.build_ui()
    
    def setup_page(self):
        """设置页面基础配置"""
        self.page.title = "SuperBizAgent - AI智能助手"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = TechBlueTheme.BG_DARK
        self.page.padding = 0
        self.page.window_width = 1500
        self.page.window_height = 950
        self.page.window_min_width = 1300
        self.page.window_min_height = 750
        
        # 设置字体
        self.page.fonts = {}
        
        # 设置主题
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=TechBlueTheme.PRIMARY,
                secondary=TechBlueTheme.ACCENT,
                background=TechBlueTheme.BG_DARK,
                surface=TechBlueTheme.BG_CARD,
            ),
        )
    
    def build_ui(self):
        """构建UI界面"""
        # 侧边栏
        sidebar = self.build_sidebar()
        
        # 主内容区
        self.content_area = ft.Container(
            content=self.build_video_page(),
            expand=True,
            padding=30,
            bgcolor=TechBlueTheme.BG_DARK,
        )
        
        # 整体布局
        main_layout = ft.Row(
            [
                sidebar,
                self.content_area,
            ],
            expand=True,
            spacing=0,
        )
        
        self.page.add(main_layout)
    
    def build_sidebar(self):
        """构建侧边栏"""
        # Logo区域 - 玻璃拟态效果
        logo = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.icons.SMART_TOY, color=TechBlueTheme.TEXT_PRIMARY, size=28),
                        width=48,
                        height=48,
                        border_radius=14,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=TechBlueTheme.GRADIENT_PRIMARY,
                        ),
                        shadow=ft.BoxShadow(
                            spread_radius=2,
                            blur_radius=15,
                            color=TechBlueTheme.PRIMARY + "40",
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "SuperBizAgent",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=TechBlueTheme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "AI智能助手",
                                size=12,
                                color=TechBlueTheme.TEXT_MUTED,
                            ),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=14,
            ),
            padding=24,
        )
        
        # 导航菜单
        menu_items = [
            ("视频处理", ft.icons.VIDEO_FILE, self.show_video_page, "video"),
            ("AI对话", ft.icons.CHAT, self.show_chat_page, "chat"),
            ("知识库", ft.icons.BOOK, self.show_knowledge_page, "knowledge"),
            ("链接分析", ft.icons.LINK, self.show_link_page, "link"),
            ("运维监控", ft.icons.MONITORING, self.show_ops_page, "ops"),
            ("系统设置", ft.icons.SETTINGS, self.show_settings_page, "settings"),
        ]
        
        self.menu_buttons = []
        for label, icon, handler, page_id in menu_items:
            btn = self.create_nav_button(label, icon, handler, page_id)
            self.menu_buttons.append(btn)
        
        # 更新当前选中状态
        self.update_nav_active_state()
        
        # 侧边栏整体 - 玻璃拟态效果
        sidebar = ft.Container(
            content=ft.Column(
                [
                    logo,
                    ft.Container(
                        content=create_divider(),
                        padding=ft.padding.symmetric(horizontal=20),
                    ),
                    ft.Column(self.menu_buttons, spacing=6),
                    ft.Container(expand=True),
                    # 底部状态卡片
                    ft.Container(
                        content=create_glass_card(
                            ft.Column(
                                [
                                    create_status_indicator("success", "系统正常运行"),
                                    ft.SizedBox(height=8),
                                    ft.Text(
                                        "v2.0.0",
                                        size=11,
                                        color=TechBlueTheme.TEXT_MUTED,
                                    ),
                                ],
                                spacing=0,
                            ),
                            padding=16,
                        ),
                        padding=20,
                    ),
                ],
                spacing=0,
            ),
            width=280,
            bgcolor=TechBlueTheme.BG_GLASS,
            border_radius=ft.border_radius.only(top_right=30, bottom_right=30),
            border=ft.border.all(1, TechBlueTheme.BORDER_LIGHT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=40,
                color=TechBlueTheme.SHADOW,
                offset=ft.Offset(4, 0),
            ),
        )
        
        return sidebar
    
    def create_nav_button(self, label: str, icon, handler, page_id: str):
        """创建导航按钮"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=TechBlueTheme.TEXT_SECONDARY, size=22),
                    ft.Text(
                        label,
                        size=14,
                        color=TechBlueTheme.TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=14,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border_radius=16,
            on_click=lambda e, h=handler, pid=page_id: self.handle_nav_click(e, h, pid),
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
            data=page_id,
        )
    
    def handle_nav_click(self, e, handler, page_id):
        """处理导航点击"""
        self.current_page = page_id
        self.update_nav_active_state()
        handler(e)
    
    def update_nav_active_state(self):
        """更新导航按钮激活状态"""
        for btn in self.menu_buttons:
            is_active = btn.data == self.current_page
            btn.bgcolor = TechBlueTheme.PRIMARY + "20" if is_active else "transparent"
            btn.border = ft.border.all(1, TechBlueTheme.PRIMARY if is_active else "transparent")
            
            # 更新图标和文字颜色
            row = btn.content
            icon = row.controls[0]
            text = row.controls[1]
            icon.color = TechBlueTheme.PRIMARY if is_active else TechBlueTheme.TEXT_SECONDARY
            text.color = TechBlueTheme.TEXT_PRIMARY if is_active else TechBlueTheme.TEXT_SECONDARY
            text.weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500
            
            if hasattr(btn, 'page') and btn.page:
                btn.update()
    
    def build_video_page(self):
        """构建视频处理页面"""
        # 标题栏
        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("视频处理", style=Typography.H2),
                        ft.Text("管理和处理视频下载任务", style=Typography.CAPTION),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                create_gradient_button(
                    "新建任务",
                    ft.icons.ADD,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # 统计卡片 - 立体效果
        stats_row = ft.Row(
            [
                self.build_stat_card("待处理", "12", ft.icons.PENDING_ACTIONS, TechBlueTheme.WARNING, "个任务等待"),
                self.build_stat_card("处理中", "3", ft.icons.LOOP, TechBlueTheme.INFO, "正在下载"),
                self.build_stat_card("已完成", "156", ft.icons.CHECK_CIRCLE, TechBlueTheme.SUCCESS, "本月累计"),
                self.build_stat_card("失败", "2", ft.icons.ERROR, TechBlueTheme.ERROR, "需要重试"),
            ],
            spacing=20,
        )
        
        # 任务列表 - 玻璃拟态卡片
        task_list = self.build_task_list()
        
        # 页面内容
        content = ft.Column(
            [
                header,
                ft.SizedBox(height=28),
                stats_row,
                ft.SizedBox(height=28),
                create_glass_card(
                    ft.Column(
                        [
                            create_section_title(
                                "任务列表",
                                ft.icons.LIST_ALT,
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.icons.FILTER_LIST,
                                            icon_color=TechBlueTheme.TEXT_SECONDARY,
                                            tooltip="筛选",
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.SEARCH,
                                            icon_color=TechBlueTheme.TEXT_SECONDARY,
                                            tooltip="搜索",
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ),
                            ft.SizedBox(height=20),
                            task_list,
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            expand=True,
            spacing=0,
        )
        
        return content
    
    def build_stat_card(self, title: str, value: str, icon, color: str, subtitle: str):
        """构建统计卡片"""
        return create_elevated_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(icon, color=color, size=26),
                                width=52,
                                height=52,
                                border_radius=16,
                                bgcolor=color + "15",
                                border=ft.border.all(2, color + "30"),
                                shadow=ft.BoxShadow(
                                    spread_radius=2,
                                    blur_radius=15,
                                    color=color + "20",
                                ),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(expand=True),
                            create_badge("+5%", color) if title == "已完成" else ft.Container(),
                        ],
                    ),
                    ft.SizedBox(height=16),
                    ft.Text(
                        value,
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=TechBlueTheme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        title,
                        size=14,
                        color=TechBlueTheme.TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        subtitle,
                        size=12,
                        color=TechBlueTheme.TEXT_MUTED,
                    ),
                ],
                spacing=4,
            ),
            width=220,
        )
    
    def build_task_list(self):
        """构建任务列表"""
        # 表头
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("任务ID", width=120, color=TechBlueTheme.TEXT_MUTED, size=12, weight=ft.FontWeight.W_500),
                    ft.Text("链接", expand=True, color=TechBlueTheme.TEXT_MUTED, size=12, weight=ft.FontWeight.W_500),
                    ft.Text("状态", width=100, color=TechBlueTheme.TEXT_MUTED, size=12, weight=ft.FontWeight.W_500),
                    ft.Text("进度", width=150, color=TechBlueTheme.TEXT_MUTED, size=12, weight=ft.FontWeight.W_500),
                    ft.Text("操作", width=120, color=TechBlueTheme.TEXT_MUTED, size=12, weight=ft.FontWeight.W_500),
                ],
                spacing=16,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border=ft.border.only(bottom=ft.BorderSide(1, TechBlueTheme.BORDER)),
            bgcolor=TechBlueTheme.BG_CARD + "80",
            border_radius=ft.border_radius.only(top_left=16, top_right=16),
        )
        
        # 示例任务数据
        tasks = [
            ("TASK-001", "https://douyin.com/xxx", "处理中", 65),
            ("TASK-002", "https://bilibili.com/xxx", "待处理", 0),
            ("TASK-003", "https://xiaohongshu.com/xxx", "已完成", 100),
            ("TASK-004", "https://youtube.com/xxx", "失败", 30),
        ]
        
        task_rows = []
        for i, (task_id, link, status, progress) in enumerate(tasks):
            status_color = {
                "处理中": TechBlueTheme.INFO,
                "待处理": TechBlueTheme.WARNING,
                "已完成": TechBlueTheme.SUCCESS,
                "失败": TechBlueTheme.ERROR,
            }.get(status, TechBlueTheme.TEXT_MUTED)
            
            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(task_id, width=120, color=TechBlueTheme.TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500),
                        ft.Text(
                            link,
                            expand=True,
                            color=TechBlueTheme.TEXT_SECONDARY,
                            size=13,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(
                                        width=8,
                                        height=8,
                                        border_radius=4,
                                        bgcolor=status_color,
                                    ),
                                    ft.Text(
                                        status,
                                        color=status_color,
                                        size=12,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=6,
                            ),
                            width=100,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.ProgressBar(
                                        value=progress / 100,
                                        width=120,
                                        color=status_color,
                                        bgcolor=TechBlueTheme.BORDER,
                                        height=6,
                                    ),
                                    ft.Text(
                                        f"{progress}%",
                                        size=11,
                                        color=TechBlueTheme.TEXT_MUTED,
                                    ),
                                ],
                                spacing=4,
                            ),
                            width=150,
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.PLAY_ARROW,
                                    icon_color=TechBlueTheme.SUCCESS,
                                    icon_size=20,
                                    tooltip="开始",
                                    style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.HOVERED: TechBlueTheme.SUCCESS + "15"},
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.STOP,
                                    icon_color=TechBlueTheme.ERROR,
                                    icon_size=20,
                                    tooltip="停止",
                                    style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.HOVERED: TechBlueTheme.ERROR + "15"},
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=TechBlueTheme.TEXT_MUTED,
                                    icon_size=20,
                                    tooltip="删除",
                                    style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.HOVERED: TechBlueTheme.ERROR + "15"},
                                    ),
                                ),
                            ],
                            spacing=4,
                        ),
                    ],
                    spacing=16,
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                border=ft.border.only(bottom=ft.BorderSide(1, TechBlueTheme.BORDER)) if i < len(tasks) - 1 else None,
                bgcolor=TechBlueTheme.BG_CARD + "40" if i % 2 == 0 else "transparent",
            )
            task_rows.append(row)
        
        return ft.Column(
            [header] + task_rows,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
    
    def build_chat_page(self):
        """构建AI对话页面"""
        # 左侧会话列表 - 玻璃拟态
        session_list = create_glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("会话列表", style=Typography.H3),
                            ft.IconButton(
                                icon=ft.icons.ADD,
                                icon_color=TechBlueTheme.PRIMARY,
                                tooltip="新建会话",
                                style=ft.ButtonStyle(
                                    bgcolor={ft.ControlState.HOVERED: TechBlueTheme.PRIMARY + "15"},
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.SizedBox(height=16),
                    # 会话项
                    self.build_session_item("会话 1", "今天 10:30", "帮我分析视频内容...", True),
                    self.build_session_item("会话 2", "昨天 15:20", "如何配置知识库？", False),
                    self.build_session_item("会话 3", "前天 09:15", "运维监控报警处理", False),
                ],
                spacing=10,
            ),
            width=320,
        )
        
        # 右侧聊天区域 - 玻璃拟态
        chat_area = create_glass_card(
            ft.Column(
                [
                    # 聊天标题
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    create_icon_badge(ft.icons.CHAT, TechBlueTheme.PRIMARY, 36),
                                    ft.Column(
                                        [
                                            ft.Text("会话 1", style=Typography.H4),
                                            ft.Text("AI助手在线", size=12, color=TechBlueTheme.SUCCESS),
                                        ],
                                        spacing=2,
                                    ),
                                ],
                                spacing=12,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color=TechBlueTheme.TEXT_MUTED,
                                tooltip="删除会话",
                            ),
                            ft.IconButton(
                                icon=ft.icons.MORE_VERT,
                                icon_color=TechBlueTheme.TEXT_MUTED,
                                tooltip="更多选项",
                            ),
                        ],
                    ),
                    create_divider(),
                    # 消息区域
                    ft.Container(
                        content=ft.Column(
                            [
                                self.build_chat_message(
                                    "你好，我是SuperBizAgent AI助手，有什么可以帮助你的吗？",
                                    is_user=False
                                ),
                                self.build_chat_message(
                                    "帮我分析一下这个视频的内容",
                                    is_user=True
                                ),
                                self.build_chat_message(
                                    "好的，我来为您分析视频内容。请提供视频的链接或上传视频文件。",
                                    is_user=False
                                ),
                            ],
                            spacing=20,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                    ),
                    # 输入区域
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.ATTACH_FILE,
                                    icon_color=TechBlueTheme.TEXT_SECONDARY,
                                ),
                                ft.TextField(
                                    hint_text="输入消息...",
                                    expand=True,
                                    border_radius=20,
                                    filled=True,
                                    bgcolor=TechBlueTheme.BG_CARD,
                                    border_color=TechBlueTheme.BORDER,
                                    focused_border_color=TechBlueTheme.PRIMARY,
                                    max_lines=4,
                                    min_lines=1,
                                ),
                                ft.IconButton(
                                    icon=ft.icons.SEND,
                                    icon_color=TechBlueTheme.PRIMARY,
                                    icon_size=24,
                                    style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.HOVERED: TechBlueTheme.PRIMARY + "15"},
                                    ),
                                ),
                            ],
                            spacing=12,
                        ),
                        bgcolor=TechBlueTheme.BG_CARD + "60",
                        border_radius=24,
                        padding=16,
                    ),
                ],
                spacing=0,
            ),
            expand=True,
        )
        
        return ft.Row(
            [session_list, ft.SizedBox(width=20), chat_area],
            expand=True,
            spacing=0,
        )
    
    def build_session_item(self, title: str, time: str, preview: str, is_active: bool):
        """构建会话项"""
        bg_color = TechBlueTheme.PRIMARY + "15" if is_active else "transparent"
        border_color = TechBlueTheme.PRIMARY if is_active else "transparent"
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.icons.CHAT_BUBBLE, size=18, color=TechBlueTheme.TEXT_PRIMARY if is_active else TechBlueTheme.TEXT_SECONDARY),
                        width=44,
                        height=44,
                        border_radius=14,
                        bgcolor=TechBlueTheme.PRIMARY if is_active else TechBlueTheme.BORDER,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        title,
                                        color=TechBlueTheme.TEXT_PRIMARY,
                                        size=14,
                                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
                                        expand=True,
                                    ),
                                    ft.Text(
                                        time,
                                        color=TechBlueTheme.TEXT_MUTED,
                                        size=11,
                                    ),
                                ],
                            ),
                            ft.Text(
                                preview,
                                color=TechBlueTheme.TEXT_SECONDARY if is_active else TechBlueTheme.TEXT_MUTED,
                                size=12,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=14,
            border_radius=18,
            bgcolor=bg_color,
            border=ft.border.all(1, border_color),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
        )
    
    def build_chat_message(self, text: str, is_user: bool):
        """构建聊天消息"""
        if is_user:
            return ft.Row(
                [
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            text,
                            color=TechBlueTheme.TEXT_PRIMARY,
                            size=14,
                        ),
                        padding=ft.padding.symmetric(horizontal=18, vertical=14),
                        border_radius=ft.border_radius.only(
                            top_left=20,
                            top_right=6,
                            bottom_left=20,
                            bottom_right=20,
                        ),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=TechBlueTheme.GRADIENT_PRIMARY,
                        ),
                        max_width=550,
                    ),
                ],
            )
        else:
            return ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.icons.SMART_TOY, size=18, color=TechBlueTheme.TEXT_PRIMARY),
                        width=40,
                        height=40,
                        border_radius=14,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[TechBlueTheme.ACCENT, TechBlueTheme.PRIMARY],
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text(
                            text,
                            color=TechBlueTheme.TEXT_PRIMARY,
                            size=14,
                        ),
                        padding=ft.padding.symmetric(horizontal=18, vertical=14),
                        border_radius=ft.border_radius.only(
                            top_left=6,
                            top_right=20,
                            bottom_left=20,
                            bottom_right=20,
                        ),
                        bgcolor=TechBlueTheme.BG_CARD,
                        border=ft.border.all(1, TechBlueTheme.BORDER),
                        max_width=550,
                    ),
                    ft.Container(expand=True),
                ],
                spacing=12,
            )
    
    def build_knowledge_page(self):
        """构建知识库页面"""
        return ft.Column(
            [
                ft.Text("知识库", style=Typography.H2),
                ft.SizedBox(height=20),
                create_glass_card(
                    ft.Column(
                        [
                            create_section_title("文档列表", ft.icons.FOLDER),
                            ft.SizedBox(height=16),
                            ft.Text("知识库功能开发中...", color=TechBlueTheme.TEXT_SECONDARY),
                        ],
                    ),
                    expand=True,
                ),
            ],
            expand=True,
        )
    
    def build_link_page(self):
        """构建链接分析页面"""
        return ft.Column(
            [
                ft.Text("链接分析", style=Typography.H2),
                ft.SizedBox(height=20),
                create_glass_card(
                    ft.Column(
                        [
                            create_section_title("分析结果", ft.icons.ANALYTICS),
                            ft.SizedBox(height=16),
                            ft.Text("链接分析功能开发中...", color=TechBlueTheme.TEXT_SECONDARY),
                        ],
                    ),
                    expand=True,
                ),
            ],
            expand=True,
        )
    
    def build_ops_page(self):
        """构建运维监控页面"""
        return ft.Column(
            [
                ft.Text("运维监控", style=Typography.H2),
                ft.SizedBox(height=20),
                create_glass_card(
                    ft.Column(
                        [
                            create_section_title("系统状态", ft.icons.MONITORING),
                            ft.SizedBox(height=16),
                            ft.Text("运维监控功能开发中...", color=TechBlueTheme.TEXT_SECONDARY),
                        ],
                    ),
                    expand=True,
                ),
            ],
            expand=True,
        )
    
    def build_settings_page(self):
        """构建系统设置页面"""
        return ft.Column(
            [
                ft.Text("系统设置", style=Typography.H2),
                ft.SizedBox(height=20),
                create_glass_card(
                    ft.Column(
                        [
                            create_section_title("通用设置", ft.icons.SETTINGS),
                            ft.SizedBox(height=16),
                            ft.Text("系统设置功能开发中...", color=TechBlueTheme.TEXT_SECONDARY),
                        ],
                    ),
                    expand=True,
                ),
            ],
            expand=True,
        )
    
    # 页面切换处理函数
    def show_video_page(self, e):
        self.content_area.content = self.build_video_page()
        self.page.update()
    
    def show_chat_page(self, e):
        self.content_area.content = self.build_chat_page()
        self.page.update()
    
    def show_knowledge_page(self, e):
        self.content_area.content = self.build_knowledge_page()
        self.page.update()
    
    def show_link_page(self, e):
        self.content_area.content = self.build_link_page()
        self.page.update()
    
    def show_ops_page(self, e):
        self.content_area.content = self.build_ops_page()
        self.page.update()
    
    def show_settings_page(self, e):
        self.content_area.content = self.build_settings_page()
        self.page.update()


def main(page: ft.Page):
    """应用入口"""
    SuperBizAgentApp(page)


if __name__ == "__main__":
    ft.app(target=main)
