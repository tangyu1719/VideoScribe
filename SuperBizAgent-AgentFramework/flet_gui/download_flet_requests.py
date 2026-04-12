#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用requests库和代理下载Flet桌面客户端
"""

import os
import sys
import zipfile
from pathlib import Path

# 设置代理环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'

import requests

def download_with_requests():
    """使用requests下载Flet客户端"""
    
    version = "0.84.0"
    filename = "flet-windows.zip"
    url = f"https://github.com/flet-dev/flet/releases/download/v{version}/{filename}"
    
    # 缓存目录
    cache_dir = Path.home() / ".flet" / "client" / f"flet-desktop-{version}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = cache_dir / "flet.zip"
    
    print(f"📥 下载Flet客户端 v{version}...")
    print(f"🔗 URL: {url}")
    print(f"📁 保存到: {cache_dir}")
    print(f"🌐 代理: http://127.0.0.1:7897\n")
    
    try:
        # 下载文件
        print("⏳ 正在下载...")
        
        response = requests.get(url, stream=True, timeout=120, verify=False)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    success = download_with_requests()
    sys.exit(0 if success else 1)
