#!/usr/bin/env python3
"""
测试yt-dlp下载功能 - 最终修复版
"""
import subprocess
import sys
import time

def test_ytdlp_final(url):
    """使用修复后的参数测试下载"""
    print(f"测试URL: {url}")
    print("-" * 50)
    
    cmd = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--progress",  # 显示进度
        # 修复后的格式选择 - B站音视频分离
        "--format", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "--merge-output-format", "mp4",
        "--concurrent-fragments", "5",
        "--buffer-size", "16K",
        "--retries", "10",
        "--fragment-retries", "10",
        "--socket-timeout", "30",
        "-o", "test_video_final_%(id)s.%(ext)s",
        url
    ]
    
    print(f"格式: bestvideo[height<=720]+bestaudio/best")
    print(f"开始下载...")
    
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
                print(f"输出:\n{result.stdout[-500:]}")
        else:
            print(f"✗ 下载失败")
            if result.stderr:
                print(f"错误:\n{result.stderr[-1500:]}")
                
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n✗ 超时！已耗时: {elapsed:.2f}秒")
    except Exception as e:
        print(f"\n✗ 异常: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.bilibili.com/video/BV1UewqzrEHt/"
    
    test_ytdlp_final(url)
