#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文字处理工具 - 带导航栏的版本
- 添加AI问答大页面
- 导航栏切换功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import concurrent.futures
import requests
import json
import os
import time
import hashlib
from datetime import datetime
import multiprocessing
import asyncio
import aiohttp

# 忽略NumPy版本警告
import warnings
warnings.filterwarnings("ignore", message="A NumPy version >=1.23.5 and <2.3.0 is required for this version of SciPy")

# AI问答系统集成
try:
    from chat_gui import ChatGUI
    CHAT_GUI_AVAILABLE = True
except ImportError:
    CHAT_GUI_AVAILABLE = False
    print("警告：AI问答系统模块未安装")

APP_TITLE = "视频转文字处理工具 (GUI)"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

# 加载配置文件
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败：{e}")
    return {}

CONFIG = load_config()


class MainApplication:
    """主应用程序类 - 带导航栏"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f4f8")
        self.root.resizable(True, True)
        
        # 创建主容器
        self.main_container = tk.Frame(self.root, bg="#f0f4f8")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 创建标题区域
        self._create_header()
        
        # 创建导航栏
        self._create_navbar()
        
        # 创建内容区域
        self.content_frame = tk.Frame(self.main_container, bg="#f0f4f8")
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建视频处理页面
        self.video_page = VideoProcessingPage(self.content_frame)
        self.video_page.pack(fill=tk.BOTH, expand=True)
        
        # 创建AI问答页面（初始隐藏）
        self.chat_page = None
        
        # 当前页面
        self.current_page = "video"
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_header(self):
        """创建标题区域"""
        title_frame = tk.Frame(self.main_container, bg="#f0f4f8")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame, 
            text="视频转文字处理工具", 
            font=("微软雅黑", 18, "bold"),
            foreground="#0066cc",
            bg="#f0f4f8"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(
            title_frame, 
            text="智能视频分析与文本转换系统", 
            font=("微软雅黑", 10, "italic"),
            foreground="#666",
            bg="#f0f4f8"
        )
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_navbar(self):
        """创建导航栏"""
        nav_frame = tk.Frame(self.main_container, bg="#ffffff", bd=1, relief=tk.RAISED)
        nav_frame.pack(fill=tk.X, pady=(0, 20))
        nav_frame.configure(highlightbackground="#0066cc", highlightthickness=1)
        
        # 导航按钮容器
        nav_container = tk.Frame(nav_frame, bg="#ffffff")
        nav_container.pack(fill=tk.X, padx=10, pady=8)
        
        # 导航按钮样式
        nav_btn_style = {
            "font": ("微软雅黑", 11, "bold"),
            "padx": 25,
            "pady": 10,
            "bd": 0,
            "cursor": "hand2"
        }
        
        # 视频处理页面按钮（默认选中）
        self.nav_video_btn = tk.Button(
            nav_container,
            text="📹 视频处理",
            command=self._show_video_page,
            bg="#0066cc",
            fg="#ffffff",
            **nav_btn_style
        )
        self.nav_video_btn.pack(side=tk.LEFT, padx=5)
        
        # AI问答页面按钮
        self.nav_chat_btn = tk.Button(
            nav_container,
            text="🤖 AI问答",
            command=self._show_chat_page,
            bg="#f0f4f8",
            fg="#333333",
            **nav_btn_style
        )
        self.nav_chat_btn.pack(side=tk.LEFT, padx=5)
    
    def _show_video_page(self):
        """显示视频处理页面"""
        if self.current_page == "video":
            return
        
        # 隐藏AI问答页面
        if self.chat_page:
            self.chat_page.pack_forget()
        
        # 显示视频处理页面
        self.video_page.pack(fill=tk.BOTH, expand=True)
        
        # 更新按钮样式
        self.nav_video_btn.configure(bg="#0066cc", fg="#ffffff")
        self.nav_chat_btn.configure(bg="#f0f4f8", fg="#333333")
        
        self.current_page = "video"
        self.root.title(f"{APP_TITLE} - 视频处理")
    
    def _show_chat_page(self):
        """显示AI问答页面"""
        if self.current_page == "chat":
            return
        
        # 隐藏视频处理页面
        self.video_page.pack_forget()
        
        # 创建AI问答页面（如果还没有创建）
        if self.chat_page is None:
            if CHAT_GUI_AVAILABLE:
                self.chat_page = ChatPage(self.content_frame)
            else:
                messagebox.showerror("错误", "AI问答系统模块未安装")
                self._show_video_page()
                return
        
        # 显示AI问答页面
        self.chat_page.pack(fill=tk.BOTH, expand=True)
        
        # 更新按钮样式
        self.nav_video_btn.configure(bg="#f0f4f8", fg="#333333")
        self.nav_chat_btn.configure(bg="#0066cc", fg="#ffffff")
        
        self.current_page = "chat"
        self.root.title(f"{APP_TITLE} - AI问答")
    
    def on_closing(self):
        """窗口关闭处理"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            # 清理资源
            if self.video_page:
                self.video_page.cleanup()
            if self.chat_page:
                self.chat_page.cleanup()
            self.root.destroy()


class VideoProcessingPage(tk.Frame):
    """视频处理页面"""
    
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f4f8")
        
        # 这里放置原来的视频处理界面代码
        # 简化版本，仅作示例
        self._build_ui()
    
    def _build_ui(self):
        """构建界面"""
        # 提示标签
        label = tk.Label(
            self,
            text="视频处理功能区域\n\n这里将放置原有的视频处理界面",
            font=("微软雅黑", 14),
            bg="#f0f4f8",
            fg="#666"
        )
        label.pack(expand=True)
    
    def cleanup(self):
        """清理资源"""
        pass


class ChatPage(tk.Frame):
    """AI问答页面"""
    
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f4f8")
        
        # 初始化AI问答系统
        if CHAT_GUI_AVAILABLE:
            self.chat_gui = ChatGUI(self)
        else:
            label = tk.Label(
                self,
                text="AI问答系统未安装",
                font=("微软雅黑", 14),
                bg="#f0f4f8",
                fg="red"
            )
            label.pack(expand=True)
    
    def cleanup(self):
        """清理资源"""
        pass


def main():
    """主函数"""
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
