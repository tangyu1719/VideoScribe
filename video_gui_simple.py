#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文字处理工具 - 简化版本
修复所有参数错误，确保基本功能正常
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import os
import time
import hashlib
from datetime import datetime
import re

APP_TITLE = "视频转文字处理工具 (GUI)"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

for d in (VIDEO_DIR, OUTPUT_DIR):
    if not os.path.exists(d):
        os.makedirs(d)

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("880x600")

        self.platform_var = tk.StringVar(value="小红书")
        self.link_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        # 顶部区域
        top = tk.Frame(self.root, padx=12, pady=10)
        top.pack(fill=tk.X)

        tk.Label(top, text="平台：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.platform_cb = ttk.Combobox(top, state="readonly", width=12,
                                         textvariable=self.platform_var,
                                         values=["小红书"])
        self.platform_cb.pack(side=tk.LEFT, padx=6)

        tk.Label(top, text="视频链接：", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.link_entry = tk.Entry(top, textvariable=self.link_var, width=70)
        self.link_entry.pack(side=tk.LEFT, padx=6)

        self.start_btn = ttk.Button(top, text="开始处理", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=8)

        # 日志区域
        mid = tk.Frame(self.root, padx=12, pady=8)
        mid.pack(fill=tk.BOTH, expand=True)
        tk.Label(mid, text="处理日志：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(mid, height=24, font=("Consolas", 10))
        self.log.pack(fill=tk.BOTH, expand=True)

        # 底部状态
        bottom = tk.Frame(self.root, padx=12, pady=6)
        bottom.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(bottom, textvariable=self.status_var, anchor=tk.W).pack(fill=tk.X)

    def append_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()

    def extract_url_from_text(self, text):
        """从文本中提取URL"""
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            if 'xiaohongshu.com' in url.lower():
                url = url.rstrip('.,;:!?')
                return url
                
        return None

    def start(self):
        link = self.link_var.get().strip()
        
        # 尝试从文本中提取URL
        extracted_url = self.extract_url_from_text(link)
        if extracted_url:
            self.append_log(f"从文本中提取到URL: {extracted_url}")
            self.link_var.set(extracted_url)
            link = extracted_url
        
        if not link:
            messagebox.showwarning("提示", "请先输入视频链接")
            return
            
        if not ('xiaohongshu.com' in link.lower()):
            messagebox.showwarning("提示", "请输入有效的小红书链接")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.append_log(f"开始处理：平台={self.platform_var.get()} 链接={link}")
        threading.Thread(target=self._run_pipeline, args=(self.platform_var.get(), link), daemon=True).start()

    def _run_pipeline(self, platform, link):
        try:
            self.set_status("下载视频...")
            self.append_log("=== 步骤1: 下载视频 ===")
            video_result = self.download_video(link, platform)
            
            if not video_result:
                self.append_log("未获取到视频，流程结束")
                self.set_status("失败")
                return

            self.set_status("语音转文字...")
            self.append_log("=== 步骤2: 语音转文字 ===")
            result_data = self.speech_to_text(video_result)
            
            if not result_data:
                self.append_log("语音转文字失败，流程结束")
                self.set_status("失败")
                return

            self.set_status("生成Markdown文档...")
            self.append_log("=== 步骤3: 生成Markdown文档 ===")
            md_file = self.generate_md(result_data, link, platform)
            
            if md_file:
                self.append_log(f"✅ 处理完成！文档已保存：{md_file}")
                self.set_status("完成")
                try:
                    os.startfile(OUTPUT_DIR)
                except:
                    self.append_log(f"输出目录：{OUTPUT_DIR}")
            else:
                self.append_log("生成文档失败")
                self.set_status("失败")
                
        except Exception as e:
            self.append_log(f"异常：{e}")
            self.set_status("失败")
        finally:
            self.start_btn.config(state=tk.NORMAL)

    def download_video(self, link, platform):
        """下载视频"""
        try:
            self.append_log("测试hellotik.app API...")
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'Referer': 'https://www.hellotik.app/zh/rednote',
                'Origin': 'https://www.hellotik.app'
            })
            
            # 测试API端点
            endpoint = "https://www.hellotik.app/api/download"
            payload = {"url": link}
            
            self.append_log(f"POST到: {endpoint}")
            self.append_log(f"数据: {json.dumps(payload, ensure_ascii=False)}")
            
            response = session.post(endpoint, json=payload, timeout=20)
            
            self.append_log(f"状态码: {response.status_code}")
            self.append_log(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'json' in content_type:
                    try:
                        data = response.json()
                        self.append_log(f"JSON响应: {json.dumps(data, ensure_ascii=False)[:300]}")
                        
                        # 查找下载链接
                        for key in ['downloadUrl', 'url', 'videoUrl', 'link', 'download_url']:
                            if key in data:
                                download_url = data[key]
                                self.append_log(f"找到下载链接: {download_url}")
                                return self.download_from_url(download_url, link)
                                
                        self.append_log("JSON响应中未找到下载链接")
                        
                    except json.JSONDecodeError as e:
                        self.append_log(f"JSON解析失败: {e}")
                        self.append_log(f"响应内容: {response.text[:200]}")
                        
                elif len(response.content) > 100000:  # 可能是视频文件
                    self.append_log(f"检测到大文件: {len(response.content)} 字节")
                    
                    url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
                    ts = int(time.time())
                    filename = f"video_{url_hash}_{ts}.mp4"
                    file_path = os.path.join(VIDEO_DIR, filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.append_log(f"视频保存成功: {filename}")
                    return file_path
                    
                else:
                    self.append_log(f"HTML响应: {response.text[:200]}")
                    
            else:
                self.append_log(f"请求失败: {response.status_code}")
                
            # API调用失败，返回None
            self.append_log("所有API调用失败，无法获取视频")
            return None
            
        except Exception as e:
            self.append_log(f"下载失败: {e}")
            return None

    def download_from_url(self, video_url, original_link):
        """从URL下载视频"""
        try:
            self.append_log(f"从URL下载: {video_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.hellotik.app/'
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            url_hash = hashlib.md5(original_link.encode()).hexdigest()[:8]
            ts = int(time.time())
            filename = f"video_{url_hash}_{ts}.mp4"
            file_path = os.path.join(VIDEO_DIR, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            file_size = os.path.getsize(file_path)
            self.append_log(f"视频下载完成，大小: {file_size} 字节")
            
            return file_path
            
        except Exception as e:
            self.append_log(f"URL下载失败: {e}")
            return None

    def speech_to_text(self, video_file):
        """语音转文字 - 使用reccloud.cn"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://reccloud.cn/speech-to-text-online',
                'Origin': 'https://reccloud.cn'
            }
            
            self.append_log("上传视频到reccloud.cn进行语音转文字...")
            
            with open(video_file, 'rb') as vf:
                files = {'file': ('video.mp4', vf, 'video/mp4')}
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
                                       files=files, data=data, headers=headers, timeout=120)
                                       
            if response.status_code != 200:
                self.append_log(f"上传失败: {response.text[:200]}")
                return None
                
            result = response.json()
            if result.get('code') != 0:
                self.append_log(f"上传错误: {result}")
                return None
                
            task_id = result['data']['task_id']
            self.append_log(f"任务ID: {task_id}")

            # 轮询任务状态
            start_time = time.time()
            while time.time() - start_time < 600:  # 最多等待10分钟
                status_response = requests.get(f"https://api.reccloud.cn/v1/task/status?task_id={task_id}", 
                                             headers=headers, timeout=15)
                
                if status_response.status_code != 200:
                    self.append_log(f"状态查询失败: {status_response.text[:120]}")
                    time.sleep(6)
                    continue
                    
                status_result = status_response.json()
                if status_result.get('code') != 0:
                    self.append_log(f"状态错误: {status_result}")
                    return None
                    
                status = status_result['data'].get('status', 'unknown')
                progress = status_result['data'].get('progress', 0)
                self.append_log(f"处理状态: {status} 进度: {progress}%")
                
                if status == 'completed':
                    break
                elif status == 'failed':
                    self.append_log(f"转写失败: {status_result['data'].get('fail_reason', '未知')}")
                    return None
                    
                time.sleep(8)

            # 获取结果
            result_response = requests.get(f"https://api.reccloud.cn/v1/task/result?task_id={task_id}", 
                                         headers=headers, timeout=30)
            
            if result_response.status_code != 200:
                self.append_log(f"获取结果失败: {result_response.text[:200]}")
                return None
                
            final_result = result_response.json()
            if final_result.get('code') != 0:
                self.append_log(f"结果错误: {final_result}")
                return None
                
            self.append_log("语音转文字完成")
            return final_result['data']
            
        except Exception as e:
            self.append_log(f"语音转文字异常: {e}")
            return None

    def generate_md(self, result_data, link, platform):
        """生成Markdown文档"""
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            md_path = os.path.join(OUTPUT_DIR, f"{platform}_视频分析_{url_hash}_{ts}.md")

            segments = result_data.get('segments', [])
            transcript_lines = []
            for seg in segments:
                start_time = seg.get('start_time', 0)
                tstr = time.strftime('%H:%M:%S', time.gmtime(start_time))
                transcript_lines.append(f"- [{tstr}] {seg.get('text','')}")
            transcript = "\n".join(transcript_lines)
            
            summary = result_data.get('summary', '')

            md_content = f"""# {platform}视频内容分析

## 📋 视频信息
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **原始链接**: {link}
- **平台**: {platform}
- **URL哈希**: {url_hash}

## 📝 语音转文字内容

{transcript}

## 🤖 AI智能分析摘要

{summary}

## 📊 统计信息
- **总段数**: {len(segments)} 段
- **处理方式**: API调用 + AI语音识别

---
*由小红书视频转文字工具自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
            self.append_log("Markdown文档生成成功")
            return md_path
            
        except Exception as e:
            self.append_log(f"生成Markdown文档失败: {e}")
            return None


def main():
    root = tk.Tk()
    app = App(root)
    
    # 添加示例文本
    example_text = "83 【【LeetCode Hot100】72.编辑距离 - 一分钟学算法chay | 小红书 - 你的生活兴趣社区】 😆 hbdHRUrSPhYwjMi 😆 https://www.xiaohongshu.com/explore/693a701a000000001e028c47?xsec_token=ABQxjuDFhWoV1jL_Ai_MbGZ04iREslilGgPuP80vv2CUQ=&xsec_source=pc_search&source=web_search_result_notes"
    app.link_var.set(example_text)
    
    app.append_log("🎉 小红书视频转文字工具已启动（简化版）")
    app.append_log("💡 测试hellotik.app API调用")
    app.append_log("📁 输出文件将保存到 output 目录")
    
    root.mainloop()

if __name__ == '__main__':
    main()
