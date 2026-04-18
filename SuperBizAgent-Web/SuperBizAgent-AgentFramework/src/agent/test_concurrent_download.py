#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试并发下载功能
验证多线程并发时的文件命名冲突和文件访问竞争问题
"""

import os
import threading
import time
import random
from video_gui import App, VIDEO_DIR
import tkinter as tk

# 测试视频链接（使用公共测试链接）
TEST_LINKS = [
    "https://www.w3schools.com/html/mov_bbb.mp4",  # 公共测试视频
    "https://samplelib.com/lib/preview/mp4/sample-5s.mp4",  # 5秒测试视频
    "https://samplelib.com/lib/preview/mp4/sample-15s.mp4",  # 15秒测试视频
    "https://samplelib.com/lib/preview/mp4/sample-30s.mp4",  # 30秒测试视频
    "https://www.sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"  # 1MB测试视频
]

def test_concurrent_download():
    """测试并发下载"""
    print("=== 测试并发下载功能 ===")
    print(f"测试链接数量: {len(TEST_LINKS)}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 创建临时测试窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏窗口
    
    # 创建App实例
    app = App(root)
    print(f"线程池大小: {app.max_workers}")
    print(f"视频目录: {VIDEO_DIR}")
    
    # 清理之前的测试文件
    print("\n=== 清理测试环境 ===")
    test_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
    print(f"清理前视频文件数量: {len(test_files)}")
    for f in test_files:
        try:
            os.remove(os.path.join(VIDEO_DIR, f))
        except:
            pass
    test_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
    print(f"清理后视频文件数量: {len(test_files)}")
    
    # 添加测试任务到队列
    print("\n=== 添加测试任务 ===")
    for i, link in enumerate(TEST_LINKS):
        print(f"添加任务 {i+1}: {link}")
        app.task_queue.append(link)
        app.add_task_to_history(link)
    
    # 开始并发处理
    print("\n=== 开始并发处理 ===")
    start_time = time.time()
    
    # 启动队列处理
    threading.Thread(target=app.start_queue_processing, daemon=True).start()
    
    # 等待处理完成
    while app.processing_queue:
        print(f"处理中... 队列长度: {len(app.task_queue)}")
        time.sleep(2)
    
    end_time = time.time()
    print(f"\n=== 处理完成 ===")
    print(f"总耗时: {end_time - start_time:.2f}秒")
    
    # 检查结果
    final_files = [f for f in os.listdir(app.VIDEO_DIR) if f.endswith('.mp4')]
    print(f"最终视频文件数量: {len(final_files)}")
    for f in final_files:
        file_path = os.path.join(app.VIDEO_DIR, f)
        file_size = os.path.getsize(file_path)
        print(f"  - {f} ({file_size/1024/1024:.2f} MB)")
    
    # 检查历史记录
    completed_tasks = [t for t in app.history.get('tasks', []) if t.get('status') == 'completed']
    print(f"\n完成的任务数: {len(completed_tasks)}")
    
    # 清理测试文件
    print("\n=== 清理测试文件 ===")
    for f in final_files:
        try:
            os.remove(os.path.join(app.VIDEO_DIR, f))
        except Exception as e:
            print(f"清理文件失败: {e}")
    
    # 销毁窗口
    root.destroy()
    
    print("\n=== 测试完成 ===")
    print(f"成功下载: {len(final_files)}个文件")
    print(f"完成任务: {len(completed_tasks)}个任务")
    
    if len(final_files) == len(TEST_LINKS):
        print("✅ 测试通过: 所有文件都成功下载")
        return True
    else:
        print("❌ 测试失败: 部分文件下载失败")
        return False

if __name__ == "__main__":
    test_concurrent_download()
