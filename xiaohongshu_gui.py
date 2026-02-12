import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import os
import time
from pathlib import Path
import threading

class XiaohongshuProcessor
    def __init__(self, root)
        self.root = root
        self.root.title(小红书视频转文字工具)
        self.root.geometry(600x500)
        
        # 创建界面元素
        main_frame = ttk.Frame(root, padding=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text=小红书视频转文字工具, font=(Arial, 14, bold))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 链接输入
        ttk.Label(main_frame, text=小红书链接).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.link_var = tk.StringVar()
        link_entry = ttk.Entry(main_frame, textvariable=self.link_var, width=60)
        link_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # 处理按钮
        process_btn = ttk.Button(main_frame, text=开始处理, command=self.start_processing)
        process_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # 日志显示区域
        ttk.Label(main_frame, text=处理日志).grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.log_area = scrolledtext.ScrolledText(main_frame, height=15, width=70)
        self.log_area.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 配置列权重
        main_frame.columnconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
    def log_message(self, message)
        self.log_area.insert(tk.END, message + n)
        self.log_area.see(tk.END)
        self.root.update_idletasks()
        
    def start_processing(self)
        link = self.link_var.get().strip()
        if not link
            messagebox.showerror(错误, 请输入小红书链接)
            return
            
        # 在新线程中执行处理，防止界面冻结
        thread = threading.Thread(target=self.process_link, args=(link,))
        thread.daemon = True
        thread.start()
        
    def process_link(self, xhs_url)
        self.progress.start()
        try
            self.log_message(f开始处理链接 {xhs_url})
            self.log_message(正在调用视频下载工具网站API...)
            
            # 第一步：调用视频下载API
            download_headers = {
                'User-Agent' 'Mozilla5.0 (Windows NT 10.0; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome91.0.4472.124 Safari537.36',
                'Accept' 'applicationjson, textplain, ',
                'Content-Type' 'applicationjson',
                'Referer' 'httpshellotik.app',
                'Origin' 'httpshellotik.app'
            }
            
            download_payload = {
                url xhs_url,
                isMobile false
            }
            
            # 尝试多个可能的API端点
            possible_endpoints = [
                httpsapi.hellotik.appapidownload,
                httpshellotik.appapivideo,
                httpshellotik.appapifetch,
                httpswww.hellotik.appapidownload
            ]
            
            video_url = None
            for endpoint in possible_endpoints
                try
                    self.log_message(f尝试API端点 {endpoint})
                    response = requests.post(endpoint, json=download_payload, headers=download_headers, timeout=10)
                    
                    if response.status_code == 200
                        result = response.json()
                        if 'video_url' in result or 'download_url' in result
                            video_url = result.get('video_url') or result.get('download_url')
                            self.log_message(fSUCCESS 成功获取视频URL {video_url[50]}...)
                            break
                        elif 'data' in result and 'video_url' in result['data']
                            video_url = result['data']['video_url']
                            self.log_message(fSUCCESS 成功获取视频URL {video_url[50]}...)
                            break
                except Exception as e
                    self.log_message(f尝试端点 {endpoint} 失败 {str(e)})
                    continue
            
            if not video_url
                self.log_message(WARNING 无法通过API获取视频URL，可能是网站没有开放API)
                self.log_message(   请手动使用网站界面下载视频)
                self.log_message(   访问 httpshellotik.app 并粘贴链接)
                return False

            # 第二步：调用语音转文字API
            self.log_message(正在上传视频进行语音转文字处理...)
            
            # 下载视频到本地
            self.log_message(下载视频文件...)
            video_response = requests.get(video_url)
            if video_response.status_code != 200
                self.log_message(ERROR 下载视频失败)
                return False
            
            # 保存临时视频文件
            import tempfile
            temp_dir = tempfile.mkdtemp()
            video_filename = os.path.join(temp_dir, temp_video.mp4)
            
            with open(video_filename, 'wb') as f
                f.write(video_response.content)
            
            self.log_message(fSUCCESS 视频已下载 {video_filename})
            
            # 上传到reccloud进行语音转文字
            reccloud_headers = {
                'User-Agent' 'Mozilla5.0 (Windows NT 10.0; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome91.0.4472.124 Safari537.36',
                'Referer' 'httpsreccloud.cnspeech-to-text-online',
                'Origin' 'httpsreccloud.cn'
            }
            
            with open(video_filename, 'rb') as video_file
                files = {
                    'file' ('video.mp4', video_file, 'videomp4')
                }
                data = {
                    'type' 'speech_to_text',
                    'config' json.dumps({
                        'enable_highlight' True,
                        'enable_seperate' True,
                        'enable_translate' False
                    })
                }
                
                upload_response = requests.post(
                    httpsapi.reccloud.cnv1taskcreate, 
                    files=files, 
                    data=data, 
                    headers=reccloud_headers
                )
            
            if upload_response.status_code != 200
                self.log_message(fERROR 上传到reccloud失败，状态码 {upload_response.status_code})
                return False
            
            upload_result = upload_response.json()
            if upload_result.get('code') != 0
                self.log_message(fERROR 上传到reccloud失败 {upload_result.get('msg', '未知错误')})
                return False
            
            task_id = upload_result['data']['task_id']
            self.log_message(fSUCCESS 视频上传成功，任务ID {task_id})
            
            # 等待处理完成
            self.log_message(PROGRESS 正在处理中，请稍候...)
            status_headers = {
                'User-Agent' 'Mozilla5.0 (Windows NT 10.0; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome91.0.4472.124 Safari537.36',
            }
            
            start_time = time.time()
            timeout = 600  # 10分钟超时
            
            while time.time() - start_time  timeout
                status_response = requests.get(
                    fhttpsapi.reccloud.cnv1taskstatustask_id={task_id},
                    headers=status_headers
                )
                
                if status_response.status_code == 200
                    status_result = status_response.json()
                    if status_result.get('code') == 0
                        status = status_result['data']['status']
                        
                        if status == 'completed'
                            self.log_message(SUCCESS 处理完成)
                            break
                        elif status == 'failed'
                            self.log_message(fERROR 处理失败 {status_result['data'].get('fail_reason', '未知错误')})
                            return False
                        else
                            self.log_message(fPROGRESS 处理中... 当前状态 {status})
                            time.sleep(10)
                            continue
                    else
                        self.log_message(fERROR 查询状态失败 {status_result.get('msg', '未知错误')})
                        return False
                else
                    self.log_message(fERROR 查询状态请求失败，状态码 {status_response.status_code})
                    return False
            
            if time.time() - start_time = timeout
                self.log_message(ERROR 处理超时)
                return False
            
            # 获取处理结果
            self.log_message(获取处理结果...)
            result_response = requests.get(
                fhttpsapi.reccloud.cnv1taskresulttask_id={task_id},
                headers=status_headers
            )
            
            if result_response.status_code != 200
                self.log_message(fERROR 获取结果失败，状态码 {result_response.status_code})
                return False
            
            result_data = result_response.json()
            if result_data.get('code') != 0
                self.log_message(fERROR 获取结果失败 {result_data.get('msg', '未知错误')})
                return False
            
            self.log_message(SUCCESS 成功获取处理结果)
            
            # 保存为Markdown文档
            self.save_as_markdown(result_data['data'])
            
            # 清理临时文件
            try
                os.remove(video_filename)
                os.rmdir(temp_dir)
            except
                pass
            
            self.log_message(nSUCCESS 处理完成！)
            messagebox.showinfo(成功, 处理完成！Markdown文档已保存到 csdn待阅览 目录)
            
        except Exception as e
            self.log_message(fERROR 处理过程中出现错误 {e})
            messagebox.showerror(错误, f处理过程中出现错误 {e})
        finally
            self.progress.stop()

    def save_as_markdown(self, content_data, output_dir=csdn待阅览)
        将内容保存为Markdown文档
        if not os.path.exists(output_dir)
            os.makedirs(output_dir)

        # 生成文件名
        timestamp = int(time.time())
        filename = f小红书视频分析_{timestamp}.md
        filepath = os.path.join(output_dir, filename)

        # 提取内容
        segments = content_data.get('segments', [])
        transcript = 
        for segment in segments
            start_time = segment.get('start_time', 0)
            text = segment.get('text', '')
            timestamp_str = time.strftime('%H%M%S', time.gmtime(start_time))
            transcript += f- [{timestamp_str}] {text}n
        
        # 获取AI摘要
        ai_summary = content_data.get('ai_summary', content_data.get('summary', ''))
        
        # 创建Markdown内容
        md_content = f# 小红书视频内容分析

## 视频信息
- 分析时间 {time.strftime('%Y-%m-%d %H%M%S', time.localtime())}

## 语音转文字内容
{transcript}

## AI智能分析摘要
{ai_summary}

---
通过小红书视频分析工具生成

        
        with open(filepath, 'w', encoding='utf-8') as f
            f.write(md_content)

        self.log_message(fSUCCESS Markdown文档已保存到 {filepath})
        return filepath

def main()
    root = tk.Tk()
    app = XiaohongshuProcessor(root)
    root.mainloop()

if __name__ == __main__
    main()