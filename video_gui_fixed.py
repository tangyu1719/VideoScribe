#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文字处理工具 - 桌面GUI（Tkinter）修复版
- 修复append_log参数错误
- 完整的小红书视频处理流程
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

PLATFORMS = {
    "小红书": {
        "api_endpoint": "https://www.hellotik.app/zh/rednote",
        "headers": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://hellotik.app/',
            'Origin': 'https://hellotik.app'
        },
        "payload": {
            "requestURL": "{url}",
            "isMobile": "false",
            "isoCode": "HK",
            "adType": "adsense",
            "uwx_id": "uwx_350696y5juIO",
            "successCount": "0",
            "totalSuccessCount": "2",
            "firstSuccessDate": "2026-01-10",
            "time": "{timestamp}",
            "key": "xaq8pkc7"
        },
        "url_key_candidates": ["video_url", "download_url", "url"]
    }
}

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
                                         values=list(PLATFORMS.keys()))
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

    # 日志与状态
    def append_log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, msg: str):
        self.status_var.set(msg)
        self.root.update_idletasks()

    def extract_url_from_text(self, text: str):
        """从用户输入文本中提取URL"""
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)

        for url in urls:
            if 'sns-video' in url.lower() and '.mp4' in url.lower():
                return url.rstrip('.,;:!?')

        for url in urls:
            if 'xiaohongshu.com' in url.lower():
                return url.rstrip('.,;:!?')

        return None

    def extract_mp4_from_text(self, text: str):
        mp4_pattern = r'https?://[^\s<>"\']+\.mp4[^\s<>"\']*'
        matches = re.findall(mp4_pattern, text, re.IGNORECASE)
        for u in matches:
            if 'xhscdn.com' in u.lower() or 'sns-video' in u.lower():
                return u
        return None

    # 入口
    def start(self):
        link = self.link_var.get().strip()
        mp4_direct = self.extract_mp4_from_text(link)
        
        # 尝试从文本中提取URL
        extracted_url = self.extract_url_from_text(link)
        if extracted_url:
            self.append_log(f"从文本中提取到URL: {extracted_url}")
            # 更新输入框为提取的URL
            self.link_var.set(extracted_url)
            link = extracted_url
            mp4_direct = self.extract_mp4_from_text(link) or mp4_direct
        
        if not link:
            messagebox.showwarning("提示", "请先输入视频链接")
            return
            
        # 更宽松的链接验证
        if not ('xiaohongshu.com' in link.lower() and ('http' in link.lower() or 'www.' in link.lower())):
            messagebox.showwarning("提示", "请输入有效的小红书链接\n提示: 链接应该包含 xiaohongshu.com")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.append_log(f"开始处理：平台={self.platform_var.get()} 链接={link}")
        threading.Thread(target=self._run_pipeline, args=(self.platform_var.get(), link, mp4_direct), daemon=True).start()

    # 主流程：下载 -> 保存 -> 转写 -> 生成MD
    def _run_pipeline(self, platform: str, link: str, mp4_direct: str | None = None):
        try:
            self.set_status("下载视频...")
            self.append_log("=== 步骤1: 下载视频 ===")
            video_result = self.download_video(link, platform, mp4_direct)
            
            if not video_result:
                self.append_log("未获取到视频，流程结束")
                self.set_status("失败")
                return

            # 判断返回的是文件路径还是URL
            if os.path.exists(video_result):
                # 直接下载的文件
                video_file = video_result
                self.append_log(f"使用直接下载的视频文件: {video_file}")
            else:
                # 需要进一步下载的URL
                self.set_status("保存视频...")
                self.append_log("=== 步骤2: 保存视频 ===")
                video_file = self.save_video(video_result, link)
                
                if not video_file:
                    self.append_log("保存视频失败，流程结束")
                    self.set_status("失败")
                    return

            self.set_status("语音转文字...")
            self.append_log("=== 步骤3: 语音转文字 ===")
            result_data = self.speech_to_text(video_file)
            
            if not result_data:
                self.append_log("语音转文字失败，流程结束")
                self.set_status("失败")
                return

            self.set_status("生成Markdown文档...")
            self.append_log("=== 步骤4: 生成Markdown文档 ===")
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

    # 步骤1：下载API
    def download_video(self, link: str, platform: str, mp4_direct: str | None = None):
        """下载视频：优先使用直链mp4；否则再尝试hellotik解析"""
        try:
            if mp4_direct:
                self.append_log("检测到直链mp4，跳过hellotik解析")
                return self.download_from_url(mp4_direct, link)

            self.append_log("模拟浏览器会话...")
            
            # 创建会话
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # 1. 访问主页面获取必要的token或参数
            self.append_log("访问hellotik.app主页...")
            main_response = session.get("https://www.hellotik.app/zh/rednote", timeout=15)
            
            if main_response.status_code != 200:
                raise Exception(f"访问主页失败: {main_response.status_code}")
            
            self.append_log("分析页面内容...")
            html_content = main_response.text
            
            # 2. 查找可能的API端点或表单提交地址
            import re
            
            # 查找认证token或key
            token_patterns = [
                r'token["\']?\s*:\s*["\']([^"\']+)["\']',
                r'key["\']?\s*:\s*["\']([^"\']+)["\']',
                r'apiKey["\']?\s*:\s*["\']([^"\']+)["\']',
                r'csrf["\']?\s*:\s*["\']([^"\']+)["\']',
                r'_token["\']?\s*:\s*["\']([^"\']+)["\']'
            ]
            
            auth_token = None
            for pattern in token_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    auth_token = matches[0]
                    self.append_log(f"找到认证token: {auth_token[:20]}...")
                    break
            
            # 查找表单action
            form_action = None
            form_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            if form_match:
                form_action = form_match.group(1)
                self.append_log(f"找到表单action: {form_action}")
            
            # 查找可能的API端点
            api_patterns = [
                r'/api/[^"\s\']+',
                r'fetch\(["\']([^"\']+)["\']',
                r'action=["\']([^"\']+)["\']'
            ]
            
            possible_endpoints = set()
            for pattern in api_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if 'api' in match.lower() or 'download' in match.lower():
                        possible_endpoints.add(match)
            
            if possible_endpoints:
                self.append_log(f"发现可能的端点: {list(possible_endpoints)}")
            
            # 3. 尝试不同的提交方式
            test_endpoints = []
            
            # 添加发现的端点
            for endpoint in possible_endpoints:
                if endpoint.startswith('/'):
                    test_endpoints.append(f"https://www.hellotik.app{endpoint}")
                elif endpoint.startswith('http'):
                    test_endpoints.append(endpoint)
            
            # 添加常见的API路径
            test_endpoints.extend([
                "https://www.hellotik.app/api/download",
                "https://www.hellotik.app/api/parse",
                "https://www.hellotik.app/download",
                "https://www.hellotik.app/parse"
            ])
            
            # 如果找到表单action，也加入测试
            if form_action:
                if form_action.startswith('/'):
                    test_endpoints.append(f"https://www.hellotik.app{form_action}")
                elif form_action.startswith('http'):
                    test_endpoints.append(form_action)
            
            # 4. 测试不同的端点和参数组合
            payloads = [
                {"url": link},
                {"link": link},
                {"requestURL": link},
                {"videoUrl": link},
                {"url": link, "platform": "rednote"},
                {"link": link, "type": "video"}
            ]
            
            # 如果找到token，添加到payload中
            if auth_token:
                for payload in payloads:
                    payload["token"] = auth_token
                    payload["key"] = auth_token
            
            for endpoint in test_endpoints[:5]:  # 限制测试前5个端点
                self.append_log(f"测试端点: {endpoint}")
                
                for payload in payloads:
                    try:
                        # 更新请求头
                        session.headers.update({
                            'Content-Type': 'application/json',
                            'Referer': 'https://www.hellotik.app/zh/rednote',
                            'Origin': 'https://www.hellotik.app'
                        })
                        
                        self.append_log(f"POST数据: {json.dumps(payload, ensure_ascii=False)}")
                        
                        response = session.post(endpoint, json=payload, timeout=20)
                        
                        self.append_log(f"状态码: {response.status_code}")
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '').lower()
                            self.append_log(f"Content-Type: {content_type}")
                            
                            if 'json' in content_type:
                                try:
                                    data = response.json()
                                    self.append_log(f"✅ JSON响应: {json.dumps(data, ensure_ascii=False)[:300]}")
                                    
                                    # 查找下载链接
                                    download_url = None
                                    for key in ['downloadUrl', 'url', 'videoUrl', 'link', 'download_url', 'video_url']:
                                        if key in data:
                                            download_url = data[key]
                                            break
                                    
                                    if download_url:
                                        self.append_log(f"✅ 找到下载链接: {download_url}")
                                        return self.download_from_url(download_url, link)
                                    else:
                                        self.append_log("JSON响应中未找到下载链接")
                                        
                                except json.JSONDecodeError as e:
                                    self.append_log(f"JSON解析失败: {e}")
                                    self.append_log(f"响应内容: {response.text[:200]}")
                                    
                            elif ('video' in content_type or 
                                  'octet-stream' in content_type or
                                  len(response.content) > 100000):  # 大于100KB可能是视频
                                
                                self.append_log(f"✅ 检测到视频文件: {len(response.content)} 字节")
                                
                                # 保存文件
                                url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
                                ts = int(time.time())
                                filename = f"video_{url_hash}_{ts}.mp4"
                                file_path = os.path.join(VIDEO_DIR, filename)
                                
                                with open(file_path, 'wb') as f:
                                    f.write(response.content)
                                
                                self.append_log(f"✅ 视频保存成功: {filename}")
                                return file_path
                                
                            else:
                                # 检查是否包含下载链接
                                response_text = response.text
                                url_pattern = r'https?://[^\s<>"]+\.mp4[^\s<>"]*'
                                video_urls = re.findall(url_pattern, response_text)
                                
                                if video_urls:
                                    video_url = video_urls[0]
                                    self.append_log(f"从响应中提取视频URL: {video_url}")
                                    return self.download_from_url(video_url, link)
                                
                        elif response.status_code == 404:
                            continue  # 端点不存在，尝试下一个
                        else:
                            self.append_log(f"请求失败: {response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        self.append_log(f"请求异常: {e}")
                        continue
                        
            # 5. 如果所有方法都失败，尝试直接解析小红书链接
            self.append_log("所有端点探测均未返回可用视频链接")
            return None
            
        except Exception as e:
            self.append_log(f"模拟浏览器失败: {e}")

    def try_alternative_download(self, link: str):
        return None

    def save_downloaded_video(self, response, link):
        """保存直接下载的视频文件"""
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            video_filename = os.path.join(VIDEO_DIR, f"video_{url_hash}_{ts}.mp4")
            
            self.append_log(f"保存视频文件到: {video_filename}")
            
            with open(video_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
 
            size = os.path.getsize(video_filename)
            self.append_log(f"视频下载完成: {video_filename} size={size} bytes")
            return video_filename
            
        except Exception as e:
            self.append_log(f"下载失败: {e}")
            return None

    def download_from_url(self, url: str, original_link: str):
        """从直链下载视频（尽量复刻浏览器Range请求）"""
        try:
            self.append_log(f"开始下载: {url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'identity;q=1, *;q=0',
                'Range': 'bytes=0-',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            }

            # 你提供的cURL里 Referer 是空的（Referer;），requests 不允许空值，这里用站点首页作为referer
            if 'xhscdn.com' in url.lower() or 'sns-video' in url.lower():
                headers['Referer'] = 'https://www.xiaohongshu.com/'

            r = requests.get(url, headers=headers, stream=True, timeout=60)
            if r.status_code not in (200, 206):
                raise Exception(f"下载失败，状态码={r.status_code}")

            ct = (r.headers.get('content-type') or '').lower()
            cl = r.headers.get('content-length')
            cr = r.headers.get('content-range')
            self.append_log(f"下载响应: status={r.status_code} content-type={ct} content-length={cl} content-range={cr}")

            if 'video' not in ct and '.mp4' in url.lower():
                self.append_log("警告：content-type非video，仍继续尝试保存")

            url_hash = hashlib.md5(original_link.encode()).hexdigest()[:8]
            ts = int(time.time())
            filename = f"video_{url_hash}_{ts}.mp4"
            file_path = os.path.join(VIDEO_DIR, filename)

            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            size = os.path.getsize(file_path)
            self.append_log(f"视频下载完成: {filename} size={size} bytes")
            return file_path
        except Exception as e:
            self.append_log(f"下载失败: {e}")
            return None

    # 步骤3：reccloud 转写
    def speech_to_text(self, video_file: str):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://reccloud.cn/speech-to-text-online',
                'Origin': 'https://reccloud.cn'
            }
            
            self.append_log("上传视频到reccloud.cn")
            
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
                
                up = requests.post("https://api.reccloud.cn/v1/task/create",
                                   files=files, data=data, headers=headers, timeout=120)
                                   
            if up.status_code != 200:
                self.append_log(f"上传失败: {up.text[:200]}")
                return None
                
            up_json = up.json()
            if up_json.get('code') != 0 or 'data' not in up_json:
                self.append_log(f"上传错误: {up_json}")
                return None
                
            task_id = up_json['data']['task_id']
            self.append_log(f"任务ID: {task_id}")

            # 轮询
            start = time.time()
            while time.time() - start < 600:
                st = requests.get(f"https://api.reccloud.cn/v1/task/status?task_id={task_id}", headers=headers, timeout=15)
                if st.status_code != 200:
                    self.append_log(f"状态查询失败: {st.text[:120]}")
                    time.sleep(6)
                    continue
                    
                st_json = st.json()
                if st_json.get('code') != 0:
                    self.append_log(f"状态错误: {st_json}")
                    return None
                    
                status = st_json['data'].get('status', 'unknown')
                prog = st_json['data'].get('progress', 0)
                self.append_log(f"处理状态: {status} 进度: {prog}%")
                
                if status == 'completed':
                    break
                if status == 'failed':
                    self.append_log(f"失败原因：{st_json['data'].get('fail_reason','未知')}")
                    return None
                time.sleep(8)

            # 结果
            rs = requests.get(f"https://api.reccloud.cn/v1/task/result?task_id={task_id}", headers=headers, timeout=30)
            if rs.status_code != 200:
                self.append_log(f"获取结果失败: {rs.text[:200]}")
                return None
                
            rs_json = rs.json()
            if rs_json.get('code') != 0 or 'data' not in rs_json:
                self.append_log(f"结果错误: {rs_json}")
                return None
                
            self.append_log("获取转写结果成功")
            return rs_json['data']
            
        except Exception as e:
            self.append_log(f"转写异常: {e}")
            return None

    # 步骤4：生成Markdown
    def generate_md(self, result_data: dict, link: str, platform: str):
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            md_path = os.path.join(OUTPUT_DIR, f"{platform}_视频分析_{url_hash}_{ts}.md")

            segs = result_data.get('segments', [])
            transcript_lines = []
            for seg in segs:
                tstr = time.strftime('%H:%M:%S', time.gmtime(seg.get('start_time', 0)))
                transcript_lines.append(f"- [{tstr}] {seg.get('text','')}")
            transcript = "\n".join(transcript_lines)
            summary = result_data.get('ai_summary', result_data.get('summary', ''))

            md = f"""# {platform}视频内容分析

## 视频信息
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 原始链接: {link}
- 平台: {platform}
- URL哈希: {url_hash}

## 📝 语音转文字内容
{transcript}

## 🤖 AI智能分析摘要
{summary}

---
*由视频转文字处理工具自动生成*
"""
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md)
                
            self.append_log(f"文档生成成功: {md_path}")
            return md_path
            
        except Exception as e:
            self.append_log(f"写入MD失败: {e}")
            return None


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
