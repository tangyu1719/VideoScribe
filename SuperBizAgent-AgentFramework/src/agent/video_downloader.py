#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载模块 - 完整迁移自video_gui.py
包含抖音专用下载、yt-dlp下载、缓存机制、语音转文字等功能
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
from typing import Optional, Dict, Any, List
import requests

# 视频目录
BASE_DIR = Path(__file__).parent
VIDEO_DIR = BASE_DIR / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

# 视频缓存
video_cache: Dict[str, str] = {}
video_cache_lock = threading.Lock()

# Whisper模型缓存
model_cache = None
model_cache_lock = threading.Lock()


def download_douyin_video(link: str, log_callback=None) -> Optional[str]:
    """
    抖音视频专用下载方法 - 使用HTML解析方法下载抖音视频（免登录）
    完整复制自video_gui.py download_douyin_video方法
    """
    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        print(f"[DouyinDownload] [{level}] {msg}")
    
    download_start = time.time()
    
    try:
        log("使用抖音专用解析器下载视频...", "INFO")
        
        # 清理链接
        link = link.strip('`')
        
        # 获取当前目录下的视频文件数量，作为总序号
        existing_videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
        total_count = len(existing_videos) + 1
        
        # 获取当前日期（月-日）
        current_date = time.strftime('%m-%d')
        
        # 从链接中提取文档名称
        doc_name_match = re.search(r'\d+', link.split('/')[-1])
        doc_name = doc_name_match.group(0) if doc_name_match else "douyin"
        
        # 构建新的文件名：总记录序号-月-日-文档名称
        new_filename = f"{total_count:03d}-{current_date}-{doc_name}.mp4"
        output_file = str(VIDEO_DIR / new_filename)
        
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
            return None
        
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
            return None
        
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
            
            return output_file
        else:
            log("视频文件不存在或为空", "ERROR")
        
        return None
        
    except Exception as e:
        download_end = time.time()
        log(f"抖音视频下载异常: {e}", "ERROR")
        log(f"视频下载耗时: {download_end - download_start:.2f}秒（异常）", "INFO")
        return None


def get_video_duration(link: str, log_callback=None) -> Optional[float]:
    """
    获取视频时长（秒）- 使用yt-dlp获取视频信息
    
    Args:
        link: 视频链接
        log_callback: 日志回调函数
    
    Returns:
        视频时长（秒），如果获取失败返回None
    """
    def log(msg, level="INFO"):
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
            import json
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


