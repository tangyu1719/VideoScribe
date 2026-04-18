#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答系统GUI - 带Memory机制和左侧导航栏
功能：
1. 左侧导航栏显示所有对话任务
2. 任务自动命名
3. 上下文记忆和压缩
4. 显示记忆上下文窗口
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import os

try:
    from ai_chat_system import AIChatSystem
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False
    print("警告：AI问答系统模块未安装")

try:
    from chat_memory_system import ChatMemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("警告：对话记忆系统模块未安装")


class ChatGUIWithMemory:
    """带Memory的AI问答GUI"""
    
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            self.root.title("🤖 AI技术专家问答系统 - 带记忆功能")
            self.root.geometry("1400x900")
            self.root.minsize(1200, 700)
            self.standalone = True
        else:
            self.root = parent
            self.standalone = False
        
        # 初始化AI系统
        if CHAT_AVAILABLE:
            self.chat_system = AIChatSystem()
        else:
            self.chat_system = None
        
        # 初始化记忆系统
        if MEMORY_AVAILABLE:
            self.memory_manager = ChatMemoryManager()
        else:
            self.memory_manager = None
        
        self.is_processing = False
        
        # 创建界面
        self._create_ui()
        
        # 加载会话列表
        self._refresh_session_list()
        
        # 显示欢迎消息
        self._show_welcome()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架 - 使用PanedWindow实现可调整的分割
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧导航栏
        self._create_sidebar(main_paned)
        
        # 右侧主内容区
        self._create_main_content(main_paned)
        
        # 设置分割比例
        main_paned.add(self.sidebar_frame, width=250)
        main_paned.add(self.content_frame, width=1150)
    
    def _create_sidebar(self, parent):
        """创建左侧导航栏"""
        self.sidebar_frame = tk.Frame(parent, bg="#f8f9fa", bd=1, relief=tk.RAISED)
        self.sidebar_frame.pack_propagate(False)
        
        # 标题
        title_frame = tk.Frame(self.sidebar_frame, bg="#f8f9fa")
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="💬 对话任务",
            font=("微软雅黑", 12, "bold"),
            bg="#f8f9fa",
            fg="#333"
        )
        title_label.pack(side=tk.LEFT)
        
        # 新建对话按钮
        new_btn = tk.Button(
            title_frame,
            text="➕",
            font=("微软雅黑", 10),
            bg="#0066cc",
            fg="white",
            bd=0,
            cursor="hand2",
            command=self._create_new_session
        )
        new_btn.pack(side=tk.RIGHT)
        
        # 分隔线
        separator = tk.Frame(self.sidebar_frame, height=1, bg="#ddd")
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        # 会话列表框架
        list_frame = tk.Frame(self.sidebar_frame, bg="#f8f9fa")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 会话列表（使用Canvas+Frame实现滚动）
        self.session_canvas = tk.Canvas(list_frame, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.session_canvas.yview)
        self.session_list_frame = tk.Frame(self.session_canvas, bg="#f8f9fa")
        
        self.session_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.session_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.session_canvas.create_window((0, 0), window=self.session_list_frame, anchor="nw", width=230)
        
        self.session_list_frame.bind("<Configure>", lambda e: self.session_canvas.configure(scrollregion=self.session_canvas.bbox("all")))
        
        # 底部按钮
        bottom_frame = tk.Frame(self.sidebar_frame, bg="#f8f9fa")
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        import_btn = tk.Button(
            bottom_frame,
            text="📄 导入文件",
            font=("微软雅黑", 9),
            bg="#e9ecef",
            fg="#333",
            bd=0,
            cursor="hand2",
            command=self._import_file
        )
        import_btn.pack(fill=tk.X, pady=2)
        
        folder_btn = tk.Button(
            bottom_frame,
            text="📁 导入文件夹",
            font=("微软雅黑", 9),
            bg="#e9ecef",
            fg="#333",
            bd=0,
            cursor="hand2",
            command=self._import_folder
        )
        folder_btn.pack(fill=tk.X, pady=2)
    
    def _create_main_content(self, parent):
        """创建右侧主内容区"""
        self.content_frame = tk.Frame(parent, bg="#f0f4f8")
        
        # 顶部标题栏
        header_frame = tk.Frame(self.content_frame, bg="#ffffff", bd=1, relief=tk.RAISED)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.configure(highlightbackground="#0066cc", highlightthickness=1)
        
        # 标题和副标题
        title_container = tk.Frame(header_frame, bg="#ffffff")
        title_container.pack(fill=tk.X, padx=15, pady=10)
        
        self.session_title = tk.Label(
            title_container,
            text="AI技术专家问答系统",
            font=("微软雅黑", 14, "bold"),
            bg="#ffffff",
            fg="#0066cc"
        )
        self.session_title.pack(anchor=tk.W)
        
        self.session_subtitle = tk.Label(
            title_container,
            text="基于RAG知识库 + Memory记忆机制",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666"
        )
        self.session_subtitle.pack(anchor=tk.W, pady=(2, 0))
        
        # 记忆上下文窗口（可折叠）
        self.memory_frame = tk.LabelFrame(
            self.content_frame,
            text="🧠 记忆上下文",
            font=("微软雅黑", 9, "bold"),
            bg="#f8f9fa",
            fg="#333"
        )
        self.memory_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.memory_text = scrolledtext.ScrolledText(
            self.memory_frame,
            height=4,
            font=("微软雅黑", 9),
            bg="#f8f9fa",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.memory_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 聊天区域
        chat_frame = tk.LabelFrame(
            self.content_frame,
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
            self.content_frame,
            text="输入问题",
            font=("微软雅黑", 10, "bold"),
            bg="#ffffff",
            fg="#333"
        )
        input_frame.pack(fill=tk.X, pady=5)
        
        # 输入文本框
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
        
        # 按钮区域
        btn_frame = tk.Frame(input_frame, bg="#ffffff")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # RAG开关
        self.use_rag_var = tk.BooleanVar(value=True)
        rag_check = ttk.Checkbutton(
            btn_frame,
            text="使用知识库",
            variable=self.use_rag_var
        )
        rag_check.pack(side=tk.LEFT)
        
        # 发送按钮
        self.send_btn = ttk.Button(
            btn_frame,
            text="发送 ⏎",
            command=self._send_message
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # 状态栏
        status_frame = tk.Frame(self.content_frame, bg="#f0f4f8")
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            font=("微软雅黑", 9),
            bg="#f0f4f8"
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = tk.Label(
            status_frame,
            text="",
            font=("微软雅黑", 9),
            bg="#f0f4f8",
            fg="#666"
        )
        self.stats_label.pack(side=tk.RIGHT)
    
    def _refresh_session_list(self):
        """刷新会话列表"""
        # 清空现有列表
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()
        
        if not self.memory_manager:
            return
        
        # 获取所有会话
        sessions = self.memory_manager.get_all_sessions()
        
        for session in sessions:
            self._create_session_button(session)
    
    def _create_session_button(self, session):
        """创建会话按钮"""
        btn_frame = tk.Frame(self.session_list_frame, bg="#f8f9fa")
        btn_frame.pack(fill=tk.X, pady=2)
        
        # 根据是否当前会话设置背景色
        bg_color = "#e3f2fd" if session['is_current'] else "#f8f9fa"
        
        btn = tk.Button(
            btn_frame,
            text=session['name'],
            font=("微软雅黑", 9),
            bg=bg_color,
            fg="#333",
            bd=0,
            cursor="hand2",
            anchor=tk.W,
            command=lambda sid=session['session_id']: self._switch_session(sid)
        )
        btn.pack(fill=tk.X, padx=5, pady=2)
        
        # 删除按钮
        delete_btn = tk.Label(
            btn_frame,
            text="✕",
            font=("微软雅黑", 8),
            bg=bg_color,
            fg="#999",
            cursor="hand2"
        )
        delete_btn.pack(side=tk.RIGHT, padx=5)
        delete_btn.bind("<Button-1>", lambda e, sid=session['session_id']: self._delete_session(sid))
    
    def _create_new_session(self):
        """创建新会话"""
        if self.memory_manager:
            self.memory_manager.create_new_session()
            self._refresh_session_list()
            self._clear_chat()
            self._update_memory_display()
            self._append_message('system', '🆕 已创建新对话\n\n')
    
    def _switch_session(self, session_id):
        """切换到指定会话"""
        if self.memory_manager:
            self.memory_manager.switch_session(session_id)
            self._refresh_session_list()
            self._load_session_content()
            self._update_memory_display()
    
    def _delete_session(self, session_id):
        """删除会话"""
        if messagebox.askyesno("确认", "确定要删除这个对话吗？"):
            if self.memory_manager:
                self.memory_manager.delete_session(session_id)
                self._refresh_session_list()
                self._load_session_content()
    
    def _load_session_content(self):
        """加载会话内容到聊天区"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        if self.memory_manager and self.memory_manager.current_session:
            session = self.memory_manager.current_session
            
            # 更新标题
            self.session_title.config(text=session.name)
            
            # 加载消息
            for msg in session.messages:
                if msg['role'] == 'user':
                    self._append_message('user', f"👤 **您**: {msg['content']}\n\n")
                elif msg['role'] == 'assistant':
                    self._append_message('assistant', f"🤖 **AI**: {msg['content']}\n\n")
    
    def _update_memory_display(self):
        """更新记忆上下文显示"""
        if not self.memory_manager or not self.memory_manager.current_session:
            return
        
        context = self.memory_manager.get_current_context(max_messages=5)
        
        self.memory_text.config(state=tk.NORMAL)
        self.memory_text.delete('1.0', tk.END)
        if context:
            self.memory_text.insert(tk.END, context)
        else:
            self.memory_text.insert(tk.END, "暂无记忆上下文")
        self.memory_text.config(state=tk.DISABLED)
    
    def _on_enter_key(self, event):
        """处理回车键"""
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
        
        # 显示用户消息
        self._append_message('user', f"👤 **您**: {user_input}\n\n")
        
        # 添加到记忆
        if self.memory_manager:
            self.memory_manager.add_message('user', user_input)
            self._refresh_session_list()
            self._update_memory_display()
        
        # 启动处理
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="正在思考...", fg="#ff6600")
        
        thread = threading.Thread(
            target=self._process_message,
            args=(user_input,),
            daemon=True
        )
        thread.start()
    
    def _process_message(self, user_input):
        """处理消息"""
        try:
            if not self.chat_system:
                self.root.after(0, lambda: self._append_message(
                    'system', '❌ 错误：AI问答系统未初始化\n\n'
                ))
                return
            
            full_response = ""
            for chunk in self.chat_system.reasoning_acting_chat(
                user_input,
                use_rag=self.use_rag_var.get()
            ):
                full_response += chunk
                self.root.after(0, lambda c=chunk: self._append_stream(c))
                time.sleep(0.01)
            
            # 添加到记忆
            if self.memory_manager:
                self.memory_manager.add_message('assistant', full_response)
                self._refresh_session_list()
                self._update_memory_display()
            
            self.root.after(0, lambda: self._append_message('system', '\n---\n\n'))
            
        except Exception as e:
            self.root.after(0, lambda: self._append_message(
                'system', f'❌ 错误: {str(e)}\n\n'
            ))
        finally:
            self.root.after(0, self._on_processing_done)
    
    def _append_stream(self, text):
        """追加流式文本"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _append_message(self, role, message):
        """追加消息"""
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
        """清空聊天区"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _on_processing_done(self):
        """处理完成"""
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="就绪", fg="#333")
    
    def _show_welcome(self):
        """显示欢迎消息"""
        welcome_msg = """👋 欢迎使用带Memory的AI技术专家问答系统！

🧠 **新功能**：
• 左侧导航栏管理多个对话任务
• 自动命名和保存对话历史
• 记忆上下文窗口实时显示
• 消息数超过50条自动压缩归档

💡 **使用提示**：
• 点击左侧"➕"创建新对话
• 每个对话自动保存，可随时切换
• 记忆窗口显示最近的对话上下文

---
"""
        self._append_message('system', welcome_msg)
    
    def _import_file(self):
        """导入文件"""
        if self.chat_system and self.chat_system.kb:
            filetypes = [
                ('文本文件', '*.txt'),
                ('Markdown文件', '*.md'),
                ('PDF文件', '*.pdf'),
                ('Word文档', '*.docx'),
                ('所有支持格式', '*.txt *.md *.pdf *.docx'),
            ]
            file_path = filedialog.askopenfilename(title="选择要导入的文件", filetypes=filetypes)
            if file_path:
                threading.Thread(target=lambda: self.chat_system.kb.add_file(file_path), daemon=True).start()
    
    def _import_folder(self):
        """导入文件夹"""
        if self.chat_system and self.chat_system.kb:
            folder_path = filedialog.askdirectory(title="选择要导入的文件夹")
            if folder_path:
                recursive = messagebox.askyesno("递归导入", "是否递归导入子文件夹？")
                threading.Thread(target=lambda: self.chat_system.kb.add_folder(folder_path, recursive), daemon=True).start()
    
    def run(self):
        if self.standalone:
            self.root.mainloop()


def main():
    app = ChatGUIWithMemory()
    app.run()


if __name__ == "__main__":
    main()
