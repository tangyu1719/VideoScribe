#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态文档处理GUI - 支持文件上传和处理
支持文件类型：图片、PDF、DOCX、MD、CSV、音频、视频
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
from pathlib import Path

# 导入MinerU文档处理器
try:
    from mineru_processor import MinerUProcessor, MinerUResult
    MINERU_AVAILABLE = True
    print("✓ MinerU处理器已加载")
except ImportError:
    MINERU_AVAILABLE = False
    print("警告：MinerU处理器模块未安装")

# 向后兼容：导入旧的文档处理器
try:
    from document_processor import DocumentProcessor, DocumentType, ProcessingResult
    DOC_PROCESSOR_AVAILABLE = True
except ImportError:
    DOC_PROCESSOR_AVAILABLE = False

# 导入视频下载器
try:
    from video_downloader import download_video, speech_to_text
    VIDEO_DOWNLOADER_AVAILABLE = True
except ImportError:
    VIDEO_DOWNLOADER_AVAILABLE = False
    print("警告：视频下载器模块未安装")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 文件类型配置
FILE_TYPE_CONFIG = {
    'image': {
        'label': '图片',
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
        'max_size': 10 * 1024 * 1024,  # 10MB
        'color': '#9333ea'  # purple
    },
    'pdf': {
        'label': 'PDF',
        'extensions': ['.pdf'],
        'max_size': 50 * 1024 * 1024,  # 50MB
        'color': '#dc2626'  # red
    },
    'docx': {
        'label': 'Word',
        'extensions': ['.docx', '.doc'],
        'max_size': 20 * 1024 * 1024,  # 20MB
        'color': '#2563eb'  # blue
    },
    'markdown': {
        'label': 'Markdown',
        'extensions': ['.md', '.markdown'],
        'max_size': 5 * 1024 * 1024,  # 5MB
        'color': '#6b7280'  # gray
    },
    'csv': {
        'label': 'CSV',
        'extensions': ['.csv'],
        'max_size': 10 * 1024 * 1024,  # 10MB
        'color': '#16a34a'  # green
    },
    'audio': {
        'label': '音频',
        'extensions': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
        'max_size': 100 * 1024 * 1024,  # 100MB
        'color': '#ea580c'  # orange
    },
    'video': {
        'label': '视频',
        'extensions': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
        'max_size': 500 * 1024 * 1024,  # 500MB
        'color': '#db2777'  # pink
    }
}


def get_file_type(file_path: str) -> tuple:
    """获取文件类型信息"""
    ext = Path(file_path).suffix.lower()
    for file_type, config in FILE_TYPE_CONFIG.items():
        if ext in config['extensions']:
            return file_type, config
    return None, None


