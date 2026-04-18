#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR API 配置界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import uuid


class OcrApiConfigGui:
    """OCR API 配置界面"""
    
    def __init__(self, parent, config: dict = None):
        self.parent = parent
        self.config = config or self._get_default_config()
        self.config_id = self.config.get('id', 'ocr_default')
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("OCR API 配置中心")
        self.window.geometry("900x700")
        self.window.configure(bg="#f0f4f8")
        
        # 标题区域（页头）
        title_frame = tk.Frame(self.window, bg="#f0f4f8")
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(
            title_frame,
            text="OCR API 配置中心",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 18, "bold"),
            fg="#0066cc",
            bg="#f0f4f8"
        ).pack(side=tk.LEFT)
        
        # 说明文字
        desc_frame = tk.Frame(self.window, bg="#f0f4f8")
        desc_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        tk.Label(
            desc_frame,
            text="说明：配置 OCR 服务的 API 接入点，用于图片文字识别功能。",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 9),
            fg="#666666",
            bg="#f0f4f8",
            wraplength=800,
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # 按钮区域（统一放在页头）
        button_frame = tk.Frame(self.window, bg="#f0f4f8")
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        save_btn = tk.Button(
            button_frame,
            text="保存配置",
            command=self._save_config,
            bg="#0066cc",
            fg="white",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            overrelief=tk.RAISED
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=self.window.destroy,
            bg="#e0e0e0",
            fg="#333333",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 11),
            padx=20,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            overrelief=tk.RAISED
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 内容区域
        self.content_frame = tk.Frame(self.window, bg="#f0f4f8")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建主配置区域
        self._create_main_config_section()
        
        # 模态窗口
        self.window.transient(self.parent)
        self.window.grab_set()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            'id': 'ocr_default',
            'name': '百度 OCR',
            'app_id': '',
            'api_key': '',
            'secret_key': '',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_main_config_section(self):
        """创建主配置区域"""
        main_frame = tk.LabelFrame(
            self.content_frame,
            text="主配置（OCR 服务接入点）",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 12, "bold"),
            fg="#0066cc",
            bg="#ffffff",
            padx=20,
            pady=20
        )
        main_frame.pack(fill=tk.X, pady=10)
        
        # 配置名称
        tk.Label(
            main_frame,
            text="配置名称:",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            bg="#ffffff"
        ).grid(row=0, column=0, sticky=tk.W, pady=8)
        
        self.name_var = tk.StringVar(value=self.config.get('name', '百度 OCR'))
        name_entry = tk.Entry(
            main_frame,
            textvariable=self.name_var,
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            width=50,
            bd=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=8)
        
        # APP ID
        tk.Label(
            main_frame,
            text="APP ID:",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            bg="#ffffff"
        ).grid(row=1, column=0, sticky=tk.W, pady=8)
        
        self.app_id_var = tk.StringVar(value=self.config.get('app_id', ''))
        app_id_entry = tk.Entry(
            main_frame,
            textvariable=self.app_id_var,
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            width=50,
            bd=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        app_id_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=8)
        
        # API Key
        tk.Label(
            main_frame,
            text="API Key:",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            bg="#ffffff"
        ).grid(row=2, column=0, sticky=tk.W, pady=8)
        
        self.api_key_var = tk.StringVar(value=self.config.get('api_key', ''))
        api_key_entry = tk.Entry(
            main_frame,
            textvariable=self.api_key_var,
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            width=50,
            bd=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#e0e0e0",
            show="*"
        )
        api_key_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Secret Key
        tk.Label(
            main_frame,
            text="Secret Key:",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            bg="#ffffff"
        ).grid(row=3, column=0, sticky=tk.W, pady=8)
        
        self.secret_key_var = tk.StringVar(value=self.config.get('secret_key', ''))
        secret_key_entry = tk.Entry(
            main_frame,
            textvariable=self.secret_key_var,
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            width=50,
            bd=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#e0e0e0",
            show="*"
        )
        secret_key_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=8)
        
        # 启用状态
        tk.Label(
            main_frame,
            text="启用状态:",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 10),
            bg="#ffffff"
        ).grid(row=4, column=0, sticky=tk.W, pady=8)
        
        self.enabled_var = tk.BooleanVar(value=self.config.get('enabled', True))
        enabled_check = tk.Checkbutton(
            main_frame,
            variable=self.enabled_var,
            bg="#ffffff",
            activebackground="#ffffff"
        )
        enabled_check.grid(row=4, column=1, sticky=tk.W, padx=10, pady=8)
        
        # 帮助信息
        help_frame = tk.Frame(main_frame, bg="#f0f4f8")
        help_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
        
        tk.Label(
            help_frame,
            text="💡 如何获取百度 OCR 密钥：\n"
                 "1. 访问百度智能云：https://cloud.baidu.com/\n"
                 "2. 创建应用并开通文字识别服务\n"
                 "3. 在应用详情页面获取 APP ID、API Key 和 Secret Key",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 9),
            fg="#666666",
            bg="#f0f4f8",
            justify=tk.LEFT
        ).pack(anchor=tk.W)
    
    def _save_config(self):
        """保存配置"""
        try:
            # 收集配置数据
            new_config = {
                'id': self.config_id,
                'name': self.name_var.get().strip(),
                'app_id': self.app_id_var.get().strip(),
                'api_key': self.api_key_var.get().strip(),
                'secret_key': self.secret_key_var.get().strip(),
                'enabled': self.enabled_var.get(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 验证必填字段
            if not new_config['app_id']:
                messagebox.showwarning("警告", "APP ID 不能为空", parent=self.window)
                return
            
            if not new_config['api_key']:
                messagebox.showwarning("警告", "API Key 不能为空", parent=self.window)
                return
            
            if not new_config['secret_key']:
                messagebox.showwarning("警告", "Secret Key 不能为空", parent=self.window)
                return
            
            # 保存到 config.json
            config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # 保存 OCR 配置
            config['ocr_config'] = new_config
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "OCR API 配置已保存！", parent=self.window)
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{e}", parent=self.window)
