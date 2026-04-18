#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态文档处理GUI - 支持文件上传和处理
支持文件类型：图片、PDF、DOCX、MD、CSV、音频、视频
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import json
import queue
from datetime import datetime
from pathlib import Path

# 导入MinerU文档处理器
try:
    from mineru_processor import MinerUProcessor, MinerUResult
    MINERU_AVAILABLE = True
    print("[OK] MinerU处理器已加载")
except ImportError:
    MINERU_AVAILABLE = False
    print("警告：MinerU处理器模块未安装")

# 向后兼容：导入旧的文档处理器
try:
    from document_processor import DocumentProcessor, DocumentType, ProcessingResult
    DOC_PROCESSOR_AVAILABLE = True
except ImportError:
    DOC_PROCESSOR_AVAILABLE = False

# 导入视频下载器
try:
    from video_downloader import download_video, speech_to_text
    VIDEO_DOWNLOADER_AVAILABLE = True
except ImportError:
    VIDEO_DOWNLOADER_AVAILABLE = False
    print("警告：视频下载器模块未安装")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# 文件类型配置
FILE_TYPE_CONFIG = {
    'image': {
        'label': '图片',
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
        'max_size': 10 * 1024 * 1024,  # 10MB
        'color': '#9333ea'  # purple
    },
    'pdf': {
        'label': 'PDF',
        'extensions': ['.pdf'],
        'max_size': 50 * 1024 * 1024,  # 50MB
        'color': '#dc2626'  # red
    },
    'docx': {
        'label': 'Word',
        'extensions': ['.docx', '.doc'],
        'max_size': 20 * 1024 * 1024,  # 20MB
        'color': '#2563eb'  # blue
    },
    'markdown': {
        'label': 'Markdown',
        'extensions': ['.md', '.markdown'],
        'max_size': 5 * 1024 * 1024,  # 5MB
        'color': '#6b7280'  # gray
    },
    'csv': {
        'label': 'CSV',
        'extensions': ['.csv'],
        'max_size': 10 * 1024 * 1024,  # 10MB
        'color': '#16a34a'  # green
    },
    'audio': {
        'label': '音频',
        'extensions': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
        'max_size': 100 * 1024 * 1024,  # 100MB
        'color': '#ea580c'  # orange
    },
    'video': {
        'label': '视频',
        'extensions': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
        'max_size': 500 * 1024 * 1024,  # 500MB
        'color': '#db2777'  # pink
    }
}

# iOS 极简风按钮主题
IOS_BTN = {
    "bg": "#f3f4f6",
    "fg": "#111827",
    "active": "#e5e7eb",
}
IOS_PRIMARY = {
    "bg": "#007aff",
    "fg": "#ffffff",
    "active": "#0062cc",
}
IOS_DANGER = {
    "bg": "#ff3b30",
    "fg": "#ffffff",
    "active": "#d8342b",
}
IOS_SUCCESS = {
    "bg": "#34c759",
    "fg": "#ffffff",
    "active": "#2ea84c",
}


def _load_runtime_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def _save_runtime_config_patch(patch: dict) -> bool:
    try:
        cfg = _load_runtime_config()
        cfg.update(patch or {})
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_file_type(file_path: str) -> tuple:
    """获取文件类型信息"""
    ext = Path(file_path).suffix.lower()
    for file_type, config in FILE_TYPE_CONFIG.items():
        if ext in config['extensions']:
            return file_type, config
    return None, None


