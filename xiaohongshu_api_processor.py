import requests
import json
import os
import sys
import time
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path


def extract_xiaohongshu_id(url):
    """从小红书URL中提取视频ID"""
    patterns = [
        r'/explore/([a-zA-Z0-9]+)',
        r'/discovery/item/([a-zA-Z0-9]+)',
        r'com/s/([a-zA-Z0-9]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def download_video_with_yt_dlp(xhs_url):
    """使用yt-dlp下载小红书视频"""
    import subprocess
    import tempfile

    try:
        # 检查yt-dlp是否安装
        subprocess.run(['yt-dlp', '--version'],
                       check=True, capture_output=True)

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        xhs_id = extract_xiaohongshu_id(xhs_url) or str(int(time.time()))
        output_file = os.path.join(temp_dir, f"xhs_video_{xhs_id}.mp4")

        # 使用yt-dlp下载视频
        cmd = [
            'yt-dlp',
            '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.0',
            '--add-header', 'Referer:https://www.xiaohongshu.com/',
            '-o', output_file,
            xhs_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_file):
            print(f"视频已下载: {output_file}")
            return output_file
        else:
            print(f"yt-dlp下载失败: {result.stderr}")
            return None

    except subprocess.CalledProcessError:
        print("未找到yt-dlp，请安装: pip install yt-dlp")
        return None
    except Exception as e:
        print(f"下载过程中出错: {e}")
        return None


def upload_video_to_reccloud_api(video_path):
    """调用reccloud API上传视频进行语音转文字"""
    print("正在上传视频到reccloud进行语音转文字...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # Reccloud上传API
    upload_url = "https://api.reccloud.cn/v1/task/create"

    try:
        with open(video_path, 'rb') as video_file:
            files = {
                'file': (os.path.basename(video_path), video_file, 'video/mp4')
            }
            data = {
                'type': 'speech_to_text',
                'config': json.dumps({
                    'enable_highlight': True,
                    'enable_seperate': True,
                    'enable_translate': False
                })
            }

            response = requests.post(
                upload_url, files=files, data=data, headers=headers)

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    task_id = result['data']['task_id']
                    print(f"视频上传成功，任务ID: {task_id}")
                    return task_id
                else:
                    print(f"上传失败: {result.get('msg', '未知错误')}")
                    return None
            else:
                print(f"上传请求失败，状态码: {response.status_code}")
                return None
    except Exception as e:
        print(f"上传过程中出现错误: {e}")
        return None


def wait_for_reccloud_completion(task_id, timeout=600):
    """等待reccloud处理完成"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    status_url = "https://api.reccloud.cn/v1/task/status"

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            params = {'task_id': task_id}
            response = requests.get(status_url, params=params, headers=headers)

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    status = result['data']['status']

                    if status == 'completed':
                        print("处理完成")
                        return result['data']
                    elif status == 'failed':
                        print(
                            f"处理失败: {result['data'].get('fail_reason', '未知错误')}")
                        return None
                    elif status == 'processing':
                        print("正在处理中...")
                        time.sleep(10)  # 等待10秒再查询
                        continue
                    else:
                        print(f"未知状态: {status}")
                        return None
                else:
                    print(f"查询状态失败: {result.get('msg', '未知错误')}")
                    return None
            else:
                print(f"查询状态请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"查询状态过程中出现错误: {e}")
            time.sleep(5)

    print("处理超时")
    return None


def get_reccloud_result(task_id):
    """获取reccloud处理结果"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    result_url = "https://api.reccloud.cn/v1/task/result"
    params = {'task_id': task_id}

    try:
        response = requests.get(result_url, params=params, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data']
            else:
                print(f"获取结果失败: {result.get('msg', '未知错误')}")
                return None
        else:
            print(f"获取结果请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取结果过程中出现错误: {e}")
        return None


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

    print(f"Markdown文档已保存到: {filepath}")
    return filepath


def process_xiaohongshu_link(xhs_url):
    """
    处理小红书链接的完整流程
    """
    print("开始处理小红书链接...")
    print(f"小红书链接: {xhs_url}")

    try:
        # 1. 下载视频（使用yt-dlp）
        print("步骤1: 下载小红书视频...")
        video_path = download_video_with_yt_dlp(xhs_url)
        if not video_path:
            print("无法下载视频，请检查链接有效性或网络连接")
            return False

        # 2. 上传到reccloud进行语音转文字
        print("步骤2: 上传到reccloud进行语音转文字...")
        task_id = upload_video_to_reccloud_api(video_path)
        if not task_id:
            print("上传失败")
            return False

        # 3. 等待处理完成
        print("步骤3: 等待处理完成...")
        status_data = wait_for_reccloud_completion(task_id)
        if not status_data:
            print("处理失败或超时")
            return False

        # 4. 获取处理结果
        print("步骤4: 获取处理结果...")
        content_data = get_reccloud_result(task_id)
        if not content_data:
            print("获取结果失败")
            return False

        # 5. 保存为Markdown文档
        save_as_markdown(content_data)

        # 6. 清理临时文件
        try:
            os.remove(video_path)
            temp_dir = os.path.dirname(video_path)
            os.rmdir(temp_dir)
        except:
            pass  # 忽略清理错误

        print("处理完成！")
        return True

    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("使用方法: python xiaohongshu_api_processor.py <小红书链接>")
        print("示例: python xiaohongshu_api_processor.py https://www.xiaohongshu.com/explore/xxx")
        sys.exit(1)

    xhs_link = sys.argv[1]

    success = process_xiaohongshu_link(xhs_link)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
