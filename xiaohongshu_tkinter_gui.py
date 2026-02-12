#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书视频转文字工具 - Tkinter GUI 重写版
使用最常见技术，确保能正常运行
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import requests
import json
import os
import time
import hashlib
from datetime import datetime

# 创建目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

for d in [VIDEO_DIR, OUTPUT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

class XiaohongshuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("小红书视频转文字工具")
        self.root.geometry("800x600")
        
        # 变量
        self.link_var = tk.StringVar()
        self.is_processing = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # 顶部框架
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # 标题
        title_label = ttk.Label(top_frame, text="小红书视频转文字工具", 
                               font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=10)
        
        # 输入框架
        input_frame = ttk.Frame(top_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(input_frame, text="视频链接：").pack(side=tk.LEFT)
        self.link_entry = ttk.Entry(input_frame, textvariable=self.link_var, width=60)
        self.link_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="开始处理", 
                                     command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(button_frame, text="清空", 
                                   command=self.clear_inputs)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_btn = ttk.Button(button_frame, text="打开输出文件夹", 
                                  command=self.open_output_folder)
        self.open_btn.pack(side=tk.RIGHT, padx=5)
        
        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        progress_label = ttk.Label(top_frame, textvariable=self.progress_var)
        progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(top_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, 
                                                font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_inputs(self):
        """清空输入"""
        self.link_var.set("")
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set("就绪")
        self.status_var.set("就绪")
        
    def open_output_folder(self):
        """打开输出文件夹"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(OUTPUT_DIR)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{OUTPUT_DIR}"' if sys.platform == 'darwin' else f'xdg-open "{OUTPUT_DIR}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
            
    def start_processing(self):
        """开始处理"""
        if self.is_processing:
            messagebox.showwarning("警告", "正在处理中，请等待完成")
            return
            
        link = self.link_var.get().strip()
        if not link:
            messagebox.showwarning("警告", "请输入视频链接")
            return
            
        if not link.startswith(('http://', 'https://')):
            messagebox.showwarning("警告", "请输入有效的链接地址")
            return
            
        # 禁用按钮
        self.process_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.is_processing = True
        
        # 启动进度条
        self.progress_bar.start()
        self.progress_var.set("处理中...")
        self.status_var.set("正在处理...")
        
        # 在新线程中处理
        threading.Thread(target=self.process_link, args=(link,), daemon=True).start()
        
    def process_link(self, link):
        """处理链接"""
        try:
            self.log_message(f"开始处理链接: {link}")
            
            # 步骤1: 下载视频
            self.log_message("步骤1: 下载视频...")
            video_url = self.download_video(link)
            
            if not video_url:
                self.log_message("下载视频失败")
                self.finish_processing(False)
                return
                
            # 步骤2: 保存视频
            self.log_message("步骤2: 保存视频...")
            video_filename = self.save_video(video_url, link)
            
            if not video_filename:
                self.log_message("保存视频失败")
                self.finish_processing(False)
                return
                
            # 步骤3: 语音转文字
            self.log_message("步骤3: 语音转文字...")
            result_data = self.speech_to_text(video_filename)
            
            if not result_data:
                self.log_message("语音转文字失败")
                self.finish_processing(False)
                return
                
            # 步骤4: 生成文档
            self.log_message("步骤4: 生成文档...")
            doc_filename = self.generate_document(result_data, link)
            
            if not doc_filename:
                self.log_message("生成文档失败")
                self.finish_processing(False)
                return
                
            self.log_message(f"处理完成! 文档保存至: {doc_filename}")
            self.finish_processing(True)
            
        except Exception as e:
            self.log_message(f"处理过程中出现错误: {e}")
            self.finish_processing(False)
            
    def download_video(self, link):
        """下载视频"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'Referer': 'https://hellotik.app/',
                'Origin': 'https://hellotik.app'
            }
            
            payload = {
                "requestURL": link,
                "isMobile": "false",
                "isoCode": "HK",
                "adType": "adsense",
                "uwx_id": "uwx_350696y5juIO",
                "successCount": "0",
                "totalSuccessCount": "2",
                "firstSuccessDate": "2026-01-10",
                "time": int(time.time()),
                "key": "xaq8pkc7"
            }
            
            endpoints = [
                "https://api.hellotik.app/api/download",
                "https://hellotik.app/api/video",
                "https://hellotik.app/api/fetch"
            ]
            
            for endpoint in endpoints:
                try:
                    self.log_message(f"尝试API端点: {endpoint}")
                    response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log_message(f"API响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        
                        # 提取视频URL
                        for key in ['video_url', 'download_url', 'url']:
                            if key in result:
                                return result[key]
                            elif 'data' in result and isinstance(result['data'], dict) and key in result['data']:
                                return result['data'][key]
                                
                except Exception as e:
                    self.log_message(f"端点 {endpoint} 请求失败: {e}")
                    continue
                    
            self.log_message("所有API端点都失败")
            return None
            
        except Exception as e:
            self.log_message(f"下载视频异常: {e}")
            return None
            
    def save_video(self, video_url, link):
        """保存视频"""
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            timestamp = int(time.time())
            video_filename = os.path.join(VIDEO_DIR, f"video_{url_hash}_{timestamp}.mp4")
            
            self.log_message(f"下载视频: {video_url}")
            self.log_message(f"保存到: {video_filename}")
            
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(video_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            self.log_message(f"视频保存成功: {video_filename}")
            return video_filename
            
        except Exception as e:
            self.log_message(f"保存视频异常: {e}")
            return None
            
    def speech_to_text(self, video_filename):
        """语音转文字"""
        try:
            self.log_message("上传视频到reccloud...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://reccloud.cn/speech-to-text-online',
                'Origin': 'https://reccloud.cn'
            }
            
            with open(video_filename, 'rb') as video_file:
                files = {
                    'file': ('video.mp4', video_file, 'video/mp4')
                }
                data = {
                    'type': 'speech_to_text',
                    'config': json.dumps({
                        'enable_highlight': True,
                        'enable_seperate': True,
                        'enable_translate': False,
                        'language': 'zh-cn'
                    })
                }
                
                response = requests.post("https://api.reccloud.cn/v1/task/create",
                                        files=files, data=data, headers=headers, timeout=60)
                
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and 'data' in result:
                    task_id = result['data']['task_id']
                    self.log_message(f"上传成功，任务ID: {task_id}")
                    
                    # 等待处理完成
                    if self.wait_for_result(task_id):
                        return self.get_result(task_id)
                    else:
                        return None
                else:
                    self.log_message(f"上传失败: {result.get('msg', '未知错误')}")
                    return None
            else:
                self.log_message(f"上传请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_message(f"语音转文字异常: {e}")
            return None
            
    def wait_for_result(self, task_id, timeout=600):
        """等待处理结果"""
        self.log_message("等待处理完成...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"https://api.reccloud.cn/v1/task/status?task_id={task_id}",
                                       headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0 and 'data' in result:
                        status = result['data'].get('status', 'unknown')
                        progress = result['data'].get('progress', 0)
                        
                        self.log_message(f"处理状态: {status}, 进度: {progress}%")
                        
                        if status == 'completed':
                            self.log_message("处理完成")
                            return True
                        elif status == 'failed':
                            fail_reason = result['data'].get('fail_reason', '未知错误')
                            self.log_message(f"处理失败: {fail_reason}")
                            return False
                        
                        time.sleep(10)
                    else:
                        self.log_message(f"状态查询失败: {result.get('msg', '未知错误')}")
                        return False
                else:
                    self.log_message(f"状态查询请求失败: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_message(f"状态查询异常: {e}")
                return False
                
        self.log_message("处理超时")
        return False
        
    def get_result(self, task_id):
        """获取处理结果"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            
            response = requests.get(f"https://api.reccloud.cn/v1/task/result?task_id={task_id}",
                                   headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and 'data' in result:
                    self.log_message("获取结果成功")
                    return result['data']
                else:
                    self.log_message(f"获取结果失败: {result.get('msg', '未知错误')}")
                    return None
            else:
                self.log_message(f"结果请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_message(f"获取结果异常: {e}")
            return None
            
    def generate_document(self, result_data, link):
        """生成文档"""
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            timestamp = int(time.time())
            doc_filename = os.path.join(OUTPUT_DIR, f"小红书视频分析_{url_hash}_{timestamp}.md")
            
            # 提取内容
            segments = result_data.get('segments', [])
            transcript = ""
            
            for segment in segments:
                start_time = segment.get('start_time', 0)
                text = segment.get('text', '')
                timestamp_str = time.strftime('%H:%M:%S', time.gmtime(start_time))
                transcript += f"- [{timestamp_str}] {text}\n"
            
            # 获取AI摘要
            ai_summary = result_data.get('ai_summary', result_data.get('summary', ''))
            
            # 创建Markdown内容
            md_content = f"""# 小红书视频内容分析

## 视频信息
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 原始链接: {link}
- URL哈希: {url_hash}

## 📝 语音转文字内容

{transcript}

## 🤖 AI智能分析摘要

{ai_summary}

---
*由小红书视频分析工具生成*
"""
            
            with open(doc_filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
            self.log_message(f"文档生成成功: {doc_filename}")
            return doc_filename
            
        except Exception as e:
            self.log_message(f"生成文档异常: {e}")
            return None
            
    def finish_processing(self, success):
        """完成处理"""
        # 停止进度条
        self.progress_bar.stop()
        
        # 恢复按钮
        self.process_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)
        self.is_processing = False
        
        if success:
            self.progress_var.set("处理完成")
            self.status_var.set("处理完成")
            messagebox.showinfo("成功", "视频处理完成！")
        else:
            self.progress_var.set("处理失败")
            self.status_var.set("处理失败")

def main():
    root = tk.Tk()
    app = XiaohongshuGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
