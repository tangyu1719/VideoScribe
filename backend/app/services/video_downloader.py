#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载服务 - 从本地工具移植
包含抖音专用下载、yt-dlp下载、动态超时计算等功能
"""

import os
import time
import re
import json
import random
import hashlib
import shutil
import subprocess
import threading
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import requests
from dataclasses import dataclass
from enum import Enum

# 配置
VIDEO_DIR = Path(os.getenv("VIDEO_STORAGE_PATH", "./storage/videos"))
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# 视频缓存
video_cache: Dict[str, str] = {}
video_cache_lock = threading.Lock()


class VideoPlatform(Enum):
    """视频平台枚举"""
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    XIAOHONGSHU = "xiaohongshu"
    YOUTUBE = "youtube"
    OTHER = "other"


@dataclass
class DownloadResult:
    """下载结果"""
    success: bool
    file_path: Optional[str]
    error_message: Optional[str]
    duration: Optional[float] = None
    platform: Optional[str] = None


class VideoDownloaderService:
    """视频下载服务"""
    
    def __init__(self):
        self.video_dir = VIDEO_DIR
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
    def download_douyin_video(self, link: str, 
                              log_callback: Optional[Callable] = None) -> DownloadResult:
        """
        抖音视频专用下载方法 - 使用HTML解析方法下载抖音视频（免登录）
        完整移植自本地工具 video_downloader.py
        """
        def log(msg: str, level: str = "INFO"):
            if log_callback:
                log_callback(msg, level)
            print(f"[DouyinDownload] [{level}] {msg}")
        
        download_start = time.time()
        
        try:
            log("使用抖音专用解析器下载视频...", "INFO")
            
            # 清理链接
            link = link.strip('`')
            
            # 获取当前目录下的视频文件数量，作为总序号
            existing_videos = [f for f in os.listdir(self.video_dir) if f.endswith('.mp4')]
            total_count = len(existing_videos) + 1
            
            # 获取当前日期（月-日）
            current_date = time.strftime('%m-%d')
            
            # 从链接中提取文档名称
            doc_name_match = re.search(r'\d+', link.split('/')[-1])
            doc_name = doc_name_match.group(0) if doc_name_match else "douyin"
            
            # 构建新的文件名：总记录序号-月-日-文档名称
            new_filename = f"{total_count:03d}-{current_date}-{doc_name}.mp4"
            output_file = str(self.video_dir / new_filename)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
            }
            
            # 步骤1: 访问分享链接获取视频ID
            log("解析抖音视频链接...", "INFO")
            response = requests.get(link, headers=headers, allow_redirects=True, timeout=30)
            video_id = response.url.split("?")[0].strip("/").split("/")[-1]
            log(f"视频ID: {video_id}", "INFO")
            
            # 步骤2: 访问分享页面获取HTML
            share_url = f'https://www.iesdouyin.com/share/video/{video_id}'
            response = requests.get(share_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 步骤3: 从HTML中解析视频信息
            pattern = re.compile(
                pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
                flags=re.DOTALL
            )
            find_res = pattern.search(response.text)
            
            if not find_res or not find_res.group(1):
                log("未能从HTML中解析视频信息", "ERROR")
                return DownloadResult(False, None, "解析视频信息失败")
            
            json_data = json.loads(find_res.group(1).strip())
            
            # 步骤4: 提取视频URL
            video_url = None
            if "loaderData" in json_data:
                loader_data = json_data["loaderData"]
                for key in loader_data:
                    if "videoInfoRes" in str(loader_data[key]):
                        data = loader_data[key]["videoInfoRes"]["item_list"][0]
                        video_url = data["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
                        log("成功获取无水印视频链接", "INFO")
                        break
            
            if not video_url:
                log("未能提取视频URL", "ERROR")
                return DownloadResult(False, None, "提取视频URL失败")
            
            # 步骤5: 下载视频
            log("下载视频中...", "INFO")
            video_response = requests.get(video_url, headers=headers, stream=True, timeout=120)
            video_response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 验证文件
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                download_end = time.time()
                log(f"视频下载成功: {output_file}", "INFO")
                log(f"视频下载耗时: {download_end - download_start:.2f}秒", "INFO")
                
                # 添加到缓存
                with video_cache_lock:
                    video_cache[link] = output_file
                
                return DownloadResult(True, output_file, None, platform="douyin")
            else:
                log("视频文件不存在或为空", "ERROR")
                return DownloadResult(False, None, "视频文件验证失败")
                
        except Exception as e:
            download_end = time.time()
            log(f"抖音视频下载异常: {e}", "ERROR")
            log(f"视频下载耗时: {download_end - download_start:.2f}秒（异常）", "INFO")
            return DownloadResult(False, None, str(e))
    
    def get_video_duration(self, link: str, 
                          log_callback: Optional[Callable] = None) -> Optional[float]:
        """
        获取视频时长（秒）- 使用yt-dlp获取视频信息
        移植自本地工具 video_downloader.py
        """
        def log(msg: str, level: str = "INFO"):
            if log_callback:
                log_callback(msg, level)
            print(f"[VideoDuration] [{level}] {msg}")
        
        try:
            log(f"正在获取视频时长信息...", "INFO")
            
            # 构建yt-dlp命令获取视频信息
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--skip-download",
                "--quiet",
                link
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout:
                video_info = json.loads(result.stdout.strip().split('\n')[0])
                duration = video_info.get('duration')
                
                if duration:
                    log(f"视频时长: {duration:.1f}秒 ({duration/60:.1f}分钟)", "INFO")
                    return float(duration)
                else:
                    log("无法获取视频时长信息", "WARNING")
                    return None
            else:
                log(f"获取视频信息失败: {result.stderr[:100]}", "WARNING")
                return None
                
        except subprocess.TimeoutExpired:
            log("获取视频信息超时", "WARNING")
            return None
        except Exception as e:
            log(f"获取视频时长失败: {e}", "WARNING")
            return None
    
    def calculate_timeout(self, duration: Optional[float], 
                         base_timeout: int = 300) -> int:
        """
        根据视频时长计算下载超时时间
        移植自本地工具 video_downloader.py
        
        Args:
            duration: 视频时长（秒）
            base_timeout: 基础超时时间（秒）
        
        Returns:
            计算后的超时时间（秒）
        """
        if duration is None:
            # 无法获取时长，使用默认超时
            return base_timeout
        
        # 根据视频时长计算超时时间
        # 公式：基础超时 + 每分钟视频增加120秒下载时间
        # 例如：10分钟视频 = 300 + 10*120 = 1500秒（25分钟）
        calculated_timeout = int(base_timeout + (duration / 60) * 120)
        
        # 设置上限和下限
        min_timeout = 300  # 最少5分钟
        max_timeout = 3600  # 最多1小时
        
        final_timeout = max(min_timeout, min(calculated_timeout, max_timeout))
        
        return final_timeout
    
    def download_video(self, link: str, 
                      log_callback: Optional[Callable] = None) -> DownloadResult:
        """
        下载视频 - 完整移植自本地工具 video_downloader.py
        支持抖音专用解析器、yt-dlp下载、缓存机制
        新增：根据视频长度动态调整超时时间
        """
        def log(msg: str, level: str = "INFO"):
            if log_callback:
                log_callback(msg, level)
            print(f"[VideoDownload] [{level}] {msg}")
        
        download_start = time.time()
        
        try:
            # 清理链接中的反引号
            link = link.strip('`')
            
            # 对于抖音链接，优先使用专用解析器
            if "douyin.com" in link or "tiktok.com" in link or "v.douyin.com" in link:
                log("检测到抖音链接，使用专用解析器...", "INFO")
                result = self.download_douyin_video(link, log_callback)
                if result.success:
                    return result
                else:
                    log("专用解析器失败，尝试使用yt-dlp...", "WARNING")
            
            # 检查视频缓存
            with video_cache_lock:
                if link in video_cache:
                    cached_file = video_cache[link]
                    if os.path.exists(cached_file) and os.path.getsize(cached_file) > 0:
                        log(f"使用缓存的视频文件: {cached_file}", "INFO")
                        download_end = time.time()
                        log(f"视频下载耗时: {download_end - download_start:.2f}秒（使用缓存）", "INFO")
                        return DownloadResult(True, cached_file, None, platform="cached")
                    else:
                        # 缓存文件不存在或为空，删除缓存条目
                        del video_cache[link]
                        log("缓存视频文件不存在，重新下载", "INFO")
            
            # 使用yt-dlp工具下载视频
            log("使用yt-dlp下载视频...", "INFO")
            
            # 获取当前日期（月-日）
            current_date = time.strftime('%m-%d')
            
            # 从链接中提取文档名称（使用链接的最后部分）
            doc_name_match = re.search(r'\d+', link.split('/')[-1])
            doc_name = doc_name_match.group(0) if doc_name_match else "unknown"
            
            # 构建唯一文件名：时间戳-随机数-文档名称
            timestamp = int(time.time() * 1000)
            random_suffix = random.randint(100, 999)
            new_filename = f"{timestamp}-{random_suffix}-{current_date}-{doc_name}.mp4"
            output_file = str(self.video_dir / new_filename)
            
            # 从链接中提取 xsec_token
            xsec_token_match = re.search(r'xsec_token=([^&]+)', link)
            xsec_token = xsec_token_match.group(1) if xsec_token_match else ""
            
            # 构建cookie字符串
            cookie_string = f"xsec_token={xsec_token}" if xsec_token else ""
            
            # 根据链接类型设置不同的referer
            referer = "https://www.xiaohongshu.com/"
            platform = VideoPlatform.OTHER
            if "bilibili.com" in link or "bilibili" in link:
                referer = "https://www.bilibili.com/"
                platform = VideoPlatform.BILIBILI
            elif "youtube.com" in link or "youtu.be" in link:
                referer = "https://www.youtube.com/"
                platform = VideoPlatform.YOUTUBE
            elif "douyin.com" in link or "tiktok.com" in link:
                referer = "https://www.douyin.com/"
                platform = VideoPlatform.DOUYIN
                log("检测到抖音链接，使用专用配置...", "INFO")
            elif "xiaohongshu.com" in link:
                platform = VideoPlatform.XIAOHONGSHU
            
            # 构建 yt-dlp 命令，直接下载到目标文件夹
            cmd = [
                "yt-dlp",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                "--referer", referer,
                "--no-check-certificate",
                "--quiet",  # 静默模式，减少输出
                "--no-warnings",  # 禁用警告
                # 下载优化参数 - 长视频优化配置
                "--format", "best[height<=480]/worst",  # 优先 480p 或最低质量，提高下载速度
                "--merge-output-format", "mp4",  # 合并为 mp4 格式
                "--concurrent-fragments", "3",  # 降低并发数，避免网络拥塞
                "--buffer-size", "32K",  # 增大缓冲区，减少网络波动影响
                "--retries", "15",  # 增加重试次数
                "--fragment-retries", "15",  # 增加片段重试次数
                "--socket-timeout", "120",  # 增加 socket 超时到 120 秒，适应长视频
                "--http-chunk-size", "10M",  # 增大 HTTP 分块大小
                "--rate-limit", "0",  # 不限速
                "--no-resize-buffer",  # 不调整缓冲区
                "--no-abort-on-error",  # 出错不中断
                "--continue",  # 断点续传
                "-o", output_file,
            ]
            
            # 对于B站链接，尝试使用浏览器cookies提高下载速度
            if platform == VideoPlatform.BILIBILI:
                log("检测到B站链接，尝试使用浏览器cookies...", "INFO")
                try:
                    # 尝试从Firefox获取cookies
                    cmd.extend(["--cookies-from-browser", "firefox"])
                    log("已添加Firefox cookies参数", "INFO")
                except Exception as e:
                    log(f"从Firefox获取cookies失败: {e}", "WARNING")
                    log("提示：在Firefox浏览器中登录B站可以提高下载速度", "INFO")
            
            # 对于抖音链接，添加额外的参数以提高下载成功率
            if platform == VideoPlatform.DOUYIN:
                # 尝试多种方式获取cookies
                cookie_added = False
                
                # 方式1: 检查是否存在抖音cookie文件
                cookie_file = Path(__file__).parent / "douyin_cookies.txt"
                if cookie_file.exists():
                    log(f"使用抖音cookie文件：{cookie_file}", "INFO")
                    cmd.extend(["--cookies", str(cookie_file)])
                    cookie_added = True
                
                # 方式2: 尝试从Firefox获取cookies
                if not cookie_added:
                    try:
                        log("尝试从Firefox浏览器获取cookies...", "INFO")
                        cmd.extend(["--cookies-from-browser", "firefox"])
                        cookie_added = True
                        log("已添加Firefox cookies参数", "INFO")
                    except Exception as e:
                        log(f"从Firefox获取cookies失败: {str(e)[:30]}", "WARNING")
                
                # 方式3: 如果Firefox失败，尝试Edge
                if not cookie_added:
                    try:
                        log("尝试从Edge浏览器获取cookies...", "INFO")
                        cmd.extend(["--cookies-from-browser", "edge"])
                        cookie_added = True
                        log("已添加Edge cookies参数", "INFO")
                    except Exception as e:
                        log(f"从Edge获取cookies失败: {str(e)[:30]}", "WARNING")
                
                if not cookie_added:
                    log("警告：无法获取抖音cookies，下载可能失败", "WARNING")
                    log("解决方案：在Firefox浏览器中登录抖音后重试", "WARNING")
                
                # 添加抖音专用参数
                cmd.extend([
                    "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                    "--max-downloads", "1",
                    "--no-check-certificate",
                    "--ignore-errors",
                    link
                ])
            else:
                cmd.append(link)
            
            # 获取视频时长并计算超时时间
            video_duration = self.get_video_duration(link, log_callback)
            download_timeout = self.calculate_timeout(video_duration, base_timeout=300)
            
            log(f"视频下载超时设置: {download_timeout}秒 ({download_timeout/60:.1f}分钟)", "INFO")
            if video_duration:
                log(f"基于视频时长 {video_duration/60:.1f}分钟 计算得出", "INFO")
            
            # 执行命令（增加超时时间，添加重试机制）
            max_retries = 2
            retry_count = 0
            result = None
            
            while retry_count < max_retries:
                try:
                    log(f"执行yt-dlp命令（尝试 {retry_count+1}/{max_retries}）...", "INFO")
                    # 使用动态计算的超时时间
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=download_timeout)
                    break
                except subprocess.TimeoutExpired as te:
                    retry_count += 1
                    log(f"yt-dlp执行超时（{te.timeout}秒），正在重试...（{retry_count}/{max_retries}）", "WARNING")
                    log(f"超时详情: B站可能限速，建议登录B站账号或使用更低清晰度", "INFO")
                    if retry_count >= max_retries:
                        log("yt-dlp执行多次超时，B站下载限速严重", "ERROR")
                        log("解决方案：1.在Firefox登录B站 2.使用其他视频源 3.降低视频清晰度", "ERROR")
                        download_end = time.time()
                        log(f"视频下载耗时: {download_end - download_start:.2f}秒（超时）", "INFO")
                        return DownloadResult(False, None, "下载超时", platform=platform.value)
                except Exception as e:
                    log(f"yt-dlp执行异常：{type(e).__name__}: {e}", "ERROR")
                    retry_count += 1
                    if retry_count >= max_retries:
                        log("yt-dlp执行失败", "ERROR")
                        download_end = time.time()
                        log(f"视频下载耗时: {download_end - download_start:.2f}秒（失败）", "INFO")
                        return DownloadResult(False, None, str(e), platform=platform.value)
            
            if result.returncode == 0:
                # 检查视频文件是否存在且大小大于0
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    log(f"视频下载成功: {output_file}", "INFO")
                    # 添加到缓存
                    with video_cache_lock:
                        video_cache[link] = output_file
                    download_end = time.time()
                    log(f"视频下载耗时: {download_end - download_start:.2f}秒", "INFO")
                    return DownloadResult(True, output_file, None, 
                                        duration=video_duration, 
                                        platform=platform.value)
                else:
                    log("视频文件不存在或为空", "ERROR")
                    return DownloadResult(False, None, "视频文件验证失败", platform=platform.value)
            else:
                # 优化：只显示部分错误信息
                error_msg = result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr
                log(f"yt-dlp执行失败: {error_msg}", "ERROR")
                
                # 特殊处理抖音链接
                if platform == VideoPlatform.DOUYIN:
                    log("抖音视频下载失败，解决方案：", "ERROR")
                    log("1. 确保使用的是直接视频链接（非用户页面或收藏页面）", "ERROR")
                    log("2. 在Firefox浏览器中登录抖音网站（www.douyin.com）", "ERROR")
                    log("3. 登录后重新运行本程序，程序会自动使用Firefox的cookies", "ERROR")
                    log("4. 如果仍失败，请关闭Chrome浏览器后重试", "ERROR")
                
                return DownloadResult(False, None, error_msg, platform=platform.value)
                
        except Exception as e:
            download_end = time.time()
            log(f"下载异常：{e}", "ERROR")
            log(f"视频下载耗时: {download_end - download_start:.2f}秒（异常）", "INFO")
            return DownloadResult(False, None, str(e))


# 便捷函数
def create_video_downloader() -> VideoDownloaderService:
    """创建视频下载服务实例"""
    return VideoDownloaderService()
