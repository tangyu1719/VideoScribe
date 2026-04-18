# -*- coding: utf-8 -*-
"""模拟 GUI 提交链接测试"""
import sys
sys.path.insert(0, 'f:/java/AIOPS/SuperBizAgent-release-2026-01-02/demo_wendanghua')

from video_gui import App
import tkinter as tk
import time

print("=" * 80)
print("开始模拟 GUI 测试小红书视频链接")
print("=" * 80)

# 创建应用
root = tk.Tk()
app = App(root)

# 测试链接
test_url = 'https://www.xiaohongshu.com/explore/69b292500000000028009849?xsec_token=ABooHNtmLa1lywHSX_GfvOvOK5_vdc3sq0jATYVEa0qMo=&xsec_source=pc_collect'

print(f"\n测试链接：{test_url}")
print("\n【步骤 1】检测平台类型...")
platform = app._detect_platform(test_url)
print(f"平台检测结果：{platform}")

if platform == "小红书视频":
    print("\n✓ 平台检测成功！")
    print("\n【步骤 2】模拟提交到线程池...")
    # 模拟 GUI 提交
    app.submit_task(test_url, "")
    print("任务已提交到线程池")
    
    print("\n【步骤 3】等待任务处理...")
    time.sleep(2)  # 等待 2 秒
    
    print("\n【步骤 4】检查输出文件...")
    import os
    output_dir = 'f:/java/AIOPS/SuperBizAgent-release-2026-01-02/demo_wendanghua/OUTPUT'
    files = sorted(os.listdir(output_dir), reverse=True)
    if files:
        latest_file = files[0]
        print(f"最新输出文件：{latest_file}")
        print(f"\n文件内容预览:")
        print("-" * 80)
        with open(os.path.join(output_dir, latest_file), 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500])
        print("-" * 80)
    else:
        print("未找到输出文件")
else:
    print(f"\n✗ 平台检测失败：{platform}")

root.destroy()
print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)
