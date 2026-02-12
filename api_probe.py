#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloTik.app API探测工具
通过系统性测试不同的API端点和参数组合，找到真实的API调用方式
"""

import requests
import json
import time
import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(xiaohongshu_url):
    """从小红书链接中提取视频ID"""
    # 从URL中提取ID
    match = re.search(r'/item/([a-f0-9]+)', xiaohongshu_url)
    if match:
        return match.group(1)
    
    match = re.search(r'/explore/([a-f0-9]+)', xiaohongshu_url)
    if match:
        return match.group(1)
    
    return None

def test_api_endpoints():
    """测试不同的API端点"""
    
    test_url = "https://www.xiaohongshu.com/discovery/item/693a701a000000001e028c47"
    video_id = extract_video_id(test_url)
    
    print(f"测试URL: {test_url}")
    print(f"提取的视频ID: {video_id}")
    
    # 基础请求头
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.hellotik.app/zh/rednote',
        'Origin': 'https://www.hellotik.app'
    }
    
    # 测试的API端点列表
    api_endpoints = [
        # Next.js API路由
        "https://www.hellotik.app/api/download",
        "https://www.hellotik.app/api/rednote",
        "https://www.hellotik.app/api/parse",
        "https://www.hellotik.app/api/video",
        
        # 可能的内部API
        "https://api.hellotik.app/download",
        "https://api.hellotik.app/rednote",
        "https://api.hellotik.app/parse",
        
        # 基于观察到的请求模式
        "https://www.hellotik.app/parse-stat",
        "https://www.hellotik.app/_next/static/chunks/parse-stat",
    ]
    
    # 不同的请求参数组合
    payload_variations = [
        # 基础格式
        {"url": test_url},
        {"requestURL": test_url},
        {"link": test_url},
        {"videoUrl": test_url},
        
        # 带平台信息
        {"url": test_url, "platform": "rednote"},
        {"url": test_url, "platform": "xiaohongshu"},
        {"requestURL": test_url, "platform": "rednote"},
        
        # 带视频ID
        {"id": video_id},
        {"videoId": video_id},
        {"itemId": video_id},
        
        # 复杂格式（基于之前的观察）
        {
            "requestURL": test_url,
            "isMobile": False,
            "platform": "rednote"
        },
        
        # 模拟表单提交
        {"url": test_url, "type": "video", "format": "mp4"},
    ]
    
    results = []
    
    for endpoint in api_endpoints:
        print(f"\n=== 测试端点: {endpoint} ===")
        
        # 测试GET请求
        try:
            print("尝试GET请求...")
            response = requests.get(endpoint, headers=base_headers, timeout=10)
            print(f"GET状态码: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                print(f"Content-Type: {content_type}")
                
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"JSON响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                        results.append({
                            'endpoint': endpoint,
                            'method': 'GET',
                            'status': response.status_code,
                            'response': data
                        })
                    except:
                        print("JSON解析失败")
                else:
                    print(f"响应内容: {response.text[:200]}")
                    
        except Exception as e:
            print(f"GET请求失败: {e}")
        
        # 测试POST请求
        for i, payload in enumerate(payload_variations):
            try:
                print(f"\n尝试POST请求 {i+1}/{len(payload_variations)}: {json.dumps(payload, ensure_ascii=False)}")
                
                headers = base_headers.copy()
                headers['Content-Type'] = 'application/json'
                
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                print(f"POST状态码: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"✅ 成功! JSON响应: {json.dumps(data, ensure_ascii=False)[:300]}")
                            results.append({
                                'endpoint': endpoint,
                                'method': 'POST',
                                'payload': payload,
                                'status': response.status_code,
                                'response': data
                            })
                        except:
                            print("JSON解析失败")
                    elif 'video' in content_type or 'octet-stream' in content_type:
                        print(f"✅ 检测到视频文件! 大小: {len(response.content)} 字节")
                        results.append({
                            'endpoint': endpoint,
                            'method': 'POST',
                            'payload': payload,
                            'status': response.status_code,
                            'response_type': 'video_file',
                            'size': len(response.content)
                        })
                    else:
                        response_text = response.text[:200]
                        if 'html' not in content_type:
                            print(f"其他响应: {response_text}")
                            
                elif response.status_code == 404:
                    print("端点不存在")
                elif response.status_code == 405:
                    print("方法不允许")
                else:
                    print(f"请求失败: {response.status_code}")
                    
            except Exception as e:
                print(f"POST请求失败: {e}")
                
        time.sleep(0.5)  # 避免请求过快
    
    return results

def analyze_page_structure():
    """分析页面结构，寻找API调用线索"""
    
    print("\n=== 分析页面结构 ===")
    
    try:
        response = requests.get("https://www.hellotik.app/zh/rednote", timeout=10)
        html_content = response.text
        
        # 查找可能的API端点
        api_patterns = [
            r'/api/[^"\s]+',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.[^(]+\(["\']([^"\']+)["\']',
            r'\.post\(["\']([^"\']+)["\']',
            r'endpoint["\']?\s*:\s*["\']([^"\']+)["\']'
        ]
        
        found_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if 'api' in match.lower() or 'download' in match.lower():
                    found_apis.add(match)
        
        if found_apis:
            print("在页面中发现可能的API端点:")
            for api in found_apis:
                print(f"  - {api}")
        else:
            print("未在页面源码中找到明显的API端点")
            
        # 查找JavaScript文件
        js_files = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html_content)
        print(f"\n发现 {len(js_files)} 个JavaScript文件")
        
        # 分析主要的JS文件
        for js_file in js_files[:3]:  # 只分析前3个
            if js_file.startswith('/'):
                js_url = f"https://www.hellotik.app{js_file}"
            else:
                js_url = js_file
                
            try:
                print(f"\n分析JS文件: {js_url}")
                js_response = requests.get(js_url, timeout=10)
                js_content = js_response.text
                
                # 在JS中查找API调用
                for pattern in api_patterns:
                    matches = re.findall(pattern, js_content)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0] if match[0] else match[1]
                        if 'api' in match.lower():
                            found_apis.add(match)
                            print(f"  发现API: {match}")
                            
            except Exception as e:
                print(f"  分析失败: {e}")
                
        return list(found_apis)
        
    except Exception as e:
        print(f"页面分析失败: {e}")
        return []

def main():
    print("=== HelloTik.app API探测工具 ===")
    
    # 1. 分析页面结构
    page_apis = analyze_page_structure()
    
    # 2. 测试API端点
    results = test_api_endpoints()
    
    # 3. 汇总结果
    print("\n" + "="*50)
    print("探测结果汇总")
    print("="*50)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 个有效响应:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['endpoint']}")
            print(f"   方法: {result['method']}")
            if 'payload' in result:
                print(f"   参数: {json.dumps(result['payload'], ensure_ascii=False)}")
            print(f"   状态: {result['status']}")
            if 'response' in result:
                response_str = json.dumps(result['response'], ensure_ascii=False)[:200]
                print(f"   响应: {response_str}")
    else:
        print("\n❌ 未找到有效的API响应")
        
    if page_apis:
        print(f"\n📄 页面中发现的API端点:")
        for api in page_apis:
            print(f"   - {api}")

if __name__ == "__main__":
    main()
