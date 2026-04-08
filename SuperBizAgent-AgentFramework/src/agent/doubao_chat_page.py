#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包AI风格聊天页面
模仿豆包AI网页版界面设计
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import time
import os
import hashlib
from datetime import datetime
import json

try:
    from ai_chat_system import AIChatSystem
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False


class ChatMessage:
    """聊天消息类"""
    def __init__(self, role, content, timestamp=None, image_path=None):
        self.role = role  # 'user' 或 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.image_path = image_path


class ChatSession:
    """聊天会话类"""
    def __init__(self, session_id=None, title=None):
        self.session_id = session_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
        self.title = title or "新对话"
        self.messages = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def add_message(self, role, content, image_path=None):
        """添加消息"""
        msg = ChatMessage(role, content, image_path=image_path)
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
        
        # 自动命名（基于第一条用户消息）
        if len(self.messages) == 1 and role == 'user':
            self.title = content[:20] + "..." if len(content) > 20 else content
        
        return msg
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'title': self.title,
            'messages': [{'role': m.role, 'content': m.content, 'timestamp': m.timestamp, 'image_path': m.image_path} for m in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        session = cls(data['session_id'], data['title'])
        session.created_at = data.get('created_at', datetime.now().isoformat())
        session.updated_at = data.get('updated_at', session.created_at)
        for m in data.get('messages', []):
            session.messages.append(ChatMessage(
                m['role'], m['content'], m['timestamp'], m.get('image_path')
            ))
        return session


class DoubaoChatPage(tk.Frame):
    """豆包AI风格聊天页面"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f5f5f5", **kwargs)
        
        # 初始化AI系统
        if CHAT_AVAILABLE:
            self.chat_system = AIChatSystem()
        else:
            self.chat_system = None
        
        # 会话管理
        self.sessions = {}
        self.current_session = None
        self.is_processing = False
        
        # 加载历史会话
        self._load_sessions()
        
        # 创建界面
        self._create_ui()
        
        # 创建新会话
        self._create_new_session()
    
    def _create_ui(self):
        """创建用户界面 - 豆包AI风格"""
        # 主分割面板
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#f5f5f5", sashwidth=1)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧边栏
        self._create_sidebar(main_paned)
        
        # 右侧聊天区域
        self._create_chat_area(main_paned)
        
        # 设置分割比例
        main_paned.add(self.sidebar, width=260)
        main_paned.add(self.chat_frame, width=1140)
    
    def _create_sidebar(self, parent):
        """创建左侧边栏"""
        self.sidebar = tk.Frame(parent, bg="#ffffff", width=260)
        self.sidebar.pack_propagate(False)
        
        # 顶部标题栏
        header = tk.Frame(self.sidebar, bg="#ffffff", height=60)
        header.pack(fill=tk.X, padx=16, pady=16)
        header.pack_propagate(False)
        
        # Logo/标题
        title_frame = tk.Frame(header, bg="#ffffff")
        title_frame.pack(fill=tk.X)
        
        tk.Label(
            title_frame,
            text="🤖 AI助手",
            font=("微软雅黑", 18, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        ).pack(side=tk.LEFT)
        
        # 新建对话按钮
        new_btn = tk.Button(
            header,
            text="＋ 新对话",
            font=("微软雅黑", 12),
            bg="#4f46e5",
            fg="white",
            bd=0,
            cursor="hand2",
            command=self._create_new_session
        )
        new_btn.pack(fill=tk.X, pady=(12, 0))
        
        # 历史会话列表
        list_frame = tk.Frame(self.sidebar, bg="#ffffff")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # 列表标题
        tk.Label(
            list_frame,
            text="历史会话",
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#666666"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        # 会话列表（带滚动条）
        canvas_frame = tk.Frame(list_frame, bg="#ffffff")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.session_canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.session_canvas.yview)
        self.session_list_frame = tk.Frame(self.session_canvas, bg="#ffffff")
        
        self.session_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.session_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.session_canvas.create_window((0, 0), window=self.session_list_frame, anchor="nw", width=236)
        
        self.session_list_frame.bind("<Configure>", 
            lambda e: self.session_canvas.configure(scrollregion=self.session_canvas.bbox("all")))
        
        # 底部设置按钮
        bottom_frame = tk.Frame(self.sidebar, bg="#ffffff", height=50)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=8)
        bottom_frame.pack_propagate(False)
        
        settings_btn = tk.Button(
            bottom_frame,
            text="⚙️ 设置",
            font=("微软雅黑", 11),
            bg="#f5f5f5",
            fg="#333333",
            bd=0,
            cursor="hand2",
            command=self._open_settings
        )
        settings_btn.pack(fill=tk.BOTH, expand=True)
    
    def _open_settings(self):
        """打开设置对话框"""
        settings_window = tk.Toplevel(self)
        settings_window.title("设置")
        settings_window.geometry("400x300")
        settings_window.configure(bg="#ffffff")
        
        # 设置窗口内容
        tk.Label(
            settings_window,
            text="⚙️ 系统设置",
            font=("微软雅黑", 16, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        ).pack(pady=20)
        
        # API设置按钮
        api_btn = tk.Button(
            settings_window,
            text="API配置",
            font=("微软雅黑", 12),
            bg="#4f46e5",
            fg="white",
            bd=0,
            cursor="hand2",
            command=self._open_api_config
        )
        api_btn.pack(fill=tk.X, padx=40, pady=10)
        
        # 知识库设置按钮
        kb_btn = tk.Button(
            settings_window,
            text="知识库管理",
            font=("微软雅黑", 12),
            bg="#10b981",
            fg="white",
            bd=0,
            cursor="hand2",
            command=self._open_kb_manager
        )
        kb_btn.pack(fill=tk.X, padx=40, pady=10)
    
    def _open_api_config(self):
        """打开API配置"""
        # 这里可以打开API配置对话框
        pass
    
    def _open_kb_manager(self):
        """打开知识库管理"""
        # 这里可以打开知识库管理窗口
        pass
    
    def _create_chat_area(self, parent):
        """创建右侧聊天区域"""
        self.chat_frame = tk.Frame(parent, bg="#f5f5f5")
        
        # 顶部标题栏
        self.header_frame = tk.Frame(self.chat_frame, bg="#ffffff", height=60)
        self.header_frame.pack(fill=tk.X)
        self.header_frame.pack_propagate(False)
        
        self.session_title_label = tk.Label(
            self.header_frame,
            text="新对话",
            font=("微软雅黑", 16, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        self.session_title_label.pack(side=tk.LEFT, padx=24, pady=16)
        
        # 清空对话按钮
        clear_btn = tk.Button(
            self.header_frame,
            text="清空",
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#666666",
            bd=0,
            cursor="hand2",
            command=self._clear_current_session
        )
        clear_btn.pack(side=tk.RIGHT, padx=24, pady=16)
        
        # 消息显示区域
        self.messages_frame = tk.Frame(self.chat_frame, bg="#f5f5f5")
        self.messages_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 0))
        
        # 消息画布（带滚动条）
        self.msg_canvas = tk.Canvas(self.messages_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.messages_frame, orient="vertical", command=self.msg_canvas.yview)
        self.msg_container = tk.Frame(self.msg_canvas, bg="#f5f5f5")
        
        self.msg_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.msg_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.msg_canvas.create_window((0, 0), window=self.msg_container, anchor="nw", width=1092)
        
        self.msg_container.bind("<Configure>", 
            lambda e: self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all")))
        
        # 底部输入区域
        self._create_input_area()
    
    def _create_input_area(self):
        """创建底部输入区域"""
        input_container = tk.Frame(self.chat_frame, bg="#f5f5f5")
        input_container.pack(fill=tk.X, padx=24, pady=24)
        
        # 输入框背景
        input_bg = tk.Frame(input_container, bg="#ffffff", bd=1, relief=tk.SOLID)
        input_bg.pack(fill=tk.X)
        input_bg.configure(highlightbackground="#e0e0e0", highlightthickness=1)
        
        # 图片预览区域
        self.image_preview_frame = tk.Frame(input_bg, bg="#ffffff")
        self.image_preview_frame.pack(fill=tk.X, padx=16, pady=(12, 0))
        self.image_preview_frame.pack_forget()
        
        self.image_thumb_label = tk.Label(self.image_preview_frame, bg="#ffffff")
        self.image_thumb_label.pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            self.image_preview_frame,
            text="✕",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666666",
            bd=0,
            cursor="hand2",
            command=self._remove_image
        ).pack(side=tk.LEFT)
        
        # 文本输入框
        self.input_text = tk.Text(
            input_bg,
            font=("微软雅黑", 14),
            height=3,
            bg="#ffffff",
            fg="#1a1a1a",
            bd=0,
            wrap=tk.WORD,
            padx=16,
            pady=12
        )
        self.input_text.pack(fill=tk.X, padx=16, pady=8)
        self.input_text.bind('<Return>', self._on_enter_key)
        self.input_text.bind('<Shift-Return>', self._on_shift_enter)
        
        # 底部工具栏
        toolbar = tk.Frame(input_bg, bg="#ffffff")
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # 左侧工具按钮
        tools_frame = tk.Frame(toolbar, bg="#ffffff")
        tools_frame.pack(side=tk.LEFT)
        
        # 上传图片按钮
        img_btn = tk.Button(
            tools_frame,
            text="📎",
            font=("微软雅黑", 16),
            bg="#ffffff",
            fg="#666666",
            bd=0,
            cursor="hand2",
            command=self._upload_image
        )
        img_btn.pack(side=tk.LEFT, padx=(0, 16))
        
        # 发送按钮
        self.send_btn = tk.Button(
            toolbar,
            text="发送",
            font=("微软雅黑", 13, "bold"),
            bg="#4f46e5",
            fg="white",
            bd=0,
            cursor="hand2",
            padx=24,
            pady=8,
            command=self._send_message
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # 存储当前图片
        self.current_image_path = None
    
    def _create_new_session(self):
        """创建新会话"""
        session = ChatSession()
        self.sessions[session.session_id] = session
        self.current_session = session
        
        self._refresh_session_list()
        self._refresh_messages()
        self._update_title(session.title)
    
    def _refresh_session_list(self):
        """刷新会话列表"""
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()
        
        # 按更新时间排序
        sorted_sessions = sorted(
            self.sessions.values(),
            key=lambda x: x.updated_at,
            reverse=True
        )
        
        for session in sorted_sessions:
            self._create_session_item(session)
    
    def _create_session_item(self, session):
        """创建会话项"""
        is_active = self.current_session and self.current_session.session_id == session.session_id
        
        # 背景色
        bg_color = "#f0f0f0" if is_active else "#ffffff"
        
        item_frame = tk.Frame(self.session_list_frame, bg=bg_color, height=44)
        item_frame.pack(fill=tk.X, pady=2)
        item_frame.pack_propagate(False)
        
        # 会话标题
        title_btn = tk.Button(
            item_frame,
            text=session.title,
            font=("微软雅黑", 12),
            bg=bg_color,
            fg="#1a1a1a" if is_active else "#666666",
            bd=0,
            cursor="hand2",
            anchor=tk.W,
            command=lambda sid=session.session_id: self._switch_session(sid)
        )
        title_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12)
        
        # 删除按钮（悬停显示）
        if len(self.sessions) > 1:
            delete_btn = tk.Label(
                item_frame,
                text="✕",
                font=("微软雅黑", 12),
                bg=bg_color,
                fg="#999999",
                cursor="hand2"
            )
            delete_btn.pack(side=tk.RIGHT, padx=12)
            delete_btn.bind("<Button-1>", lambda e, sid=session.session_id: self._delete_session(sid))
    
    def _switch_session(self, session_id):
        """切换会话"""
        if session_id in self.sessions:
            self.current_session = self.sessions[session_id]
            self._refresh_session_list()
            self._refresh_messages()
            self._update_title(self.current_session.title)
    
    def _delete_session(self, session_id):
        """删除会话"""
        if len(self.sessions) <= 1:
            messagebox.showwarning("提示", "至少保留一个会话")
            return
        
        if messagebox.askyesno("确认", "确定要删除这个会话吗？"):
            del self.sessions[session_id]
            
            if self.current_session.session_id == session_id:
                self.current_session = list(self.sessions.values())[0]
                self._refresh_messages()
                self._update_title(self.current_session.title)
            
            self._refresh_session_list()
            self._save_sessions()
    
    def _refresh_messages(self):
        """刷新消息显示"""
        for widget in self.msg_container.winfo_children():
            widget.destroy()
        
        if not self.current_session:
            return
        
        for msg in self.current_session.messages:
            self._create_message_bubble(msg)
        
        # 滚动到底部
        self.msg_canvas.update_idletasks()
        self.msg_canvas.yview_moveto(1.0)
    
    def _create_message_bubble(self, msg):
        """创建消息气泡"""
        is_user = msg.role == 'user'
        
        # 消息行容器
        row_frame = tk.Frame(self.msg_container, bg="#f5f5f5")
        row_frame.pack(fill=tk.X, pady=8)
        
        if is_user:
            # 用户消息 - 右对齐
            spacer = tk.Frame(row_frame, bg="#f5f5f5")
            spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            bubble_container = tk.Frame(row_frame, bg="#f5f5f5")
            bubble_container.pack(side=tk.RIGHT)
            
            # 头像
            avatar = tk.Label(
                bubble_container,
                text="👤",
                font=("微软雅黑", 20),
                bg="#f5f5f5"
            )
            avatar.pack(side=tk.RIGHT, padx=(8, 0))
            
            # 气泡
            bubble = tk.Frame(bubble_container, bg="#4f46e5", padx=16, pady=12)
            bubble.pack(side=tk.RIGHT)
            
            # 如果有图片，先显示图片
            if msg.image_path and os.path.exists(msg.image_path):
                try:
                    img = Image.open(msg.image_path)
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label = tk.Label(bubble, image=photo, bg="#4f46e5")
                    img_label.image = photo
                    img_label.pack(pady=(0, 8))
                except:
                    pass
            
            # 文本内容
            text_label = tk.Label(
                bubble,
                text=msg.content,
                font=("微软雅黑", 14),
                bg="#4f46e5",
                fg="white",
                wraplength=600,
                justify=tk.LEFT
            )
            text_label.pack()
        else:
            # AI消息 - 左对齐
            bubble_container = tk.Frame(row_frame, bg="#f5f5f5")
            bubble_container.pack(side=tk.LEFT)
            
            # 头像
            avatar = tk.Label(
                bubble_container,
                text="🤖",
                font=("微软雅黑", 20),
                bg="#f5f5f5"
            )
            avatar.pack(side=tk.LEFT, padx=(0, 8))
            
            # 气泡
            bubble = tk.Frame(bubble_container, bg="#ffffff", padx=16, pady=12)
            bubble.pack(side=tk.LEFT)
            
            # 文本内容
            text_label = tk.Label(
                bubble,
                text=msg.content,
                font=("微软雅黑", 14),
                bg="#ffffff",
                fg="#1a1a1a",
                wraplength=600,
                justify=tk.LEFT
            )
            text_label.pack()
            
            # 操作按钮区域（复制、导出、重新回答）
            actions_frame = tk.Frame(bubble, bg="#ffffff")
            actions_frame.pack(fill=tk.X, pady=(8, 0))
            
            # 复制按钮
            copy_btn = tk.Button(
                actions_frame,
                text="📋 复制",
                font=("微软雅黑", 10),
                bg="#f5f5f5",
                fg="#666666",
                bd=0,
                cursor="hand2",
                command=lambda: self._copy_message(msg.content)
            )
            copy_btn.pack(side=tk.LEFT, padx=(0, 8))
            
            # 导出MD按钮
            export_btn = tk.Button(
                actions_frame,
                text="📄 导出MD",
                font=("微软雅黑", 10),
                bg="#f5f5f5",
                fg="#666666",
                bd=0,
                cursor="hand2",
                command=lambda: self._export_message_md(msg)
            )
            export_btn.pack(side=tk.LEFT, padx=(0, 8))
            
            # 重新回答按钮
            retry_btn = tk.Button(
                actions_frame,
                text="🔄 重新回答",
                font=("微软雅黑", 10),
                bg="#f5f5f5",
                fg="#666666",
                bd=0,
                cursor="hand2",
                command=lambda: self._retry_message(msg)
            )
            retry_btn.pack(side=tk.LEFT)
            
            spacer = tk.Frame(row_frame, bg="#f5f5f5")
            spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)
    
    def _copy_message(self, content):
        """复制消息内容到剪贴板"""
        try:
            self.clipboard_clear()
            self.clipboard_append(content)
            self.update()  # 必须调用update才能生效
            # 显示提示
            self._show_tooltip("已复制到剪贴板")
        except Exception as e:
            print(f"复制失败: {e}")
    
    def _export_message_md(self, msg):
        """导出消息为Markdown文件"""
        try:
            from tkinter import filedialog
            from datetime import datetime
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")],
                initialfile=f"message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )
            
            if file_path:
                # 构建Markdown内容
                md_content = f"""# 对话记录

**时间**: {msg.timestamp}
**角色**: {'用户' if msg.role == 'user' else 'AI助手'}

## 内容

{msg.content}
"""
                
                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                self._show_tooltip(f"已导出到: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"导出失败: {e}")
            self._show_tooltip("导出失败")
    
    def _retry_message(self, msg):
        """重新回答消息"""
        try:
            # 找到对应的上一条用户消息
            if not self.current_session:
                return
            
            messages = self.current_session.messages
            msg_index = None
            for i, m in enumerate(messages):
                if m == msg:
                    msg_index = i
                    break
            
            if msg_index is not None and msg_index > 0:
                # 获取上一条用户消息
                prev_msg = messages[msg_index - 1]
                if prev_msg.role == 'user':
                    # 删除当前AI回复
                    self.current_session.messages.pop(msg_index)
                    # 重新发送请求
                    self._send_message_with_content(prev_msg.content, prev_msg.image_path)
        except Exception as e:
            print(f"重新回答失败: {e}")
    
    def _show_tooltip(self, text):
        """显示提示信息"""
        tooltip = tk.Toplevel(self)
        tooltip.overrideredirect(True)
        tooltip.configure(bg="#333333")
        
        label = tk.Label(
            tooltip,
            text=text,
            font=("微软雅黑", 11),
            bg="#333333",
            fg="white",
            padx=16,
            pady=8
        )
        label.pack()
        
        # 居中显示
        tooltip.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - tooltip.winfo_width()) // 2
        y = self.winfo_rooty() + self.winfo_height() - 100
        tooltip.geometry(f"+{x}+{y}")
        
        # 2秒后自动关闭
        tooltip.after(2000, tooltip.destroy)
    
    def _update_title(self, title):
        """更新标题"""
        self.session_title_label.config(text=title)
    
    def _on_enter_key(self, event):
        """处理回车键"""
        if not event.state & 0x1:  # 没有按住Shift
            self._send_message()
            return 'break'
    
    def _on_shift_enter(self, event):
        """处理Shift+Enter - 换行"""
        pass  # 允许默认行为（换行）
    
    def _send_message(self):
        """发送消息"""
        if self.is_processing:
            return
        
        content = self.input_text.get('1.0', tk.END).strip()
        if not content and not self.current_image_path:
            return
        
        # 清空输入框
        self.input_text.delete('1.0', tk.END)
        
        # 添加用户消息
        if self.current_session:
            self.current_session.add_message('user', content, self.current_image_path)
            self._refresh_session_list()
            self._refresh_messages()
            self._update_title(self.current_session.title)
        
        # 移除图片
        self._remove_image()
        
        # 启动AI处理
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED, text="思考中...")
        
        thread = threading.Thread(target=self._process_message, args=(content,), daemon=True)
        thread.start()
    
    def _process_message(self, content):
        """处理消息（后台线程）"""
        try:
            if not self.chat_system:
                self.after(0, lambda: self._add_ai_message("❌ AI系统未初始化"))
                return
            
            # 流式获取回答
            full_response = ""
            for chunk in self.chat_system.reasoning_acting_chat(content, use_rag=True):
                full_response += chunk
                # 更新UI需要在主线程
                self.after(0, lambda: self._update_streaming_message(full_response))
                time.sleep(0.01)
            
            # 保存到会话
            if self.current_session:
                self.current_session.add_message('assistant', full_response)
                self._save_sessions()
            
        except Exception as e:
            self.after(0, lambda: self._add_ai_message(f"❌ 错误: {str(e)}"))
        finally:
            self.after(0, self._on_processing_done)
    
    def _update_streaming_message(self, content):
        """更新流式消息"""
        # 移除临时的流式消息（如果有）
        for widget in self.msg_container.winfo_children():
            if hasattr(widget, '_is_streaming'):
                widget.destroy()
        
        # 创建临时消息气泡
        self._create_streaming_bubble(content)
        
        # 滚动到底部
        self.msg_canvas.update_idletasks()
        self.msg_canvas.yview_moveto(1.0)
    
    def _create_streaming_bubble(self, content):
        """创建流式消息气泡"""
        row_frame = tk.Frame(self.msg_container, bg="#f5f5f5")
        row_frame.pack(fill=tk.X, pady=8)
        row_frame._is_streaming = True
        
        bubble_container = tk.Frame(row_frame, bg="#f5f5f5")
        bubble_container.pack(side=tk.LEFT)
        
        avatar = tk.Label(
            bubble_container,
            text="🤖",
            font=("微软雅黑", 20),
            bg="#f5f5f5"
        )
        avatar.pack(side=tk.LEFT, padx=(0, 8))
        
        bubble = tk.Frame(bubble_container, bg="#ffffff", padx=16, pady=12)
        bubble.pack(side=tk.LEFT)
        
        text_label = tk.Label(
            bubble,
            text=content,
            font=("微软雅黑", 14),
            bg="#ffffff",
            fg="#1a1a1a",
            wraplength=600,
            justify=tk.LEFT
        )
        text_label.pack()
        
        spacer = tk.Frame(row_frame, bg="#f5f5f5")
        spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)
    
    def _add_ai_message(self, content):
        """添加AI消息"""
        if self.current_session:
            self.current_session.add_message('assistant', content)
            self._refresh_messages()
    
    def _on_processing_done(self):
        """处理完成"""
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL, text="发送")
        self._refresh_messages()
    
    def _upload_image(self):
        """上传图片"""
        filetypes = [
            ('图片文件', '*.png *.jpg *.jpeg *.gif'),
            ('PNG', '*.png'),
            ('JPEG', '*.jpg *.jpeg'),
            ('GIF', '*.gif')
        ]
        file_path = filedialog.askopenfilename(title="选择图片", filetypes=filetypes)
        
        if file_path:
            try:
                # 显示缩略图
                img = Image.open(file_path)
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                self.image_thumb_label.config(image=photo)
                self.image_thumb_label.image = photo
                
                self.image_preview_frame.pack(fill=tk.X, padx=16, pady=(12, 0))
                self.current_image_path = file_path
                
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def _remove_image(self):
        """移除图片"""
        self.current_image_path = None
        self.image_thumb_label.config(image="")
        self.image_thumb_label.image = None
        self.image_preview_frame.pack_forget()
    
    def _clear_current_session(self):
        """清空当前会话"""
        if self.current_session:
            self.current_session.messages = []
            self._refresh_messages()
    
    def _save_sessions(self):
        """保存会话到文件"""
        try:
            data = {sid: s.to_dict() for sid, s in self.sessions.items()}
            with open('chat_sessions.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话失败: {e}")
    
    def _load_sessions(self):
        """从文件加载会话"""
        try:
            if os.path.exists('chat_sessions.json'):
                with open('chat_sessions.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for sid, sdata in data.items():
                        self.sessions[sid] = ChatSession.from_dict(sdata)
        except Exception as e:
            print(f"加载会话失败: {e}")


# 测试
if __name__ == "__main__":
    root = tk.Tk()
    root.title("AI助手 - 豆包风格")
    root.geometry("1400x900")
    
    app = DoubaoChatPage(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
