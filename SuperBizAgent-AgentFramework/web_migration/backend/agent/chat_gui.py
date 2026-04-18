#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI问答系统GUI - 简化版本
基于RAG和火山引擎的Reasoning-Acting模式
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


class ChatGUI:
    """AI问答系统图形界面"""
    
    def __init__(self, parent=None):
        """
        初始化GUI
        
        Args:
            parent: 父窗口，如果为None则创建独立窗口
        """
        if parent is None:
            self.root = tk.Tk()
            self.root.title("AI技术专家问答系统 - 基于RAG知识库")
            self.root.geometry("1200x800")
            self.root.minsize(1000, 600)
            self.standalone = True
        else:
            self.root = parent
            self.standalone = False
        
        # 初始化AI系统
        if CHAT_AVAILABLE:
            self.chat_system = AIChatSystem()
            self.chat_history = []
        else:
            self.chat_system = None
            self.chat_history = []
        
        self.is_processing = False
        
        # 创建界面
        self._create_ui()
        
        # 显示欢迎消息
        self._show_welcome()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = tk.Frame(self.root, bg="#f0f4f8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部标题栏
        header_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief=tk.RAISED)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.configure(highlightbackground="#0066cc", highlightthickness=1)
        
        title_container = tk.Frame(header_frame, bg="#ffffff")
        title_container.pack(fill=tk.X, padx=15, pady=10)
        
        title_label = tk.Label(
            title_container,
            text="AI技术专家问答系统",
            font=("微软雅黑", 14, "bold"),
            bg="#ffffff",
            fg="#0066cc"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(
            title_container,
            text="基于RAG知识库 + Reasoning-Acting模式",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 工具栏
        toolbar = tk.Frame(main_frame, bg="#f8f9fa", height=40)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        btn_style = {"font": ("微软雅黑", 9), "bg": "#e3f2fd", "fg": "#0066cc", 
                     "bd": 0, "cursor": "hand2", "padx": 10, "pady": 5}
        
        import_file_btn = tk.Button(toolbar, text="导入文件", command=self._import_file, **btn_style)
        import_file_btn.pack(side=tk.LEFT, padx=5)
        
        import_folder_btn = tk.Button(toolbar, text="导入文件夹", command=self._import_folder, **btn_style)
        import_folder_btn.pack(side=tk.LEFT, padx=5)
        
        index_btn = tk.Button(toolbar, text="索引Output", command=self._index_output, **btn_style)
        index_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(toolbar, text="清空对话", command=self._clear_chat, **btn_style)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        help_btn = tk.Button(toolbar, text="帮助", command=self._show_help, **btn_style)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # 聊天区域
        chat_frame = tk.LabelFrame(
            main_frame,
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
            main_frame,
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
        
        self.send_btn = ttk.Button(btn_frame, text="发送", command=self._send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        # 状态栏
        status_frame = tk.Frame(main_frame, bg="#f0f4f8")
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(status_frame, text="就绪", font=("微软雅黑", 9), bg="#f0f4f8")
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = tk.Label(status_frame, text="", font=("微软雅黑", 9), bg="#f0f4f8", fg="#666")
        self.stats_label.pack(side=tk.RIGHT)
    
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
        self._append_message('user', f"您: {user_input}\n\n")
        
        # 启动处理线程
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="正在思考...", fg="#ff6600")
        
        thread = threading.Thread(target=self._process_message, args=(user_input,), daemon=True)
        thread.start()
    
    def _process_message(self, user_input):
        """在后台线程处理消息"""
        try:
            if self.chat_system is None:
                self.root.after(0, lambda: self._append_message('system', '错误：AI问答系统未初始化\n\n'))
                return
            
            # 流式获取回答
            full_response = ""
            for chunk in self.chat_system.reasoning_acting_chat(user_input, use_rag=self.use_rag_var.get()):
                full_response += chunk
                # 使用after方法在主线程更新UI
                self.root.after(0, lambda c=chunk: self._append_stream(c))
                time.sleep(0.01)
            
            # 添加分隔符
            self.root.after(0, lambda: self._append_message('system', '\n---\n\n'))
            
            # 记录对话历史
            self.chat_history.append({'user': user_input, 'assistant': full_response})
            
        except Exception as e:
            self.root.after(0, lambda: self._append_message('system', f'错误: {str(e)}\n\n'))
        finally:
            self.root.after(0, self._on_processing_done)
    
    def _append_stream(self, text):
        """追加流式文本"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _append_message(self, role, message):
        """追加消息到聊天记录"""
        self.chat_text.config(state=tk.NORMAL)
        
        if role == 'user':
            self.chat_text.insert(tk.END, message, 'user')
        elif role == 'assistant':
            self.chat_text.insert(tk.END, message, 'assistant')
        else:
            self.chat_text.insert(tk.END, message, 'system')
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _on_processing_done(self):
        """处理完成回调"""
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="就绪", fg="black")
    
    def _clear_chat(self):
        """清空聊天记录"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_history.clear()
    
    def _import_file(self):
        """导入文件"""
        if self.chat_system and self.chat_system.kb:
            filetypes = [
                ('文本文件', '*.txt'),
                ('Markdown文件', '*.md'),
                ('PDF文件', '*.pdf'),
                ('Word文档', '*.docx'),
            ]
            file_path = filedialog.askopenfilename(title="选择要导入的文件", filetypes=filetypes)
            if file_path:
                threading.Thread(target=lambda: self.chat_system.kb.add_file(file_path), daemon=True).start()
    
    def _import_folder(self):
        """导入文件夹"""
        if self.chat_system and self.chat_system.kb:
            folder_path = filedialog.askdirectory(title="选择要导入的文件夹")
            if folder_path:
                recursive = messagebox.askyesno("递归导入", "是否递归导入子文件夹中的文件？")
                threading.Thread(target=lambda: self.chat_system.kb.add_folder(folder_path, recursive), daemon=True).start()
    
    def _index_output(self):
        """索引output目录"""
        if self.chat_system:
            threading.Thread(target=self.chat_system.index_output_documents, daemon=True).start()
    
    def _show_help(self):
        """显示帮助"""
        help_text = """AI技术专家问答系统 - 使用帮助

【功能说明】
1. 智能问答：基于RAG技术，结合知识库给出专业回答
2. 知识库：支持导入TXT、MD、PDF、Word等多种格式文档
3. 流式输出：实时显示AI思考过程和回答

【操作指南】
• 输入问题后按Enter发送，Shift+Enter换行
• 勾选"使用知识库"可启用RAG增强
• 点击"导入文件"导入单个文档
• 点击"导入文件夹"批量导入整个文件夹
• 点击"索引Output"索引output目录中的文档

【支持文件格式】
• 文本文件：.txt, .md, .markdown
• PDF文档：.pdf
• Word文档：.docx, .doc

【技术特点】
• Reasoning-Acting模式：先分析、再检索、后回答
• 角色设定：资深Java和AI应用开发专家
• 向量检索：使用FAISS进行高效语义搜索
• 多格式支持：自动解析PDF、Word等文档

【支持话题】
• Java开发、Spring框架、JVM调优
• 高并发架构、微服务设计
• AI应用开发、RAG系统、模型微调
• 代码优化、性能调优、工程实践
"""
        messagebox.showinfo("帮助", help_text)
    
    def _show_welcome(self):
        """显示欢迎消息"""
        welcome_msg = """欢迎使用AI技术专家问答系统！

【系统特点】：
• 基于RAG（检索增强生成）技术，结合知识库回答
• 采用Reasoning-Acting模式，先思考再回答
• 角色：资深Java和AI应用开发专家

【使用提示】：
• 直接输入技术问题，系统会自动检索知识库
• 支持Java、Spring、AI、架构设计等技术话题
• 首次使用请先点击"索引文档"建立知识库

【示例问题】：
• "如何优化Java高并发系统？"
• "解释一下RAG系统的原理"
• "Spring Boot最佳实践有哪些？"

---
"""
        self._append_message('system', welcome_msg)
    
    def run(self):
        """运行GUI"""
        if self.standalone:
            self.root.mainloop()


def main():
    """主函数"""
    app = ChatGUI()
    app.run()


if __name__ == "__main__":
    main()
