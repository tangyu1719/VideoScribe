#!/usr/bin/env python3
"""
测试yt-dlp下载功能 - 简化版测试
"""
import subprocess
import sys
import time
import threading

def test_ytdlp_simple(url):
    """简化测试 - 只获取视频信息不下载"""
    print(f"测试URL: {url}")
    print("-" * 50)
    
    # 先测试获取视频信息（不下载）
    cmd_info = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--dump-json",  # 只获取信息
        "--skip-download",
        url
    ]
    
    print(f"步骤1: 获取视频信息...")
    print(f"命令: {' '.join(cmd_info[:8])}...")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd_info, 
            capture_output=True, 
            text=True, 
            timeout=30,
            encoding='utf-8',
            errors='ignore'
        )
        elapsed = time.time() - start_time
        
        print(f"耗时: {elapsed:.2f}秒")
        
        if result.returncode == 0 and result.stdout:
            import json
            try:
                info = json.loads(result.stdout.strip().split('\n')[0])
                print(f"✓ 获取信息成功!")
                print(f"  标题: {info.get('title', 'N/A')[:50]}...")
                print(f"  时长: {info.get('duration', 'N/A')}秒")
                print(f"  格式数: {len(info.get('formats', []))}")
            except:
                print(f"✓ 有输出但解析失败")
        else:
            print(f"✗ 获取信息失败")
            if result.stderr:
                print(f"错误: {result.stderr[:500]}")
            return
                
    except subprocess.TimeoutExpired:
        print(f"✗ 获取信息超时（30秒）")
        print("可能原因：")
        print("1. B站需要登录才能访问该视频")
        print("2. IP被限制")
        print("3. 视频不存在或需要特定权限")
        return
    except Exception as e:
        print(f"✗ 异常: {e}")
        return
    
    # 如果获取信息成功，尝试下载
    print("\n" + "-" * 50)
    print("步骤2: 尝试下载视频...")
    
    cmd_download = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://www.bilibili.com/",
        "--no-check-certificate",
        "--progress",  # 显示进度
        "-o", "test_video_%(id)s.%(ext)s",
        url
    ]
    
    print(f"命令: {' '.join(cmd_download[:8])}...")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd_download, 
            capture_output=True, 
            text=True, 
            timeout=180,  # 3分钟
            encoding='utf-8',
            errors='ignore'
        )
        elapsed = time.time() - start_time
        
        print(f"耗时: {elapsed:.2f}秒")
        
        if result.returncode == 0:
            print("✓ 下载成功!")
        else:
            print(f"✗ 下载失败")
            if result.stderr:
                print(f"错误: {result.stderr[:1000]}")
                
    except subprocess.TimeoutExpired:
        print(f"✗ 下载超时（180秒）")
    except Exception as e:
        print(f"✗ 异常: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.bilibili.com/video/BV1UewqzrEHt/"
    
    test_ytdlp_simple(url)
