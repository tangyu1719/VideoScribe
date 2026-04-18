#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用aiohttp和代理下载Flet桌面客户端
"""

import asyncio
import aiohttp
import zipfile
from pathlib import Path

async def download_with_aiohttp():
    """使用aiohttp下载Flet客户端"""
    
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
    
    # 代理设置
    connector = aiohttp.TCPConnector(ssl=False)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            print("⏳ 正在下载...")
            
            async with session.get(
                url, 
                proxy="http://127.0.0.1:7897",
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status != 200:
                    print(f"❌ HTTP错误: {response.status}")
                    return False
                
                total_size = int(response.headers.get('content-length', 0))
                print(f"   文件大小: {total_size / 1024 / 1024:.1f} MB")
                
                downloaded = 0
                with open(zip_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   进度: {percent:.1f}% ({downloaded/1024/1024:.1f}/{total_size/1024/1024:.1f} MB)", end='', flush=True)
                
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
    # 安装aiohttp
    import subprocess
    subprocess.run(["pip", "install", "aiohttp", "-q"])
    
    success = asyncio.run(download_with_aiohttp())
    exit(0 if success else 1)
