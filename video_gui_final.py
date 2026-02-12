#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文字处理工具 - 最终版本
使用模拟数据演示完整流程，避免第三方API依赖
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
                                         values=["小红书", "抖音", "B站"])
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

    def append_log(self, msg, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, msg: str):
        self.status_var.set(msg)
        self.root.update_idletasks()

    def extract_url_from_text(self, text: str) -> str:
        """从文本中提取URL"""
        import re
        
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
            
        if not ('xiaohongshu.com' in link.lower() or 'douyin.com' in link.lower() or 'bilibili.com' in link.lower()):
            messagebox.showwarning("提示", "请输入有效的视频链接")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.append_log(f"开始处理：平台={self.platform_var.get()} 链接={link}")
        threading.Thread(target=self._run_pipeline, args=(self.platform_var.get(), link), daemon=True).start()

    def _run_pipeline(self, platform: str, link: str):
        try:
            # 步骤1: 模拟视频下载
            self.set_status("模拟视频下载...")
            self.append_log("=== 步骤1: 模拟视频下载 ===")
            video_file = self.simulate_video_download(platform, link)
            
            if not video_file:
                self.append_log("模拟视频下载失败")
                self.set_status("失败")
                return

            # 步骤2: 模拟语音转文字
            self.set_status("模拟语音转文字...")
            self.append_log("=== 步骤2: 模拟语音转文字 ===")
            result_data = self.simulate_speech_to_text(video_file)
            
            if not result_data:
                self.append_log("模拟语音转文字失败")
                self.set_status("失败")
                return

            # 步骤3: 生成Markdown文档
            self.set_status("生成Markdown文档...")
            self.append_log("=== 步骤3: 生成Markdown文档 ===")
            md_file = self.generate_md(result_data, link, platform)
            
            if md_file:
                self.append_log(f"✅ 处理完成！文档已保存：{md_file}")
                self.set_status("完成")
                
                # 打开输出文件夹
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

    def simulate_video_download(self, platform: str, link: str):
        """模拟视频下载"""
        try:
            self.append_log("正在模拟视频下载过程...")
            time.sleep(1)  # 模拟网络延迟
            
            # 创建模拟视频文件
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            video_file = os.path.join(VIDEO_DIR, f"video_{url_hash}_{ts}.mp4")
            
            # 写入模拟视频数据
            with open(video_file, 'w', encoding='utf-8') as f:
                f.write(f"模拟视频文件\n平台: {platform}\n链接: {link}\n创建时间: {datetime.now()}")
            
            self.append_log(f"✅ 模拟视频下载完成: {video_file}")
            return video_file
            
        except Exception as e:
            self.append_log(f"❌ 模拟视频下载失败: {e}")
            return None

    def simulate_speech_to_text(self, video_file: str):
        """模拟语音转文字"""
        try:
            self.append_log("正在模拟语音转文字过程...")
            
            # 模拟处理进度
            for i in range(1, 6):
                time.sleep(0.5)
                self.append_log(f"处理进度: {i*20}%")
            
            # 模拟转写结果
            segments = [
                {'start_time': 0, 'text': '大家好，今天我要给大家分享一个非常实用的AI工具'},
                {'start_time': 5, 'text': '这个工具可以帮助我们快速处理视频内容'},
                {'start_time': 10, 'text': '通过智能语音识别技术，自动生成文字稿'},
                {'start_time': 15, 'text': '并且还能提供AI智能分析和总结'},
                {'start_time': 20, 'text': '大大提高了我们的工作效率'},
                {'start_time': 25, 'text': '如果你觉得有用的话，记得点赞收藏哦'}
            ]
            
            ai_summary = """### 视频主要内容
- 介绍了一个AI视频处理工具
- 具备智能语音识别功能
- 可以自动生成文字稿和分析报告
- 显著提升工作效率

### 核心特点
1. **智能识别**：高精度语音转文字
2. **自动分析**：AI智能内容总结
3. **效率提升**：一键完成视频处理
4. **易于使用**：简单直观的操作界面

### 适用场景
- 会议记录整理
- 教学视频转录
- 内容创作辅助
- 学习笔记生成"""

            result_data = {
                'segments': segments,
                'ai_summary': ai_summary
            }
            
            self.append_log("✅ 模拟语音转文字完成")
            return result_data
            
        except Exception as e:
            self.append_log(f"❌ 模拟语音转文字失败: {e}")
            return None

    def generate_md(self, result_data: dict, link: str, platform: str):
        """生成Markdown文档"""
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            md_path = os.path.join(OUTPUT_DIR, f"{platform}_视频分析_{url_hash}_{ts}.md")

            segments = result_data.get('segments', [])
            transcript_lines = []
            for seg in segments:
                tstr = time.strftime('%H:%M:%S', time.gmtime(seg.get('start_time', 0)))
                transcript_lines.append(f"- [{tstr}] {seg.get('text','')}")
            transcript = "\n".join(transcript_lines)
            
            summary = result_data.get('ai_summary', '')

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
- **总时长**: {len(segments) * 5} 秒（估算）
- **文字段数**: {len(segments)} 段
- **处理方式**: 自动化AI处理

---
*由小红书视频转文字工具自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
            self.append_log(f"✅ Markdown文档生成成功")
            self.append_log(f"📄 文件路径: {md_path}")
            return md_path
            
        except Exception as e:
            self.append_log(f"❌ 生成Markdown文档失败: {e}")
            return None


def main():
    root = tk.Tk()
    app = App(root)
    
    # 添加示例文本
    example_text = "83 【【LeetCode Hot100】72.编辑距离 - 一分钟学算法chay | 小红书 - 你的生活兴趣社区】 😆 hbdHRUrSPhYwjMi 😆 https://www.xiaohongshu.com/discovery/item/693a701a000000001e028c47?source=webshare&xhsshare=pc_web&xsec_token=ABQxjuDFhWoV1jL_Ai_MbGZ04iREslilGgPuP80vv2CUQ=&xsec_source=pc_share"
    app.link_var.set(example_text)
    
    app.append_log("🎉 小红书视频转文字工具已启动")
    app.append_log("💡 提示: 已预填示例链接，点击'开始处理'即可体验完整流程")
    app.append_log("📁 输出文件将保存到 output 目录")
    
    root.mainloop()

if __name__ == '__main__':
    main()
