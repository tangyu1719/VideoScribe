import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import sys


class VideoProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("视频转文字工具")
        self.root.geometry("600x400")

        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')

        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 文件选择
        ttk.Label(main_frame, text="选择视频文件:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=(0, 10))

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(
            file_frame, textvariable=self.file_path_var, width=60)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.browse_btn = ttk.Button(
            file_frame, text="浏览", command=self.browse_file)
        self.browse_btn.grid(row=0, column=1)

        file_frame.columnconfigure(0, weight=1)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        # 处理按钮
        self.process_btn = ttk.Button(
            button_frame, text="开始处理", command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清空按钮
        self.clear_btn = ttk.Button(
            button_frame, text="清空", command=self.clear_inputs)
        self.clear_btn.pack(side=tk.LEFT)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2,
                           sticky=(tk.W, tk.E), pady=10)

        # 输出框
        ttk.Label(main_frame, text="处理结果:").grid(
            row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.output_text = scrolledtext.ScrolledText(
            main_frame, height=12, width=70)
        self.output_text.grid(row=5, column=0, columnspan=2,
                              sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def browse_file(self):
        """浏览并选择视频文件"""
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def start_processing(self):
        """开始处理，使用线程避免界面卡顿"""
        video_file = self.file_path_var.get()

        if not video_file:
            messagebox.showwarning("警告", "请选择视频文件")
            return

        if not os.path.exists(video_file):
            messagebox.showerror("错误", "视频文件不存在")
            return

        # 启动处理线程
        thread = threading.Thread(target=self.process_file, args=(video_file,))
        thread.daemon = True
        thread.start()

    def process_file(self, video_file):
        """处理视频文件的后台函数"""
        self.root.after(0, lambda: self.progress.start())
        self.root.after(0, lambda: self.process_btn.config(state='disabled'))
        self.root.after(0, lambda: self.output_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.output_text.insert(
            tk.END, f"开始处理视频: {video_file}\n"))
        self.root.after(0, lambda: self.output_text.insert(
            tk.END, "正在上传到reccloud进行语音转文字...\n"))

        try:
            # 执行外部脚本
            cmd = [sys.executable, "xiaohongshu_to_text.py", video_file]
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding='utf-8')

            # 在主线程中更新UI
            self.root.after(0, lambda: self.handle_result(result))

        except Exception as e:
            self.root.after(0, lambda: self.handle_error(e))

    def handle_result(self, result):
        """处理结果回调"""
        self.progress.stop()
        self.process_btn.config(state='normal')

        self.output_text.insert(tk.END, "\n处理完成！\n")
        if result.stdout:
            self.output_text.insert(tk.END, f"输出信息:\n{result.stdout}\n")
        if result.stderr:
            self.output_text.insert(tk.END, f"错误信息:\n{result.stderr}\n")

    def handle_error(self, error):
        """处理错误回调"""
        self.progress.stop()
        self.process_btn.config(state='normal')
        self.output_text.insert(tk.END, f"\n发生错误: {str(error)}\n")

    def clear_inputs(self):
        """清空输入"""
        self.file_path_var.set("")
        self.output_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = VideoProcessor(root)

    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')  # 如果有图标文件
    except:
        pass

    # 居中显示
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
