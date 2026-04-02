#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一链接+文档处理GUI组件
将链接分析和多模态文档处理集成到一个界面

界面布局：
┌─────────────────────────────────────────────────────────────┐
│  链接输入框 + 多模态文档上传区（并排或上下布局）              │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │  📎 链接输入        │  │  📁 多模态文档上传          │  │
│  │  [输入链接URL...]   │  │  [拖放文件/点击选择]        │  │
│  │                     │  │  支持：PDF、Word、图片等    │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  处理按钮区域                                                │
│  [开始处理] [AI配置] [批量导入] [历史记录] [规则配置]        │
├─────────────────────────────────────────────────────────────┤
│  处理进度 + 日志显示区域                                     │
└─────────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
from pathlib import Path

# 导入统一处理器
try:
    from unified_link_document_processor import (
        UnifiedLinkDocumentProcessor, InputType, ContentType,
        UnifiedProcessingResult
    )
    UNIFIED_PROCESSOR_AVAILABLE = True
except ImportError:
    UNIFIED_PROCESSOR_AVAILABLE = False
    print("警告：统一处理器未安装")

# 导入多模态GUI的文件类型配置
try:
    from multimodal_gui import FILE_TYPE_CONFIG, get_file_type
    MULTIMODAL_GUI_AVAILABLE = True
except ImportError:
    MULTIMODAL_GUI_AVAILABLE = False
    # 定义默认文件类型配置
    FILE_TYPE_CONFIG = {
        'image': {
            'label': '图片',
            'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
            'max_size': 10 * 1024 * 1024,
            'color': '#9333ea'
        },
        'pdf': {
            'label': 'PDF',
            'extensions': ['.pdf'],
            'max_size': 50 * 1024 * 1024,
            'color': '#dc2626'
        },
        'docx': {
            'label': 'Word',
            'extensions': ['.docx', '.doc'],
            'max_size': 20 * 1024 * 1024,
            'color': '#2563eb'
        },
        'markdown': {
            'label': 'Markdown',
            'extensions': ['.md', '.markdown'],
            'max_size': 5 * 1024 * 1024,
            'color': '#6b7280'
        },
        'csv': {
            'label': 'CSV',
            'extensions': ['.csv'],
            'max_size': 10 * 1024 * 1024,
            'color': '#16a34a'
        },
        'audio': {
            'label': '音频',
            'extensions': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
            'max_size': 100 * 1024 * 1024,
            'color': '#ea580c'
        },
        'video': {
            'label': '视频',
            'extensions': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
            'max_size': 500 * 1024 * 1024,
            'color': '#db2777'
        }
    }
    
    def get_file_type(file_path: str) -> tuple:
        """获取文件类型信息"""
        ext = Path(file_path).suffix.lower()
        for file_type, config in FILE_TYPE_CONFIG.items():
            if ext in config['extensions']:
                return file_type, config
        return None, None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "OUTPUT")


