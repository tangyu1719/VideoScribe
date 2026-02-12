#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文字处理工具 - 工作版本
基于浏览器自动化获取真实视频下载链接
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    def append_log(self, msg: str):
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
            
        if not ('xiaohongshu.com' in link.lower()):
            messagebox.showwarning("提示", "请输入有效的小红书链接")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.append_log(f"开始处理：平台={self.platform_var.get()} 链接={link}")
        threading.Thread(target=self._run_pipeline, args=(self.platform_var.get(), link), daemon=True).start()

    def _run_pipeline(self, platform: str, link: str):
        try:
            self.set_status("使用浏览器自动化下载视频...")
            self.append_log("=== 步骤1: 使用浏览器自动化下载视频 ===")
            video_file = self.download_video_with_browser(link)
            
            if not video_file:
                self.append_log("视频下载失败，流程结束")
                self.set_status("失败")
                return

            self.set_status("语音转文字...")
            self.append_log("=== 步骤2: 语音转文字 ===")
            result_data = self.speech_to_text(video_file)
            
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

    def download_video_with_browser(self, link: str):
        """使用浏览器自动化下载视频"""
        driver = None
        try:
            self.append_log("启动浏览器...")
            
            # 设置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 设置下载目录
            prefs = {
                "download.default_directory": VIDEO_DIR,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=chrome_options)
            
            self.append_log("访问hellotik.app...")
            driver.get("https://www.hellotik.app/zh/rednote")
            
            # 等待页面加载
            wait = WebDriverWait(driver, 10)
            
            self.append_log("查找输入框...")
            
            # 尝试多种输入框选择器
            input_selectors = [
                'input[type="text"]',
                'input[placeholder*="链接"]',
                'input[placeholder*="URL"]',
                'input[placeholder*="url"]',
                'textarea',
                '.url-input',
                '#url-input'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    self.append_log(f"找到输入框: {selector}")
                    break
                except:
                    continue
                    
            if not input_element:
                self.append_log("未找到输入框，尝试通用方法...")
                # 查找所有input元素
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.get_attribute("type") in ["text", "url"] or "url" in inp.get_attribute("placeholder", "").lower():
                        input_element = inp
                        self.append_log("找到可能的输入框")
                        break
                        
            if not input_element:
                raise Exception("未找到输入框")
                
            # 输入链接
            self.append_log(f"输入链接: {link}")
            input_element.clear()
            input_element.send_keys(link)
            
            # 查找下载按钮
            self.append_log("查找下载按钮...")
            
            button_selectors = [
                'button[type="submit"]',
                'button:contains("下载")',
                'button:contains("Download")',
                '.download-btn',
                '#download-btn',
                '.btn-download'
            ]
            
            button_element = None
            for selector in button_selectors:
                try:
                    if ':contains(' in selector:
                        # 使用XPath查找包含文本的按钮
                        xpath = "//button[contains(text(), '下载') or contains(text(), 'Download') or contains(text(), 'download')]"
                        button_element = driver.find_element(By.XPATH, xpath)
                    else:
                        button_element = driver.find_element(By.CSS_SELECTOR, selector)
                    self.append_log(f"找到按钮: {selector}")
                    break
                except:
                    continue
                    
            if not button_element:
                # 查找所有按钮
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    text = btn.text.lower()
                    if any(word in text for word in ['下载', 'download', '获取', 'get']):
                        button_element = btn
                        self.append_log(f"找到可能的按钮: {btn.text}")
                        break
                        
            if not button_element:
                raise Exception("未找到下载按钮")
                
            # 记录下载前的文件
            before_files = set(os.listdir(VIDEO_DIR))
            
            # 点击下载按钮
            self.append_log("点击下载按钮...")
            driver.execute_script("arguments[0].click();", button_element)
            
            # 等待下载完成
            self.append_log("等待下载完成...")
            max_wait = 30  # 最多等待30秒
            for i in range(max_wait):
                time.sleep(1)
                current_files = set(os.listdir(VIDEO_DIR))
                new_files = current_files - before_files
                
                if new_files:
                    # 检查是否有完整的视频文件
                    for filename in new_files:
                        if filename.endswith('.mp4') and not filename.endswith('.crdownload'):
                            file_path = os.path.join(VIDEO_DIR, filename)
                            if os.path.getsize(file_path) > 1000:  # 文件大小大于1KB
                                self.append_log(f"下载完成: {filename}")
                                return file_path
                                
                self.append_log(f"等待下载... ({i+1}/{max_wait})")
                
            # 如果没有直接下载，尝试获取下载链接
            self.append_log("尝试获取下载链接...")
            
            # 查找可能的下载链接
            links = driver.find_elements(By.TAG_NAME, "a")
            for link_elem in links:
                href = link_elem.get_attribute("href")
                if href and ('.mp4' in href or 'video' in href.lower()):
                    self.append_log(f"找到视频链接: {href}")
                    return self.download_from_url(href, link)
                    
            raise Exception("未能获取视频文件或下载链接")
            
        except Exception as e:
            self.append_log(f"浏览器自动化失败: {e}")
            return None
        finally:
            if driver:
                driver.quit()
                self.append_log("关闭浏览器")

    def download_from_url(self, video_url: str, original_link: str):
        """从URL下载视频"""
        try:
            self.append_log(f"从URL下载视频: {video_url}")
            
            url_hash = hashlib.md5(original_link.encode()).hexdigest()[:8]
            ts = int(time.time())
            filename = f"video_{url_hash}_{ts}.mp4"
            file_path = os.path.join(VIDEO_DIR, filename)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.hellotik.app/'
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
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

    def speech_to_text(self, video_file: str):
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

    def generate_md(self, result_data: dict, link: str, platform: str):
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
            
            summary = result_data.get('ai_summary', result_data.get('summary', ''))

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
- **处理方式**: 浏览器自动化 + AI语音识别

---
*由小红书视频转文字工具自动生成 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
            self.append_log(f"✅ Markdown文档生成成功")
            return md_path
            
        except Exception as e:
            self.append_log(f"❌ 生成Markdown文档失败: {e}")
            return None


def main():
    root = tk.Tk()
    app = App(root)
    
    # 添加示例文本
    example_text = "83 【【LeetCode Hot100】72.编辑距离 - 一分钟学算法chay | 小红书 - 你的生活兴趣社区】 😆 hbdHRUrSPhYwjMi 😆 https://www.xiaohongshu.com/explore/693a701a000000001e028c47?xsec_token=ABQxjuDFhWoV1jL_Ai_MbGZ04iREslilGgPuP80vv2CUQ=&xsec_source=pc_search&source=web_search_result_notes"
    app.link_var.set(example_text)
    
    app.append_log("🎉 小红书视频转文字工具已启动")
    app.append_log("💡 使用浏览器自动化技术获取真实视频下载")
    app.append_log("📁 输出文件将保存到 output 目录")
    app.append_log("⚠️  首次运行需要下载Chrome驱动，请稍等...")
    
    root.mainloop()

if __name__ == '__main__':
    main()