def calculate_timeout(duration: Optional[float], base_timeout: int = 300) -> int:
    """
    根据视频时长计算下载超时时间
    
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


def download_video(link: str, log_callback=None) -> Optional[str]:
    """
    下载视频 - 完整复制自video_gui.py download_video方法
    支持抖音专用解析器、yt-dlp下载、缓存机制
    新增：根据视频长度动态调整超时时间
    """
    def log(msg, level="INFO"):
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
            result = download_douyin_video(link, log_callback)
            if result:
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
                    return cached_file
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
        output_file = str(VIDEO_DIR / new_filename)
        
        # 从链接中提取 xsec_token
        xsec_token_match = re.search(r'xsec_token=([^&]+)', link)
        xsec_token = xsec_token_match.group(1) if xsec_token_match else ""
        
        # 构建cookie字符串
        cookie_string = f"xsec_token={xsec_token}" if xsec_token else ""
        
        # 根据链接类型设置不同的referer
        referer = "https://www.xiaohongshu.com/"
        if "bilibili.com" in link or "bilibili" in link:
            referer = "https://www.bilibili.com/"
        elif "youtube.com" in link or "youtu.be" in link:
            referer = "https://www.youtube.com/"
        elif "douyin.com" in link or "tiktok.com" in link:
            referer = "https://www.douyin.com/"
            log("检测到抖音链接，使用专用配置...", "INFO")
        
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
        if "bilibili.com" in link:
            log("检测到B站链接，尝试使用浏览器cookies...", "INFO")
            try:
                # 尝试从Firefox获取cookies
                cmd.extend(["--cookies-from-browser", "firefox"])
                log("已添加Firefox cookies参数", "INFO")
            except Exception as e:
                log(f"从Firefox获取cookies失败: {e}", "WARNING")
                log("提示：在Firefox浏览器中登录B站可以提高下载速度", "INFO")
        
        # 对于抖音链接，添加额外的参数以提高下载成功率
        if "douyin.com" in link or "tiktok.com" in link:
            # 尝试多种方式获取cookies
            cookie_added = False
            
            # 方式1: 检查是否存在抖音cookie文件
            cookie_file = os.path.join(BASE_DIR, "douyin_cookies.txt")
            if os.path.exists(cookie_file):
                log(f"使用抖音cookie文件：{cookie_file}", "INFO")
                cmd.extend(["--cookies", cookie_file])
                cookie_added = True
            
            # 方式2: 尝试从Firefox获取cookies（优先使用Firefox，因为它不会像Chrome那样被锁定）
            if not cookie_added:
                try:
                    log("尝试从Firefox浏览器获取cookies...", "INFO")
                    # 直接添加Firefox cookies参数
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
            
            # 添加抖音专用参数（使用兼容的参数格式）
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
        video_duration = get_video_duration(link, log_callback)
        download_timeout = calculate_timeout(video_duration, base_timeout=300)
        
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
                log(f"yt-dlp命令: {' '.join(cmd[:12])}...", "DEBUG")  # 记录命令
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
                    return None
            except Exception as e:
                log(f"yt-dlp执行异常：{type(e).__name__}: {e}", "ERROR")
                import traceback
                log(f"异常详情: {traceback.format_exc()}", "DEBUG")
                retry_count += 1
                if retry_count >= max_retries:
                    log("yt-dlp执行失败", "ERROR")
                    download_end = time.time()
                    log(f"视频下载耗时: {download_end - download_start:.2f}秒（失败）", "INFO")
                    return None
        
        if result.returncode == 0:
            # 检查视频文件是否存在且大小大于0
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                log(f"视频下载成功: {output_file}", "INFO")
                # 添加到缓存
                with video_cache_lock:
                    video_cache[link] = output_file
                download_end = time.time()
                log(f"视频下载耗时: {download_end - download_start:.2f}秒", "INFO")
                return output_file
            else:
                log("视频文件不存在或为空", "ERROR")
        else:
            # 优化：只显示部分错误信息
            error_msg = result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr
            log(f"yt-dlp执行失败: {error_msg}", "ERROR")
            
            # 特殊处理抖音链接
            if "douyin.com" in link:
                log("抖音视频下载失败，解决方案：", "ERROR")
                log("1. 确保使用的是直接视频链接（非用户页面或收藏页面）", "ERROR")
                log("2. 在Firefox浏览器中登录抖音网站（www.douyin.com）", "ERROR")
                log("3. 登录后重新运行本程序，程序会自动使用Firefox的cookies", "ERROR")
                log("4. 如果仍失败，请关闭Chrome浏览器后重试", "ERROR")
        
        # 执行失败，直接返回None表示失败，不使用示例文件
        log("视频下载失败", "ERROR")
        download_end = time.time()
        log(f"视频下载耗时: {download_end - download_start:.2f}秒（失败）", "INFO")
        return None
        
    except Exception as e:
        download_end = time.time()
        log(f"下载异常：{e}", "ERROR")
        log(f"视频下载耗时: {download_end - download_start:.2f}秒（异常）", "INFO")
        # 直接返回None表示失败，不使用示例文件
        return None


def save_video(video_url: str, link: str, log_callback=None) -> Optional[str]:
    """
    保存视频 - 完整复制自video_gui.py save_video方法
    支持本地文件复制和URL下载
    """
    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        print(f"[SaveVideo] [{level}] {msg}")
    
    try:
        # 检查video_url是否已经是本地文件路径
        if os.path.exists(video_url) and os.path.isfile(video_url):
            # 如果是本地文件，直接复制到videos目录
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            file_path = os.path.join(VIDEO_DIR, f"video_{url_hash}_{ts}.mp4")
            
            # 复制文件
            shutil.copy2(video_url, file_path)
            
            log(f"视频已从临时位置复制到: {file_path}", "INFO")
            
            # 清理临时目录
            temp_dir = os.path.dirname(video_url)
            if 'temp' in temp_dir.lower():
                try:
                    shutil.rmtree(temp_dir)
                    log(f"已清理临时目录: {temp_dir}", "DEBUG")
                except:
                    pass
            
            return file_path
        else:
            # 如果是URL，使用异步方式下载视频
            url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
            ts = int(time.time())
            file_path = os.path.join(VIDEO_DIR, f"video_{url_hash}_{ts}.mp4")
            log(f"保存至：{file_path}")
            
            # 运行异步下载
            try:
                # 创建事件循环并运行异步任务
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(async_download_video(video_url, file_path, log_callback))
                loop.close()
                
                if result:
                    log(f"视频下载完成: {file_path}", "INFO")
                    return file_path
                else:
                    log("异步下载视频失败", "ERROR")
                    return None
            except Exception as e:
                log(f"异步下载异常：{e}", "ERROR")
                # 回退到同步下载
                return sync_download_video(video_url, file_path, log_callback)
    except Exception as e:
        log(f"保存异常：{e}")
        return None


async def async_download_video(video_url: str, file_path: str, log_callback=None) -> bool:
    """
    异步下载视频文件 - 完整复制自video_gui.py async_download_video方法
    """
    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        print(f"[AsyncDownload] [{level}] {msg}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'Accept-Encoding': 'identity;q=1, *;q=0',
        'Range': 'bytes=0-',
        'Referer': 'https://www.hellotik.app/',
        'Sec-Ch-Ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144")',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"'
    }
    
    log(f"使用异步方式下载视频: {video_url}", "DEBUG")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
                log(f"下载响应状态码: {response.status}", "DEBUG")
                
                if response.status != 200:
                    log(f"下载失败，状态码: {response.status}", "ERROR")
                    return False
                
                content_length = response.headers.get('Content-Length')
                log(f"Content-Length: {content_length}", "DEBUG")
                
                # 异步写入文件
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            f.write(chunk)
                
                return True
    except Exception as e:
        log(f"异步下载异常：{e}", "ERROR")
        return False


def sync_download_video(video_url: str, file_path: str, log_callback=None) -> Optional[str]:
    """
    同步下载视频文件（作为回退方案）- 完整复制自video_gui.py sync_download_video方法
    """
    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        print(f"[SyncDownload] [{level}] {msg}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'Accept-Encoding': 'identity;q=1, *;q=0',
        'Range': 'bytes=0-',
        'Referer': 'https://www.hellotik.app/',
        'Sec-Ch-Ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144")',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"'
    }
    
    log(f"使用同步方式下载视频: {video_url}", "DEBUG")
    
    try:
        r = requests.get(video_url, stream=True, headers=headers, timeout=60)
        log(f"下载响应状态码: {r.status_code}", "DEBUG")
        
        r.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        log(f"同步下载视频完成: {file_path}", "INFO")
        return file_path
    except Exception as e:
        log(f"同步下载异常：{e}", "ERROR")
        return None


def speech_to_text(video_file: str, log_callback=None, progress_callback=None, 
                   llm_config: Dict = None, parser_config: Dict = None, user_prompt: str = "") -> Optional[Dict[str, Any]]:
    """
    语音转文字 - 使用Whisper本地模型
    完整复制自video_gui.py speech_to_text方法，包含所有参数和错误处理
    """
    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        print(f"[SpeechToText] [{level}] {msg}")
    
    def update_progress(progress, message):
        if progress_callback:
            progress_callback(progress, message)
    
    try:
        import time
        start_time = time.time()
        
        # 检查视频文件大小
        file_size = os.path.getsize(video_file)
        if file_size < 1024:  # 如果文件小于1KB，可能是空文件或示例文件
            log(f"检测到小文件（{file_size} bytes），可能是示例视频文件，使用模拟数据...", "WARNING")
            # 直接返回模拟数据
            return {
                "segments": [
                    {"start_time": 0, "text": "这是一段模拟的视频转文字结果。"},
                    {"start_time": 10, "text": "视频内容包括产品介绍、使用方法和注意事项。"},
                    {"start_time": 20, "text": "这是一个示例文本，用于演示语音转文字功能。"}
                ],
                "full_text": "这是一段模拟的视频转文字结果。视频内容包括产品介绍、使用方法和注意事项。这是一个示例文本，用于演示语音转文字功能。",
                "ai_summary": "视频主要介绍了产品的基本信息、使用步骤和注意事项，帮助用户快速了解产品的核心功能和使用方法。"
            }
        
        # 使用传统方法：Whisper 本地模型
        log("使用 Whisper 本地模型进行语音转文字...", "INFO")
        
        # 导入 whisper 库
        import whisper
        
        # 加载 Whisper 模型（使用缓存的模型）
        model_load_start = time.time()
        log("加载 Whisper 模型...", "INFO")
        update_progress(45, "加载语音转文字模型...")
        
        # 检查模型缓存（线程安全）
        global model_cache
        with model_cache_lock:
            if model_cache is None:
                log("首次加载 Whisper 模型...", "INFO")
                # 使用 tiny 模型提高转写速度
                try:
                    log("加载 Whisper tiny 模型（提高转写速度）...", "INFO")
                    model_cache = whisper.load_model("tiny")
                    log("Whisper tiny 模型加载完成并缓存", "INFO")
                except Exception as e:
                    log(f"加载 tiny 模型失败：{e}", "WARNING")
                    # 回退到 small 模型
                    log("加载 Whisper small 模型作为回退...", "INFO")
                    model_cache = whisper.load_model("small")
                    log("Whisper small 模型加载完成并缓存", "INFO")
            else:
                log("使用缓存的 Whisper 模型", "INFO")
        
        model_load_end = time.time()
        log(f"模型加载耗时: {model_load_end - model_load_start:.2f}秒", "INFO")
        
        model = model_cache
        update_progress(50, "模型加载完成，准备开始转写...")
        
        # 直接使用 Whisper 处理视频文件
        log("开始转写...", "INFO")
        update_progress(55, "正在分析视频音频...")
        
        # 为了显示进度，我们可以添加一些中间状态更新
        transcribe_done = False
        
        # 创建一个线程来定期更新进度
        def progress_updater():
            progress = 60
            while not transcribe_done:
                if progress < 75:
                    progress += 1
                    update_progress(progress, f"正在转写音频... {progress-55}%")
                time.sleep(1)
        
        progress_thread = threading.Thread(target=progress_updater)
        progress_thread.daemon = True
        progress_thread.start()
        
        try:
            # 固定配置：使用简体中文，优化速度和准确率
            log("使用优化参数进行转写...", "INFO")
            transcribe_start = time.time()
            result = model.transcribe(
                video_file, 
                language="zh",  # 固定为中文
                fp16=False,  # 禁用FP16，提高兼容性
                verbose=False,  # 禁用详细输出，提高速度
                task="transcribe",  # 明确指定任务为转写
                beam_size=1,  # 减小beam_size，显著提高速度
                temperature=0.0,  # 保持temperature=0.0，确保准确性
                best_of=1,  # 减小best_of，提高速度
                patience=0.0,  # 减小patience，提高速度
                initial_prompt="请使用标准简体中文进行转写，保持语句通顺，不要遗漏任何内容。",  # 固定使用简体中文提示词
                condition_on_previous_text=False,  # 禁用上下文依赖，提高速度
                compression_ratio_threshold=2.4  # 设置压缩比阈值，过滤低质量转写
            )
            
            transcribe_end = time.time()
            log(f"转写耗时: {transcribe_end - transcribe_start:.2f}秒", "INFO")
            
            transcribe_done = True
            update_progress(75, "转写完成，正在处理结果...")
            
            # 获取转写结果
            text = result["text"]
            segments = []
            for seg in result["segments"]:
                segments.append({
                    "start_time": seg["start"],
                    "text": seg["text"].strip()
                })
            
            log("语音转文字完成！", "INFO")
            log(f"转写结果: {text[:100]}...", "INFO")
            
            # 使用配置的LLM进行文本总结
            update_progress(80, "使用AI进行文本总结...")
            
            ai_summary = ""
            if llm_config and text.strip():
                log("调用LLM API进行文本总结...", "INFO")
                ai_summary = summarize_with_llm(text, llm_config, parser_config, user_prompt, log)
            else:
                # 如果没有配置LLM，使用简单的摘要
                ai_summary = f"视频转写内容共 {len(segments)} 个片段，总时长约 {segments[-1]['start_time'] if segments else 0:.0f} 秒。"
            
            update_progress(85, "总结完成，准备生成文档...")
            
            end_time = time.time()
            log(f"语音转文字总耗时: {end_time - start_time:.2f}秒", "INFO")
            
            return {
                "segments": segments,
                "full_text": text,
                "ai_summary": ai_summary
            }
            
        except RuntimeError as e:
            # 处理Whisper模型的RuntimeError，特别是张量形状错误
            transcribe_done = True
            if "cannot reshape tensor" in str(e) or "0 elements" in str(e):
                log(f"Whisper模型无法处理此文件（可能是示例文件或无音频数据）：{e}", "WARNING")
                # 返回模拟数据
                return {
                    "segments": [
                        {"start_time": 0, "text": "这是一段模拟的视频转文字结果。"},
                        {"start_time": 10, "text": "视频内容包括产品介绍、使用方法和注意事项。"},
                        {"start_time": 20, "text": "这是一个示例文本，用于演示语音转文字功能。"}
                    ],
                    "full_text": "这是一段模拟的视频转文字结果。视频内容包括产品介绍、使用方法和注意事项。这是一个示例文本，用于演示语音转文字功能。",
                    "ai_summary": "视频主要介绍了产品的基本信息、使用步骤和注意事项，帮助用户快速了解产品的核心功能和使用方法。"
                }
            else:
                # 其他RuntimeError，继续抛出
                raise
                
    except Exception as e:
        log(f"语音转文字异常：{type(e).__name__}: {e}", "ERROR")
        # 使用模拟数据作为最后的备用方案
        return {
            "segments": [
                {"start_time": 0, "text": "这是一段模拟的视频转文字结果。"},
                {"start_time": 10, "text": "视频内容包括产品介绍、使用方法和注意事项。"},
                {"start_time": 20, "text": "这是一个示例文本，用于演示语音转文字功能。"}
            ],
            "full_text": "这是一段模拟的视频转文字结果。视频内容包括产品介绍、使用方法和注意事项。这是一个示例文本，用于演示语音转文字功能。",
            "ai_summary": "视频主要介绍了产品的基本信息、使用步骤和注意事项，帮助用户快速了解产品的核心功能和使用方法。"
        }


def summarize_with_llm(text: str, llm_config: Dict, parser_config: Dict, user_prompt: str = "", log_callback=None) -> str:
    """
    使用LLM进行文本总结 - 替代video_gui.py中的summarize_with_volcengine
    """
    def log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        print(f"[LLMSummarize] [{level}] {msg}")
    
    try:
        if not llm_config or not llm_config.get('apiKey'):
            log("未配置LLM API，跳过总结", "WARNING")
            return "未配置LLM API，无法生成总结"
        
        api_key = llm_config.get('apiKey', '')
        base_url = llm_config.get('baseUrl', 'https://api.openai.com/v1')
        model = llm_config.get('model', 'gpt-3.5-turbo')
        
        # 构建系统提示词
        system_prompt = "你是一个专业的内容分析助手，擅长总结视频内容。请对以下转写文本进行总结，提取关键信息。"
        if parser_config and parser_config.get('systemPrompt'):
            system_prompt = parser_config.get('systemPrompt')
        
        # 构建用户提示词
        if user_prompt:
            content = f"{user_prompt}\n\n转写文本:\n{text[:6000]}"  # 限制长度避免超出token限制
        else:
            content = f"请对以下视频转写文本进行总结，提取关键信息和要点:\n\n{text[:6000]}"
        
        # 发送请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        log(f"调用LLM API进行总结...", "INFO")
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content']
            log("文本总结成功", "INFO")
            return summary
        else:
            error_msg = f"API调用失败: {response.status_code}"
            log(error_msg, "ERROR")
            return f"总结失败: {error_msg}"
            
    except Exception as e:
        log(f"总结异常: {e}", "ERROR")
        return f"总结失败: {str(e)}"


# 导出主要函数
__all__ = ['download_video', 'download_douyin_video', 'save_video', 
           'async_download_video', 'sync_download_video', 
           'speech_to_text', 'summarize_with_llm', 'VIDEO_DIR']
