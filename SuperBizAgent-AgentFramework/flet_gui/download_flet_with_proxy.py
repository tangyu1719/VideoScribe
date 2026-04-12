#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用代理下载Flet桌面客户端 v0.84.0
"""

import os
import sys
import urllib.request
import zipfile
import ssl
from pathlib import Path

def download_with_proxy():
    """使用代理下载Flet客户端"""
    
    version = "0.84.0"  # 与安装的flet版本匹配
    filename = "flet-windows.zip"  # Windows文件名
    url = f"https://github.com/flet-dev/flet/releases/download/v{version}/{filename}"
    
    # 缓存目录 (根据flet_desktop的目录结构)
    cache_dir = Path.home() / ".flet" / "client" / f"flet-desktop-{version}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = cache_dir / "flet.zip"
    
    print(f"📥 下载Flet客户端 v{version}...")
    print(f"🔗 URL: {url}")
    print(f"📁 保存到: {cache_dir}")
    print(f"🌐 代理: http://127.0.0.1:7897\n")
    
    # 创建SSL上下文（忽略证书验证）
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # 设置代理
    proxy_handler = urllib.request.ProxyHandler({
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897'
    })
    
    # 创建opener
    opener = urllib.request.build_opener(
        proxy_handler,
        urllib.request.HTTPSHandler(context=ssl_context)
    )
    urllib.request.install_opener(opener)
    
    try:
        # 下载文件
        print("⏳ 正在下载...")
        
        # 使用urlopen来跟踪进度
        response = urllib.request.urlopen(url, timeout=120)
        total_size = int(response.headers.get('Content-Length', 0))
        
        with open(zip_path, 'wb') as f:
            downloaded = 0
            chunk_size = 8192
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r   进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print(f"\n✅ 下载完成: {zip_path}\n")
        
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
        print(f"\n❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    success = download_with_proxy()
    sys.exit(0 if success else 1)
