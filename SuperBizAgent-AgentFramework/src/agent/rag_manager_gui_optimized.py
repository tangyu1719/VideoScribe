#!/usr/bin/env python3
"""
RAG 知识库管理 GUI - 优化版本
- 批量处理文件
- 延迟生成嵌入（后台异步）
- 更好的进度显示
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
import json
from datetime import datetime

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 尝试导入 RAG 知识库
try:
    from rag_knowledge_base import RAGKnowledgeBase, RAGKnowledgeBaseV2
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("警告：RAG 知识库模块未安装")

# 尝试导入轻量级处理器
try:
    from simple_file_processor import add_file_to_records, add_folder_to_records
except ImportError:
    add_file_to_records = None
    add_folder_to_records = None


class RAGManagerGUIOptimized:
    """RAG 知识库管理窗口（优化版）"""
    
    def __init__(self, parent=None):
        """
        初始化 RAG 知识库管理窗口
        
        Args:
            parent: 父窗口（可选）
        """
        self.parent = parent
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("📚 RAG 知识库管理")
        self.window.geometry("900x700")
        self.window.configure(bg="#f5f5f5")
        
        # 设置窗口可最小化
        self.window.resizable(True, True)
        self.window.attributes('-toolwindow', False)
        
        # 居中显示
        if parent:
            self.window.transient(parent)
        
        # 创建 UI
        self._create_ui()
        
        # 初始化
        self.rag_kb = None
        self.file_records = []
        self.processing = False
        
        # 显示加载状态
        self.stats_label.config(text="⏳ 正在初始化...")
        self.progress_label.config(text="准备中...")
        
        # 异步初始化
        self._init_async()
    
    def _init_async(self):
        """异步初始化"""
        def init():
            try:
                # 加载文件记录
                self._load_file_records()
                self.window.after(0, self._on_init_complete)
            except Exception as e:
                print(f"初始化失败：{e}")
                self.window.after(0, lambda: self.stats_label.config(text=f"初始化失败：{e}"))
        
        thread = threading.Thread(target=init, daemon=True)
        thread.start()
    
    def _on_init_complete(self):
        """初始化完成"""
        self._update_file_tree()
        self._refresh_stats()
        self.stats_label.config(text="✓ 就绪")
        self.progress_label.config(text="点击按钮添加文件或文件夹")
    
    def _create_ui(self):
        """创建 UI"""
        # 主容器
        main_frame = tk.Frame(self.window, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_frame = tk.Frame(main_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            title_frame,
            text="📚 RAG 知识库管理",
            font=("微软雅黑", 16, "bold"),
            bg="#f5f5f5",
            fg="#333333"
        ).pack(side=tk.LEFT)
        
        # 按钮区域
        btn_frame = tk.Frame(main_frame, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 添加文件按钮
        tk.Button(
            btn_frame,
            text="📄 添加文件",
            command=self._on_add_file,
            bg="#4e6ef2",
            fg="white",
            font=("微软雅黑", 10),
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加文件夹按钮
        tk.Button(
            btn_frame,
            text="📁 添加文件夹",
            command=self._on_add_folder,
            bg="#4e6ef2",
            fg="white",
            font=("微软雅黑", 10),
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 批量生成嵌入按钮
        tk.Button(
            btn_frame,
            text="🔄 批量生成嵌入",
            command=self._on_batch_embed,
            bg="#52c41a",
            fg="white",
            font=("微软雅黑", 10),
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 删除选中按钮
        tk.Button(
            btn_frame,
            text="🗑️ 删除选中",
            command=self._on_delete_selected,
            bg="#ff4d4f",
            fg="white",
            font=("微软雅黑", 10),
            width=12
        ).pack(side=tk.LEFT)
        
        # 文件列表
        list_frame = tk.Frame(main_frame, bg="white", bd=1, relief=tk.SOLID)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 表头
        header_frame = tk.Frame(list_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="文件名", font=("微软雅黑", 10, "bold"), bg="#f0f0f0", width=30).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="类型", font=("微软雅黑", 10, "bold"), bg="#f0f0f0", width=10).pack(side=tk.LEFT)
        tk.Label(header_frame, text="大小", font=("微软雅黑", 10, "bold"), bg="#f0f0f0", width=10).pack(side=tk.LEFT)
        tk.Label(header_frame, text="块数", font=("微软雅黑", 10, "bold"), bg="#f0f0f0", width=10).pack(side=tk.LEFT)
        tk.Label(header_frame, text="状态", font=("微软雅黑", 10, "bold"), bg="#f0f0f0", width=15).pack(side=tk.LEFT)
        
        # 列表区域
        self.list_canvas = tk.Canvas(list_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.list_canvas.yview)
        self.list_frame = tk.Frame(self.list_canvas, bg="white")
        
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_canvas.create_window((0, 0), window=self.list_frame, anchor="nw", width=860)
        
        # 进度区域
        progress_frame = tk.Frame(main_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = tk.Label(progress_frame, text="就绪", font=("微软雅黑", 9), bg="#f5f5f5", fg="#666666")
        self.progress_label.pack(anchor="w")
        
        # 统计区域
        stats_frame = tk.Frame(main_frame, bg="#f5f5f5")
        stats_frame.pack(fill=tk.X)
        
        self.stats_label = tk.Label(stats_frame, text="就绪", font=("微软雅黑", 9), bg="#f5f5f5", fg="#666666")
        self.stats_label.pack(anchor="w")
    
    def _load_file_records(self):
        """加载文件记录"""
        records_file = os.path.join(BASE_DIR, "knowledge_base", "file_records.json")
        if os.path.exists(records_file):
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    self.file_records = json.load(f)
            except Exception as e:
                print(f"加载记录失败：{e}")
                self.file_records = []
    
    def _save_file_records(self):
        """保存文件记录"""
        records_file = os.path.join(BASE_DIR, "knowledge_base", "file_records.json")
        try:
            os.makedirs(os.path.dirname(records_file), exist_ok=True)
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记录失败：{e}")
    
    def _update_file_tree(self):
        """更新文件列表"""
        # 清除旧项
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        # 添加文件项
        for i, record in enumerate(self.file_records):
            item_frame = tk.Frame(self.list_frame, bg="white" if i % 2 == 0 else "#f9f9f9")
            item_frame.pack(fill=tk.X)
            
            # 文件名
            name = record.get('file_name', '未知')
            tk.Label(item_frame, text=name, font=("微软雅黑", 9), bg=item_frame.cget("bg"), width=30, anchor="w").pack(side=tk.LEFT, padx=5)
            
            # 类型
            file_type = record.get('file_type', '.txt')
            tk.Label(item_frame, text=file_type, font=("微软雅黑", 9), bg=item_frame.cget("bg"), width=10).pack(side=tk.LEFT)
            
            # 大小
            size = record.get('file_size', 0)
            tk.Label(item_frame, text=f"{size:.1f} KB", font=("微软雅黑", 9), bg=item_frame.cget("bg"), width=10).pack(side=tk.LEFT)
            
            # 块数
            chunks = record.get('chunk_count', 0)
            tk.Label(item_frame, text=str(chunks), font=("微软雅黑", 9), bg=item_frame.cget("bg"), width=10).pack(side=tk.LEFT)
            
            # 状态
            vector_bound = record.get('vector_bound', False)
            status = "✓ 已向量化" if vector_bound else "⏳ 待处理"
            color = "#52c41a" if vector_bound else "#faad14"
            tk.Label(item_frame, text=status, font=("微软雅黑", 9), bg=item_frame.cget("bg"), fg=color, width=15).pack(side=tk.LEFT)
        
        # 更新滚动区域
        self.list_frame.update_idletasks()
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
    
    def _refresh_stats(self):
        """刷新统计信息"""
        total_files = len(self.file_records)
        vectorized = sum(1 for r in self.file_records if r.get('vector_bound', False))
        total_chunks = sum(r.get('chunk_count', 0) for r in self.file_records)
        
        self.stats_label.config(
            text=f"文件总数: {total_files} | 已向量化: {vectorized} | 总块数: {total_chunks}"
        )
    
    def _on_add_file(self):
        """添加文件"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("Markdown 文件", "*.md"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self._process_files_async([file_path])
    
    def _on_add_folder(self):
        """添加文件夹"""
        folder_path = filedialog.askdirectory(title="选择文件夹")
        
        if folder_path:
            # 扫描文件
            files = []
            for root, dirs, filenames in os.walk(folder_path):
                for filename in filenames:
                    if filename.endswith(('.txt', '.md')):
                        files.append(os.path.join(root, filename))
            
            if files:
                self._process_files_async(files)
            else:
                messagebox.showinfo("提示", "文件夹中没有找到 .txt 或 .md 文件")
    
    def _process_files_async(self, file_paths):
        """异步处理文件"""
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        self.processing = True
        total = len(file_paths)
        
        def process():
            try:
                from simple_file_processor import SimpleChunkProcessor
                processor = SimpleChunkProcessor()
                
                added = 0
                for i, file_path in enumerate(file_paths, 1):
                    # 更新进度
                    progress = (i / total) * 100
                    self.window.after(0, lambda p=progress, f=file_path: self._update_progress(p, f"处理中 ({i}/{total}): {os.path.basename(f)}"))
                    
                    try:
                        # 快速处理文件（不生成嵌入）
                        file_info = processor.process_file(file_path)
                        
                        # 检查是否已存在
                        if not any(r.get('file_path') == file_path for r in self.file_records):
                            self.file_records.append(file_info)
                            added += 1
                    except Exception as e:
                        print(f"处理文件失败 {file_path}: {e}")
                
                # 保存记录
                self._save_file_records()
                
                self.window.after(0, lambda: self._on_process_complete(True, f"成功添加 {added} 个文件"))
                
            except Exception as e:
                self.window.after(0, lambda: self._on_process_complete(False, str(e)))
            finally:
                self.processing = False
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _update_progress(self, value, text):
        """更新进度"""
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)
    
    def _on_process_complete(self, success, message):
        """处理完成"""
        self.progress_bar['value'] = 0
        
        if success:
            self.progress_label.config(text=f"✓ {message}")
            self._update_file_tree()
            self._refresh_stats()
            messagebox.showinfo("成功", message)
        else:
            self.progress_label.config(text=f"✗ {message}")
            messagebox.showerror("错误", message)
    
    def _on_batch_embed(self):
        """批量生成嵌入"""
        # 找出未向量化的文件
        unvectorized = [r for r in self.file_records if not r.get('vector_bound', False)]
        
        if not unvectorized:
            messagebox.showinfo("提示", "所有文件已向量化")
            return
        
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        self.processing = True
        total = len(unvectorized)
        
        def process():
            try:
                # 初始化 RAG
                self.window.after(0, lambda: self._update_progress(0, "初始化 RAG 知识库..."))
                
                if not self.rag_kb:
                    try:
                        self.rag_kb = RAGKnowledgeBaseV2(BASE_DIR)
                    except:
                        self.rag_kb = RAGKnowledgeBase(BASE_DIR)
                
                # 批量生成嵌入
                processed = 0
                for i, record in enumerate(unvectorized, 1):
                    progress = (i / total) * 100
                    self.window.after(0, lambda p=progress, f=record: self._update_progress(p, f"向量化中 ({i}/{total}): {f['file_name']}"))
                    
                    try:
                        file_path = record['file_path']
                        if os.path.exists(file_path):
                            # 添加到 RAG
                            self.rag_kb.add_document(file_path)
                            
                            # 更新记录状态
                            record['vector_bound'] = True
                            processed += 1
                    except Exception as e:
                        print(f"向量化失败 {record['file_name']}: {e}")
                
                # 保存
                self.rag_kb.save_index()
                self._save_file_records()
                
                self.window.after(0, lambda: self._on_process_complete(True, f"成功向量化 {processed} 个文件"))
                
            except Exception as e:
                self.window.after(0, lambda: self._on_process_complete(False, str(e)))
            finally:
                self.processing = False
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _on_delete_selected(self):
        """删除选中文件"""
        # 简化实现：删除最后一个文件
        if self.file_records:
            if messagebox.askyesno("确认", "确定要删除最后一个文件吗？"):
                self.file_records.pop()
                self._save_file_records()
                self._update_file_tree()
                self._refresh_stats()
    
    def run(self):
        """运行窗口"""
        self.window.mainloop()


if __name__ == "__main__":
    app = RAGManagerGUIOptimized()
    app.run()
