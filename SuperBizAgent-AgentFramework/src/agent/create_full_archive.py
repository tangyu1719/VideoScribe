#!/usr/bin/env python3
"""
创建项目完整压缩包
"""
import os
import zipfile
from datetime import datetime
import shutil

def create_archive():
    """创建项目压缩包"""
    base_dir = r"f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua"
    
    # 生成压缩包名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"SuperBizAgent_完整文档_{timestamp}.zip"
    archive_path = os.path.join(os.path.dirname(base_dir), archive_name)
    
    print(f"开始创建压缩包: {archive_name}")
    print(f"源目录: {base_dir}")
    
    # 排除的文件和目录
    exclude_patterns = [
        '.git',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.pytest_cache',
        'node_modules',
        '.zip',
        'create_archive.py',
        'create_full_archive.py',
    ]
    
    def should_exclude(filepath):
        """检查是否应该排除该文件/目录"""
        for pattern in exclude_patterns:
            if pattern in filepath:
                return True
        return False
    
    # 创建压缩包
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(base_dir):
            # 过滤掉需要排除的目录
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            
            for file in files:
                if should_exclude(file):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(base_dir))
                
                try:
                    file_size = os.path.getsize(file_path)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    total_size += file_size
                    
                    if file_count % 50 == 0:
                        print(f"已添加 {file_count} 个文件...")
                        
                except Exception as e:
                    print(f"跳过文件 {file_path}: {e}")
    
    # 获取压缩包大小
    archive_size = os.path.getsize(archive_path)
    archive_size_mb = archive_size / (1024 * 1024)
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n✅ 压缩包创建成功!")
    print(f"📦 文件名: {archive_name}")
    print(f"📍 路径: {archive_path}")
    print(f"📊 文件数量: {file_count}")
    print(f"📈 原始大小: {total_size_mb:.2f} MB")
    print(f"📉 压缩后大小: {archive_size_mb:.2f} MB")
    print(f"🎯 压缩率: {(1 - archive_size/total_size)*100:.1f}%")
    
    return archive_path

if __name__ == "__main__":
    archive_path = create_archive()
    print(f"\n压缩包已保存到: {archive_path}")
