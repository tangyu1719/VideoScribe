#!/usr/bin/env python3
"""
测试yt-dlp下载功能 - 使用优化参数
"""
import subprocess
import sys
import time

def test_ytdlp_optimized(url):
    """使用优化参数测试下载"""
    print(f"测试URL: {url}")
    print("-" * 50)
    
    cmd = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--progress",  # 显示进度
        # 下载优化参数
        "--format", "best[height<=720]",  # 限制最高720p
        "--concurrent-fragments", "5",  # 5个并发片段下载
        "--buffer-size", "16K",
        "--retries", "10",
        "--fragment-retries", "10",
        "--socket-timeout", "30",
        "-o", "test_video_%(id)s.%(ext)s",
        url
    ]
    
    print(f"命令: yt-dlp --format best[height<=720] --concurrent-fragments 5 ...")
    print("开始下载...")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5分钟
            encoding='utf-8',
            errors='ignore'
        )
        elapsed = time.time() - start_time
        
        print(f"\n耗时: {elapsed:.2f}秒")
        
        if result.returncode == 0:
            print("✓ 下载成功!")
            if result.stdout:
                print(f"输出:\n{result.stdout[-1000:]}")
        else:
            print(f"✗ 下载失败")
            if result.stderr:
                print(f"错误:\n{result.stderr[-1500:]}")
                
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n✗ 超时！已耗时: {elapsed:.2f}秒")
        print("即使使用优化参数仍然超时，可能原因：")
        print("1. B站严格限制了下载速度")
        print("2. 网络带宽不足")
        print("3. 视频文件过大")
    except Exception as e:
        print(f"\n✗ 异常: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.bilibili.com/video/BV1UewqzrEHt/"
    
    test_ytdlp_optimized(url)
