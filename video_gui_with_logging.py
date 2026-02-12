#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转文字处理工具 - 桌面GUI（Tkinter）增强版
- 完善的日志系统，按大小分级存储
- 详细的执行链路提示和错误提示
- 链接验证逻辑修复
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import os
import time
import hashlib
import logging
from datetime import datetime

APP_TITLE = "视频转文字处理工具 (GUI)"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

for d in (VIDEO_DIR, OUTPUT_DIR, LOG_DIR):
    if not os.path.exists(d):
        os.makedirs(d)

# 配置日志系统
def setup_logging():
    """配置按大小分级的日志系统"""
    # 创建日志记录器
    logger = logging.getLogger('video_processor')
    logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 文件处理器 - 按大小轮转
    from logging.handlers import RotatingFileHandler
    
    # 主日志文件 (10MB轮转)
    main_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'video_processor.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.INFO)
    
    # 错误日志文件 (5MB轮转)
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'video_processor_error.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    # 调试日志文件 (20MB轮转)
    debug_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'video_processor_debug.log'),
        maxBytes=20*1024*1024,  # 20MB
        backupCount=2,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    main_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    debug_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(main_handler)
    logger.addHandler(error_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志
logger = setup_logging()

PLATFORMS = {
    "小红书": {
        "api_endpoint": "https://api.hellotik.app/api/download",
        "headers": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://hellotik.app/zh/rednote',
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
        logger.info("GUI应用启动完成")

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
    def append_log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{ts}] {level}: {msg}\n"
        self.log.insert(tk.END, log_entry)
        self.log.see(tk.END)
        self.root.update_idletasks()
        
        # 同时写入日志文件
        if level == "ERROR":
            logger.error(msg)
        elif level == "WARNING":
            logger.warning(msg)
        elif level == "DEBUG":
            logger.debug(msg)
        else:
            logger.info(msg)

    def set_status(self, msg: str):
        self.status_var.set(msg)
        self.root.update_idletasks()
        logger.info(f"状态更新: {msg}")

    # 链接验证
    def validate_link(self, link: str) -> bool:
        """验证链接格式，支持从文本中提取URL"""
        self.append_log(f"开始验证链接: {link}", "DEBUG")
        
        if not link:
            self.append_log("链接为空", "ERROR")
            return False
            
        # 尝试从文本中提取URL
        extracted_url = self.extract_url_from_text(link)
        if extracted_url:
            self.append_log(f"从文本中提取到URL: {extracted_url}", "INFO")
            # 更新输入框为提取的URL
            self.link_var.set(extracted_url)
            link = extracted_url
        
        # 验证URL格式
        if not ('xiaohongshu.com' in link.lower() and ('http' in link.lower() or 'www.' in link.lower())):
            self.append_log(f"链接格式无效: {link}", "ERROR")
            self.append_log("提示: 链接应该包含 xiaohongshu.com", "WARNING")
            return False
            
        self.append_log("链接验证通过", "INFO")
        return True

    def extract_url_from_text(self, text: str) -> str:
        """从文本中提取URL"""
        import re
        
        # 匹配http/https开头的URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        # 找到包含xiaohongshu.com的URL
        for url in urls:
            if 'xiaohongshu.com' in url.lower():
                # 移除末尾可能的标点符号
                url = url.rstrip('.,;:!?')
                return url
                
        return None

    # 入口
    def start(self):
        link = self.link_var.get().strip()
        
        self.append_log("用户点击开始处理", "INFO")
        self.append_log(f"输入链接: {link}", "DEBUG")
        
        if not self.validate_link(link):
            messagebox.showwarning("提示", "请输入有效的小红书链接\n提示: 链接应该包含 xiaohongshu.com")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.append_log(f"开始处理：平台={self.platform_var.get()} 链接={link}", "INFO")
        threading.Thread(target=self._run_pipeline, args=(self.platform_var.get(), link), daemon=True).start()

    # 主流程：下载 -> 保存 -> 转写 -> 生成MD
    def _run_pipeline(self, platform: str, link: str):
        try:
            logger.info(f"开始处理流程 - 平台: {platform}, 链接: {link}")
            
            # 步骤1: 下载视频
            self.set_status("下载视频URL...")
            self.append_log("=== 步骤1: 下载视频 ===", "INFO")
            video_url = self.download_video(platform, link)
            
            if not video_url:
                self.append_log("未获取到视频URL，流程结束", "ERROR")
                self.set_status("失败")
                logger.error("视频下载失败")
                return

            # 步骤2: 保存视频
            self.set_status("保存视频...")
            self.append_log("=== 步骤2: 保存视频 ===", "INFO")
            video_file = self.save_video(video_url, link)
            
            if not video_file:
                self.append_log("保存视频失败，流程结束", "ERROR")
                self.set_status("失败")
                logger.error("视频保存失败")
                return

            # 步骤3: 语音转文字
            self.set_status("语音转文字...")
            self.append_log("=== 步骤3: 语音转文字 ===", "INFO")
            result_data = self.speech_to_text(video_file)
            
            if not result_data:
                self.append_log("语音转文字失败，流程结束", "ERROR")
                self.set_status("失败")
                logger.error("语音转文字失败")
                return

            # 步骤4: 生成MD
            self.set_status("生成Markdown文档...")
            self.append_log("=== 步骤4: 生成Markdown文档 ===", "INFO")
            md_file = self.generate_md(result_data, link, platform)
            
            if md_file:
                self.append_log(f"处理完成！文档已保存：{md_file}", "INFO")
                self.set_status("完成")
                logger.info(f"处理成功完成: {md_file}")
            else:
                self.append_log("生成文档失败", "ERROR")
                self.set_status("失败")
                logger.error("文档生成失败")
                
        except Exception as e:
            error_msg = f"处理过程中出现异常: {e}"
            self.append_log(error_msg, "ERROR")
            self.set_status("失败")
            logger.error(error_msg, exc_info=True)
        finally:
            self.start_btn.config(state=tk.NORMAL)

    # 步骤1：下载API
    def download_video(self, platform: str, link: str):
        conf = PLATFORMS.get(platform)
        if not conf:
            self.append_log(f"不支持的平台：{platform}", "ERROR")
            return None
            
        try:
            payload = json.loads(json.dumps(conf["payload"]))  # 深拷贝模板
            if "requestURL" in payload:
                payload["requestURL"] = link
            if "url" in payload:
                payload["url"] = link
            if "time" in payload and isinstance(payload["time"], str):
                payload["time"] = int(time.time())

            self.append_log(f"请求API: {conf['api_endpoint']}", "DEBUG")
            self.append_log(f"请求数据: {json.dumps(payload, ensure_ascii=False)}", "DEBUG")
            
            resp = requests.post(conf["api_endpoint"], json=payload,
                                 headers=conf["headers"], timeout=30)
            
            self.append_log(f"API响应状态码: {resp.status_code}", "DEBUG")
            
            if resp.status_code != 200:
                self.append_log(f"下载API失败: {resp.text[:200]}", "ERROR")
                return None
                
            data = resp.json()
            self.append_log(f"API响应数据: {json.dumps(data, ensure_ascii=False)[:300]}", "DEBUG")
            
            # 提取视频URL
            for k in conf["url_key_candidates"]:
                if k in data:
                    video_url = data[k]
                    self.append_log(f"找到视频URL: {video_url}", "INFO")
                    return video_url
                if isinstance(data.get("data"), dict) and k in data["data"]:
                    video_url = data["data"][k]
                    self.append_log(f"找到视频URL: {video_url}", "INFO")
                    return video_url
                    
            self.append_log("未找到视频URL字段", "ERROR")
            return None
            
        except Exception as e:
            self.append_log(f"下载异常: {e}", "ERROR")
            logger.error("下载视频异常", exc_info=True)
            return None

    # 步骤2：保存视频
    def save_video(self, video_url: str, link: str):
        try:
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            file_path = os.path.join(VIDEO_DIR, f"video_{url_hash}_{ts}.mp4")
            
            self.append_log(f"保存视频到: {file_path}", "INFO")
            
            r = requests.get(video_url, stream=True, timeout=60)
            r.raise_for_status()
            
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.append_log(f"下载进度: {progress:.1f}%", "DEBUG")
                            
            self.append_log(f"视频保存成功: {file_path}", "INFO")
            return file_path
            
        except Exception as e:
            self.append_log(f"保存异常: {e}", "ERROR")
            logger.error("保存视频异常", exc_info=True)
            return None

    # 步骤3：reccloud 转写
    def speech_to_text(self, video_file: str):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://reccloud.cn/speech-to-text-online',
                'Origin': 'https://reccloud.cn'
            }
            
            self.append_log("上传视频到reccloud.cn", "INFO")
            
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
                self.append_log(f"上传失败: {up.text[:200]}", "ERROR")
                return None
                
            up_json = up.json()
            if up_json.get('code') != 0 or 'data' not in up_json:
                self.append_log(f"上传错误: {up_json}", "ERROR")
                return None
                
            task_id = up_json['data']['task_id']
            self.append_log(f"任务ID: {task_id}", "INFO")

            # 轮询
            start = time.time()
            while time.time() - start < 600:
                st = requests.get(f"https://api.reccloud.cn/v1/task/status?task_id={task_id}", headers=headers, timeout=15)
                if st.status_code != 200:
                    self.append_log(f"状态查询失败: {st.text[:120]}", "ERROR")
                    time.sleep(6)
                    continue
                    
                st_json = st.json()
                if st_json.get('code') != 0:
                    self.append_log(f"状态错误: {st_json}", "ERROR")
                    return None
                    
                status = st_json['data'].get('status', 'unknown')
                prog = st_json['data'].get('progress', 0)
                self.append_log(f"处理状态: {status} 进度: {prog}%", "DEBUG")
                
                if status == 'completed':
                    break
                if status == 'failed':
                    fail_reason = st_json['data'].get('fail_reason','未知')
                    self.append_log(f"处理失败: {fail_reason}", "ERROR")
                    return None
                    
                time.sleep(8)

            # 结果
            rs = requests.get(f"https://api.reccloud.cn/v1/task/result?task_id={task_id}", headers=headers, timeout=30)
            if rs.status_code != 200:
                self.append_log(f"获取结果失败: {rs.text[:200]}", "ERROR")
                return None
                
            rs_json = rs.json()
            if rs_json.get('code') != 0 or 'data' not in rs_json:
                self.append_log(f"结果错误: {rs_json}", "ERROR")
                return None
                
            self.append_log("获取转写结果成功", "INFO")
            return rs_json['data']
            
        except Exception as e:
            self.append_log(f"转写异常: {e}", "ERROR")
            logger.error("语音转文字异常", exc_info=True)
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
                
            self.append_log(f"文档生成成功: {md_path}", "INFO")
            return md_path
            
        except Exception as e:
            self.append_log(f"写入MD失败: {e}", "ERROR")
            logger.error("生成文档异常", exc_info=True)
            return None


def main():
    logger.info("应用程序启动")
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    logger.info("应用程序关闭")

if __name__ == '__main__':
    main()
