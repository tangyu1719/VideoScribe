#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 知识库管理 GUI - 独立的文件管理窗口
功能：
1. 添加/删除文件（支持 TXT 和 MD）
2. 文件记录和统计
3. 文件和向量绑定管理
4. 进度条显示（避免死机）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import threading
import queue  # 添加queue模块导入
from datetime import datetime
from typing import List, Dict

# 尝试导入快速知识库管理器（BGE-Large 1024维）
try:
    from kb_manager_fast import get_fast_knowledge_base as get_knowledge_base, FastKnowledgeBaseManager as KnowledgeBaseManager
    KB_MANAGER_AVAILABLE = True
    print("使用快速知识库管理器（BGE-Large 1024维）")
except ImportError as e:
    KB_MANAGER_AVAILABLE = False
    print(f"警告：知识库管理器未安装: {e}")

# 导入数据库管理器（新的MySQL存储）
try:
    from db_manager import get_db_manager
    from db_models import Tag, Document
    DB_AVAILABLE = True
    print("使用MySQL数据库管理器")
except ImportError as e:
    DB_AVAILABLE = False
    print(f"警告：数据库管理器未安装: {e}")

# 导入元数据对话框
try:
    from metadata_dialog import show_metadata_dialog
    from rag_tools import DocumentMetadata
    METADATA_DIALOG_AVAILABLE = True
    print("使用元数据编辑对话框")
except ImportError as e:
    METADATA_DIALOG_AVAILABLE = False
    print(f"警告：元数据对话框未安装: {e}")

# 尝试导入 RAG 知识库（向后兼容）
try:
    from rag_knowledge_base_v2 import RAGKnowledgeBase
    RAG_AVAILABLE = True
    print("使用 RAG 知识库 v2 版本（支持 TXT 和 MD）")
except ImportError:
    try:
        from rag_knowledge_base import RAGKnowledgeBase
        RAG_AVAILABLE = True
        print("使用 RAG 知识库 v1 版本")
    except ImportError:
        RAG_AVAILABLE = False
        print("警告：RAG 知识库模块未安装")

# 导入轻量级文件处理器
try:
    from simple_file_processor import add_file_to_records, add_folder_to_records
    print("使用轻量级文件处理器")
except ImportError:
    print("警告：轻量级文件处理器未安装")
    add_file_to_records = None
    add_folder_to_records = None


