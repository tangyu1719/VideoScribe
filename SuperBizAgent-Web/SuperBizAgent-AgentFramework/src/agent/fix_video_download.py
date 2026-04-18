#!/usr/bin/env python3
"""
视频下载优化脚本
修复长视频下载超时问题
"""
import re
from pathlib import Path

# 修复旧项目的 video_downloader.py
old_file = Path(r"f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\video_downloader.py")

if old_file.exists():
    content = old_file.read_text(encoding='utf-8')
    
    # 1. 优化 yt-dlp 参数
    content = re.sub(
        r'--concurrent-fragments", "5"',
        '--concurrent-fragments", "3"',
        content
    )
    content = re.sub(
        r'--buffer-size", "16K"',
        '--buffer-size", "32K"',
        content
    )
    content = re.sub(
        r'--retries", "10"',
        '--retries", "15"',
        content
    )
    content = re.sub(
        r'--fragment-retries", "10"',
        '--fragment-retries", "15"',
        content
    )
    content = re.sub(
        r'--socket-timeout", "30"',
        '--socket-timeout", "120"',
        content
    )
    content = re.sub(
        r'--format", "30016\+30216/worst"',
        '--format", "best[height<=480]/worst"',
        content
    )
    
    # 添加额外的优化参数
    content = content.replace(
        '"--socket-timeout", "120",  # socket 超时\n            "-o", output_file,',
        '''"--socket-timeout", "120",  # socket 超时
            "--http-chunk-size", "10M",  # 增大 HTTP 分块大小
            "--rate-limit", "0",  # 不限速
            "--no-resize-buffer",  # 不调整缓冲区
            "--no-abort-on-error",  # 出错不中断
            "--continue",  # 断点续传
            "-o", output_file,'''
    )
    
    # 2. 增加超时时间到 1800 秒（30 分钟）
    content = re.sub(
        r'timeout=600\)',
        'timeout=1800)',
        content
    )
    content = re.sub(
        r'max_retries = 2',
        'max_retries = 3',
        content
    )
    
    # 3. 更新注释
    content = content.replace(
        'B 站下载限速严重，增加超时时间到 600 秒（10 分钟）',
        '长视频下载超时时间增加到 1800 秒（30 分钟）'
    )
    content = content.replace(
        '超时详情：B 站可能限速，建议登录 B 站账号或使用更低清晰度',
        '超时详情：长视频下载时间较长，请耐心等待'
    )
    content = content.replace(
        'yt-dlp 执行多次超时，B 站下载限速严重',
        'yt-dlp 执行多次超时'
    )
    content = content.replace(
        '解决方案：1.在 Firefox 登录 B 站 2.使用其他视频源 3.降低视频清晰度',
        '解决方案：1.检查网络连接 2.使用更低清晰度 3.更换视频源'
    )
    
    # 写回文件
    old_file.write_text(content, encoding='utf-8')
    print("✓ 已修复 video_downloader.py")

# 同步到新项目
new_file = Path(r"f:\java\AIOPS\SuperBizAgent_v2\src\services\video_downloader.py")
if new_file.exists():
    new_content = old_file.read_text(encoding='utf-8')
    new_file.write_text(new_content, encoding='utf-8')
    print("✓ 已同步到新项目")

print("\n✅ 视频下载优化完成！")
print("\n优化内容:")
print("1. 增加 socket 超时：30 秒 → 120 秒")
print("2. 增加重试次数：10 次 → 15 次")
print("3. 降低并发数：5 → 3（避免网络拥塞）")
print("4. 增大缓冲区：16K → 32K")
print("5. 增加断点续传功能")
print("6. 增加 subprocess 超时：600 秒 → 1800 秒")
print("7. 优化视频质量：优先 480p（提高下载速度）")
print("8. 增加 HTTP 分块大小：减少请求次数")
