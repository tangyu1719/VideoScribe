#!/usr/bin/env python3
"""
测试yt-dlp下载功能，用于排查问题
"""
import subprocess
import sys
import time

def test_ytdlp(url):
    """测试yt-dlp下载"""
    print(f"测试URL: {url}")
    print("-" * 50)
    
    # 基础命令
    cmd = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--verbose",  # 详细模式，显示更多信息
        "--print-traffic",  # 打印网络流量
        "-o", "test_video_%(id)s.%(ext)s",
        url
    ]
    
    print(f"命令: {' '.join(cmd)}")
    print("-" * 50)
    
    start_time = time.time()
    try:
        # 使用120秒超时
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,
            encoding='utf-8',
            errors='ignore'
        )
        elapsed = time.time() - start_time
        
        print(f"\n执行时间: {elapsed:.2f}秒")
        print(f"返回码: {result.returncode}")
        
        if result.returncode == 0:
            print("✓ 下载成功！")
            if result.stdout:
                print(f"\n输出:\n{result.stdout[-2000:]}")  # 只显示最后2000字符
        else:
            print("✗ 下载失败")
            if result.stderr:
                print(f"\n错误信息:\n{result.stderr[-3000:]}")  # 只显示最后3000字符
                
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n✗ 超时！执行时间: {elapsed:.2f}秒")
        print("可能原因：")
        print("1. 网络连接问题")
        print("2. 视频文件过大")
        print("3. B站服务器响应慢")
        print("4. 需要登录/Cookies")
    except Exception as e:
        print(f"\n✗ 异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.bilibili.com/video/BV1UewqzrEHt/"
    
    test_ytdlp(url)
