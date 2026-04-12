#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用国内镜像下载Flet桌面客户端
"""

import os
import sys
import zipfile
from pathlib import Path

import requests

def download_from_mirror():
    """从国内镜像下载Flet客户端"""
    
    version = "0.84.0"
    filename = "flet-windows.zip"
    
    # 尝试多个镜像源
    mirrors = [
        f"https://ghproxy.com/https://github.com/flet-dev/flet/releases/download/v{version}/{filename}",
        f"https://mirror.ghproxy.com/https://github.com/flet-dev/flet/releases/download/v{version}/{filename}",
        f"https://gh.api.99988866.xyz/https://github.com/flet-dev/flet/releases/download/v{version}/{filename}",
        f"https://ghps.cc/https://github.com/flet-dev/flet/releases/download/v{version}/{filename}",
        f"https://gh.idayer.com/https://github.com/flet-dev/flet/releases/download/v{version}/{filename}",
    ]
    
    # 缓存目录
    cache_dir = Path.home() / ".flet" / "client" / f"flet-desktop-{version}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = cache_dir / "flet.zip"
    
    print(f"📥 下载Flet客户端 v{version}...")
    print(f"📁 保存到: {cache_dir}\n")
    
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    for i, url in enumerate(mirrors):
        print(f"🔄 尝试镜像源 {i+1}/{len(mirrors)}: {url[:60]}...")
        
        try:
            response = requests.get(url, stream=True, timeout=60, verify=False)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                print(f"   ⚠️ 文件大小为0，尝试下一个镜像...\n")
                continue
            
            print(f"   ✅ 连接成功，文件大小: {total_size / 1024 / 1024:.1f} MB")
            print(f"   ⏳ 正在下载...")
            
            downloaded = 0
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   进度: {percent:.1f}% ({downloaded/1024/1024:.1f}/{total_size/1024/1024:.1f} MB)", end='', flush=True)
            
            print(f"\n   ✅ 下载完成!\n")
            
            # 解压
            print("⏳ 正在解压...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(cache_dir)
            print("✅ 解压完成\n")
            
            # 删除zip文件
            zip_path.unlink()
            print("✅ 清理完成\n")
            
            print("=" * 50)
            print(f"🎉 Flet客户端安装成功！")
            print(f"📂 安装位置: {cache_dir}")
            print("=" * 50)
            print("\n现在可以运行: py main_app.py")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 失败: {e}\n")
            continue
    
    print("❌ 所有镜像源都失败了")
    return False

if __name__ == "__main__":
    success = download_from_mirror()
    sys.exit(0 if success else 1)