class UnifiedLinkDocumentPage(tk.Frame):
    """统一链接+文档处理页面"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f5f5f5", **kwargs)
        
        self.processor = UnifiedLinkDocumentProcessor() if UNIFIED_PROCESSOR_AVAILABLE else None
        self.selected_files = []  # 选择的本地文件
        self.processing = False
        self.task_queue = []  # 任务队列
        
        # 配置
        self.config = self._load_config()
        
        # 创建UI
        self._create_ui()
        
    def _load_config(self) -> dict:
        """加载配置"""
        config_file = os.path.join(BASE_DIR, "unified_processor_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
        return {
            'llm_config': {},
            'output_dir': OUTPUT_DIR,
            'user_prompt': ''
        }
    
    def _save_config(self):
        """保存配置"""
        config_file = os.path.join(BASE_DIR, "unified_processor_config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def _create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = tk.Frame(self, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ========== 标题区域 ==========
        title_frame = tk.Frame(main_container, bg="#f5f5f5")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            title_frame,
            text="🔗📁 链接+文档统一处理",
            font=("微软雅黑", 20, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="支持链接分析、多模态文档处理、统一文字分析流程",
            font=("微软雅黑", 11),
            bg="#f5f5f5",
            fg="#6b7280"
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # ========== 输入区域（链接 + 文档上传）==========
        input_frame = tk.LabelFrame(
            main_container,
            text="输入内容",
            font=("微软雅黑", 12, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 左侧：链接输入
        link_frame = tk.Frame(input_frame, bg="#ffffff")
        link_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            link_frame,
            text="📎 链接输入",
            font=("微软雅黑", 12, "bold"),
            bg="#ffffff",
            fg="#2563eb"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 链接输入框
        self.link_entry = tk.Entry(
            link_frame,
            font=("微软雅黑", 11),
            bg="#f9fafb",
            fg="#1a1a1a",
            relief=tk.SOLID,
            bd=1
        )
        self.link_entry.pack(fill=tk.X, pady=(0, 5))
        self.link_entry.insert(0, "输入链接URL（小红书、抖音、网页等）...")
        self.link_entry.bind('<FocusIn>', lambda e: self._on_entry_focus_in())
        self.link_entry.bind('<FocusOut>', lambda e: self._on_entry_focus_out())
        
        # 链接提示
        tk.Label(
            link_frame,
            text="支持：小红书图文/视频、抖音图文/视频、B站、YouTube、网页等",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#6b7280"
        ).pack(anchor=tk.W)
        
        # 分隔线
        separator = tk.Frame(input_frame, bg="#e5e7eb", width=2)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # 右侧：文档上传
        doc_frame = tk.Frame(input_frame, bg="#ffffff")
        doc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            doc_frame,
            text="📁 多模态文档上传",
            font=("微软雅黑", 12, "bold"),
            bg="#ffffff",
            fg="#9333ea"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 文档拖放区域
        self.drop_frame = tk.Frame(
            doc_frame,
            bg="#f9fafb",
            highlightbackground="#d1d5db",
            highlightthickness=2,
            height=80
        )
        self.drop_frame.pack(fill=tk.X)
        self.drop_frame.pack_propagate(False)
        
        self.drop_label = tk.Label(
            self.drop_frame,
            text="📤 拖拽文件到此处，或点击选择文件\n支持：图片、PDF、Word、Markdown、CSV、音频、视频",
            font=("微软雅黑", 10),
            bg="#f9fafb",
            fg="#6b7280",
            justify=tk.CENTER
        )
        self.drop_label.pack(expand=True)
        
        # 绑定点击事件
        self.drop_frame.bind("<Button-1>", lambda e: self._select_files())
        self.drop_label.bind("<Button-1>", lambda e: self._select_files())
        
        # 支持的文件类型标签
        types_frame = tk.Frame(doc_frame, bg="#ffffff")
        types_frame.pack(fill=tk.X, pady=(5, 0))
        
        for file_type, config in FILE_TYPE_CONFIG.items():
            badge = tk.Label(
                types_frame,
                text=f" {config['label']} ",
                font=("微软雅黑", 8),
                bg=config['color'],
                fg="#ffffff",
                relief=tk.FLAT
            )
            badge.pack(side=tk.LEFT, padx=(0, 5))
        
        # ========== 已选择内容区域 ==========
        content_frame = tk.LabelFrame(
            main_container,
            text="已选择的内容",
            font=("微软雅黑", 12, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        content_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 内容列表
        list_container = tk.Frame(content_frame, bg="#ffffff")
        list_container.pack(fill=tk.X, padx=10, pady=10)
        
        # 链接显示
        self.link_display = tk.Label(
            list_container,
            text="链接：未输入",
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#6b7280",
            anchor=tk.W
        )
        self.link_display.pack(fill=tk.X, pady=(0, 5))
        
        # 文件列表
        self.files_listbox = tk.Listbox(
            list_container,
            font=("微软雅黑", 10),
            selectmode=tk.SINGLE,
            bg="#ffffff",
            fg="#1a1a1a",
            relief=tk.FLAT,
            height=3
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.files_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        # ========== 按钮区域 ==========
        btn_frame = tk.Frame(main_container, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 左侧按钮组
        left_btns = tk.Frame(btn_frame, bg="#f5f5f5")
        left_btns.pack(side=tk.LEFT)
        
        self.process_btn = tk.Button(
            left_btns,
            text="▶️ 开始处理",
            command=self._start_processing,
            font=("微软雅黑", 12, "bold"),
            bg="#10b981",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=15,
            height=2
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = tk.Button(
            left_btns,
            text="🗑️ 清空",
            command=self._clear_all,
            font=("微软雅黑", 11),
            bg="#ef4444",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=10
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧按钮组
        right_btns = tk.Frame(btn_frame, bg="#f5f5f5")
        right_btns.pack(side=tk.RIGHT)
        
        self.ai_config_btn = tk.Button(
            right_btns,
            text="⚙️ AI配置",
            command=self._open_ai_config,
            font=("微软雅黑", 10),
            bg="#3b82f6",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=10
        )
        self.ai_config_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_btn = tk.Button(
            right_btns,
            text="📋 批量导入",
            command=self._batch_import,
            font=("微软雅黑", 10),
            bg="#8b5cf6",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=10
        )
        self.batch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.history_btn = tk.Button(
            right_btns,
            text="📚 历史记录",
            command=self._show_history,
            font=("微软雅黑", 10),
            bg="#f59e0b",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=10
        )
        self.history_btn.pack(side=tk.LEFT)
        
        # ========== 进度区域 ==========
        self.progress_frame = tk.LabelFrame(
            main_container,
            text="处理进度",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)
        
        # 状态标签
        self.status_label = tk.Label(
            self.progress_frame,
            text="就绪",
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#6b7280"
        )
        self.status_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # ========== 日志区域 ==========
        log_frame = tk.LabelFrame(
            main_container,
            text="处理日志",
            font=("微软雅黑", 11, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            relief=tk.FLAT,
            wrap=tk.WORD,
            height=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _on_entry_focus_in(self):
        """链接输入框获得焦点"""
        if self.link_entry.get() == "输入链接URL（小红书、抖音、网页等）...":
            self.link_entry.delete(0, tk.END)
            self.link_entry.config(fg="#1a1a1a")
    
    def _on_entry_focus_out(self):
        """链接输入框失去焦点"""
        if not self.link_entry.get():
            self.link_entry.insert(0, "输入链接URL（小红书、抖音、网页等）...")
            self.link_entry.config(fg="#6b7280")
        self._update_link_display()
    
    def _update_link_display(self):
        """更新链接显示"""
        link = self.link_entry.get()
        if link and link != "输入链接URL（小红书、抖音、网页等）...":
            # 截断显示
            display_link = link[:60] + "..." if len(link) > 60 else link
            self.link_display.config(text=f"链接：{display_link}", fg="#2563eb")
        else:
            self.link_display.config(text="链接：未输入", fg="#6b7280")
    
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
    
    def _add_file(self, file_path: str):
        """添加文件到列表"""
        file_type, config = get_file_type(file_path)
        
        if not file_type:
            self._log(f"❌ 不支持的文件类型: {os.path.basename(file_path)}")
            return
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > config['max_size']:
            self._log(f"❌ 文件过大: {os.path.basename(file_path)}")
            return
        
        # 添加到列表
        self.selected_files.append({
            'path': file_path,
            'type': file_type,
            'config': config,
            'size': file_size
        })
        
        # 更新列表显示
        display_text = f"[{config['label']}] {os.path.basename(file_path)}"
        self.files_listbox.insert(tk.END, display_text)
        
        self._log(f"✅ 已添加文件: {os.path.basename(file_path)}")
    
    def _clear_all(self):
        """清空所有内容"""
        # 清空链接
        self.link_entry.delete(0, tk.END)
        self.link_entry.insert(0, "输入链接URL（小红书、抖音、网页等）...")
        self.link_entry.config(fg="#6b7280")
        self._update_link_display()
        
        # 清空文件
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 重置进度
        self.progress_var.set(0)
        self.status_label.config(text="就绪", fg="#6b7280")
        
        self._log("🗑️ 已清空所有内容")
    
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()
    
    def _update_progress(self, stage: str, progress: int, message: str):
        """更新进度"""
        self.progress_var.set(progress)
        self.status_label.config(text=f"[{stage}] {message}", fg="#2563eb")
        self._log(f"📊 {stage}: {progress}% - {message}")
        self.update()
    
    def _start_processing(self):
        """开始处理"""
        # 获取链接
        link = self.link_entry.get()
        has_link = link and link != "输入链接URL（小红书、抖音、网页等）..."
        
        # 检查是否有内容可处理
        if not has_link and not self.selected_files:
            messagebox.showwarning("警告", "请输入链接或选择要处理的文件")
            return
        
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请等待")
            return
        
        if not UNIFIED_PROCESSOR_AVAILABLE:
            messagebox.showerror("错误", "统一处理器模块未安装")
            return
        
        # 构建任务队列
        self.task_queue = []
        
        if has_link:
            self.task_queue.append({
                'type': 'url',
                'source': link
            })
        
        for file_info in self.selected_files:
            self.task_queue.append({
                'type': 'file',
                'source': file_info['path'],
                'file_info': file_info
            })
        
        # 开始处理
        self.processing = True
        self.process_btn.config(state=tk.DISABLED, text="⏳ 处理中...")
        
        thread = threading.Thread(target=self._processing_thread)
        thread.daemon = True
        thread.start()
    
    def _processing_thread(self):
        """处理线程"""
        try:
            total_tasks = len(self.task_queue)
            
            for i, task in enumerate(self.task_queue, 1):
                self._log(f"\n{'='*50}")
                self._log(f"📝 处理任务 {i}/{total_tasks}")
                
                # 设置回调
                self.processor.set_callbacks(
                    progress_callback=lambda s, p, m: self._update_progress(s, int((i-1)*100/total_tasks + p/total_tasks), m),
                    log_callback=lambda m, l: self._log(m)
                )
                
                # 处理
                result = self.processor.process(
                    task['source'],
                    is_url=(task['type'] == 'url'),
                    llm_config=self.config.get('llm_config', {}),
                    output_dir=self.config.get('output_dir', OUTPUT_DIR),
                    user_prompt=self.config.get('user_prompt', '')
                )
                
                if result.success:
                    self._log(f"✅ 任务完成: {result.output_file}")
                else:
                    self._log(f"❌ 任务失败: {result.error}")
            
            self.after(0, self._processing_complete)
            
        except Exception as e:
            self.after(0, lambda: self._processing_error(str(e)))
    
    def _processing_complete(self):
        """处理完成"""
        self.processing = False
        self.process_btn.config(state=tk.NORMAL, text="▶️ 开始处理")
        self.progress_var.set(100)
        self.status_label.config(text="处理完成", fg="#10b981")
        self._log("\n🎉 所有任务处理完成！")
        messagebox.showinfo("完成", "所有任务处理完成！")
    
    def _processing_error(self, error: str):
        """处理错误"""
        self.processing = False
        self.process_btn.config(state=tk.NORMAL, text="▶️ 开始处理")
        self.status_label.config(text=f"处理失败: {error}", fg="#ef4444")
        self._log(f"\n❌ 处理失败: {error}")
        messagebox.showerror("错误", f"处理失败: {error}")
    
    def _open_ai_config(self):
        """打开AI配置"""
        # TODO: 实现AI配置对话框
        self._log("⚙️ 打开AI配置...")
        messagebox.showinfo("AI配置", "AI配置功能待实现")
    
    def _batch_import(self):
        """批量导入"""
        # TODO: 实现批量导入功能
        self._log("📋 批量导入...")
        messagebox.showinfo("批量导入", "批量导入功能待实现")
    
    def _show_history(self):
        """显示历史记录"""
        # TODO: 实现历史记录功能
        self._log("📚 显示历史记录...")
        messagebox.showinfo("历史记录", "历史记录功能待实现")


# 测试运行
if __name__ == "__main__":
    root = tk.Tk()
    root.title("链接+文档统一处理")
    root.geometry("900x700")
    root.configure(bg="#f5f5f5")
    
    # 创建页面
    page = UnifiedLinkDocumentPage(root)
    page.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
