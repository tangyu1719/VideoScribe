#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答页面 - 集成任务管理和对话功能
仿ChatGPT/Claude界面设计
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import time
import os
import hashlib
from datetime import datetime

try:
    from ai_chat_system import AIChatSystem
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False


class ChatTask:
    """聊天任务类"""
    def __init__(self, task_id=None, name=None):
        self.task_id = task_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
        self.name = name or f"新对话 {datetime.now().strftime('%H:%M')}"
        self.messages = []  # 消息历史
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.is_active = False
    
    def add_message(self, role, content):
        """添加消息"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now().isoformat()
        
        # 自动命名（基于第一条用户消息）
        if len(self.messages) == 1 and role == 'user':
            self.name = content[:20] + "..." if len(content) > 20 else content
    
    def get_context(self, max_messages=10):
        """获取上下文"""
        return self.messages[-max_messages:]


class AIChatPage(tk.Frame):
    """AI问答页面 - 集成任务管理和对话"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f0f4f8", **kwargs)
        
        # 初始化AI系统
        if CHAT_AVAILABLE:
            self.chat_system = AIChatSystem()
        else:
            self.chat_system = None
        
        # 任务管理
        self.tasks = {}  # 所有任务
        self.current_task = None  # 当前任务
        self.is_processing = False
        
        # 创建界面
        self._create_ui()
        
        # 初始状态：创建一个新任务
        self._create_new_task()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主分割面板
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#f0f4f8")
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧任务管理面板
        self._create_left_panel(main_paned)
        
        # 右侧对话区域
        self._create_right_panel(main_paned)
        
        # 设置分割比例
        main_paned.add(self.left_panel, width=260)
        main_paned.add(self.right_panel, width=1140)
    
    def _create_left_panel(self, parent):
        """创建左侧任务管理面板"""
        self.left_panel = tk.Frame(parent, bg="#f8f9fa", bd=1, relief=tk.RAISED)
        self.left_panel.pack_propagate(False)
        
        # 面板标题栏
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
            text="➕",
            font=("微软雅黑", 12),
            bg="#4caf50",
            fg="white",
            bd=0,
            cursor="hand2",
            width=3,
            command=self._create_new_task
        )
        new_btn.pack(side=tk.RIGHT, padx=10, pady=8)
        
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
        self.task_canvas.create_window((0, 0), window=self.task_list_frame, anchor="nw", width=240)
        
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
        """创建右侧对话区域"""
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
            text="基于RAG知识库 + Reasoning-Acting模式",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666"
        )
        self.task_subtitle.pack(anchor=tk.W, pady=(2, 0))
        
        # 工具栏
        toolbar = tk.Frame(self.right_panel, bg="#f8f9fa", height=40)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        btn_style = {"font": ("微软雅黑", 9), "bg": "#e3f2fd", "fg": "#0066cc", 
                     "bd": 0, "cursor": "hand2", "padx": 10, "pady": 5}
        
        tk.Button(toolbar, text="📄 导入文件", command=self._import_file, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="📁 导入文件夹", command=self._import_folder, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="📚 索引Output", command=self._index_output, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="🗑️ 清空对话", command=self._clear_chat, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="❓ 帮助", command=self._show_help, **btn_style).pack(side=tk.RIGHT, padx=5)
        
        # 对话记录区域
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
            height=15,
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
        
        # 图片预览区域
        self.image_preview_frame = tk.Frame(input_frame, bg="#ffffff", height=80)
        self.image_preview_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        self.image_preview_frame.pack_propagate(False)
        self.image_preview_frame.pack_forget()  # 初始隐藏
        
        self.image_preview_label = tk.Label(
            self.image_preview_frame,
            text="",
            bg="#ffffff"
        )
        self.image_preview_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 删除图片按钮
        self.remove_image_btn = tk.Button(
            self.image_preview_frame,
            text="✕",
            font=("微软雅黑", 8),
            bg="#ff4444",
            fg="white",
            bd=0,
            cursor="hand2",
            command=self._remove_image
        )
        self.remove_image_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
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
        
        # 左侧按钮组
        left_btn_frame = tk.Frame(btn_frame, bg="#ffffff")
        left_btn_frame.pack(side=tk.LEFT)
        
        self.use_rag_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_btn_frame, text="使用知识库", variable=self.use_rag_var).pack(side=tk.LEFT, padx=(0, 10))
        
        # 上传图片按钮
        upload_img_btn = tk.Button(
            left_btn_frame,
            text="📎 图片",
            font=("微软雅黑", 9),
            bg="#e3f2fd",
            fg="#0066cc",
            bd=0,
            cursor="hand2",
            command=self._upload_image
        )
        upload_img_btn.pack(side=tk.LEFT)
        
        self.send_btn = ttk.Button(btn_frame, text="发送 ⏎", command=self._send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        # 存储当前图片路径
        self.current_image_path = None
        
        # 状态栏
        status_frame = tk.Frame(self.right_panel, bg="#f0f4f8")
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(status_frame, text="就绪", font=("微软雅黑", 9), bg="#f0f4f8")
        self.status_label.pack(side=tk.LEFT)
    
    def _create_new_task(self):
        """创建新任务"""
        # 保存当前任务
        if self.current_task:
            self.current_task.is_active = False
        
        # 创建新任务
        task = ChatTask()
        task.is_active = True
        self.tasks[task.task_id] = task
        self.current_task = task
        
        # 清空对话区
        self._clear_chat()
        
        # 刷新任务列表
        self._refresh_task_list()
        
        # 更新标题
        self._update_title(task.name)
        
        # 显示欢迎消息
        self._show_welcome()
    
    def _refresh_task_list(self):
        """刷新任务列表"""
        # 清空现有列表
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        
        # 按更新时间排序
        sorted_tasks = sorted(self.tasks.values(), 
                             key=lambda x: x.updated_at, reverse=True)
        
        for task in sorted_tasks:
            self._create_task_button(task)
        
        # 更新任务计数
        self.task_count_label.config(text=f"任务数: {len(self.tasks)}")
    
    def _create_task_button(self, task):
        """创建任务按钮"""
        # 根据是否当前任务设置背景色
        bg_color = "#e3f2fd" if task.task_id == self.current_task.task_id else "#f8f9fa"
        
        btn_frame = tk.Frame(self.task_list_frame, bg=bg_color)
        btn_frame.pack(fill=tk.X, pady=2, padx=5)
        
        # 任务名称按钮
        btn = tk.Button(
            btn_frame,
            text=task.name,
            font=("微软雅黑", 10),
            bg=bg_color,
            fg="#333",
            bd=0,
            cursor="hand2",
            anchor=tk.W,
            command=lambda tid=task.task_id: self._switch_task(tid)
        )
        btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=8)
        
        # 删除按钮
        if len(self.tasks) > 1:  # 至少保留一个任务
            delete_btn = tk.Label(
                btn_frame,
                text="✕",
                font=("微软雅黑", 10),
                bg=bg_color,
                fg="#999",
                cursor="hand2",
                width=3
            )
            delete_btn.pack(side=tk.RIGHT, padx=5)
            delete_btn.bind("<Button-1>", lambda e, tid=task.task_id: self._delete_task(tid))
    
    def _switch_task(self, task_id):
        """切换到指定任务"""
        if task_id not in self.tasks:
            return
        
        # 保存当前任务状态
        if self.current_task:
            self.current_task.is_active = False
        
        # 切换任务
        self.current_task = self.tasks[task_id]
        self.current_task.is_active = True
        
        # 刷新界面
        self._refresh_task_list()
        self._load_task_content()
        self._update_title(self.current_task.name)
    
    def _delete_task(self, task_id):
        """删除任务"""
        if len(self.tasks) <= 1:
            messagebox.showwarning("提示", "至少保留一个任务")
            return
        
        if messagebox.askyesno("确认", "确定要删除这个任务吗？"):
            del self.tasks[task_id]
            
            # 如果删除的是当前任务，切换到第一个任务
            if self.current_task.task_id == task_id:
                self.current_task = list(self.tasks.values())[0]
                self.current_task.is_active = True
                self._load_task_content()
                self._update_title(self.current_task.name)
            
            self._refresh_task_list()
    
    def _load_task_content(self):
        """加载任务内容"""
        self._clear_chat()
        
        if not self.current_task:
            return
        
        for msg in self.current_task.messages:
            if msg['role'] == 'user':
                self._append_message('user', f"👤 **您**: {msg['content']}\n\n")
            elif msg['role'] == 'assistant':
                self._append_message('assistant', f"🤖 **AI**: {msg['content']}\n\n")
    
    def _update_title(self, name):
        """更新标题"""
        self.task_title.config(text=name)
    
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
        
        # 添加到当前任务
        if self.current_task:
            self.current_task.add_message('user', user_input)
            self._refresh_task_list()
        
        # 启动处理
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="正在思考...", fg="#ff6600")
        
        thread = threading.Thread(target=self._process_message, args=(user_input,), daemon=True)
        thread.start()
    
    def _process_message(self, user_input):
        """处理消息"""
        import logging
        import sys
        
        # 配置日志
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chat_debug.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"开始处理消息: {user_input[:50]}...")
            
            if not self.chat_system:
                logger.error("AI系统未初始化")
                self.after(0, lambda: self._append_message('system', '❌ AI系统未初始化\n\n'))
                return
            
            logger.info("AI系统已初始化，开始调用API")
            
            # 先显示AI标记
            self.after(0, lambda: self._append_message('assistant', '🤖 **AI**: '))
            
            full_response = ""
            chunk_count = 0
            
            logger.info("开始流式获取响应...")
            for chunk in self.chat_system.reasoning_acting_chat(user_input, use_rag=self.use_rag_var.get()):
                chunk_count += 1
                full_response += chunk
                logger.debug(f"收到chunk {chunk_count}: {chunk[:50]}...")
                # 使用默认参数捕获当前chunk值
                self.after(0, lambda text=chunk: self._append_stream(text))
                time.sleep(0.01)
            
            logger.info(f"流式响应完成，共 {chunk_count} 个chunks")
            
            # 添加到当前任务
            if self.current_task:
                self.current_task.add_message('assistant', full_response)
                self.after(0, self._refresh_task_list)
                logger.info("消息已添加到任务")
            
            self.after(0, lambda: self._append_message('system', '\n\n---\n\n'))
            logger.info("消息处理完成")
            
        except Exception as e:
            import traceback
            error_msg = f'❌ 错误: {str(e)}\n{traceback.format_exc()}\n'
            logger.error(f"处理消息时出错: {error_msg}")
            self.after(0, lambda: self._append_message('system', error_msg))
        finally:
            logger.info("处理结束，恢复UI状态")
            self.after(0, self._on_processing_done)
    
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
        """清空对话区"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _on_processing_done(self):
        """处理完成"""
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="就绪", fg="#333")
    
    def _import_file(self):
        """导入文件"""
        if self.chat_system and self.chat_system.kb:
            filetypes = [('文本文件', '*.txt'), ('Markdown文件', '*.md'), 
                        ('PDF文件', '*.pdf'), ('Word文档', '*.docx')]
            file_path = filedialog.askopenfilename(title="选择文件", filetypes=filetypes)
            if file_path:
                threading.Thread(target=lambda: self.chat_system.kb.add_file(file_path), daemon=True).start()
    
    def _import_folder(self):
        """导入文件夹"""
        if self.chat_system and self.chat_system.kb:
            folder_path = filedialog.askdirectory(title="选择文件夹")
            if folder_path:
                recursive = messagebox.askyesno("递归导入", "是否递归子文件夹？")
                threading.Thread(target=lambda: self.chat_system.kb.add_folder(folder_path, recursive), daemon=True).start()
    
    def _index_output(self):
        """索引Output目录"""
        if self.chat_system:
            threading.Thread(target=self.chat_system.index_output_documents, daemon=True).start()
    
    def _upload_image(self):
        """上传图片"""
        filetypes = [
            ('图片文件', '*.png *.jpg *.jpeg *.gif *.bmp'),
            ('PNG图片', '*.png'),
            ('JPEG图片', '*.jpg *.jpeg'),
            ('GIF图片', '*.gif'),
            ('所有文件', '*.*')
        ]
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=filetypes
        )
        
        if file_path:
            try:
                # 打开并显示图片预览
                image = Image.open(file_path)
                
                # 调整图片大小以适应预览区域
                max_size = (70, 70)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 转换为PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # 显示预览
                self.image_preview_label.config(image=photo, text="")
                self.image_preview_label.image = photo  # 保持引用
                
                # 显示预览区域
                self.image_preview_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
                
                # 保存图片路径
                self.current_image_path = file_path
                
                self.status_label.config(text=f"已选择图片: {os.path.basename(file_path)}", fg="#0066cc")
                
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def _remove_image(self):
        """移除已选择的图片"""
        self.current_image_path = None
        self.image_preview_label.config(image="", text="")
        self.image_preview_label.image = None
        self.image_preview_frame.pack_forget()
        self.status_label.config(text="已移除图片", fg="#666")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """AI技术专家问答系统 - 使用帮助

【功能说明】
• 左侧任务管理：创建、切换、删除对话任务
• 每个任务独立保存对话历史
• 支持多任务并行，随时切换上下文

【操作指南】
• 点击"➕"创建新任务
• 点击左侧任务项切换对话
• 点击"✕"删除任务（至少保留一个）

【支持格式】
• TXT、MD、PDF、DOCX文档导入
"""
        messagebox.showinfo("帮助", help_text)
    
    def _show_welcome(self):
        """显示欢迎消息"""
        welcome_msg = """👋 欢迎使用AI技术专家问答系统！

🧠 **系统特点**：
• 左侧任务管理面板，支持多任务并行
• 每个任务独立保存对话上下文
• 自动命名任务（基于第一条消息）

💡 **使用提示**：
• 点击左侧"➕"创建新任务
• 点击任务项切换不同对话
• 每个任务的对话历史独立保存

---
"""
        self._append_message('system', welcome_msg)


# 测试
if __name__ == "__main__":
    root = tk.Tk()
    root.title("AI技术专家问答系统")
    root.geometry("1400x900")
    
    app = AIChatPage(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
