#!/usr/bin/env python3
"""
测试yt-dlp下载功能 - 极速版（使用最低清晰度）
"""
import subprocess
import sys
import time

def test_ytdlp_fast(url):
    """使用最低清晰度快速下载"""
    print(f"测试URL: {url}")
    print("-" * 50)
    
    # 方案1: 只下载360p视频（最小文件）
    cmd1 = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--progress",
        "--format", "30016+30216",  # 360p视频 + 低质量音频（具体格式ID）
        "--merge-output-format", "mp4",
        "-o", "test_video_360p_%(id)s.%(ext)s",
        url
    ]
    
    print("方案1: 使用360p格式 (30016+30216)")
    print("开始下载...")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd1, 
            capture_output=True, 
            text=True, 
            timeout=120,
            encoding='utf-8',
            errors='ignore'
        )
        elapsed = time.time() - start_time
        
        print(f"\n耗时: {elapsed:.2f}秒")
        
        if result.returncode == 0:
            print("✓ 方案1下载成功!")
            return
        else:
            print(f"✗ 方案1失败: {result.stderr[-500:] if result.stderr else '未知错误'}")
    except subprocess.TimeoutExpired:
        print(f"✗ 方案1超时")
    except Exception as e:
        print(f"✗ 方案1异常: {e}")
    
    # 方案2: 使用worst质量
    print("\n" + "-" * 50)
    print("方案2: 使用worst质量")
    
    cmd2 = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--progress",
        "--format", "worst",  # 最低质量
        "-o", "test_video_worst_%(id)s.%(ext)s",
        url
    ]
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd2, 
            capture_output=True, 
            text=True, 
            timeout=120,
            encoding='utf-8',
            errors='ignore'
        )
        elapsed = time.time() - start_time
        
        print(f"\n耗时: {elapsed:.2f}秒")
        
        if result.returncode == 0:
            print("✓ 方案2下载成功!")
        else:
            print(f"✗ 方案2失败")
            if result.stderr:
                print(f"错误: {result.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        print(f"✗ 方案2超时")
    except Exception as e:
        print(f"✗ 方案2异常: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.bilibili.com/video/BV1UewqzrEHt/"
    
    test_ytdlp_fast(url)
