#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据编辑对话框
- 支持自动提取和手动编辑
- 必填字段验证
- 预设选项下拉框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from rag_tools import DocumentMetadata, MetadataManager


class MetadataDialog:
    """元数据编辑对话框"""
    
    def __init__(self, parent, file_path: str, 
                 initial_metadata: Optional[DocumentMetadata] = None,
                 on_save: Optional[Callable[[DocumentMetadata], None]] = None):
        self.parent = parent
        self.file_path = file_path
        self.on_save = on_save
        self.metadata_manager = MetadataManager()
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"📋 元数据编辑 - {file_path}")
        self.dialog.geometry("500x450")
        self.dialog.configure(bg="#f5f5f5")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 初始化元数据
        if initial_metadata:
            self.metadata = initial_metadata
        else:
            self.metadata = DocumentMetadata(domain="", module="", doc_type="")
        
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        # 主容器
        main_frame = tk.Frame(self.dialog, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="📋 文档元数据",
            font=("微软雅黑", 16, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        )
        title_label.pack(pady=(0, 20))
        
        # 文件信息
        file_label = tk.Label(
            main_frame,
            text=f"文件: {self.file_path}",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#666666",
            wraplength=450
        )
        file_label.pack(pady=(0, 15))
        
        # 必填字段说明
        required_label = tk.Label(
            main_frame,
            text="* 为必填字段",
            font=("微软雅黑", 9),
            bg="#f5f5f5",
            fg="#ff5722"
        )
        required_label.pack(anchor="w", pady=(0, 10))
        
        # 表单区域
        form_frame = tk.Frame(main_frame, bg="#ffffff", padx=15, pady=15)
        form_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Domain (必填)
        self._create_combobox_row(
            form_frame, 0, "*领域 (Domain):", 
            self.metadata_manager.DOMAINS,
            self.metadata.domain
        )
        
        # Module (必填)
        self._create_combobox_row(
            form_frame, 1, "*模块 (Module):",
            self.metadata_manager.MODULES,
            self.metadata.module
        )
        
        # Doc Type (必填)
        self._create_combobox_row(
            form_frame, 2, "*文档类型 (Doc Type):",
            self.metadata_manager.DOC_TYPES,
            self.metadata.doc_type
        )
        
        # Keyword 1 (可选)
        self._create_entry_row(
            form_frame, 3, "关键词 1:",
            self.metadata.keyword1
        )
        
        # Keyword 2 (可选)
        self._create_entry_row(
            form_frame, 4, "关键词 2:",
            self.metadata.keyword2
        )
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 自动提取按钮
        auto_btn = tk.Button(
            button_frame,
            text="🔄 自动提取",
            font=("微软雅黑", 11),
            bg="#2196F3",
            fg="white",
            cursor="hand2",
            command=self._auto_extract,
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        auto_btn.pack(side=tk.LEFT)
        
        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text="💾 保存",
            font=("微软雅黑", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            command=self._save,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="❌ 取消",
            font=("微软雅黑", 11),
            bg="#9e9e9e",
            fg="white",
            cursor="hand2",
            command=self.dialog.destroy,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def _create_combobox_row(self, parent, row, label_text, values, initial_value):
        """创建下拉框行"""
        label = tk.Label(
            parent,
            text=label_text,
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#333333"
        )
        label.grid(row=row, column=0, sticky="w", pady=10)
        
        var = tk.StringVar(value=initial_value)
        combobox = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            state="readonly",
            font=("微软雅黑", 10),
            width=25
        )
        combobox.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=10)
        
        # 存储引用
        setattr(self, f"var_{label_text.split('(')[1].lower().replace(')', '').replace('*', '')}", var)
        
        parent.grid_columnconfigure(1, weight=1)
    
    def _create_entry_row(self, parent, row, label_text, initial_value):
        """创建输入框行"""
        label = tk.Label(
            parent,
            text=label_text,
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#333333"
        )
        label.grid(row=row, column=0, sticky="w", pady=10)
        
        var = tk.StringVar(value=initial_value)
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=("微软雅黑", 10),
            width=28,
            relief=tk.SOLID,
            bd=1
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=10)
        
        # 存储引用
        attr_name = label_text.lower().replace(' ', '_').replace(':', '')
        setattr(self, f"var_{attr_name}", var)
    
    def _auto_extract(self):
        """自动提取元数据"""
        try:
            # 读取文件内容
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 自动提取
            extracted = self.metadata_manager.auto_extract_metadata(
                content, self.file_path
            )
            
            # 更新UI
            self.var_domain.set(extracted.domain)
            self.var_module.set(extracted.module)
            self.var_doc_type.set(extracted.doc_type)
            self.var_keyword1.set(extracted.keyword1)
            self.var_keyword2.set(extracted.keyword2)
            
            messagebox.showinfo("成功", "元数据已自动提取并填充")
            
        except Exception as e:
            messagebox.showerror("错误", f"自动提取失败: {e}")
    
    def _save(self):
        """保存元数据"""
        # 收集数据
        metadata = DocumentMetadata(
            domain=self.var_domain.get(),
            module=self.var_module.get(),
            doc_type=self.var_doc_type.get(),
            keyword1=self.var_keyword1.get(),
            keyword2=self.var_keyword2.get()
        )
        
        # 验证
        is_valid, msg = self.metadata_manager.validate_metadata(metadata)
        if not is_valid:
            messagebox.showerror("验证失败", msg)
            return
        
        # 回调
        if self.on_save:
            self.on_save(metadata)
        
        self.dialog.destroy()


def show_metadata_dialog(parent, file_path: str, 
                        initial_metadata: Optional[DocumentMetadata] = None,
                        on_save: Optional[Callable[[DocumentMetadata], None]] = None):
    """
    显示元数据编辑对话框
    
    Args:
        parent: 父窗口
        file_path: 文件路径
        initial_metadata: 初始元数据
        on_save: 保存回调函数
    """
    dialog = MetadataDialog(parent, file_path, initial_metadata, on_save)
    return dialog
