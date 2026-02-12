#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书视频转文字工具 - 纯命令行版本
不依赖任何GUI库，只要python能跑就行
"""

import requests
import json
import os
import time
import hashlib
from datetime import datetime

# 创建目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

for d in [VIDEO_DIR, OUTPUT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

def main():
    print("=" * 60)
    print("小红书视频转文字工具")
    print("=" * 60)
    
    # 获取用户输入
    link = input("请输入小红书链接: ").strip()
    
    if not link:
        print("错误: 链接不能为空")
        return
        
    # 更宽松的链接验证
    if not ('xiaohongshu.com' in link.lower() and ('http' in link.lower() or 'www.' in link.lower())):
        print("错误: 请输入有效的小红书链接")
        print("提示: 链接应该包含 xiaohongshu.com")
        return
    
    print(f"\n开始处理链接: {link}")
    
    try:
        # 步骤1: 下载视频
        print("\n" + "=" * 40)
        print("步骤1: 下载视频")
        print("=" * 40)
        
        video_url = download_video(link)
        if not video_url:
            print("❌ 下载视频失败")
            return
            
        print(f"✅ 获取到视频URL: {video_url}")
        
        # 步骤2: 保存视频
        print("\n" + "=" * 40)
        print("步骤2: 保存视频")
        print("=" * 40)
        
        video_filename = save_video(video_url, link)
        if not video_filename:
            print("❌ 保存视频失败")
            return
            
        print(f"✅ 视频已保存: {video_filename}")
        
        # 步骤3: 语音转文字
        print("\n" + "=" * 40)
        print("步骤3: 语音转文字")
        print("=" * 40)
        
        result_data = speech_to_text(video_filename)
        if not result_data:
            print("❌ 语音转文字失败")
            return
            
        print("✅ 语音转文字完成")
        
        # 步骤4: 生成文档
        print("\n" + "=" * 40)
        print("步骤4: 生成文档")
        print("=" * 40)
        
        doc_filename = generate_document(result_data, link)
        if not doc_filename:
            print("❌ 生成文档失败")
            return
            
        print(f"✅ 文档已生成: {doc_filename}")
        
        print("\n" + "=" * 60)
        print("🎉 处理完成!")
        print(f"📄 文档位置: {doc_filename}")
        print(f"📁 视频文件: {video_filename}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 处理过程中出现错误: {e}")

def download_video(link):
    """下载视频"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://hellotik.app/',
            'Origin': 'https://hellotik.app'
        }
        
        payload = {
            "requestURL": link,
            "isMobile": "false",
            "isoCode": "HK",
            "adType": "adsense",
            "uwx_id": "uwx_350696y5juIO",
            "successCount": "0",
            "totalSuccessCount": "2",
            "firstSuccessDate": "2026-01-10",
            "time": int(time.time()),
            "key": "xaq8pkc7"
        }
        
        endpoints = [
            "https://api.hellotik.app/api/download",
            "https://hellotik.app/api/video",
            "https://hellotik.app/api/fetch"
        ]
        
        for endpoint in endpoints:
            try:
                print(f"尝试API端点: {endpoint}")
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"API响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    # 提取视频URL
                    for key in ['video_url', 'download_url', 'url']:
                        if key in result:
                            return result[key]
                        elif 'data' in result and isinstance(result['data'], dict) and key in result['data']:
                            return result['data'][key]
                            
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"端点 {endpoint} 请求失败: {e}")
                continue
                
        print("所有API端点都失败")
        return None
        
    except Exception as e:
        print(f"下载视频异常: {e}")
        return None

def save_video(video_url, link):
    """保存视频"""
    try:
        url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        video_filename = os.path.join(VIDEO_DIR, f"video_{url_hash}_{timestamp}.mp4")
        
        print(f"下载视频: {video_url}")
        print(f"保存到: {video_filename}")
        
        response = requests.get(video_url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(video_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 显示下载进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"下载进度: {progress:.1f}%", end='\r')
        
        print(f"\n视频保存成功: {video_filename}")
        return video_filename
        
    except Exception as e:
        print(f"保存视频异常: {e}")
        return None

def speech_to_text(video_filename):
    """语音转文字"""
    try:
        print("上传视频到reccloud...")
        
        headers = {
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
                    'enable_translate': False,
                    'language': 'zh-cn'
                })
            }
            
            response = requests.post("https://api.reccloud.cn/v1/task/create",
                                    files=files, data=data, headers=headers, timeout=60)
            
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0 and 'data' in result:
                task_id = result['data']['task_id']
                print(f"上传成功，任务ID: {task_id}")
                
                # 等待处理完成
                if wait_for_result(task_id):
                    return get_result(task_id)
                else:
                    return None
            else:
                print(f"上传失败: {result.get('msg', '未知错误')}")
                return None
        else:
            print(f"上传请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"语音转文字异常: {e}")
        return None

def wait_for_result(task_id, timeout=600):
    """等待处理结果"""
    print("等待处理完成...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"https://api.reccloud.cn/v1/task/status?task_id={task_id}",
                                   headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and 'data' in result:
                    status = result['data'].get('status', 'unknown')
                    progress = result['data'].get('progress', 0)
                    
                    print(f"处理状态: {status}, 进度: {progress}%")
                    
                    if status == 'completed':
                        print("处理完成")
                        return True
                    elif status == 'failed':
                        fail_reason = result['data'].get('fail_reason', '未知错误')
                        print(f"处理失败: {fail_reason}")
                        return False
                    
                    time.sleep(10)
                else:
                    print(f"状态查询失败: {result.get('msg', '未知错误')}")
                    return False
            else:
                print(f"状态查询请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"状态查询异常: {e}")
            return False
            
    print("处理超时")
    return False

def get_result(task_id):
    """获取处理结果"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(f"https://api.reccloud.cn/v1/task/result?task_id={task_id}",
                               headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0 and 'data' in result:
                print("获取结果成功")
                return result['data']
            else:
                print(f"获取结果失败: {result.get('msg', '未知错误')}")
                return None
        else:
            print(f"结果请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"获取结果异常: {e}")
        return None

def generate_document(result_data, link):
    """生成文档"""
    try:
        url_hash = hashlib.md5(link.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        doc_filename = os.path.join(OUTPUT_DIR, f"小红书视频分析_{url_hash}_{timestamp}.md")
        
        # 提取内容
        segments = result_data.get('segments', [])
        transcript = ""
        
        for segment in segments:
            start_time = segment.get('start_time', 0)
            text = segment.get('text', '')
            timestamp_str = time.strftime('%H:%M:%S', time.gmtime(start_time))
            transcript += f"- [{timestamp_str}] {text}\n"
        
        # 获取AI摘要
        ai_summary = result_data.get('ai_summary', result_data.get('summary', ''))
        
        # 创建Markdown内容
        md_content = f"""# 小红书视频内容分析

## 视频信息
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 原始链接: {link}
- URL哈希: {url_hash}

## 📝 语音转文字内容

{transcript}

## 🤖 AI智能分析摘要

{ai_summary}

---
*由小红书视频分析工具生成*
"""
        
        with open(doc_filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"文档生成成功: {doc_filename}")
        return doc_filename
        
    except Exception as e:
        print(f"生成文档异常: {e}")
        return None

if __name__ == "__main__":
    main()