class MultimodalProcessingPage(tk.Frame):
    """多模态文档处理页面 - 基于MinerU技术"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f5f5f5", **kwargs)
        runtime_cfg = _load_runtime_config()
        
        # 优先使用MinerU处理器
        if MINERU_AVAILABLE:
            self.mineru_processor = MinerUProcessor(output_dir=OUTPUT_DIR)
            self.processor = None
            print("[OK] 使用MinerU处理器")
        elif DOC_PROCESSOR_AVAILABLE:
            self.mineru_processor = None
            self.processor = DocumentProcessor()
            print("[WARN] 使用旧版文档处理器")
        else:
            self.mineru_processor = None
            self.processor = None
            print("[ERR] 无可用处理器")
        
        self.selected_files = []
        self.edit_mode = False
        self.processing = False
        self.output_dir_var = tk.StringVar(value=(runtime_cfg.get("multimodal_output_dir") or OUTPUT_DIR))
        self.output_format_var = tk.StringVar(value=(runtime_cfg.get("multimodal_output_format") or "md"))
        self._log_queue = queue.Queue()
        self._log_after_id = None
        self._warmup_running = False
        self._mineru_ready = False
        
        # 创建UI
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面"""
        # 外层滚动容器（满足“界面可上下滑动”）
        outer = tk.Frame(self, bg="#f5f5f5")
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, bg="#f5f5f5", highlightthickness=0)
        vbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 主容器
        main_container = tk.Frame(canvas, bg="#f5f5f5")
        win = canvas.create_window((0, 0), window=main_container, anchor="nw")
        main_container.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(win, width=e.width),
        )
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"),
        )
        main_container.configure(padx=20, pady=20)
        
        # 标题
        title_frame = tk.Frame(main_container, bg="#f5f5f5")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            title_frame,
            text="多模态文档处理",
            font=("微软雅黑", 18, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        ).pack(side=tk.LEFT)
        
        # 文件拖放区域
        self.drop_frame = tk.Frame(
            main_container,
            bg="#ffffff",
            highlightbackground="#d1d5db",
            highlightthickness=2,
            height=200
        )
        self.drop_frame.pack(fill=tk.X, pady=(0, 20))
        self.drop_frame.pack_propagate(False)
        
        # 拖放提示
        self.drop_label = tk.Label(
            self.drop_frame,
            text="拖拽文件到此处，或点击选择文件\n支持：图片、PDF、Word、Markdown、CSV、音频、视频",
            font=("微软雅黑", 12),
            bg="#ffffff",
            fg="#6b7280",
            justify=tk.CENTER
        )
        self.drop_label.pack(expand=True)
        
        # 绑定点击事件
        self.drop_frame.bind("<Button-1>", lambda e: self._select_files())
        self.drop_label.bind("<Button-1>", lambda e: self._select_files())
        
        # 支持的文件类型
        types_frame = tk.Frame(main_container, bg="#f5f5f5")
        types_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            types_frame,
            text="支持的文件类型：",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#6b7280"
        ).pack(side=tk.LEFT)
        
        for file_type, config in FILE_TYPE_CONFIG.items():
            badge = tk.Label(
                types_frame,
                text=f" {config['label']} ",
                font=("微软雅黑", 9),
                bg=config['color'],
                fg="#ffffff",
                relief=tk.FLAT
            )
            badge.pack(side=tk.LEFT, padx=(5, 0))
        
        # 已选择文件列表
        files_frame = tk.LabelFrame(
            main_container,
            text="已选择文件",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 文件列表操作栏（极简风）
        files_toolbar = tk.Frame(files_frame, bg="#ffffff")
        files_toolbar.pack(fill=tk.X, padx=6, pady=(6, 2))

        self.edit_btn = tk.Button(
            files_toolbar,
            text="编辑",
            command=self._toggle_edit_mode,
            font=("微软雅黑", 10),
            bg=IOS_BTN["bg"],
            fg=IOS_BTN["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=IOS_BTN["active"],
            activeforeground=IOS_BTN["fg"],
            width=8,
            bd=0
        )
        self.edit_btn.pack(side=tk.LEFT)

        self.select_all_btn = tk.Button(
            files_toolbar,
            text="全选",
            command=self._select_all_checks,
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#007aff",
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#eff6ff",
            activeforeground="#007aff",
            width=8,
            bd=0
        )

        self.unselect_all_btn = tk.Button(
            files_toolbar,
            text="全不选",
            command=self._clear_all_checks,
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#007aff",
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#eff6ff",
            activeforeground="#007aff",
            width=8,
            bd=0
        )

        self.delete_checked_btn = tk.Button(
            files_toolbar,
            text="删除",
            command=self._delete_checked_files,
            font=("微软雅黑", 10),
            bg=IOS_DANGER["bg"],
            fg=IOS_DANGER["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=IOS_DANGER["active"],
            activeforeground=IOS_DANGER["fg"],
            width=8,
            bd=0
        )
        
        # 文件列表
        self.files_listbox = tk.Listbox(
            files_frame,
            font=("微软雅黑", 10),
            selectmode=tk.SINGLE,
            bg="#ffffff",
            fg="#1a1a1a",
            relief=tk.FLAT
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.files_listbox.bind("<ButtonRelease-1>", self._on_files_click)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 按钮区域
        btn_frame = tk.Frame(main_container, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X)
        
        self.clear_btn = tk.Button(
            btn_frame,
            text="清空",
            command=self._clear_files,
            font=("微软雅黑", 11),
            bg=IOS_DANGER["bg"],
            fg=IOS_DANGER["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=IOS_DANGER["active"],
            activeforeground=IOS_DANGER["fg"],
            width=12,
            bd=0
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_btn = tk.Button(
            btn_frame,
            text="选择文件",
            command=self._select_files,
            font=("微软雅黑", 11),
            bg=IOS_PRIMARY["bg"],
            fg=IOS_PRIMARY["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=IOS_PRIMARY["active"],
            activeforeground=IOS_PRIMARY["fg"],
            width=12,
            bd=0
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.select_folder_btn = tk.Button(
            btn_frame,
            text="选择文件夹",
            command=self._select_folder,
            font=("微软雅黑", 11),
            bg=IOS_PRIMARY["bg"],
            fg=IOS_PRIMARY["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=IOS_PRIMARY["active"],
            activeforeground=IOS_PRIMARY["fg"],
            width=12,
            bd=0
        )
        self.select_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.process_btn = tk.Button(
            btn_frame,
            text="开始处理",
            command=self._start_processing,
            font=("微软雅黑", 11),
            bg=IOS_SUCCESS["bg"],
            fg=IOS_SUCCESS["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=IOS_SUCCESS["active"],
            activeforeground=IOS_SUCCESS["fg"],
            width=12,
            bd=0
        )
        self.process_btn.pack(side=tk.LEFT)
        # MinerU 场景下：预热完成前禁止处理
        if self.mineru_processor is not None:
            self.process_btn.configure(state=tk.DISABLED, text="⏳ 预热中", bg="#9ca3af")

        # 预热改为启动自动进行，界面不再展示单独黄色按钮（保持极简风）

        # 导出/默认目录区域
        export_frame = tk.LabelFrame(
            main_container,
            text="导出设置",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        export_frame.pack(fill=tk.X, pady=(12, 0))
        tk.Label(
            export_frame,
            text="默认导出位置：",
            bg="#ffffff",
            fg="#333333",
            font=("微软雅黑", 10),
        ).pack(side=tk.LEFT, padx=(10, 6), pady=8)
        ttk.Entry(
            export_frame,
            textvariable=self.output_dir_var,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=8)
        ttk.Button(
            export_frame,
            text="选择目录",
            command=self._choose_output_dir,
        ).pack(side=tk.LEFT, padx=(0, 6), pady=8)
        ttk.Button(
            export_frame,
            text="打开目录",
            command=self._open_output_dir,
        ).pack(side=tk.LEFT, padx=(0, 10), pady=8)
        tk.Label(
            export_frame,
            text="导出类型：",
            bg="#ffffff",
            fg="#333333",
            font=("微软雅黑", 10),
        ).pack(side=tk.LEFT, padx=(8, 6), pady=8)
        fmt_combo = ttk.Combobox(
            export_frame,
            textvariable=self.output_format_var,
            state="readonly",
            values=["md", "txt"],
            width=6,
        )
        fmt_combo.pack(side=tk.LEFT, padx=(0, 10), pady=8)
        fmt_combo.bind("<<ComboboxSelected>>", lambda _e: self._persist_output_settings())
        
        # 进度区域
        self.progress_frame = tk.LabelFrame(
            main_container,
            text="处理进度",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        
        # 日志区域
        log_frame = tk.LabelFrame(
            main_container,
            text="处理日志",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._log_after_id = self.after(80, self._flush_log_queue)
        # 服务启动即后台预热 MinerU，不阻塞 UI
        self.after(400, lambda: self._start_mineru_warmup(auto=True, force=False))
        
    def _select_files(self):
        """选择文件"""
        # 构建文件类型过滤器
        all_extensions = []
        for config in FILE_TYPE_CONFIG.values():
            all_extensions.extend(config['extensions'])
        
        filetypes = [
            ("所有支持的文件", " ".join(f"*{ext}" for ext in all_extensions)),
            ("图片文件", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
            ("PDF文件", "*.pdf"),
            ("Word文件", "*.docx *.doc"),
            ("Markdown文件", "*.md *.markdown"),
            ("CSV文件", "*.csv"),
            ("音频文件", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac"),
            ("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
            ("所有文件", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="选择要处理的文件",
            filetypes=filetypes
        )
        
        if files:
            for file_path in files:
                self._add_file(file_path)
            self._refresh_files_list()

    def _select_folder(self):
        """选择文件夹并导入支持格式文件（递归）"""
        folder = filedialog.askdirectory(title="选择文件夹（将自动导入支持格式文件）")
        if not folder:
            return

        imported = 0
        for root, _, filenames in os.walk(folder):
            for name in filenames:
                path = os.path.join(root, name)
                if self._add_file(path):
                    imported += 1

        self._refresh_files_list()
        self._log(f"📁 文件夹导入完成：{imported} 个文件（目录：{folder}）")
                
    def _add_file(self, file_path: str):
        """添加文件到列表"""
        # 去重：避免重复添加
        for f in self.selected_files:
            if os.path.normcase(f['path']) == os.path.normcase(file_path):
                return False

        file_type, config = get_file_type(file_path)
        
        if not file_type:
            return False
        
        # 检查文件大小
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            return False
        if file_size > config['max_size']:
            self._log(f"❌ 文件过大: {os.path.basename(file_path)} ({self._format_size(file_size)} > {self._format_size(config['max_size'])})")
            return False
        
        # 添加到列表
        self.selected_files.append({
            'path': file_path,
            'type': file_type,
            'config': config,
            'size': file_size,
            'checked': False
        })

        self._log(f"✅ 已添加: {os.path.basename(file_path)}")
        return True

    def _refresh_files_list(self):
        """刷新文件列表显示"""
        self.files_listbox.delete(0, tk.END)
        for f in self.selected_files:
            if self.edit_mode:
                check = "☑" if f.get('checked') else "☐"
                text = f"{check} [{f['config']['label']}] {os.path.basename(f['path'])} ({self._format_size(f['size'])})"
            else:
                text = f"[{f['config']['label']}] {os.path.basename(f['path'])} ({self._format_size(f['size'])})"
            self.files_listbox.insert(tk.END, text)

    def _toggle_edit_mode(self):
        """切换编辑模式（复选删除）"""
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.edit_btn.configure(text="完成", bg="#e8f1ff", fg="#007aff")
            self.select_all_btn.pack(side=tk.RIGHT, padx=(6, 0))
            self.unselect_all_btn.pack(side=tk.RIGHT, padx=(6, 0))
            self.delete_checked_btn.pack(side=tk.RIGHT, padx=(6, 0))
        else:
            self.edit_btn.configure(text="编辑", bg=IOS_BTN["bg"], fg=IOS_BTN["fg"])
            self.select_all_btn.pack_forget()
            self.unselect_all_btn.pack_forget()
            self.delete_checked_btn.pack_forget()
            for f in self.selected_files:
                f['checked'] = False
        self._refresh_files_list()

    def _on_files_click(self, _event=None):
        """编辑模式下：点击切换勾选"""
        if not self.edit_mode:
            return
        sel = self.files_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self.selected_files):
            self.selected_files[idx]['checked'] = not self.selected_files[idx].get('checked', False)
            self._refresh_files_list()
            self.files_listbox.selection_set(idx)

    def _select_all_checks(self):
        for f in self.selected_files:
            f['checked'] = True
        self._refresh_files_list()

    def _clear_all_checks(self):
        for f in self.selected_files:
            f['checked'] = False
        self._refresh_files_list()

    def _delete_checked_files(self):
        before = len(self.selected_files)
        self.selected_files = [f for f in self.selected_files if not f.get('checked')]
        deleted = before - len(self.selected_files)
        self._refresh_files_list()
        self._log(f"🗑️ 已删除 {deleted} 个文件")
        
    def _clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self._refresh_files_list()
        self._log("🗑️ 已清空文件列表")
        
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
        
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_queue.put(f"[{timestamp}] {message}\n")

    def _flush_log_queue(self):
        """主线程异步刷新日志，避免子线程直接操作UI导致卡顿"""
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return

        try:
            while True:
                line = self._log_queue.get_nowait()
                self.log_text.insert(tk.END, line)
            # no break
        except queue.Empty:
            pass
        self.log_text.see(tk.END)
        try:
            self._log_after_id = self.after(80, self._flush_log_queue)
        except tk.TclError:
            self._log_after_id = None
        
    def _start_processing(self):
        """开始处理文件"""
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择要处理的文件")
            return
            
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请等待")
            return
        if self.mineru_processor is not None and not self._mineru_ready:
            messagebox.showwarning("提示", "MinerU 仍在预热中，请稍候。")
            return
            
        if not DOC_PROCESSOR_AVAILABLE and not MINERU_AVAILABLE:
            messagebox.showerror("错误", "文档处理器模块未安装")
            return
            
        # 在后台线程中处理
        self.processing = True
        self.process_btn.configure(state=tk.DISABLED, text="⏳ 处理中...")
        
        thread = threading.Thread(target=self._process_files_thread)
        thread.daemon = True
        thread.start()

    def _start_mineru_warmup(self, auto: bool = False, force: bool = False):
        if self.mineru_processor is None:
            return
        if self._warmup_running:
            if not auto:
                self._log("ℹ️ MinerU 预热进行中，请稍候")
            return
        self._warmup_running = True
        self.process_btn.configure(state=tk.DISABLED, text="⏳ 预热中", bg="#9ca3af")
        if auto:
            self._log("🚀 服务启动：开始后台预热 MinerU（首次会较慢）")
        else:
            self._log("🚀 手动触发：开始预热 MinerU")
        t = threading.Thread(target=self._mineru_warmup_thread, args=(auto, force), daemon=True)
        t.start()

    def _mineru_warmup_thread(self, auto: bool, force: bool):
        try:
            res = self.mineru_processor.warmup(force=force)
            method = (res.metadata or {}).get("method", "")
            if res.success and method == "warmup_cached":
                self._mineru_ready = True
                self._log("✅ MinerU 已预热（缓存命中）")
            elif res.success and method == "mineru_pipeline":
                self._mineru_ready = True
                self._log("✅ MinerU 预热完成（mineru_pipeline 已加载）")
            elif res.success and method == "fallback":
                # 允许备用解析可用，避免“预热失败但无错误信息”且一直禁用开始处理
                self._mineru_ready = True
                self._log("⚠️ MinerU 当前走备用解析（fallback），可正常开始处理")
            else:
                self._mineru_ready = False
                err = (res.error or "").strip() or "未知错误（可能是模型未就绪或依赖缺失）"
                self._log(f"❌ MinerU 预热失败: {err}")
            if not self._mineru_ready:
                self._log("⏳ MinerU 尚未完成可用预热，开始处理保持禁用")
        except Exception as e:
            self._mineru_ready = False
            self._log(f"❌ MinerU 预热异常: {e}")
        finally:
            self._warmup_running = False
            if self._mineru_ready:
                self.after(0, lambda: self.process_btn.configure(state=tk.NORMAL, text="▶️ 开始处理", bg="#10b981"))
            else:
                self.after(0, lambda: self.process_btn.configure(state=tk.DISABLED, text="⏳ 预热中", bg="#9ca3af"))
        
    def _process_files_thread(self):
        """在后台线程中处理文件"""
        try:
            succeeded_paths = []
            # 使用快照迭代，避免处理中列表被 UI 刷新修改
            for file_info in list(self.selected_files):
                ok = self._process_single_file(file_info)
                if ok:
                    succeeded_paths.append(file_info['path'])
            
            self.after(0, lambda: self._processing_complete(succeeded_paths))
        except Exception as e:
            self.after(0, lambda: self._processing_error(str(e)))
            
    def _process_single_file(self, file_info: dict):
        """处理单个文件"""
        file_path = file_info['path']
        file_type = file_info['type']
        file_name = os.path.basename(file_path)
        
        self._log(f"\n{'='*50}")
        self._log(f"📝 开始处理: {file_name}")
        self._log(f"📂 文件类型: {file_info['config']['label']}")
        self._log(f"📊 文件大小: {self._format_size(file_info['size'])}")
        
        try:
            # 处理文件（优先 MinerU，失败可回退旧处理器）
            result = self._process_with_best_available(file_path, file_type)
            
            if result.success:
                self._log(f"✅ 处理成功")
                self._log(f"📄 提取文本长度: {len(result.content.text)} 字符")
                
                if result.content.images:
                    self._log(f"🖼️ 提取图片数量: {len(result.content.images)}")
                    
                if result.content.tables:
                    self._log(f"📊 提取表格数量: {len(result.content.tables)}")
                    
                # 保存结果
                self._save_result(file_name, result)
                return True
            else:
                self._log(f"❌ 处理失败: {result.error}")
                return False
                
        except Exception as e:
            self._log(f"❌ 处理异常: {str(e)}")
            return False
            
    def _save_result(self, file_name: str, result):
        """保存处理结果"""
        try:
            # 创建输出目录
            out_dir = self.output_dir_var.get().strip() or OUTPUT_DIR
            os.makedirs(out_dir, exist_ok=True)
            self._persist_output_settings()
            
            # 生成输出文件名（可选 txt/md，默认 md）
            base_name = Path(file_name).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_format = (self.output_format_var.get() or "md").strip().lower()
            if output_format not in ("md", "txt"):
                output_format = "md"
            output_file = os.path.join(out_dir, f"{base_name}_{timestamp}.{output_format}")
            
            # 构建纯文本输出
            header = [
                f"文件名: {file_name}",
                f"文件类型: {result.doc_type.value}",
                f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"处理耗时: {result.processing_time:.2f} 秒",
                ""
            ]
            raw_text = (result.content.text or "")
            if output_format == "md":
                content = (
                    f"# 多模态解析结果 - {base_name}\n\n"
                    f"## 基本信息\n"
                    f"- 文件名: {file_name}\n"
                    f"- 文件类型: {result.doc_type.value}\n"
                    f"- 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"- 处理耗时: {result.processing_time:.2f} 秒\n\n"
                    f"## 原始文字内容\n\n{raw_text}\n"
                )
            else:
                content = "\n".join(header) + raw_text
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self._log(f"💾 结果已保存: {output_file}")
            
        except Exception as e:
            self._log(f"❌ 保存结果失败: {str(e)}")

    def _choose_output_dir(self):
        p = filedialog.askdirectory(title="选择导出目录")
        if p:
            self.output_dir_var.set(p)
            self._persist_output_settings()
            self._log(f"📁 已设置默认导出目录: {p}")

    def _open_output_dir(self):
        p = self.output_dir_var.get().strip() or OUTPUT_DIR
        try:
            os.makedirs(p, exist_ok=True)
            os.startfile(p)
        except Exception as e:
            self._log(f"❌ 打开导出目录失败: {e}")

    def _persist_output_settings(self):
        fmt = (self.output_format_var.get() or "md").strip().lower()
        if fmt not in ("md", "txt"):
            fmt = "md"
            self.output_format_var.set(fmt)
        _save_runtime_config_patch(
            {
                "multimodal_output_dir": (self.output_dir_var.get() or OUTPUT_DIR).strip(),
                "multimodal_output_format": fmt,
            }
        )

    def _process_with_best_available(self, file_path: str, file_type: str):
        """
        统一处理入口，避免 self.processor 为空导致崩溃。
        - PDF/Word/Markdown/图片优先走 MinerU
        - 其余类型或 MinerU 失败时回退旧处理器
        """
        ext = Path(file_path).suffix.lower()
        mineru_supported = ext in ['.pdf', '.docx', '.doc', '.md', '.markdown', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        is_pdf = ext == ".pdf"

        if self.mineru_processor is not None and mineru_supported:
            mr = self.mineru_processor.process_document(file_path)
            if mr and getattr(mr, "success", False):
                if is_pdf and (mr.metadata or {}).get("method") == "fallback":
                    raise RuntimeError("PDF要求强制使用MinerU，当前命中了fallback，请检查MinerU环境/依赖后重试。")
                class _Compat:  # 轻量兼容旧结果结构
                    pass
                c = _Compat()
                c.success = True
                c.error = None
                c.doc_type = type("T", (), {"value": file_type})()
                c.processing_time = 0.0
                c.content = type("C", (), {})()
                c.content.text = (mr.content or mr.markdown or "")
                c.content.images = getattr(mr, "images", []) or []
                c.content.tables = getattr(mr, "tables", []) or []
                c.content.metadata = getattr(mr, "metadata", {}) or {}
                return c
            else:
                err = getattr(mr, 'error', 'unknown')
                if is_pdf:
                    raise RuntimeError(f"PDF要求强制使用MinerU，但MinerU处理失败: {err}")
                self._log(f"⚠️ MinerU处理失败，回退旧处理器: {err}")

        if self.processor is None:
            raise RuntimeError("无可用文档处理器（MinerU与旧处理器都不可用）")
        if is_pdf:
            raise RuntimeError("PDF要求强制使用MinerU，当前未启用MinerU处理器。")
        return self.processor.process(file_path)
            
    def _processing_complete(self, succeeded_paths=None):
        """处理完成"""
        succeeded_paths = succeeded_paths or []
        self.processing = False
        self.process_btn.configure(state=tk.NORMAL, text="▶️ 开始处理")
        
        # 将转化成功的文件从列表中移除，失败文件保留便于重试
        if succeeded_paths:
            succeeded_norm = {os.path.normcase(p) for p in succeeded_paths}
            self.selected_files = [
                f for f in self.selected_files
                if os.path.normcase(f.get('path', '')) not in succeeded_norm
            ]
            self._refresh_files_list()
            self._log(f"🧹 已从列表移除 {len(succeeded_paths)} 个成功转化文件")
        
        self._log(f"\n{'='*50}")
        self._log("🎉 所有文件处理完成！")
        messagebox.showinfo("完成", "所有文件处理完成！")
        
    def _processing_error(self, error: str):
        """处理错误"""
        self.processing = False
        self.process_btn.configure(state=tk.NORMAL, text="▶️ 开始处理")
        self._log(f"❌ 处理过程中发生错误: {error}")
        messagebox.showerror("错误", f"处理失败: {error}")


class MultimodalGUI:
    """多模态文档处理GUI主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("多模态文档处理工具")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f5f5f5")
        
        # 创建主界面
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面"""
        # 创建多模态处理页面
        self.processing_page = MultimodalProcessingPage(self.root)
        self.processing_page.pack(fill=tk.BOTH, expand=True)
        
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    app = MultimodalGUI()
    app.run()


if __name__ == "__main__":
    main()