class MultimodalProcessingPage(tk.Frame):
    """多模态文档处理页面 - 基于MinerU技术"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f5f5f5", **kwargs)
        
        # 优先使用MinerU处理器
        if MINERU_AVAILABLE:
            self.mineru_processor = MinerUProcessor(output_dir=OUTPUT_DIR)
            self.processor = None
            print("✓ 使用MinerU处理器")
        elif DOC_PROCESSOR_AVAILABLE:
            self.mineru_processor = None
            self.processor = DocumentProcessor()
            print("⚠ 使用旧版文档处理器")
        else:
            self.mineru_processor = None
            self.processor = None
            print("✗ 无可用处理器")
        
        self.selected_files = []
        self.processing = False
        
        # 创建UI
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = tk.Frame(self, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_frame = tk.Frame(main_container, bg="#f5f5f5")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            title_frame,
            text="📁 多模态文档处理",
            font=("微软雅黑", 18, "bold"),
            bg="#f5f5f5",
            fg="#1a1a1a"
        ).pack(side=tk.LEFT)
        
        # 文件拖放区域
        self.drop_frame = tk.Frame(
            main_container,
            bg="#ffffff",
            highlightbackground="#d1d5db",
            highlightthickness=2,
            height=200
        )
        self.drop_frame.pack(fill=tk.X, pady=(0, 20))
        self.drop_frame.pack_propagate(False)
        
        # 拖放提示
        self.drop_label = tk.Label(
            self.drop_frame,
            text="📤\n拖拽文件到此处，或点击选择文件\n支持：图片、PDF、Word、Markdown、CSV、音频、视频",
            font=("微软雅黑", 12),
            bg="#ffffff",
            fg="#6b7280",
            justify=tk.CENTER
        )
        self.drop_label.pack(expand=True)
        
        # 绑定点击事件
        self.drop_frame.bind("<Button-1>", lambda e: self._select_files())
        self.drop_label.bind("<Button-1>", lambda e: self._select_files())
        
        # 支持的文件类型
        types_frame = tk.Frame(main_container, bg="#f5f5f5")
        types_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            types_frame,
            text="支持的文件类型：",
            font=("微软雅黑", 10),
            bg="#f5f5f5",
            fg="#6b7280"
        ).pack(side=tk.LEFT)
        
        for file_type, config in FILE_TYPE_CONFIG.items():
            badge = tk.Label(
                types_frame,
                text=f" {config['label']} ",
                font=("微软雅黑", 9),
                bg=config['color'],
                fg="#ffffff",
                relief=tk.FLAT
            )
            badge.pack(side=tk.LEFT, padx=(5, 0))
        
        # 已选择文件列表
        files_frame = tk.LabelFrame(
            main_container,
            text="已选择文件",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 文件列表
        self.files_listbox = tk.Listbox(
            files_frame,
            font=("微软雅黑", 10),
            selectmode=tk.SINGLE,
            bg="#ffffff",
            fg="#1a1a1a",
            relief=tk.FLAT
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 按钮区域
        btn_frame = tk.Frame(main_container, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X)
        
        self.clear_btn = tk.Button(
            btn_frame,
            text="🗑️ 清空",
            command=self._clear_files,
            font=("微软雅黑", 11),
            bg="#ef4444",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=12
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_btn = tk.Button(
            btn_frame,
            text="📂 选择文件",
            command=self._select_files,
            font=("微软雅黑", 11),
            bg="#3b82f6",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=12
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.process_btn = tk.Button(
            btn_frame,
            text="▶️ 开始处理",
            command=self._start_processing,
            font=("微软雅黑", 11),
            bg="#10b981",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            width=12
        )
        self.process_btn.pack(side=tk.LEFT)
        
        # 进度区域
        self.progress_frame = tk.LabelFrame(
            main_container,
            text="处理进度",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        
        # 日志区域
        log_frame = tk.LabelFrame(
            main_container,
            text="处理日志",
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#1a1a1a"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _select_files(self):
        """选择文件"""
        # 构建文件类型过滤器
        all_extensions = []
        for config in FILE_TYPE_CONFIG.values():
            all_extensions.extend(config['extensions'])
        
        filetypes = [
            ("所有支持的文件", " ".join(f"*{ext}" for ext in all_extensions)),
            ("图片文件", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
            ("PDF文件", "*.pdf"),
            ("Word文件", "*.docx *.doc"),
            ("Markdown文件", "*.md *.markdown"),
            ("CSV文件", "*.csv"),
            ("音频文件", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac"),
            ("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
            ("所有文件", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="选择要处理的文件",
            filetypes=filetypes
        )
        
        if files:
            for file_path in files:
                self._add_file(file_path)
                
    def _add_file(self, file_path: str):
        """添加文件到列表"""
        file_type, config = get_file_type(file_path)
        
        if not file_type:
            self._log(f"❌ 不支持的文件类型: {os.path.basename(file_path)}")
            return
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > config['max_size']:
            self._log(f"❌ 文件过大: {os.path.basename(file_path)} ({self._format_size(file_size)} > {self._format_size(config['max_size'])})")
            return
        
        # 添加到列表
        self.selected_files.append({
            'path': file_path,
            'type': file_type,
            'config': config,
            'size': file_size
        })
        
        # 更新列表显示
        display_text = f"[{config['label']}] {os.path.basename(file_path)} ({self._format_size(file_size)})"
        self.files_listbox.insert(tk.END, display_text)
        
        self._log(f"✅ 已添加: {os.path.basename(file_path)}")
        
    def _clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        self._log("🗑️ 已清空文件列表")
        
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
        
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()
        
    def _start_processing(self):
        """开始处理文件"""
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择要处理的文件")
            return
            
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请等待")
            return
            
        if not DOC_PROCESSOR_AVAILABLE:
            messagebox.showerror("错误", "文档处理器模块未安装")
            return
            
        # 在后台线程中处理
        self.processing = True
        self.process_btn.configure(state=tk.DISABLED, text="⏳ 处理中...")
        
        thread = threading.Thread(target=self._process_files_thread)
        thread.daemon = True
        thread.start()
        
    def _process_files_thread(self):
        """在后台线程中处理文件"""
        try:
            for file_info in self.selected_files:
                self._process_single_file(file_info)
                
            self.after(0, self._processing_complete)
        except Exception as e:
            self.after(0, lambda: self._processing_error(str(e)))
            
    def _process_single_file(self, file_info: dict):
        """处理单个文件"""
        file_path = file_info['path']
        file_type = file_info['type']
        file_name = os.path.basename(file_path)
        
        self._log(f"\n{'='*50}")
        self._log(f"📝 开始处理: {file_name}")
        self._log(f"📂 文件类型: {file_info['config']['label']}")
        self._log(f"📊 文件大小: {self._format_size(file_info['size'])}")
        
        try:
            # 处理文件
            result = self.processor.process(file_path)
            
            if result.success:
                self._log(f"✅ 处理成功")
                self._log(f"📄 提取文本长度: {len(result.content.text)} 字符")
                
                if result.content.images:
                    self._log(f"🖼️ 提取图片数量: {len(result.content.images)}")
                    
                if result.content.tables:
                    self._log(f"📊 提取表格数量: {len(result.content.tables)}")
                    
                # 保存结果
                self._save_result(file_name, result)
            else:
                self._log(f"❌ 处理失败: {result.error}")
                
        except Exception as e:
            self._log(f"❌ 处理异常: {str(e)}")
            
    def _save_result(self, file_name: str, result: ProcessingResult):
        """保存处理结果"""
        try:
            # 创建输出目录
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            # 生成输出文件名
            base_name = Path(file_name).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(OUTPUT_DIR, f"{base_name}_{timestamp}.md")
            
            # 构建Markdown内容
            content = f"""# {base_name} 处理结果

