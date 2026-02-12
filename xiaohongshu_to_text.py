import requests
import json
import os
import sys
import time
import tempfile


def upload_video_to_reccloud_api(video_path):
    """使用reccloud API上传视频"""
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


def save_content_to_file(content_data, output_dir="csdn/待阅览"):
    """将内容保存到文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成文件名
    timestamp = int(time.time())
    filename = f"小红书视频转文字_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    # 提取内容并格式化
    segments = content_data.get('segments', [])
    transcript = ""
    for segment in segments:
        start_time = segment.get('start_time', 0)
        text = segment.get('text', '')
        timestamp_str = time.strftime('%H:%M:%S', time.gmtime(start_time))
        transcript += f"[{timestamp_str}] {text}\n"

    # 获取AI摘要
    ai_summary = content_data.get(
        'ai_summary', content_data.get('summary', ''))

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("逐字稿：\n")
        f.write(transcript)
        f.write("\n\n=== AI智能解析文本 ===\n")
        f.write(ai_summary)

    print(f"内容已保存到: {filepath}")
    return filepath


def process_video_file(video_path):
    """
    处理视频文件的完整流程
    """
    print("开始处理视频转文字...")
    print(f"视频文件: {video_path}")

    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        return False

    try:
        # 1. 上传到reccloud进行语音转文字
        print("步骤1: 正在上传到reccloud进行语音转文字...")
        task_id = upload_video_to_reccloud_api(video_path)
        if not task_id:
            print("上传失败")
            return False

        # 2. 等待处理完成
        print("步骤2: 正在等待处理完成...")
        status_data = wait_for_reccloud_completion(task_id)
        if not status_data:
            print("处理失败或超时")
            return False

        # 3. 获取处理结果
        print("步骤3: 正在获取处理结果...")
        content_data = get_reccloud_result(task_id)
        if not content_data:
            print("获取结果失败")
            return False

        # 4. 保存结果
        save_content_to_file(content_data)

        print("处理完成！")
        return True

    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("使用方法:")
        print("1. 处理已下载的视频文件: python xiaohongshu_to_text.py <视频文件路径>")
        print("2. 从头开始处理小红书视频:")
        print("   a. 手动从小红书链接下载视频到本地")
        print("   b. 运行此脚本处理视频文件")
        sys.exit(1)

    input_path = sys.argv[1]

    # 检查是否为文件路径
    if os.path.isfile(input_path):
        # 处理本地视频文件
        success = process_video_file(input_path)
    else:
        print(f"文件不存在: {input_path}")
        print("请确保视频文件已下载到本地后再运行此脚本")
        sys.exit(1)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
