#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
召回片段显示组件
- 可折叠显示
- 显示原文本片段
- 显示元数据信息
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict


class RetrievedChunksView:
    """召回片段显示组件"""
    
    def __init__(self, parent, chunks: List[Dict] = None):
        self.parent = parent
        self.chunks = chunks or []
        self.frame = None
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        # 主容器
        self.frame = tk.Frame(self.parent, bg="#f5f5f5")
        self.frame.pack(fill=tk.X, pady=(10, 0))
        
        # 头部（可点击折叠/展开）
        self.header_frame = tk.Frame(self.frame, bg="#e3f2fd", cursor="hand2")
        self.header_frame.pack(fill=tk.X)
        self.header_frame.bind("<Button-1>", lambda e: self.toggle())
        
        # 展开/折叠图标
        self.toggle_icon = tk.Label(
            self.header_frame,
            text="▼",
            font=("微软雅黑", 10),
            bg="#e3f2fd",
            fg="#1976d2"
        )
        self.toggle_icon.pack(side=tk.LEFT, padx=(10, 5))
        self.toggle_icon.bind("<Button-1>", lambda e: self.toggle())
        
        # 标题
        count = len(self.chunks)
        self.title_label = tk.Label(
            self.header_frame,
            text=f"📚 召回片段 ({count}个)",
            font=("微软雅黑", 10, "bold"),
            bg="#e3f2fd",
            fg="#1976d2"
        )
        self.title_label.pack(side=tk.LEFT)
        self.title_label.bind("<Button-1>", lambda e: self.toggle())
        
        # 内容区域（默认展开）
        self.content_frame = tk.Frame(self.frame, bg="#f5f5f5")
        self.content_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 显示片段
        self._display_chunks()
    
    def _display_chunks(self):
        """显示召回的片段"""
        # 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if not self.chunks:
            no_data_label = tk.Label(
                self.content_frame,
                text="未召回相关片段",
                font=("微软雅黑", 10),
                bg="#f5f5f5",
                fg="#999999"
            )
            no_data_label.pack(pady=10)
            return
        
        # 显示每个片段
        for i, chunk in enumerate(self.chunks, 1):
            self._create_chunk_card(i, chunk)
    
    def _create_chunk_card(self, index: int, chunk: Dict):
        """创建片段卡片"""
        # 卡片容器
        card = tk.Frame(self.content_frame, bg="#ffffff", padx=10, pady=10)
        card.pack(fill=tk.X, pady=(0, 8))
        
        # 头部信息
        header = tk.Frame(card, bg="#ffffff")
        header.pack(fill=tk.X)
        
        # 序号和相似度
        similarity = chunk.get('score', 0) or chunk.get('similarity', 0)
        info_text = f"片段 {index} | 相似度: {similarity:.3f}"
        info_label = tk.Label(
            header,
            text=info_text,
            font=("微软雅黑", 9, "bold"),
            bg="#ffffff",
            fg="#1976d2"
        )
        info_label.pack(side=tk.LEFT)
        
        # 元数据标签
        metadata = chunk.get('metadata', {})
        if metadata:
            tags_frame = tk.Frame(header, bg="#ffffff")
            tags_frame.pack(side=tk.RIGHT)
            
            # Domain标签
            if metadata.get('domain'):
                domain_tag = tk.Label(
                    tags_frame,
                    text=metadata['domain'],
                    font=("微软雅黑", 8),
                    bg="#e3f2fd",
                    fg="#1976d2",
                    padx=5,
                    pady=2
                )
                domain_tag.pack(side=tk.LEFT, padx=(0, 5))
            
            # Module标签
            if metadata.get('module'):
                module_tag = tk.Label(
                    tags_frame,
                    text=metadata['module'],
                    font=("微软雅黑", 8),
                    bg="#f3e5f5",
                    fg="#7b1fa2",
                    padx=5,
                    pady=2
                )
                module_tag.pack(side=tk.LEFT, padx=(0, 5))
            
            # DocType标签
            if metadata.get('doc_type'):
                type_tag = tk.Label(
                    tags_frame,
                    text=metadata['doc_type'],
                    font=("微软雅黑", 8),
                    bg="#e8f5e9",
                    fg="#388e3c",
                    padx=5,
                    pady=2
                )
                type_tag.pack(side=tk.LEFT)
        
        # 来源文件
        source_file = chunk.get('source_file', '未知来源')
        source_label = tk.Label(
            card,
            text=f"📄 {source_file}",
            font=("微软雅黑", 9),
            bg="#ffffff",
            fg="#666666"
        )
        source_label.pack(anchor="w", pady=(5, 0))
        
        # 内容（可选择）
        content = chunk.get('content', '')
        content_text = tk.Text(
            card,
            font=("微软雅黑", 10),
            bg="#fafafa",
            fg="#333333",
            wrap=tk.WORD,
            height=min(5, max(2, len(content) // 80)),
            padx=10,
            pady=8,
            relief=tk.SOLID,
            bd=1,
            selectbackground="#b3d9ff",
            selectforeground="#000000"
        )
        content_text.insert("1.0", content[:500] + ("..." if len(content) > 500 else ""))
        content_text.config(state=tk.DISABLED)
        content_text.pack(fill=tk.X, pady=(5, 0))
        
        # 关键词
        keywords = []
        if metadata.get('keyword1'):
            keywords.append(metadata['keyword1'])
        if metadata.get('keyword2'):
            keywords.append(metadata['keyword2'])
        
        if keywords:
            keywords_text = f"关键词: {', '.join(keywords)}"
            keywords_label = tk.Label(
                card,
                text=keywords_text,
                font=("微软雅黑", 8),
                bg="#ffffff",
                fg="#999999"
            )
            keywords_label.pack(anchor="w", pady=(5, 0))
    
    def toggle(self):
        """切换折叠/展开"""
        if self.content_frame.winfo_viewable():
            self.content_frame.pack_forget()
            self.toggle_icon.config(text="▶")
            self.header_frame.config(bg="#bbdefb")
            self.toggle_icon.config(bg="#bbdefb")
            self.title_label.config(bg="#bbdefb")
        else:
            self.content_frame.pack(fill=tk.X, padx=10, pady=5)
            self.toggle_icon.config(text="▼")
            self.header_frame.config(bg="#e3f2fd")
            self.toggle_icon.config(bg="#e3f2fd")
            self.title_label.config(bg="#e3f2fd")
    
    def update_chunks(self, chunks: List[Dict]):
        """更新显示的片段"""
        self.chunks = chunks
        self.title_label.config(text=f"📚 召回片段 ({len(chunks)}个)")
        self._display_chunks()
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.frame.pack(**kwargs)
    
    def pack_forget(self):
        """包装pack_forget方法"""
        self.frame.pack_forget()


def create_retrieved_chunks_view(parent, chunks: List[Dict] = None) -> RetrievedChunksView:
    """
    创建召回片段显示组件
    
    Args:
        parent: 父容器
        chunks: 召回的片段列表
    
    Returns:
        RetrievedChunksView: 组件实例
    """
    return RetrievedChunksView(parent, chunks)