## 文件信息
- **原始文件**: {file_name}
- **文件类型**: {result.doc_type.value}
- **处理时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **处理耗时**: {result.processing_time:.2f} 秒

## 提取内容

{result.content.text}

"""
            
            # 添加图片信息
            if result.content.images:
                content += "## 图片信息\n\n"
                for i, img in enumerate(result.content.images):
                    content += f"- 图片 {i+1}\n"
                content += "\n"
                
            # 添加表格信息
            if result.content.tables:
                content += "## 表格数据\n\n"
                for i, table in enumerate(result.content.tables):
                    content += f"### 表格 {i+1}\n\n"
                    for row in table:
                        content += "| " + " | ".join(str(cell) for cell in row) + " |\n"
                    content += "\n"
                    
            # 添加元数据
            if result.content.metadata:
                content += "## 元数据\n\n"
                for key, value in result.content.metadata.items():
                    content += f"- **{key}**: {value}\n"
                content += "\n"
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self._log(f"💾 结果已保存: {output_file}")
            
        except Exception as e:
            self._log(f"❌ 保存结果失败: {str(e)}")
            
    def _processing_complete(self):
        """处理完成"""
        self.processing = False
        self.process_btn.configure(state=tk.NORMAL, text="▶️ 开始处理")
        self._log(f"\n{'='*50}")
        self._log("🎉 所有文件处理完成！")
        messagebox.showinfo("完成", "所有文件处理完成！")
        
    def _processing_error(self, error: str):
        """处理错误"""
        self.processing = False
        self.process_btn.configure(state=tk.NORMAL, text="▶️ 开始处理")
        self._log(f"❌ 处理过程中发生错误: {error}")
        messagebox.showerror("错误", f"处理失败: {error}")


class MultimodalGUI:
    """多模态文档处理GUI主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("多模态文档处理工具")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f5f5f5")
        
        # 创建主界面
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面"""
        # 创建多模态处理页面
        self.processing_page = MultimodalProcessingPage(self.root)
        self.processing_page.pack(fill=tk.BOTH, expand=True)
        
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    app = MultimodalGUI()
    app.run()


if __name__ == "__main__":
    main()
