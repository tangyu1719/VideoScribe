#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答系统GUI - 最终版本
- 左侧任务管理面板（按图1样式）
- 上下文使用进度圆圈显示
- 任务切换和管理功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import os
import math

try:
    from ai_chat_system import AIChatSystem
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False

try:
    from chat_memory_system import ChatMemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


class CircularProgress(tk.Canvas):
    """圆形进度条组件"""
    def __init__(self, parent, size=40, thickness=4, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#f8f9fa", highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.progress = 0
        self.max_value = 100
        
        # 绘制背景圆
        self.bg_circle = self.create_oval(
            thickness, thickness, size-thickness, size-thickness,
            outline="#e0e0e0", width=thickness
        )
        
        # 绘制进度弧
        self.arc = self.create_arc(
            thickness, thickness, size-thickness, size-thickness,
            start=90, extent=0, outline="#0066cc", width=thickness, style="arc"
        )
        
        # 中心文字
        self.text = self.create_text(
            size//2, size//2, text="0%", font=("微软雅黑", 9, "bold"), fill="#333"
        )
    
    def set_progress(self, value, max_value=100):
        """设置进度值"""
        self.progress = min(value, max_value)
        self.max_value = max_value
        percentage = (self.progress / max_value) * 100
        
        # 计算角度
        extent = -(self.progress / max_value) * 360
        
        # 更新弧
        self.itemconfig(self.arc, extent=extent)
        
        # 更新文字
        self.itemconfig(self.text, text=f"{int(percentage)}%")
        
        # 根据进度改变颜色
        if percentage < 50:
            color = "#4caf50"  # 绿色
        elif percentage < 80:
            color = "#ff9800"  # 橙色
        else:
            color = "#f44336"  # 红色
        
        self.itemconfig(self.arc, outline=color)


class TaskItem(tk.Frame):
    """任务列表项"""
    def __init__(self, parent, session_data, on_click=None, on_delete=None, **kwargs):
        super().__init__(parent, bg="#f8f9fa", **kwargs)
        
        self.session_id = session_data['session_id']
        self.is_current = session_data.get('is_current', False)
        
        # 背景色
        bg_color = "#e3f2fd" if self.is_current else "#f8f9fa"
        self.configure(bg=bg_color)
        
        # 任务名称
        name_label = tk.Label(
            self,
            text=session_data['name'],
            font=("微软雅黑", 10),
            bg=bg_color,
            fg="#333",
            anchor=tk.W,
            cursor="hand2"
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)
        
        # 上下文进度圆圈
        msg_count = session_data.get('message_count', 0)
        max_msgs = 50  # 最大消息数
        progress = min(msg_count / max_msgs * 100, 100)
        
        self.progress_circle = CircularProgress(self, size=36, thickness=3)
        self.progress_circle.pack(side=tk.RIGHT, padx=5)
        self.progress_circle.set_progress(msg_count, max_msgs)
        
        # 删除按钮
        delete_btn = tk.Label(
            self,
            text="✕",
            font=("微软雅黑", 10),
            bg=bg_color,
            fg="#999",
            cursor="hand2",
            width=3
        )
        delete_btn.pack(side=tk.RIGHT, padx=5)
        delete_btn.bind("<Button-1>", lambda e: on_delete(self.session_id) if on_delete else None)
        
        # 点击事件
        if on_click:
            name_label.bind("<Button-1>", lambda e: on_click(self.session_id))
            self.bind("<Button-1>", lambda e: on_click(self.session_id))


class ChatGUIFinal:
    """最终版AI问答GUI"""
    
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            self.root.title("🤖 AI技术专家问答系统")
            self.root.geometry("1400x900")
            self.root.minsize(1200, 700)
            self.standalone = True
        else:
            self.root = parent
            self.standalone = False
        
        # 初始化系统
        self.chat_system = AIChatSystem() if CHAT_AVAILABLE else None
        self.memory_manager = ChatMemoryManager() if MEMORY_AVAILABLE else None
        
        self.is_processing = False
        self.current_session_id = None
        
        # 创建界面
        self._create_ui()
        
        # 加载任务列表
        self._refresh_task_list()
        
        # 显示欢迎消息
        self._show_welcome()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主分割面板
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#f0f4f8")
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧任务管理面板
        self._create_left_panel(main_paned)
        
        # 右侧主内容区
        self._create_right_panel(main_paned)
        
        # 设置分割比例
        main_paned.add(self.left_panel, width=300)
        main_paned.add(self.right_panel, width=1100)
    
    def _create_left_panel(self, parent):
        """创建左侧任务管理面板"""
        self.left_panel = tk.Frame(parent, bg="#f8f9fa", bd=1, relief=tk.RAISED)
        self.left_panel.pack_propagate(False)
        
        # 面板标题
        header_frame = tk.Frame(self.left_panel, bg="#0066cc", height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="💬 任务管理",
            font=("微软雅黑", 12, "bold"),
            bg="#0066cc",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # 新建任务按钮
        new_btn = tk.Button(
            header_frame,
            text="➕ 新建",
            font=("微软雅黑", 9),
            bg="#4caf50",
            fg="white",
            bd=0,
            cursor="hand2",
            command=self._create_new_task
        )
        new_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # 任务列表区域
        list_container = tk.Frame(self.left_panel, bg="#f8f9fa")
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 任务列表（带滚动条）
        self.task_canvas = tk.Canvas(list_container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.task_canvas.yview)
        self.task_list_frame = tk.Frame(self.task_canvas, bg="#f8f9fa")
        
        self.task_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.task_canvas.create_window((0, 0), window=self.task_list_frame, anchor="nw", width=280)
        
        self.task_list_frame.bind("<Configure>", 
            lambda e: self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all")))
        
        # 底部信息
        info_frame = tk.Frame(self.left_panel, bg="#f8f9fa", height=40)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.task_count_label = tk.Label(
            info_frame,
            text="任务数: 0",
            font=("微软雅黑", 9),
            bg="#f8f9fa",
            fg="#666"
        )
        self.task_count_label.pack(side=tk.LEFT, padx=10, pady=10)
    
    def _create_right_panel(self, parent):
        """创建右侧主内容区"""
        self.right_panel = tk.Frame(parent, bg="#f0f4f8")
        
        # 顶部标题栏
        header_frame = tk.Frame(self.right_panel, bg="#ffffff", bd=1, relief=tk.RAISED)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_container = tk.Frame(header_frame, bg="#ffffff")
        title_container.pack(fill=tk.X, padx=15, pady=10)
        
        self.task_title = tk.Label(
            title_container,
            text="AI技术专家问答系统",
            font=("微软雅黑", 14, "bold"),
            bg="#ffffff",
            fg="#0066cc"
        )
        self.task_title.pack(anchor=tk.W)
        
        self.task_subtitle = tk.Label(
            title_container,
            text="基于RAG知识库 + Memory记忆机制",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666"
        )
        self.task_subtitle.pack(anchor=tk.W, pady=(2, 0))
        
        # 工具栏
        toolbar = tk.Frame(self.right_panel, bg="#f8f9fa", height=40)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 导入按钮
        btn_style = {"font": ("微软雅黑", 9), "bg": "#e3f2fd", "fg": "#0066cc", 
                     "bd": 0, "cursor": "hand2", "padx": 10, "pady": 5}
        
        import_file_btn = tk.Button(toolbar, text="📄 导入文件", command=self._import_file, **btn_style)
        import_file_btn.pack(side=tk.LEFT, padx=5)
        
        import_folder_btn = tk.Button(toolbar, text="📁 导入文件夹", command=self._import_folder, **btn_style)
        import_folder_btn.pack(side=tk.LEFT, padx=5)
        
        index_btn = tk.Button(toolbar, text="📚 索引Output", command=self._index_output, **btn_style)
        index_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(toolbar, text="🗑️ 清空对话", command=self._clear_chat, **btn_style)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        help_btn = tk.Button(toolbar, text="❓ 帮助", command=self._show_help, **btn_style)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # 聊天区域
        chat_frame = tk.LabelFrame(
            self.right_panel,
            text="对话记录",
            font=("微软雅黑", 10, "bold"),
            bg="#ffffff",
            fg="#0066cc"
        )
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置标签样式
        self.chat_text.tag_configure('user', foreground='#0066cc', font=('Microsoft YaHei', 11, 'bold'))
        self.chat_text.tag_configure('assistant', foreground='#009900', font=('Microsoft YaHei', 11, 'bold'))
        self.chat_text.tag_configure('system', foreground='#666666', font=('Microsoft YaHei', 10))
        
        # 输入区域
        input_frame = tk.LabelFrame(
            self.right_panel,
            text="输入问题",
            font=("微软雅黑", 10, "bold"),
            bg="#ffffff",
            fg="#333"
        )
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 11),
            height=3,
            padx=5,
            pady=5
        )
        self.input_text.pack(fill=tk.X, padx=5, pady=5)
        self.input_text.bind('<Return>', self._on_enter_key)
        
        # 底部按钮区
        btn_frame = tk.Frame(input_frame, bg="#ffffff")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_rag_var = tk.BooleanVar(value=True)
        rag_check = ttk.Checkbutton(btn_frame, text="使用知识库", variable=self.use_rag_var)
        rag_check.pack(side=tk.LEFT)
        
        self.send_btn = ttk.Button(btn_frame, text="发送 ⏎", command=self._send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        # 状态栏
        status_frame = tk.Frame(self.right_panel, bg="#f0f4f8")
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(status_frame, text="就绪", font=("微软雅黑", 9), bg="#f0f4f8")
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = tk.Label(status_frame, text="", font=("微软雅黑", 9), bg="#f0f4f8", fg="#666")
        self.stats_label.pack(side=tk.RIGHT)
    
    def _refresh_task_list(self):
        """刷新任务列表"""
        # 清空现有列表
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        
        if not self.memory_manager:
            return
        
        # 获取所有任务
        sessions = self.memory_manager.get_all_sessions()
        
        # 更新任务计数
        self.task_count_label.config(text=f"任务数: {len(sessions)}")
        
        # 创建任务项
        for session in sessions:
            task_item = TaskItem(
                self.task_list_frame,
                session,
                on_click=self._switch_task,
                on_delete=self._delete_task
            )
            task_item.pack(fill=tk.X, pady=2, padx=5)
    
    def _create_new_task(self):
        """创建新任务"""
        if self.memory_manager:
            session = self.memory_manager.create_new_session()
            self.current_session_id = session.session_id
            self._refresh_task_list()
            self._clear_chat()
            self._update_title(session.name)
            self._append_message('system', '🆕 已创建新任务\n\n')
    
    def _switch_task(self, session_id):
        """切换到指定任务"""
        if self.memory_manager:
            session = self.memory_manager.switch_session(session_id)
            if session:
                self.current_session_id = session_id
                self._refresh_task_list()
                self._load_task_content(session)
                self._update_title(session.name)
    
    def _delete_task(self, session_id):
        """删除任务"""
        if messagebox.askyesno("确认", "确定要删除这个任务吗？"):
            if self.memory_manager:
                self.memory_manager.delete_session(session_id)
                self._refresh_task_list()
                if self.current_session_id == session_id:
                    self._clear_chat()
                    self._update_title("AI技术专家问答系统")
    
    def _load_task_content(self, session):
        """加载任务内容"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        
        for msg in session.messages:
            if msg['role'] == 'user':
                self._append_message('user', f"👤 **您**: {msg['content']}\n\n")
            elif msg['role'] == 'assistant':
                self._append_message('assistant', f"🤖 **AI**: {msg['content']}\n\n")
        
        self.chat_text.config(state=tk.DISABLED)
    
    def _update_title(self, name):
        """更新标题"""
        self.task_title.config(text=name)
    
    def _on_enter_key(self, event):
        if not event.state & 0x1:
            self._send_message()
            return 'break'
    
    def _send_message(self):
        """发送消息"""
        if self.is_processing:
            return
        
        user_input = self.input_text.get('1.0', tk.END).strip()
        if not user_input:
            return
        
        self.input_text.delete('1.0', tk.END)
        self._append_message('user', f"👤 **您**: {user_input}\n\n")
        
        if self.memory_manager:
            self.memory_manager.add_message('user', user_input)
            self._refresh_task_list()
        
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="正在思考...", fg="#ff6600")
        
        thread = threading.Thread(target=self._process_message, args=(user_input,), daemon=True)
        thread.start()
    
    def _process_message(self, user_input):
        try:
            if not self.chat_system:
                self.root.after(0, lambda: self._append_message('system', '❌ AI系统未初始化\n\n'))
                return
            
            full_response = ""
            for chunk in self.chat_system.reasoning_acting_chat(user_input, use_rag=self.use_rag_var.get()):
                full_response += chunk
                self.root.after(0, lambda c=chunk: self._append_stream(c))
                time.sleep(0.01)
            
            if self.memory_manager:
                self.memory_manager.add_message('assistant', full_response)
                self._refresh_task_list()
            
            self.root.after(0, lambda: self._append_message('system', '\n---\n\n'))
            
        except Exception as e:
            self.root.after(0, lambda: self._append_message('system', f'❌ 错误: {str(e)}\n\n'))
        finally:
            self.root.after(0, self._on_processing_done)
    
    def _append_stream(self, text):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _append_message(self, role, message):
        self.chat_text.config(state=tk.NORMAL)
        if role == 'user':
            self.chat_text.insert(tk.END, message, 'user')
        elif role == 'assistant':
            self.chat_text.insert(tk.END, message, 'assistant')
        else:
            self.chat_text.insert(tk.END, message, 'system')
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _clear_chat(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _on_processing_done(self):
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="就绪", fg="#333")
    
    def _import_file(self):
        if self.chat_system and self.chat_system.kb:
            filetypes = [('文本文件', '*.txt'), ('Markdown文件', '*.md'), 
                        ('PDF文件', '*.pdf'), ('Word文档', '*.docx')]
            file_path = filedialog.askopenfilename(title="选择文件", filetypes=filetypes)
            if file_path:
                threading.Thread(target=lambda: self.chat_system.kb.add_file(file_path), daemon=True).start()
    
    def _import_folder(self):
        if self.chat_system and self.chat_system.kb:
            folder_path = filedialog.askdirectory(title="选择文件夹")
            if folder_path:
                recursive = messagebox.askyesno("递归导入", "是否递归子文件夹？")
                threading.Thread(target=lambda: self.chat_system.kb.add_folder(folder_path, recursive), daemon=True).start()
    
    def _index_output(self):
        if self.chat_system:
            threading.Thread(target=self.chat_system.index_output_documents, daemon=True).start()
    
    def _show_help(self):
        help_text = """AI技术专家问答系统 - 使用帮助

【功能说明】
• 左侧任务管理：创建、切换、删除对话任务
• 上下文进度：圆圈显示当前任务的上下文使用量
• 记忆机制：自动保存对话历史，支持多任务并行

【操作指南】
• 点击"➕ 新建"创建新任务
• 点击左侧任务项切换对话
• 圆圈颜色：绿色(<50%)、橙色(50-80%)、红色(>80%)

【支持格式】
• TXT、MD、PDF、DOCX文档导入
"""
        messagebox.showinfo("帮助", help_text)
    
    def _show_welcome(self):
        welcome_msg = """👋 欢迎使用AI技术专家问答系统！

🧠 **系统特点**：
• 左侧任务管理面板，支持多任务并行
• 上下文使用进度实时显示（圆圈）
• 自动保存对话历史，随时切换任务

💡 **使用提示**：
• 点击左侧"➕ 新建"创建新任务
• 每个任务独立保存上下文
• 圆圈显示上下文使用量，超过80%会变红

---
"""
        self._append_message('system', welcome_msg)
    
    def run(self):
        if self.standalone:
            self.root.mainloop()


def main():
    app = ChatGUIFinal()
    app.run()


if __name__ == "__main__":
    main()
