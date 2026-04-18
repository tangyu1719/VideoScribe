#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动下载Flet桌面客户端脚本
需要开启代理后运行
"""

import os
import sys
import urllib.request
import zipfile
from pathlib import Path

def download_flet_client():
    """下载Flet桌面客户端"""
    
    # Flet客户端版本
    version = "0.24.1"  # 与flet版本匹配
    
    # 下载URL (Windows x64)
    url = f"https://github.com/flet-dev/flet/releases/download/v{version}/flet-windows-amd64.zip"
    
    # 缓存目录
    cache_dir = Path.home() / ".flet" / "bin" / f"flet-{version}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = cache_dir / "flet.zip"
    
    print(f"下载Flet客户端 v{version}...")
    print(f"URL: {url}")
    print(f"保存到: {cache_dir}")
    
    # 设置代理 (如果需要)
    # proxy = urllib.request.ProxyHandler({
    #     'http': 'http://127.0.0.1:7897',
    #     'https': 'http://127.0.0.1:7897'
    # })
    # opener = urllib.request.build_opener(proxy)
    # urllib.request.install_opener(opener)
    
    try:
        # 下载文件
        urllib.request.urlretrieve(url, str(zip_path))
        print(f"下载完成: {zip_path}")
        
        # 解压
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(cache_dir)
        print(f"解压完成")
        
        # 删除zip文件
        zip_path.unlink()
        print("清理完成")
        
        print(f"\nFlet客户端已安装到: {cache_dir}")
        print("现在可以运行 main_app.py 启动桌面应用了！")
        
    except Exception as e:
        print(f"下载失败: {e}")
        print("\n请确保:")
        print("1. 已开启代理/VPN")
        print("2. 可以访问 GitHub")
        print("\n或者手动下载:")
        print(f"  {url}")
        print(f"解压到: {cache_dir}")

if __name__ == "__main__":
    download_flet_client()
