#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建项目压缩包
"""

import os
import zipfile
from datetime import datetime

def create_archive():
    """创建项目压缩包"""
    
    # 要包含的文件扩展名
    extensions = ['.py', '.json', '.txt', '.md', '.bat', '.sql', '.html', '.css', '.js', '.ts', '.tsx']
    
    # 要排除的文件/目录
    exclude = ['.git', '__pycache__', 'node_modules', '.zip', 'Pictures', 'wechat_images', 'uploads']
    
    # 创建压缩包
    archive_name = f"SuperBizAgent_v2.0_{datetime.now().strftime('%Y%m%d')}.zip"
    
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # 排除不需要的目录
            dirs[:] = [d for d in dirs if d not in exclude and not d.startswith('.')]
            
            for file in files:
                # 检查文件扩展名
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    # 排除不需要的文件
                    if not any(ex in file_path for ex in exclude):
                        zipf.write(file_path)
                        print(f"添加: {file_path}")
    
    print(f"\n✓ 压缩包创建完成: {archive_name}")
    print(f"✓ 文件大小: {os.path.getsize(archive_name) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    create_archive()
