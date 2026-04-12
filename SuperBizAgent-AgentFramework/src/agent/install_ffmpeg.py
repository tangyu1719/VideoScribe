#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动下载并安装ffmpeg
"""

import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

# 配置
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
INSTALL_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "ffmpeg"))
TEMP_ZIP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg_temp.zip")

def download_file(url, destination, chunk_size=8192):
    """下载文件并显示进度"""
    print(f"正在下载: {url}")
    print(f"保存到: {destination}")
    
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"✓ 下载完成: {destination}")
        return True
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """解压zip文件"""
    print(f"正在解压: {zip_path}")
    print(f"解压到: {extract_to}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ 解压完成")
        return True
    except Exception as e:
        print(f"✗ 解压失败: {e}")
        return False

def find_ffmpeg_bin(extract_dir):
    """在解压后的目录中找到ffmpeg bin目录"""
    for root, dirs, files in os.walk(extract_dir):
        if "ffmpeg.exe" in files and "ffprobe.exe" in files:
            return root
    return None

def install_ffmpeg():
    """安装ffmpeg"""
    print("=" * 60)
    print("FFmpeg 自动安装脚本")
    print("=" * 60)
    print()
    
    # 检查是否已安装
    if os.path.exists(os.path.join(INSTALL_DIR, "bin", "ffmpeg.exe")):
        print("✓ FFmpeg 已安装")
        print(f"  路径: {INSTALL_DIR}")
        return True
    
    # 创建安装目录
    os.makedirs(INSTALL_DIR, exist_ok=True)
    print(f"✓ 创建安装目录: {INSTALL_DIR}")
    
    # 下载ffmpeg
    print()
    print("步骤1: 下载 FFmpeg")
    print("-" * 60)
    if not download_file(FFMPEG_DOWNLOAD_URL, TEMP_ZIP):
        print("✗ 下载失败，请手动下载并安装")
        print(f"下载地址: {FFMPEG_DOWNLOAD_URL}")
        return False
    
    # 解压ffmpeg
    print()
    print("步骤2: 解压 FFmpeg")
    print("-" * 60)
    temp_extract_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg_temp")
    if not extract_zip(TEMP_ZIP, temp_extract_dir):
        return False
    
    # 找到ffmpeg bin目录
    print()
    print("步骤3: 查找 FFmpeg 可执行文件")
    print("-" * 60)
    ffmpeg_bin_dir = find_ffmpeg_bin(temp_extract_dir)
    if not ffmpeg_bin_dir:
        print("✗ 未找到 ffmpeg.exe")
        return False
    print(f"✓ 找到 FFmpeg: {ffmpeg_bin_dir}")
    
    # 移动到安装目录
    print()
    print("步骤4: 安装到目标目录")
    print("-" * 60)
    try:
        # 如果目标目录已存在，先删除
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR)
        
        # 移动ffmpeg目录
        shutil.move(os.path.dirname(ffmpeg_bin_dir), INSTALL_DIR)
        print(f"✓ 安装完成: {INSTALL_DIR}")
    except Exception as e:
        print(f"✗ 安装失败: {e}")
        return False
    
    # 清理临时文件
    print()
    print("步骤5: 清理临时文件")
    print("-" * 60)
    try:
        if os.path.exists(TEMP_ZIP):
            os.remove(TEMP_ZIP)
            print(f"✓ 删除: {TEMP_ZIP}")
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
            print(f"✓ 删除: {temp_extract_dir}")
    except Exception as e:
        print(f"⚠ 清理临时文件失败: {e}")
    
    # 验证安装
    print()
    print("步骤6: 验证安装")
    print("-" * 60)
    ffmpeg_exe = os.path.join(INSTALL_DIR, "bin", "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print(f"✓ FFmpeg 安装成功!")
        print(f"  路径: {ffmpeg_exe}")
        return True
    else:
        print("✗ 安装验证失败")
        return False

def main():
    """主函数"""
    try:
        success = install_ffmpeg()
        if success:
            print()
            print("=" * 60)
            print("FFmpeg 安装完成!")
            print("=" * 60)
            print()
            print("现在可以正常使用视频转文字功能了。")
            print("请重新启动程序。")
            return 0
        else:
            print()
            print("=" * 60)
            print("FFmpeg 安装失败")
            print("=" * 60)
            print()
            print("请手动下载并安装:")
            print(f"1. 下载: {FFMPEG_DOWNLOAD_URL}")
            print(f"2. 解压到: {INSTALL_DIR}")
            return 1
    except KeyboardInterrupt:
        print("\n\n用户取消安装")
        return 1
    except Exception as e:
        print(f"\n\n安装过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