class RAGManagerGUI:
    """RAG 知识库管理 GUI"""
    
    def __init__(self, parent=None, rag_kb=None):
        """
        初始化 RAG 知识库管理窗口
        
        Args:
            parent: 父窗口
            rag_kb: 已初始化的RAG知识库实例（可选，如果传入则不再初始化）
        """
        self.parent = parent
        self.rag_kb = rag_kb  # 使用传入的RAG实例，不再重新初始化
        # 创建独立窗口，确保有完整标题栏（包括最小化按钮）
        self.window = tk.Tk()
        self.window.title("📚 RAG 知识库管理")
        self.window.geometry("900x700")
        self.window.configure(bg="#f5f5f5")
        
        # 强制显示完整标题栏（包括最小化、最大化、关闭按钮）
        self.window.resizable(True, True)
        
        # Windows系统下使用Win32 API强制显示最小化按钮
        try:
            import ctypes
            from ctypes import wintypes
            
            # 获取窗口句柄
            hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
            
            # 获取当前窗口样式
            GWL_STYLE = -16
            WS_MINIMIZEBOX = 0x00020000
            WS_MAXIMIZEBOX = 0x00010000
            WS_SYSMENU = 0x00080000
            WS_CAPTION = 0x00C00000
            
            # 设置窗口样式，确保有最小化按钮
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style |= WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU | WS_CAPTION
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
            
            # 刷新窗口
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 
                0x0027 | 0x0002 | 0x0001 | 0x0020)
        except Exception as e:
            print(f"设置窗口样式失败: {e}")
        
        # 居中显示
        self._center_window()
        
        # 先创建 UI（立即显示窗口）
        self._create_ui()
        
        # 初始化文件记录列表
        self.file_records = []
        
        # 检查是否已传入初始化的RAG实例（服务启动时已初始化）
        if self.rag_kb is not None:
            # 使用已初始化的RAG实例，立即可用
            print("✓ 使用服务启动时已初始化的RAG知识库")
            self.stats_label.config(text="✓ 知识库已就绪")
            self.progress_label.config(text="正在加载文件列表...")
            self.progress_bar.start(10)
            self._load_data_async(use_initialized_rag=True)
        else:
            # 没有传入RAG实例，需要异步初始化（向后兼容）
            print("⚠ 未传入RAG实例，将异步初始化")
            self.stats_label.config(text="⏳ 正在初始化知识库...")
            self.progress_label.config(text="正在加载数据，请稍候...")
            self.progress_bar.start(10)
            self._load_data_async(use_initialized_rag=False)
    
    def _load_data_async(self, use_initialized_rag=False):
        """
        异步加载数据
        
        Args:
            use_initialized_rag: 是否使用已初始化的RAG实例（服务启动时已初始化）
        """
        # 创建线程安全的队列来传递数据
        import queue
        self._ui_queue = queue.Queue()
        
        def load():
            try:
                # 1. 快速加载文件记录
                self.file_records = []
                print("开始加载文件记录...")
                self._load_file_records()
                print(f"加载了 {len(self.file_records)} 条文件记录")
                
                # 2. 发送消息到UI队列
                self._ui_queue.put(('file_records_loaded', None))
                
                # 3. 处理RAG知识库
                if use_initialized_rag:
                    # 使用已初始化的RAG实例，直接更新统计
                    print("✓ RAG知识库已在服务启动时初始化，直接使用")
                    self._ui_queue.put(('rag_initialized', None))
                elif RAG_AVAILABLE and self.rag_kb is None:
                    # 后台异步初始化 RAG（向后兼容）
                    print("开始在后台初始化 RAG 知识库...")
                    def init_rag():
                        try:
                            print("正在加载嵌入模型（这可能需要几秒钟）...")
                            self.rag_kb = RAGKnowledgeBase()
                            print("✓ RAG 知识库初始化成功")
                            self._ui_queue.put(('rag_initialized', None))
                        except Exception as e:
                            print(f"✗ RAG 初始化失败：{e}")
                            self.rag_kb = None
                    
                    rag_thread = threading.Thread(target=init_rag, daemon=True)
                    rag_thread.start()
                    
            except Exception as e:
                print(f"✗ 加载数据失败：{e}")
                self._ui_queue.put(('error', str(e)))
        
        # 启动后台线程
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
        
        # 启动UI更新检查
        self._check_ui_queue()
    
    def _check_ui_queue(self):
        """检查UI队列并更新界面（线程安全）"""
        try:
            while True:
                # 非阻塞方式获取消息
                msg_type, msg_data = self._ui_queue.get_nowait()
                
                if msg_type == 'file_records_loaded':
                    self._on_file_records_loaded()
                elif msg_type == 'rag_initialized':
                    self._on_rag_initialized()
                elif msg_type == 'error':
                    self._on_data_load_error(msg_data)
                    
        except queue.Empty:
            # 队列为空，继续等待
            pass
        except Exception as e:
            print(f"处理UI队列时出错: {e}")
        
        # 100ms后再次检查
        if hasattr(self, 'window') and self.window:
            self.window.after(100, self._check_ui_queue)
    
    def _on_file_records_loaded(self):
        """文件记录加载完成（立即显示列表）"""
        self.progress_bar.stop()
        self.progress_label.config(text="就绪")
        self._update_file_tree()  # 先显示文件列表
        self._refresh_stats_from_records()  # 从记录显示统计
    
    def _on_rag_initialized(self):
        """RAG 初始化完成"""
        if self.rag_kb:
            self._refresh_stats()  # 更新完整统计
    
    def _refresh_stats_from_records(self):
        """从文件记录刷新统计（不需要 RAG）"""
        total_files = len(self.file_records)
        total_chunks = sum(r.get('chunk_count', 0) for r in self.file_records)
        
        stats_text = (
            f"📊 知识库统计："
            f"  文件总数：{total_files}  "
            f"  向量块数：{total_chunks}  "
            f"  状态：{'✓ 已就绪' if self.rag_kb else '⏳ 初始化中...'}"
        )
        self.stats_label.config(text=stats_text)
    
    def _init_rag_kb(self):
        """初始化 RAG 知识库"""
        if RAG_AVAILABLE:
            try:
                self.rag_kb = RAGKnowledgeBase()
                print("RAG 知识库初始化成功")
            except Exception as e:
                print(f"RAG 知识库初始化失败：{e}")
                self.rag_kb = None
        else:
            print("RAG 知识库不可用")
    
    def _center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = 900
        height = 700
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_ui(self):
        """创建 UI 界面"""
        # 主容器
        main_frame = tk.Frame(self.window, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="📚 RAG 知识库管理",
            font=("微软雅黑", 20, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        )
        title_label.pack(pady=(0, 20))
        
        # 统计信息卡片
        stats_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.RAISED, bd=2)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.stats_label = tk.Label(
            stats_frame,
            text="加载中...",
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#333333",
            justify=tk.LEFT,
            padx=20,
            pady=15,
            anchor="w"
        )
        self.stats_label.pack(fill=tk.X)
        
        # 操作按钮区域
        button_frame = tk.Frame(main_frame, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 添加文件按钮
        add_file_btn = tk.Button(
            button_frame,
            text="📄 添加文件",
            font=("微软雅黑", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            command=self._on_add_file,
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        add_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加文件夹按钮
        add_folder_btn = tk.Button(
            button_frame,
            text="📁 添加文件夹",
            font=("微软雅黑", 11, "bold"),
            bg="#2196F3",
            fg="white",
            cursor="hand2",
            command=self._on_add_folder,
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        add_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 删除选中文件按钮
        delete_btn = tk.Button(
            button_frame,
            text="🗑️ 删除选中",
            font=("微软雅黑", 11, "bold"),
            bg="#f44336",
            fg="white",
            cursor="hand2",
            command=self._on_delete_selected,
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 配置按钮
        config_btn = tk.Button(
            button_frame,
            text="⚙️ 配置",
            font=("微软雅黑", 11),
            bg="#FF9800",
            fg="white",
            cursor="hand2",
            command=self._on_config,
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        config_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 刷新按钮
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 刷新",
            font=("微软雅黑", 11),
            bg="#9e9e9e",
            fg="white",
            cursor="hand2",
            command=self._on_refresh,
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # 进度条区域
        progress_frame = tk.Frame(main_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="就绪",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666666"
        )
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=800
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 文件列表表格
        list_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.RAISED, bd=2)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建 Treeview - 添加标签列
        columns = ("序号", "文件名", "路径", "类型", "大小", "块数", "领域", "模块", "文档类型", "添加时间")
        self.file_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="extended"
        )
        
        # 设置列标题
        self.file_tree.heading("序号", text="序号")
        self.file_tree.heading("文件名", text="文件名")
        self.file_tree.heading("路径", text="路径")
        self.file_tree.heading("类型", text="类型")
        self.file_tree.heading("大小", text="大小 (KB)")
        self.file_tree.heading("块数", text="向量块数")
        self.file_tree.heading("领域", text="领域")
        self.file_tree.heading("模块", text="模块")
        self.file_tree.heading("文档类型", text="文档类型")
        self.file_tree.heading("添加时间", text="添加时间")
        
        # 设置列宽
        self.file_tree.column("序号", width=50, anchor="center")
        self.file_tree.column("文件名", width=150, anchor="w")
        self.file_tree.column("路径", width=200, anchor="w")
        self.file_tree.column("类型", width=60, anchor="center")
        self.file_tree.column("大小", width=70, anchor="center")
        self.file_tree.column("块数", width=70, anchor="center")
        self.file_tree.column("领域", width=80, anchor="center")
        self.file_tree.column("模块", width=80, anchor="center")
        self.file_tree.column("文档类型", width=80, anchor="center")
        self.file_tree.column("添加时间", width=120, anchor="center")
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定双击事件
        self.file_tree.bind("<Double-1>", self._on_tree_double_click)
        
        # 底部说明
        info_label = tk.Label(
            main_frame,
            text="💡 提示：支持 .txt 和 .md 格式文件 | 双击可查看文件详情 | 删除文件将同时删除对应的向量数据",
            font=("微软雅黑", 9),
            bg="#f5f5f5",
            fg="#666666"
        )
        info_label.pack(pady=(10, 0))
    
    def _refresh_stats(self):
        """刷新统计信息（从文件列表汇总计算，确保与显示一致）"""
        try:
            # 从文件列表汇总计算（与文件列表显示保持一致）
            total_files = len(self.file_records)
            total_chunks = sum(r.get('chunk_count', 0) for r in self.file_records)
            
            # 获取嵌入维度和最后更新时间
            embedding_dim = 'N/A'
            updated_at = 'N/A'
            if self.rag_kb:
                try:
                    stats = self.rag_kb.get_stats()
                    embedding_dim = stats.get('embedding_dim', 'N/A')
                    updated_at = stats.get('updated_at', 'N/A')
                except:
                    pass
            
            stats_text = (
                f"📊 知识库统计："
                f"  文件总数：{total_files}  "
                f"  向量块数：{total_chunks}  "
                f"  嵌入维度：{embedding_dim}  "
                f"  最后更新：{updated_at}"
            )
            
            self.stats_label.config(text=stats_text)
        except Exception as e:
            self.stats_label.config(text=f"❌ 获取统计信息失败：{e}")
    
    def _load_file_records(self):
        """加载文件记录"""
        records_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "knowledge_base",
            "file_records.json"
        )
        
        try:
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    self.file_records = json.load(f)
                print(f"加载了 {len(self.file_records)} 条文件记录")
            else:
                self.file_records = []
        except Exception as e:
            print(f"加载文件记录失败：{e}")
            self.file_records = []
    
    def _save_file_records(self):
        """保存文件记录"""
        records_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "knowledge_base",
            "file_records.json"
        )
        
        try:
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_records, f, ensure_ascii=False, indent=2)
            print("文件记录已保存")
        except Exception as e:
            print(f"保存文件记录失败：{e}")
    
    def _update_file_tree(self):
        """更新文件列表 - 从数据库获取标签信息"""
        # 清空现有项
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 尝试从数据库获取文档和标签信息
        doc_tag_map = {}
        if DB_AVAILABLE:
            try:
                db = get_db_manager()
                # 获取所有文档及其标签
                documents = db.get_all_documents()
                tags = {t.tag_id: t for t in db.get_all_tags()}
                
                for doc in documents:
                    tag = tags.get(doc.tag_id)
                    if tag:
                        doc_tag_map[doc.file_path] = {
                            'domain': tag.domain,
                            'module': tag.module,
                            'doc_type': tag.doc_type,
                            'keyword1': tag.keyword1,
                            'keyword2': tag.keyword2
                        }
            except Exception as e:
                print(f"从数据库获取标签信息失败: {e}")
        
        # 添加记录
        for i, record in enumerate(self.file_records, 1):
            file_path = record.get('file_path', '未知')
            
            # 获取标签信息
            tag_info = doc_tag_map.get(file_path, {})
            domain = tag_info.get('domain', '-')
            module = tag_info.get('module', '-')
            doc_type = tag_info.get('doc_type', '-')
            
            self.file_tree.insert(
                "",
                tk.END,
                iid=file_path,
                values=(
                    i,
                    os.path.basename(file_path),
                    file_path,
                    record.get('file_type', '未知'),
                    f"{record.get('file_size', 0):.1f}",
                    record.get('chunk_count', 0),
                    domain,
                    module,
                    doc_type,
                    record.get('added_at', '未知')
                )
            )
    
    def _on_add_file(self):
        """添加文件按钮点击事件"""
        if not RAG_AVAILABLE:
            messagebox.showerror("错误", "RAG 知识库模块未安装")
            return
        
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("Markdown 文件", "*.md"),
                ("所有支持的文件", "*.txt *.md"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            # 弹出元数据编辑对话框
            if METADATA_DIALOG_AVAILABLE:
                self._show_metadata_dialog_then_process(file_path)
            else:
                # 直接处理（无元数据）
                self._process_file_async(file_path)
    
    def _show_metadata_dialog_then_process(self, file_path: str):
        """显示元数据对话框，然后处理文件"""
        def on_save(metadata):
            # 保存元数据到文件记录
            self._pending_metadata = metadata
            # 处理文件
            self._process_file_async(file_path, metadata)
        
        show_metadata_dialog(self.window, file_path, on_save=on_save)
    
    def _on_add_folder(self):
        """添加文件夹按钮点击事件"""
        if not RAG_AVAILABLE:
            messagebox.showerror("错误", "RAG 知识库模块未安装")
            return
        
        folder_path = filedialog.askdirectory(title="选择文件夹")
        
        if folder_path:
            # 在新线程中处理，避免界面卡死
            self._process_folder_async(folder_path)
    
    def _process_file_async(self, file_path, metadata=None):
        """异步处理文件添加（真正向量化）"""
        self.progress_bar.start()
        self.progress_label.config(text=f"正在处理：{os.path.basename(file_path)}")
        
        # 创建结果队列和完成标志
        result_queue = queue.Queue()
        done_event = threading.Event()
        
        def process():
            try:
                import os
                import hashlib
                from datetime import datetime
                
                # 检查文件
                if not os.path.exists(file_path):
                    result_queue.put(('error', file_path, "文件不存在"))
                    return
                
                # 检查文件大小（限制10MB）
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    result_queue.put(('error', file_path, "文件太大（超过10MB）"))
                    return
                
                # 计算文件哈希
                file_hash = hashlib.md5(file_path.encode()).hexdigest()
                
                # 保存元数据到数据库
                tag_id = None
                if metadata and DB_AVAILABLE:
                    try:
                        db = get_db_manager()
                        tag = db.get_or_create_tag(
                            domain=metadata.domain,
                            module=metadata.module,
                            doc_type=metadata.doc_type,
                            keyword1=metadata.keyword1 or "",
                            keyword2=metadata.keyword2 or ""
                        )
                        tag_id = tag.tag_id
                        print(f"[GUI] 标签已创建/获取: tag_id={tag_id}")
                    except Exception as e:
                        print(f"[GUI] 保存元数据失败: {e}")
                
                # 使用快速知识库管理器真正向量化文件
                if KB_MANAGER_AVAILABLE:
                    try:
                        from kb_manager_fast import get_fast_knowledge_base
                        kb = get_fast_knowledge_base()
                        
                        success, message = kb.add_document(file_path)
                        
                        if success:
                            # 获取实际添加的块数
                            stats = kb.get_stats()
                            actual_chunks = stats.get('total_chunks', 0)
                            
                            # 更新文件记录（包含元数据）
                            self._update_file_record_with_metadata(
                                file_path, file_size, actual_chunks, 
                                metadata, tag_id
                            )
                            
                            # 保存文档到数据库
                            if DB_AVAILABLE and tag_id:
                                try:
                                    db = get_db_manager()
                                    doc = db.add_document(
                                        file_name=os.path.basename(file_path),
                                        file_path=file_path,
                                        file_hash=file_hash,
                                        tag_id=tag_id,
                                        file_size=file_size,
                                        chunk_count=actual_chunks
                                    )
                                    print(f"[GUI] 文档已保存到数据库: doc_id={doc.doc_id}")
                                except Exception as e:
                                    print(f"[GUI] 保存文档到数据库失败: {e}")
                            
                            result_queue.put(('success', file_path, f"成功向量化，共 {actual_chunks} 个块"))
                        else:
                            result_queue.put(('error', file_path, message))
                        return
                    except Exception as e:
                        print(f"[GUI] 知识库添加失败：{e}")
                        import traceback
                        traceback.print_exc()
                        result_queue.put(('error', file_path, f"向量化失败: {str(e)}"))
                        return
                else:
                    # 回退：只保存记录（不向量化）
                    self._save_file_record_only(file_path, file_size)
                    result_queue.put(('success', file_path, "已添加记录（未向量化）"))
                
            except Exception as e:
                print(f"[GUI] 处理文件失败：{e}")
                import traceback
                traceback.print_exc()
                result_queue.put(('error', file_path, str(e)))
            finally:
                # 标记处理完成
                done_event.set()
                print(f"[GUI] 处理线程结束: {file_path}")
        
        # 启动后台线程
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
        
        # 启动检查结果队列
        self._check_process_result(result_queue, done_event)
    
    def _update_file_record(self, file_path, file_size, chunk_count):
        """更新文件记录（与RAG知识库同步）"""
        try:
            from datetime import datetime
            
            records_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "knowledge_base",
                "file_records.json"
            )
            
            # 加载现有记录
            records = []
            if os.path.exists(records_file):
                try:
                    with open(records_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except:
                    records = []
            
            # 检查是否已存在
            for record in records:
                if record.get('file_path') == file_path:
                    # 更新记录
                    record['chunk_count'] = chunk_count
                    record['vector_bound'] = True
                    break
            else:
                # 添加新记录
                file_info = {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_type': os.path.splitext(file_path)[1].lower(),
                    'file_size': file_size / 1024,
                    'chunk_count': chunk_count,
                    'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'vector_bound': True
                }
                records.append(file_info)
            
            # 保存
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            # 重新加载记录
            self.file_records = records
            
        except Exception as e:
            print(f"更新文件记录失败：{e}")
    
    def _update_file_record_with_metadata(self, file_path, file_size, chunk_count, metadata=None, tag_id=None):
        """更新文件记录（包含元数据）"""
        try:
            from datetime import datetime
            
            records_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "knowledge_base",
                "file_records.json"
            )
            
            # 加载现有记录
            records = []
            if os.path.exists(records_file):
                try:
                    with open(records_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except:
                    records = []
            
            # 构建记录数据
            file_info = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': os.path.splitext(file_path)[1].lower(),
                'file_size': file_size / 1024,
                'chunk_count': chunk_count,
                'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'vector_bound': True,
                'tag_id': tag_id
            }
            
            # 添加元数据
            if metadata:
                file_info['domain'] = metadata.domain
                file_info['module'] = metadata.module
                file_info['doc_type'] = metadata.doc_type
                file_info['keyword1'] = metadata.keyword1
                file_info['keyword2'] = metadata.keyword2
            
            # 检查是否已存在
            found = False
            for record in records:
                if record.get('file_path') == file_path:
                    # 更新记录
                    record.update(file_info)
                    found = True
                    break
            
            if not found:
                records.append(file_info)
            
            # 保存
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            # 重新加载记录
            self.file_records = records
            
        except Exception as e:
            print(f"更新文件记录（含元数据）失败：{e}")
    
    def _save_file_record_only(self, file_path, file_size):
        """仅保存文件记录（不向量化）"""
        try:
            from datetime import datetime
            
            records_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "knowledge_base",
                "file_records.json"
            )
            
            records = []
            if os.path.exists(records_file):
                try:
                    with open(records_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except:
                    records = []
            
            # 检查是否已存在
            for record in records:
                if record.get('file_path') == file_path:
                    return
            
            # 添加记录
            records.append({
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': os.path.splitext(file_path)[1].lower(),
                'file_size': file_size / 1024,
                'chunk_count': 0,
                'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'vector_bound': False
            })
            
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            self.file_records = records
            
        except Exception as e:
            print(f"保存文件记录失败：{e}")
    
    def _check_process_result(self, result_queue, done_event=None, processed_count=0, last_message=""):
        """检查文件处理结果（线程安全）"""
        try:
            # 非阻塞方式获取结果
            result = result_queue.get_nowait()
            status, file_path, message = result
            processed_count += 1
            last_message = message
            
            # 更新进度显示，不停止进度条
            if status == 'success':
                self.progress_label.config(text=f"✓ {file_path}: {message}")
                print(f"[GUI] 处理成功: {file_path} - {message}")
            else:
                self.progress_label.config(text=f"✗ {file_path}: {message}")
                print(f"[GUI] 处理失败: {file_path} - {message}")
            
            # 刷新文件列表显示
            self._refresh_stats()
            self._update_file_tree()
            
            # 继续检查队列（可能还有更多结果）
            self.window.after(100, lambda: self._check_process_result(result_queue, done_event, processed_count, last_message))
                
        except queue.Empty:
            # 队列为空，检查是否处理完成
            if done_event and done_event.is_set():
                # 线程已结束且队列为空，处理完成
                self.progress_bar.stop()
                if processed_count > 0:
                    self.progress_label.config(text=f"完成: {last_message}")
                    messagebox.showinfo("完成", f"文件处理完成\n{last_message}")
                else:
                    self.progress_label.config(text="就绪")
                print(f"[GUI] 所有处理完成，共处理 {processed_count} 个结果")
            else:
                # 线程还在运行，继续等待
                self.window.after(100, lambda: self._check_process_result(result_queue, done_event, processed_count, last_message))
        except Exception as e:
            print(f"[GUI] 检查结果时出错: {e}")
            import traceback
            traceback.print_exc()
            self.progress_bar.stop()
    
    def _process_folder_async(self, folder_path):
        """异步处理文件夹添加（快速模式，不生成嵌入）"""
        self.progress_bar.start()
        self.progress_label.config(text=f"正在扫描文件夹...")
        
        def process():
            try:
                # 扫描文件夹
                files_to_add = []
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith(('.txt', '.md')):
                            file_path = os.path.join(root, file)
                            files_to_add.append(file_path)
                
                total_files = len(files_to_add)
                if total_files == 0:
                    self.window.after(0, lambda: messagebox.showinfo("提示", "文件夹中没有找到 .txt 或 .md 文件"))
                    self.window.after(0, self._on_process_complete)
                    return
                
                print(f"[RAG] 找到 {total_files} 个文件，开始快速处理（不生成嵌入）...")
                
                # 处理每个文件（快速模式，不生成嵌入）
                added_count = 0
                for i, file_path in enumerate(files_to_add, 1):
                    self.window.after(0, lambda p=file_path, idx=i, total=total_files: self.progress_label.config(
                        text=f"快速处理中 ({idx}/{total}): {os.path.basename(p)}"))
                    
                    try:
                        # 快速读取文件（不生成嵌入）
                        if not os.path.exists(file_path):
                            continue
                        
                        # 尝试多种编码读取
                        content = None
                        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                            try:
                                with open(file_path, 'r', encoding=encoding) as f:
                                    content = f.read()
                                break
                            except:
                                continue
                        
                        if not content:
                            print(f"[RAG] 无法读取文件: {file_path}")
                            continue
                        
                        # 简单分块（不生成嵌入）
                        chunk_size = 500
                        overlap = 100
                        chunks = []
                        start = 0
                        text_len = len(content)
                        
                        while start < text_len and len(chunks) < 100:  # 限制最多100个块
                            end = min(start + chunk_size, text_len)
                            chunk_text = content[start:end].strip()
                            if chunk_text:
                                chunks.append(chunk_text)
                            start = end - overlap if end < text_len else end
                        
                        # 创建记录
                        file_size = os.path.getsize(file_path) / 1024
                        file_type = os.path.splitext(file_path)[1].lower()
                        
                        record = {
                            'file_path': file_path,
                            'file_name': os.path.basename(file_path),
                            'file_type': file_type,
                            'file_size': file_size,
                            'chunk_count': len(chunks),
                            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'vector_bound': False  # 标记为未向量化
                        }
                        
                        # 检查是否已存在
                        exists = False
                        for r in self.file_records:
                            if r.get('file_path') == file_path:
                                exists = True
                                break
                        
                        if not exists:
                            self.file_records.append(record)
                            added_count += 1
                            print(f"[RAG] 已添加: {os.path.basename(file_path)} ({len(chunks)} 个块)")
                        
                    except Exception as e:
                        print(f"[RAG] 添加文件失败 {file_path}: {e}")
                
                # 保存记录
                self._save_file_records()
                
                print(f"[RAG] 导入完成: 成功添加 {added_count}/{total_files} 个文件")
                
                # 立即通知用户导入完成
                self.window.after(0, lambda: self._on_process_complete(True, f"成功导入 {added_count}/{total_files} 个文件\n正在后台生成嵌入向量..."))
                
                # 【企业级流程】后台异步生成嵌入向量
                if added_count > 0:
                    print(f"[RAG] 启动后台嵌入生成线程...")
                    self.window.after(0, lambda: self._start_background_embedding())
                
            except Exception as e:
                print(f"[RAG] 处理文件夹失败：{e}")
                import traceback
                traceback.print_exc()
                self.window.after(0, lambda: self._on_process_complete(False, str(e)))
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _start_background_embedding(self):
        """后台异步生成嵌入向量（企业级流程）"""
        def embed_process():
            try:
                # 找出未向量化的文件
                unvectorized = [r for r in self.file_records if not r.get('vector_bound', False)]
                
                if not unvectorized:
                    print("[RAG] 所有文件已向量化")
                    return
                
                total = len(unvectorized)
                print(f"[RAG] 后台嵌入: 共 {total} 个文件需要生成向量")
                
                # 初始化 RAG（如果未初始化）
                if not self.rag_kb:
                    try:
                        self._init_rag_kb()
                    except Exception as e:
                        print(f"[RAG] 初始化RAG失败: {e}")
                        return
                
                # 批量生成嵌入
                processed = 0
                for i, record in enumerate(unvectorized, 1):
                    try:
                        file_path = record['file_path']
                        file_name = record['file_name']
                        
                        if not os.path.exists(file_path):
                            print(f"[RAG] 文件不存在: {file_name}")
                            continue
                        
                        print(f"[RAG] 后台嵌入 ({i}/{total}): {file_name}")
                        
                        # 使用RAG生成嵌入
                        result = self.rag_kb.add_document(file_path)
                        
                        # 兼容新旧API：新的返回 (bool, str) 元组，旧的返回 bool
                        if isinstance(result, tuple):
                            success = result[0]
                            message = result[1]
                        else:
                            success = result
                            message = ""
                        
                        if success:
                            # 更新记录状态
                            record['vector_bound'] = True
                            processed += 1
                            print(f"[RAG] ✓ 嵌入完成: {file_name}")
                            
                            # 每5个文件保存一次
                            if processed % 5 == 0:
                                self.rag_kb.save_index()
                                self._save_file_records()
                                print(f"[RAG] 已保存进度: {processed}/{total}")
                        else:
                            print(f"[RAG] ✗ 嵌入失败: {file_name}")
                            
                    except Exception as e:
                        print(f"[RAG] 嵌入异常: {e}")
                
                # 最终保存
                self.rag_kb.save_index()
                self._save_file_records()
                
                print(f"[RAG] 后台嵌入完成: 成功处理 {processed}/{total} 个文件")
                
                # 更新UI（可选）
                self.window.after(0, lambda: self._refresh_stats())
                
            except Exception as e:
                print(f"[RAG] 后台嵌入失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 启动后台线程
        embed_thread = threading.Thread(target=embed_process, daemon=True)
        embed_thread.start()
        print("[RAG] 后台嵌入线程已启动")
    
    def _on_process_complete(self, success=None, message=None):
        """处理完成回调"""
        self.progress_bar.stop()
        
        if success is not None:
            if success:
                self.progress_label.config(text=f"✓ {message or '处理完成'}")
                messagebox.showinfo("成功", message or "文件已成功添加到知识库")
            else:
                self.progress_label.config(text=f"✗ {message or '处理失败'}")
                messagebox.showerror("错误", message or "处理失败")
        
        self._refresh_stats()
        self._update_file_tree()
        self.progress_label.config(text="就绪")
    
    def _on_delete_selected(self):
        """删除选中文件"""
        selected_items = self.file_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要删除的文件")
            return
        
        # 确认删除
        count = len(selected_items)
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {count} 个文件吗？\n\n注意：删除文件将同时删除对应的向量数据，此操作不可恢复！"):
            return
        
        # 在新线程中处理删除
        self.progress_bar.start()
        self.progress_label.config(text="正在删除文件...")
        
        def delete():
            try:
                deleted_count = 0
                
                for item_id in selected_items:
                    # 获取文件路径
                    item_values = self.file_tree.item(item_id, 'values')
                    if len(item_values) >= 3:
                        file_path = item_values[2]  # 路径列
                        
                        # 从记录中删除
                        self.file_records = [r for r in self.file_records if r.get('file_path') != file_path]
                        deleted_count += 1
                
                # 保存记录
                self._save_file_records()
                
                # 重建索引（移除已删除文件的向量）
                if self.rag_kb:
                    # 获取所有保留的文件路径
                    retained_paths = {r.get('file_path') for r in self.file_records}
                    
                    # 过滤 chunks
                    original_count = len(self.rag_kb.chunks)
                    self.rag_kb.chunks = [c for c in self.rag_kb.chunks if c.source_file in retained_paths]
                    removed_chunks = original_count - len(self.rag_kb.chunks)
                    
                    # 保存索引
                    self.rag_kb.save_index()
                    
                    print(f"删除了 {deleted_count} 个文件记录，移除了 {removed_chunks} 个向量块")
                
                self.window.after(0, lambda: self._on_delete_complete(deleted_count))
                
            except Exception as e:
                print(f"删除文件失败：{e}")
                import traceback
                traceback.print_exc()
                self.window.after(0, lambda: self._on_delete_complete(0, str(e)))
        
        thread = threading.Thread(target=delete, daemon=True)
        thread.start()
    
    def _on_delete_complete(self, count, error=None):
        """删除完成回调"""
        self.progress_bar.stop()
        
        if error:
            self.progress_label.config(text=f"✗ 删除失败：{error}")
            messagebox.showerror("错误", f"删除失败：{error}")
        else:
            self.progress_label.config(text=f"✓ 成功删除 {count} 个文件")
            messagebox.showinfo("成功", f"成功删除 {count} 个文件")
        
        self._refresh_stats()
        self._update_file_tree()
        self.progress_label.config(text="就绪")
    
    def _on_refresh(self):
        """刷新按钮点击事件"""
        self._refresh_stats()
        self._update_file_tree()
        self.progress_label.config(text="✓ 已刷新")
        self.window.after(1000, lambda: self.progress_label.config(text="就绪"))

    def _on_config(self):
        """配置按钮点击事件 - 打开配置对话框"""
        self._open_config_dialog()

    def _open_config_dialog(self):
        """打开配置对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("⚙️ 知识库配置")
        dialog.geometry("500x400")
        dialog.configure(bg="#f5f5f5")
        dialog.transient(self.window)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # 主容器
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="知识库配置",
            font=("微软雅黑", 16, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        )
        title_label.pack(pady=(0, 20))

        # 1. 文本分割策略配置
        strategy_frame = tk.LabelFrame(
            main_frame,
            text="文本分割策略",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#333333",
            padx=15,
            pady=15
        )
        strategy_frame.pack(fill=tk.X, pady=(0, 15))

        # 获取当前策略
        current_strategy = 'sentence_boundary'
        if KB_MANAGER_AVAILABLE:
            try:
                from kb_manager_fast import get_fast_knowledge_base
                kb = get_fast_knowledge_base()
                strategies = kb.get_available_strategies()
                current_strategy = kb._text_splitter_strategy_name
            except:
                strategies = {
                    'fixed_window': '固定窗口分割',
                    'sentence_boundary': '句子边界分割',
                    'dynamic_semantic': '动态语义聚类分割'
                }
        else:
            strategies = {
                'fixed_window': '固定窗口分割',
                'sentence_boundary': '句子边界分割',
                'dynamic_semantic': '动态语义聚类分割'
            }

        tk.Label(
            strategy_frame,
            text="选择分割策略:",
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#333333"
        ).pack(anchor="w", pady=(0, 5))

        strategy_var = tk.StringVar(value=current_strategy)
        strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=strategy_var,
            values=list(strategies.keys()),
            state="readonly",
            font=("微软雅黑", 10)
        )
        strategy_combo.pack(fill=tk.X, pady=(0, 5))

        # 策略描述
        strategy_desc = tk.Label(
            strategy_frame,
            text=strategies.get(current_strategy, ""),
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666666",
            wraplength=400,
            justify=tk.LEFT
        )
        strategy_desc.pack(anchor="w")

        def on_strategy_change(event):
            selected = strategy_var.get()
            strategy_desc.config(text=strategies.get(selected, ""))

        strategy_combo.bind("<<ComboboxSelected>>", on_strategy_change)

        # 2. 向量模型配置
        model_frame = tk.LabelFrame(
            main_frame,
            text="向量模型配置",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#333333",
            padx=15,
            pady=15
        )
        model_frame.pack(fill=tk.X, pady=(0, 15))

        # 当前模型信息
        model_info = "BAAI/bge-large-zh-v1.5 (1024维)"
        if KB_MANAGER_AVAILABLE:
            try:
                from kb_manager_fast import get_fast_knowledge_base
                kb = get_fast_knowledge_base()
                model_info = f"当前模型: BAAI/bge-large-zh-v1.5 ({kb.embedding_dim}维)"
            except:
                pass

        tk.Label(
            model_frame,
            text=model_info,
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#333333"
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            model_frame,
            text="说明: 当前使用BGE-Large中文模型，支持1024维向量嵌入。",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666666",
            wraplength=400,
            justify=tk.LEFT
        ).pack(anchor="w")

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(20, 0))

        def save_config():
            """保存配置"""
            selected_strategy = strategy_var.get()
            if KB_MANAGER_AVAILABLE:
                try:
                    from kb_manager_fast import get_fast_knowledge_base
                    kb = get_fast_knowledge_base()
                    kb.set_text_splitter_strategy(selected_strategy)
                    messagebox.showinfo("成功", f"已切换到策略: {strategies.get(selected_strategy, selected_strategy)}")
                except Exception as e:
                    messagebox.showerror("错误", f"切换策略失败: {e}")
            dialog.destroy()

        def cancel():
            """取消"""
            dialog.destroy()

        save_btn = tk.Button(
            button_frame,
            text="💾 保存",
            font=("微软雅黑", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            command=save_config,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = tk.Button(
            button_frame,
            text="❌ 取消",
            font=("微软雅黑", 11),
            bg="#9e9e9e",
            fg="white",
            cursor="hand2",
            command=cancel,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def _on_tree_double_click(self, event):
        """Treeview 双击事件"""
        selected_items = self.file_tree.selection()
        
        if not selected_items:
            return
        
        # 获取第一个选中项的详细信息
        item_id = selected_items[0]
        item_values = self.file_tree.item(item_id, 'values')
        
        if len(item_values) >= 3:
            file_path = item_values[2]
            
            # 显示文件详情对话框
            self._show_file_details(file_path)
    
    def _show_file_details(self, file_path):
        """显示文件详情（包含标签信息，支持编辑）"""
        # 查找记录
        record = None
        for r in self.file_records:
            if r.get('file_path') == file_path:
                record = r
                break
        
        if not record:
            messagebox.showerror("错误", "未找到文件记录")
            return
        
        # 从数据库获取标签信息
        tag_info = None
        if DB_AVAILABLE and record.get('tag_id'):
            try:
                db = get_db_manager()
                tag_info = db.get_tag_by_id(record['tag_id'])
            except Exception as e:
                print(f"获取标签信息失败: {e}")
        
        # 如果没有从数据库获取到，尝试从记录中获取
        if not tag_info:
            tag_info = {
                'domain': record.get('domain', '-'),
                'module': record.get('module', '-'),
                'doc_type': record.get('doc_type', '-'),
                'keyword1': record.get('keyword1', '-'),
                'keyword2': record.get('keyword2', '-')
            }
        
        # 创建详情窗口
        detail_window = tk.Toplevel(self.window)
        detail_window.title("📄 文件详情")
        detail_window.geometry("500x550")
        detail_window.configure(bg="#f5f5f5")
        detail_window.transient(self.window)
        
        # 标题
        title_label = tk.Label(
            detail_window,
            text="📄 文件详细信息",
            font=("微软雅黑", 16, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        )
        title_label.pack(pady=20)
        
        # 详情信息
        info_frame = tk.Frame(detail_window, bg="#ffffff", relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 基础信息
        details = [
            ("文件名:", record.get('file_name', '未知')),
            ("完整路径:", record.get('file_path', '未知')),
            ("文件类型:", record.get('file_type', '未知').upper()),
            ("文件大小:", f"{record.get('file_size', 0):.1f} KB"),
            ("向量块数:", record.get('chunk_count', 0)),
            ("向量绑定:", "✓ 已绑定" if record.get('vector_bound') else "✗ 未绑定"),
            ("添加时间:", record.get('added_at', '未知'))
        ]
        
        # 标签信息
        if isinstance(tag_info, dict):
            tag_details = [
                ("", ""),  # 空行分隔
                ("【元数据标签】", ""),
                ("领域 (Domain):", tag_info.get('domain', '-')),
                ("模块 (Module):", tag_info.get('module', '-')),
                ("文档类型:", tag_info.get('doc_type', '-')),
                ("关键词 1:", tag_info.get('keyword1', '-')),
                ("关键词 2:", tag_info.get('keyword2', '-'))
            ]
        else:
            tag_details = [
                ("", ""),  # 空行分隔
                ("【元数据标签】", ""),
                ("领域 (Domain):", tag_info.domain if tag_info else '-'),
                ("模块 (Module):", tag_info.module if tag_info else '-'),
                ("文档类型:", tag_info.doc_type if tag_info else '-'),
                ("关键词 1:", tag_info.keyword1 if tag_info else '-'),
                ("关键词 2:", tag_info.keyword2 if tag_info else '-')
            ]
        
        all_details = details + tag_details
        
        for i, (label, value) in enumerate(all_details):
            if label == "" and value == "":
                # 空行
                continue
            
            label_widget = tk.Label(
                info_frame,
                text=label,
                font=("微软雅黑", 10, "bold" if "【" in label else ""),
                bg="#ffffff",
                fg="#333333" if "【" not in label else "#2196F3",
                anchor="w",
                padx=15,
                pady=8
            )
            label_widget.grid(row=i, column=0, sticky="w")
            
            value_widget = tk.Label(
                info_frame,
                text=value,
                font=("微软雅黑", 10),
                bg="#ffffff",
                fg="#666666",
                anchor="w",
                padx=10,
                pady=8,
                wraplength=300
            )
            value_widget.grid(row=i, column=1, sticky="w")
        
        info_frame.grid_columnconfigure(1, weight=1)
        
        # 按钮区域
        button_frame = tk.Frame(detail_window, bg="#f5f5f5")
        button_frame.pack(pady=15)
        
        # 编辑标签按钮
        edit_btn = tk.Button(
            button_frame,
            text="✏️ 编辑标签",
            font=("微软雅黑", 11, "bold"),
            bg="#2196F3",
            fg="white",
            cursor="hand2",
            command=lambda: self._edit_metadata_tags(file_path, record, detail_window),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 关闭按钮
        close_btn = tk.Button(
            button_frame,
            text="关闭",
            font=("微软雅黑", 11),
            bg="#9e9e9e",
            fg="white",
            cursor="hand2",
            command=detail_window.destroy,
            relief=tk.FLAT,
            padx=30,
            pady=8
        )
        close_btn.pack(side=tk.LEFT)
    
    def _edit_metadata_tags(self, file_path: str, record: dict, parent_window):
        """编辑元数据标签"""
        if not METADATA_DIALOG_AVAILABLE:
            messagebox.showerror("错误", "元数据编辑对话框不可用")
            return
        
        # 获取当前标签信息
        current_metadata = None
        if DB_AVAILABLE and record.get('tag_id'):
            try:
                db = get_db_manager()
                tag = db.get_tag_by_id(record['tag_id'])
                if tag:
                    current_metadata = DocumentMetadata(
                        domain=tag.domain,
                        module=tag.module,
                        doc_type=tag.doc_type,
                        keyword1=tag.keyword1,
                        keyword2=tag.keyword2
                    )
            except Exception as e:
                print(f"获取当前标签失败: {e}")
        
        # 如果没有从数据库获取到，从记录中获取
        if not current_metadata:
            current_metadata = DocumentMetadata(
                domain=record.get('domain', ''),
                module=record.get('module', ''),
                doc_type=record.get('doc_type', ''),
                keyword1=record.get('keyword1', ''),
                keyword2=record.get('keyword2', '')
            )
        
        def on_save(metadata):
            """保存标签回调"""
            self._save_metadata_tags(file_path, record, metadata)
            # 关闭父窗口并刷新
            parent_window.destroy()
            self._refresh_stats()
            self._update_file_tree()
        
        # 显示元数据编辑对话框
        show_metadata_dialog(self.window, file_path, current_metadata, on_save)
    
    def _save_metadata_tags(self, file_path: str, record: dict, metadata):
        """保存元数据标签到数据库和本地记录"""
        try:
            # 1. 更新数据库
            if DB_AVAILABLE:
                db = get_db_manager()
                
                # 获取或创建新标签
                new_tag = db.get_or_create_tag(
                    domain=metadata.domain,
                    module=metadata.module,
                    doc_type=metadata.doc_type,
                    keyword1=metadata.keyword1 or "",
                    keyword2=metadata.keyword2 or ""
                )
                
                # 更新文档的tag_id
                # 注意：这里我们需要更新文档记录，但db_manager目前没有update_document方法
                # 我们可以通过删除旧记录并添加新记录来实现
                import hashlib
                file_hash = hashlib.md5(file_path.encode()).hexdigest()
                
                # 重新添加文档（会更新tag_id）
                doc = db.add_document(
                    file_name=record.get('file_name', os.path.basename(file_path)),
                    file_path=file_path,
                    file_hash=file_hash,
                    tag_id=new_tag.tag_id,
                    file_size=record.get('file_size', 0) * 1024,  # 转换回字节
                    chunk_count=record.get('chunk_count', 0)
                )
                
                print(f"[GUI] 标签已更新: tag_id={new_tag.tag_id}")
            
            # 2. 更新本地记录
            record['domain'] = metadata.domain
            record['module'] = metadata.module
            record['doc_type'] = metadata.doc_type
            record['keyword1'] = metadata.keyword1
            record['keyword2'] = metadata.keyword2
            
            # 保存到文件
            self._save_file_records()
            
            messagebox.showinfo("成功", "元数据标签已更新")
            
        except Exception as e:
            print(f"[GUI] 保存标签失败: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"保存标签失败: {e}")


def main():
    """主函数"""
    app = RAGManagerGUI()
    app.window.mainloop()


if __name__ == "__main__":
    main()
