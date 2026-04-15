#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReAct风格思考链显示组件
- 链式堆叠显示thought步骤
- 每个thought可下拉展开/收起
- 支持多种thought类型：意图识别、Query改写、知识检索、推理等
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ThoughtStep:
    """思考步骤"""
    step_type: str  # 步骤类型：intent, rewrite, retrieve, reason, final
    title: str  # 显示标题
    content: str  # 内容
    status: str = "pending"  # 状态：pending, running, completed, failed
    timestamp: Optional[str] = None
    details: Optional[Dict] = None  # 额外详情
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%H:%M:%S")


class ThoughtStepWidget:
    """单个思考步骤组件（可折叠）"""
    
    # 步骤类型对应的图标和颜色
    STEP_STYLES = {
        "intent": {"icon": "🎯", "color": "#2196F3", "bg": "#E3F2FD"},
        "rewrite": {"icon": "✏️", "color": "#FF9800", "bg": "#FFF3E0"},
        "retrieve": {"icon": "🔍", "color": "#9C27B0", "bg": "#F3E5F5"},
        "reason": {"icon": "🧠", "color": "#4CAF50", "bg": "#E8F5E9"},
        "final": {"icon": "✨", "color": "#F44336", "bg": "#FFEBEE"},
    }
    
    def __init__(self, parent, thought: ThoughtStep, on_toggle: Optional[Callable] = None):
        self.parent = parent
        self.thought = thought
        self.on_toggle = on_toggle
        self.is_expanded = False
        
        self._create_widget()
    
    def _create_widget(self):
        """创建组件"""
        style = self.STEP_STYLES.get(self.thought.step_type, 
                                     {"icon": "💭", "color": "#757575", "bg": "#F5F5F5"})
        
        # 主框架
        self.frame = tk.Frame(self.parent, bg="#ffffff", relief=tk.FLAT, bd=0)
        self.frame.pack(fill=tk.X, pady=2)
        
        # 头部（可点击折叠）
        self.header = tk.Frame(self.frame, bg=style["bg"], relief=tk.RAISED, bd=1)
        self.header.pack(fill=tk.X)
        self.header.bind("<Button-1>", self._toggle)
        
        # 状态图标
        status_icon = self._get_status_icon()
        self.status_label = tk.Label(
            self.header,
            text=status_icon,
            font=("微软雅黑", 12),
            bg=style["bg"],
            fg=style["color"]
        )
        self.status_label.pack(side=tk.LEFT, padx=(10, 5), pady=8)
        self.status_label.bind("<Button-1>", self._toggle)
        
        # 步骤图标
        self.icon_label = tk.Label(
            self.header,
            text=style["icon"],
            font=("微软雅黑", 12),
            bg=style["bg"]
        )
        self.icon_label.pack(side=tk.LEFT, padx=5, pady=8)
        self.icon_label.bind("<Button-1>", self._toggle)
        
        # 标题
        self.title_label = tk.Label(
            self.header,
            text=self.thought.title,
            font=("微软雅黑", 11, "bold"),
            bg=style["bg"],
            fg=style["color"]
        )
        self.title_label.pack(side=tk.LEFT, padx=5, pady=8)
        self.title_label.bind("<Button-1>", self._toggle)
        
        # 时间戳
        self.time_label = tk.Label(
            self.header,
            text=self.thought.timestamp,
            font=("微软雅黑", 9),
            bg=style["bg"],
            fg="#999999"
        )
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=8)
        self.time_label.bind("<Button-1>", self._toggle)
        
        # 展开/收起箭头
        self.arrow_label = tk.Label(
            self.header,
            text="▼",
            font=("微软雅黑", 10),
            bg=style["bg"],
            fg="#666666"
        )
        self.arrow_label.pack(side=tk.RIGHT, padx=5, pady=8)
        self.arrow_label.bind("<Button-1>", self._toggle)
        
        # 内容区域（默认隐藏）
        self.content_frame = tk.Frame(self.frame, bg="#ffffff", relief=tk.SUNKEN, bd=1)
        # 默认不pack，点击后展开
        
        # 内容文本
        self.content_text = tk.Text(
            self.content_frame,
            font=("微软雅黑", 10),
            bg="#fafafa",
            fg="#333333",
            wrap=tk.WORD,
            height=3,
            padx=10,
            pady=8,
            relief=tk.FLAT
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        self.content_text.insert("1.0", self.thought.content)
        self.content_text.config(state=tk.DISABLED)
        
        # 如果有详情，添加详情区域
        if self.thought.details:
            self._add_details()
    
    def _get_status_icon(self) -> str:
        """获取状态图标"""
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✓",
            "failed": "✗"
        }
        return status_icons.get(self.thought.status, "⏳")
    
    def _add_details(self):
        """添加详情显示"""
        if not self.thought.details:
            return
        
        details_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        details_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        for key, value in self.thought.details.items():
            detail_row = tk.Frame(details_frame, bg="#f0f0f0")
            detail_row.pack(fill=tk.X, pady=2)
            
            key_label = tk.Label(
                detail_row,
                text=f"{key}:",
                font=("微软雅黑", 9, "bold"),
                bg="#f0f0f0",
                fg="#666666"
            )
            key_label.pack(side=tk.LEFT)
            
            value_label = tk.Label(
                detail_row,
                text=str(value),
                font=("微软雅黑", 9),
                bg="#f0f0f0",
                fg="#333333",
                wraplength=400
            )
            value_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def _toggle(self, event=None):
        """切换展开/收起状态"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            self.arrow_label.config(text="▲")
        else:
            self.content_frame.pack_forget()
            self.arrow_label.config(text="▼")
        
        if self.on_toggle:
            self.on_toggle(self.is_expanded)
    
    def update_status(self, status: str):
        """更新状态"""
        self.thought.status = status
        self.status_label.config(text=self._get_status_icon())
    
    def update_content(self, content: str):
        """更新内容"""
        self.thought.content = content
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", content)
        self.content_text.config(state=tk.DISABLED)
        
        # 调整高度
        lines = content.split('\n')
        height = max(3, min(len(lines), 20))
        self.content_text.config(height=height)


class ReActThoughtChain:
    """ReAct思考链组件"""
    
    def __init__(self, parent, on_step_toggle: Optional[Callable] = None):
        self.parent = parent
        self.on_step_toggle = on_step_toggle
        self.steps: List[ThoughtStepWidget] = []
        
        self._create_widget()
    
    def _create_widget(self):
        """创建组件"""
        # 主框架
        self.frame = tk.Frame(self.parent, bg="#f5f5f5")
        self.frame.pack(fill=tk.X, pady=5)
        
        # 标题
        self.header = tk.Frame(self.frame, bg="#f5f5f5")
        self.header.pack(fill=tk.X, padx=10, pady=5)
        
        self.title_label = tk.Label(
            self.header,
            text="🧠 思考过程",
            font=("微软雅黑", 11, "bold"),
            bg="#f5f5f5",
            fg="#333333"
        )
        self.title_label.pack(side=tk.LEFT)
        
        # 展开/收起全部按钮
        self.toggle_all_btn = tk.Label(
            self.header,
            text="[展开全部]",
            font=("微软雅黑", 9),
            bg="#f5f5f5",
            fg="#2196F3",
            cursor="hand2"
        )
        self.toggle_all_btn.pack(side=tk.RIGHT)
        self.toggle_all_btn.bind("<Button-1>", self._toggle_all)
        
        # 步骤容器
        self.steps_container = tk.Frame(self.frame, bg="#ffffff", relief=tk.RAISED, bd=1)
        self.steps_container.pack(fill=tk.X, padx=10, pady=5)
    
    def add_step(self, step_type: str, title: str, content: str = "", 
                 status: str = "pending", details: Optional[Dict] = None) -> ThoughtStepWidget:
        """添加思考步骤"""
        thought = ThoughtStep(
            step_type=step_type,
            title=title,
            content=content,
            status=status,
            details=details
        )
        
        widget = ThoughtStepWidget(
            self.steps_container,
            thought,
            on_toggle=self.on_step_toggle
        )
        self.steps.append(widget)
        
        return widget
    
    def update_step(self, index: int, content: str = None, status: str = None):
        """更新指定步骤"""
        if 0 <= index < len(self.steps):
            widget = self.steps[index]
            if content is not None:
                widget.update_content(content)
            if status is not None:
                widget.update_status(status)
    
    def get_step(self, index: int) -> Optional[ThoughtStepWidget]:
        """获取指定步骤"""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None
    
    def clear(self):
        """清空所有步骤"""
        for widget in self.steps:
            widget.frame.destroy()
        self.steps.clear()

    def collapse_all(self):
        """收起全部步骤内容"""
        for step in self.steps:
            if step.is_expanded:
                step._toggle()
        self.toggle_all_btn.config(text="[展开全部]")

    def expand_last(self):
        """展开最后一个步骤，便于查看最新进展"""
        if not self.steps:
            return
        last = self.steps[-1]
        if not last.is_expanded:
            last._toggle()
    
    def _toggle_all(self, event=None):
        """展开/收起全部"""
        # 检查当前状态
        any_expanded = any(step.is_expanded for step in self.steps)
        
        # 如果任意一个展开，则全部收起；否则全部展开
        expand = not any_expanded
        
        for step in self.steps:
            if expand and not step.is_expanded:
                step._toggle()
            elif not expand and step.is_expanded:
                step._toggle()
        
        self.toggle_all_btn.config(text="[收起全部]" if expand else "[展开全部]")


def create_react_thought_chain(parent, on_step_toggle: Optional[Callable] = None) -> ReActThoughtChain:
    """创建ReAct思考链组件的便捷函数"""
    return ReActThoughtChain(parent, on_step_toggle)


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("ReAct思考链测试")
    root.geometry("600x500")
    root.configure(bg="#f5f5f5")
    
    # 创建思考链
    chain = create_react_thought_chain(root)
    
    # 添加测试步骤
    chain.add_step("intent", "意图识别", "用户询问关于Python的GIL问题，属于知识查询类问题", 
                   status="completed", details={"意图": "knowledge_query", "置信度": "0.95"})
    
    chain.add_step("rewrite", "Query改写", "原始查询：什么是GIL？\n改写后：Python中的全局解释器锁（GIL）是什么，它的作用机制是什么？",
                   status="completed", details={"关键词": "Python, GIL, 全局解释器锁"})
    
    chain.add_step("retrieve", "知识检索", "从知识库中检索到3条相关内容\n1. GIL的定义和作用...\n2. GIL对多线程的影响...\n3. 如何绕过GIL...",
                   status="completed", details={"召回数量": 3, "相似度最高": "0.92"})
    
    chain.add_step("reason", "推理分析", "基于检索到的知识，GIL是Python解释器的核心机制，它保证了线程安全但限制了多核利用...",
                   status="running")
    
    root.mainloop()
