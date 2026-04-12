#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperBizAgent - AI 文档处理与知识库系统
工程化版本入口文件

版本: 2.0
作者: AI Assistant
日期: 2026-04-08
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# 添加src目录到Python路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(BASE_DIR, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 添加各模块路径
for module_dir in ['core', 'knowledge_base', 'document_processing', 'link_analysis', 'ai_chat', 'gui']:
    module_path = os.path.join(src_path, module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)


def check_dependencies():
    """检查核心依赖"""
    print("=" * 60)
    print("检查核心依赖...")
    print("=" * 60)
    
    dependencies = {
        "knowledge_base.agentic_rag_final": False,
        "knowledge_base.kb_manager_advanced": False,
        "ai_chat.ai_chat_system": False,
        "link_analysis.unified_link_document_processor": False,
        "document_processing.mineru_processor": False,
        "gui.multimodal_gui": False,
        "gui.rag_manager_gui_optimized": False,
    }
    
    for module_name in dependencies:
        try:
            __import__(module_name)
            dependencies[module_name] = True
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
    
    return dependencies


def create_main_window():
    """创建主窗口"""
    root = tk.Tk()
    root.title("SuperBizAgent - AI 文档处理与知识库系统 v2.0")
    root.geometry("1200x800")
    root.configure(bg="#f5f5f5")
    
    # 创建菜单栏
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # 文件菜单
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="文件", menu=file_menu)
    file_menu.add_command(label="退出", command=root.quit)
    
    # 功能菜单
    func_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="功能", menu=func_menu)
    
    # 知识库管理
    def open_kb_manager():
        try:
            from gui.rag_manager_gui_optimized import RAGManagerGUIOptimized
            RAGManagerGUIOptimized(parent=root)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开知识库管理器: {e}")
    
    func_menu.add_command(label="📚 知识库管理", command=open_kb_manager)
    
    # 多模态文档处理
    def open_multimodal():
        try:
            from gui.multimodal_gui import MultimodalProcessingPage
            page = MultimodalProcessingPage(root)
            page.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开多模态处理器: {e}")
    
    func_menu.add_command(label="📁 多模态文档处理", command=open_multimodal)
    
    # 统一处理器
    def open_unified():
        try:
            from gui.unified_link_document_gui import UnifiedLinkDocumentGUI
            UnifiedLinkDocumentGUI(parent=root)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开统一处理器: {e}")
    
    func_menu.add_command(label="🔗 链接+文档统一处理", command=open_unified)
    
    # 视频下载
    def open_video_downloader():
        try:
            from gui.video_gui import VideoDownloaderGUI
            VideoDownloaderGUI(parent=root)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开视频下载器: {e}")
    
    func_menu.add_command(label="🎬 视频下载", command=open_video_downloader)
    
    # 帮助菜单
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="帮助", menu=help_menu)
    
    def show_about():
        messagebox.showinfo(
            "关于",
            "SuperBizAgent - AI 文档处理与知识库系统\n\n"
            "版本: 2.0 (工程化版本)\n"
            "主模型: Doubao-Seed-2.0-Code\n"
            "备用模型: Doubao-Seed-2.0-mini\n"
            "嵌入模型: BGE-Large\n\n"
            "支持功能:\n"
            "- RAG 知识库问答\n"
            "- 多模态文档处理\n"
            "- 链接内容分析\n"
            "- AI 对话系统\n"
            "- 视频下载处理"
        )
    
    help_menu.add_command(label="关于", command=show_about)
    
    # 创建主界面
    main_frame = tk.Frame(root, bg="#f5f5f5")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 标题
    title_label = tk.Label(
        main_frame,
        text="🤖 SuperBizAgent",
        font=("微软雅黑", 28, "bold"),
        bg="#f5f5f5",
        fg="#1a1a1a"
    )
    title_label.pack(pady=(0, 10))
    
    subtitle_label = tk.Label(
        main_frame,
        text="AI 文档处理与知识库系统 - 工程化版本",
        font=("微软雅黑", 14),
        bg="#f5f5f5",
        fg="#666666"
    )
    subtitle_label.pack(pady=(0, 40))
    
    # 功能按钮区域
    buttons_frame = tk.Frame(main_frame, bg="#f5f5f5")
    buttons_frame.pack(fill=tk.BOTH, expand=True)
    
    # 功能按钮配置
    buttons = [
        {
            "text": "📚 知识库管理",
            "command": open_kb_manager,
            "description": "管理文档、生成索引、配置参数",
            "color": "#10b981",
            "icon": "📚"
        },
        {
            "text": "📁 多模态文档处理",
            "command": open_multimodal,
            "description": "处理 PDF、Word、图片、音频、视频",
            "color": "#3b82f6",
            "icon": "📁"
        },
        {
            "text": "🔗 链接+文档统一处理",
            "command": open_unified,
            "description": "分析链接内容并生成结构化文档",
            "color": "#8b5cf6",
            "icon": "🔗"
        },
        {
            "text": "🎬 视频下载",
            "command": open_video_downloader,
            "description": "下载抖音、小红书等平台视频",
            "color": "#f59e0b",
            "icon": "🎬"
        },
    ]
    
    for btn_config in buttons:
        btn_frame = tk.Frame(buttons_frame, bg="#ffffff", padx=20, pady=20)
        btn_frame.pack(fill=tk.X, pady=10)
        
        btn = tk.Button(
            btn_frame,
            text=btn_config["text"],
            font=("微软雅黑", 14, "bold"),
            bg=btn_config["color"],
            fg="white",
            activebackground=btn_config["color"],
            activeforeground="white",
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor="hand2",
            command=btn_config["command"]
        )
        btn.pack(side=tk.LEFT)
        
        desc_label = tk.Label(
            btn_frame,
            text=btn_config["description"],
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#666666"
        )
        desc_label.pack(side=tk.LEFT, padx=(20, 0))
    
    # 状态栏
    status_frame = tk.Frame(root, bg="#e5e7eb", height=30)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    status_label = tk.Label(
        status_frame,
        text="就绪 | 主模型: Doubao-Seed-2.0-Code | 备用模型: Doubao-Seed-2.0-mini | 嵌入模型: BGE-Large",
        font=("微软雅黑", 9),
        bg="#e5e7eb",
        fg="#374151"
    )
    status_label.pack(side=tk.LEFT, padx=10, pady=5)
    
    return root


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("启动 SuperBizAgent - 工程化版本")
    print("=" * 60)
    
    # 检查依赖
    deps = check_dependencies()
    
    # 创建主窗口
    root = create_main_window()
    
    print("\n✅ 应用程序已启动")
    print("=" * 60)
    
    # 运行主循环
    root.mainloop()
    
    print("\n应用程序已关闭")


if __name__ == "__main__":
    main()
