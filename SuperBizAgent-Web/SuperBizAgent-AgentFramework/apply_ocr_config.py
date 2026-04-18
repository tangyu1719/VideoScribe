#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完成 OCR API 配置和移除输入模态的脚本
"""

import re

# 读取文件
with open(r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在设置页面按钮行添加 OCR API 配置按钮
old_btn_row = '''        ttk.Button(btn_row, text="AI 配置", command=self.open_ai_config_window).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="API 设置", command=self.open_ai_api_config_window).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="线程配置", command=self.open_thread_config_window).pack(side=tk.LEFT, padx=(0, 8))'''

new_btn_row = '''        ttk.Button(btn_row, text="AI 配置", command=self.open_ai_config_window).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="API 设置", command=self.open_ai_api_config_window).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="OCR API 配置", command=self.open_ocr_api_config_window).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="线程配置", command=self.open_thread_config_window).pack(side=tk.LEFT, padx=(0, 8))'''

content = content.replace(old_btn_row, new_btn_row)

# 2. 在 open_ai_api_config_window 方法后添加 open_ocr_api_config_window 方法
ocr_method = '''
    def open_ocr_api_config_window(self):
        """打开 OCR API 配置窗口"""
        try:
            from ocr_api_config_gui import OcrApiConfigGui
            ocr_config = CONFIG.get('ocr_config', {})
            OcrApiConfigGui(self.root, ocr_config)
        except ImportError:
            messagebox.showwarning(
                "模块未加载",
                "OCR API 配置模块 (ocr_api_config_gui) 未找到，请确保文件存在。"
            )
        except Exception as e:
            messagebox.showerror("错误", f"打开 OCR API 配置失败：{e}")
'''

# 找到 open_ai_api_config_window 方法的结束位置
pattern = r'(    def open_ai_api_config_window\(self\):.*?^\n)(    def open_task_node_center_window)'
match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
if match:
    content = content.replace(
        match.group(0),
        match.group(1) + ocr_method + '\n' + match.group(2)
    )

# 写入文件
with open(r'f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已完成：")
print("  1. 在设置页面添加 OCR API 配置按钮")
print("  2. 添加 open_ocr_api_config_window 方法")
print("\n请手动删除输入模态相关代码（第 3009-3065 行）")
