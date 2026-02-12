import requests
import json
import os
import sys
import time
from pathlib import Path


def process_xiaohongshu_link(xhs_url):
    """
    直接处理小红书链接，调用两个工具网站API
    """
    print("开始处理小红书链接...")
    print(f"输入链接: {xhs_url}")

    try:
        # 第一步：使用第一个工具网站（视频下载）的API
        print("\n=== 步骤1: 调用视频下载工具网站API ===")
        print("正在请求视频下载服务...")

        # 从你提供的信息中，我们可以看到API请求格式
        # 但需要找到正确的API端点
        download_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://hellotik.app/',
            'Origin': 'https://hellotik.app'
        }

        # 构造请求数据，基于你提供的信息
        download_payload = {
            "url": xhs_url,
            "isMobile": "false"
        }

        # 尝试多个可能的API端点
        possible_endpoints = [
            "https://api.hellotik.app/api/download",
            "https://hellotik.app/api/video",
            "https://hellotik.app/api/fetch",
            "https://www.hellotik.app/api/download"
        ]

        video_url = None
        for endpoint in possible_endpoints:
            try:
                print(f"尝试API端点: {endpoint}")
                response = requests.post(
                    endpoint, json=download_payload, headers=download_headers, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    if 'video_url' in result or 'download_url' in result:
                        video_url = result.get(
                            'video_url') or result.get('download_url')
                        print(f"SUCCESS: 成功获取视频URL: {video_url[:50]}...")
                        break
                    elif 'data' in result and 'video_url' in result['data']:
                        video_url = result['data']['video_url']
                        print(f"SUCCESS: 成功获取视频URL: {video_url[:50]}...")
                        break
            except:
                continue

        if not video_url:
            print("WARNING: 无法通过API获取视频URL，可能是网站没有开放API")
            print("   请手动使用网站界面下载视频")
            print("   访问: https://hellotik.app/ 并粘贴链接")
            return False

        # 第二步：使用第二个工具网站（语音转文字）的API
        print("\n=== 步骤2: 调用语音转文字工具网站API ===")
        print("正在上传视频进行语音转文字处理...")

        # 首先下载视频到本地
        print("下载视频文件...")
        video_response = requests.get(video_url)
        if video_response.status_code != 200:
            print("ERROR: 下载视频失败")
            return False

        # 保存临时视频文件
        import tempfile
        temp_dir = tempfile.mkdtemp()
        video_filename = os.path.join(temp_dir, "temp_video.mp4")

        with open(video_filename, 'wb') as f:
            f.write(video_response.content)

        print(f"SUCCESS: 视频已下载: {video_filename}")

        # 上传到reccloud进行语音转文字
        reccloud_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://reccloud.cn/speech-to-text-online',
            'Origin': 'https://reccloud.cn'
        }

        with open(video_filename, 'rb') as video_file:
            files = {
                'file': ('video.mp4', video_file, 'video/mp4')
            }
            data = {
                'type': 'speech_to_text',
                'config': json.dumps({
                    'enable_highlight': True,
                    'enable_seperate': True,
                    'enable_translate': False
                })
            }

            upload_response = requests.post(
                "https://api.reccloud.cn/v1/task/create",
                files=files,
                data=data,
                headers=reccloud_headers
            )

        if upload_response.status_code != 200:
            print(f"ERROR: 上传到reccloud失败，状态码: {upload_response.status_code}")
            return False

        upload_result = upload_response.json()
        if upload_result.get('code') != 0:
            print(f"ERROR: 上传到reccloud失败: {upload_result.get('msg', '未知错误')}")
            return False

        task_id = upload_result['data']['task_id']
        print(f"SUCCESS: 视频上传成功，任务ID: {task_id}")

        # 等待处理完成
        print("PROGRESS: 正在处理中，请稍候...")
        status_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

        start_time = time.time()
        timeout = 600  # 10分钟超时

        while time.time() - start_time < timeout:
            status_response = requests.get(
                f"https://api.reccloud.cn/v1/task/status?task_id={task_id}",
                headers=status_headers
            )

            if status_response.status_code == 200:
                status_result = status_response.json()
                if status_result.get('code') == 0:
                    status = status_result['data']['status']

                    if status == 'completed':
                        print("SUCCESS: 处理完成")
                        break
                    elif status == 'failed':
                        print(
                            f"ERROR: 处理失败: {status_result['data'].get('fail_reason', '未知错误')}")
                        return False
                    else:
                        print(f"PROGRESS: 处理中... 当前状态: {status}")
                        time.sleep(10)
                        continue
                else:
                    print(f"ERROR: 查询状态失败: {status_result.get('msg', '未知错误')}")
                    return False
            else:
                print(f"ERROR: 查询状态请求失败，状态码: {status_response.status_code}")
                return False

        if time.time() - start_time >= timeout:
            print("ERROR: 处理超时")
            return False

        # 获取处理结果
        print("获取处理结果...")
        result_response = requests.get(
            f"https://api.reccloud.cn/v1/task/result?task_id={task_id}",
            headers=status_headers
        )

        if result_response.status_code != 200:
            print(f"ERROR: 获取结果失败，状态码: {result_response.status_code}")
            return False

        result_data = result_response.json()
        if result_data.get('code') != 0:
            print(f"ERROR: 获取结果失败: {result_data.get('msg', '未知错误')}")
            return False

        print("SUCCESS: 成功获取处理结果")

        # 保存为Markdown文档
        save_as_markdown(result_data['data'])

        # 清理临时文件
        try:
            os.remove(video_filename)
            os.rmdir(temp_dir)
        except:
            pass

        print("\nSUCCESS: 处理完成！")
        return True

    except Exception as e:
        print(f"ERROR: 处理过程中出现错误: {e}")
        return False


def save_as_markdown(content_data, output_dir="csdn/待阅览"):
    """将内容保存为Markdown文档"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成文件名
    timestamp = int(time.time())
    filename = f"小红书视频分析_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    # 提取内容
    segments = content_data.get('segments', [])
    transcript = ""
    for segment in segments:
        start_time = segment.get('start_time', 0)
        text = segment.get('text', '')
        timestamp_str = time.strftime('%H:%M:%S', time.gmtime(start_time))
        transcript += f"- [{timestamp_str}] {text}\n"

    # 获取AI摘要
    ai_summary = content_data.get(
        'ai_summary', content_data.get('summary', ''))

    # 创建Markdown内容
    md_content = f"""# 小红书视频内容分析

## 视频信息
- 分析时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}

## 语音转文字内容
{transcript}

## AI智能分析摘要
{ai_summary}

---
*通过小红书视频分析工具生成*
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"SUCCESS: Markdown文档已保存到: {filepath}")
    return filepath


def main():
    print("欢迎使用小红书视频转文字工具")
    print("=" * 40)

    # 获取用户输入
    xhs_link = input("请输入小红书链接: ").strip()

    if not xhs_link:
        print("ERROR: 链接不能为空")
        sys.exit(1)

    print(f"\n开始处理链接: {xhs_link}")
    success = process_xiaohongshu_link(xhs_link)

    if not success:
        print("\nWARNING: 如果API调用失败，可以尝试:")
        print("   1. 检查网络连接")
        print("   2. 确认API端点是否正确")
        print("   3. 使用网站界面手动处理")
        print("   4. 确保链接是有效的完整小红书链接")
        sys.exit(1)

    print("\n处理完成！Markdown文档已保存到 csdn/待阅览 目录")


if __name__ == "__main__":
    main()
