#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析hellotik.app的JavaScript代码，找到真实的API调用逻辑
"""

import requests
import re
import json
from urllib.parse import urljoin

def analyze_javascript_files():
    """分析JavaScript文件中的API调用"""
    
    print("=== 分析hellotik.app的JavaScript代码 ===")
    
    try:
        # 获取主页面
        response = requests.get("https://www.hellotik.app/zh/rednote", timeout=15)
        html_content = response.text
        
        print("✅ 成功获取页面内容")
        
        # 提取所有JavaScript文件
        js_patterns = [
            r'src=["\']([^"\']+\.js[^"\']*)["\']',
            r'href=["\']([^"\']+\.js[^"\']*)["\']'
        ]
        
        js_files = set()
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if match.startswith('/'):
                    js_url = f"https://www.hellotik.app{match}"
                elif match.startswith('http'):
                    js_url = match
                else:
                    js_url = f"https://www.hellotik.app/{match}"
                js_files.add(js_url)
        
        print(f"发现 {len(js_files)} 个JavaScript文件")
        
        # 分析每个JS文件
        api_calls = []
        for js_url in list(js_files)[:10]:  # 限制分析前10个文件
            print(f"\n分析: {js_url}")
            
            try:
                js_response = requests.get(js_url, timeout=10)
                js_content = js_response.text
                
                # 查找API调用模式
                api_patterns = [
                    # fetch调用
                    r'fetch\s*\(\s*["\']([^"\']+)["\']',
                    r'fetch\s*\(\s*`([^`]+)`',
                    
                    # axios调用
                    r'axios\s*\.\s*post\s*\(\s*["\']([^"\']+)["\']',
                    r'axios\s*\.\s*get\s*\(\s*["\']([^"\']+)["\']',
                    
                    # 一般的HTTP调用
                    r'\.post\s*\(\s*["\']([^"\']+)["\']',
                    r'\.get\s*\(\s*["\']([^"\']+)["\']',
                    
                    # API端点定义
                    r'["\']([^"\']*api[^"\']*)["\']',
                    r'["\']([^"\']*download[^"\']*)["\']',
                    
                    # URL常量
                    r'const\s+\w*[Uu][Rr][Ll]\w*\s*=\s*["\']([^"\']+)["\']',
                    r'let\s+\w*[Uu][Rr][Ll]\w*\s*=\s*["\']([^"\']+)["\']',
                ]
                
                found_apis = set()
                for pattern in api_patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    for match in matches:
                        if ('api' in match.lower() or 
                            'download' in match.lower() or
                            '/rednote' in match.lower() or
                            match.startswith('/')):
                            found_apis.add(match)
                
                if found_apis:
                    print(f"  发现API端点:")
                    for api in found_apis:
                        print(f"    - {api}")
                        api_calls.append({
                            'source': js_url,
                            'endpoint': api
                        })
                
                # 查找请求参数模式
                param_patterns = [
                    r'\{\s*["\']?url["\']?\s*:\s*[^,}]+',
                    r'\{\s*["\']?requestURL["\']?\s*:\s*[^,}]+',
                    r'\{\s*["\']?link["\']?\s*:\s*[^,}]+',
                    r'JSON\.stringify\s*\(\s*\{[^}]+\}',
                ]
                
                for pattern in param_patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    if matches:
                        print(f"  发现参数模式:")
                        for match in matches[:3]:  # 只显示前3个
                            print(f"    - {match}")
                
            except Exception as e:
                print(f"  分析失败: {e}")
        
        # 在主页面HTML中查找内联JavaScript
        print(f"\n分析页面内联JavaScript...")
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
        
        for i, script in enumerate(script_blocks):
            if len(script.strip()) > 100:  # 只分析较长的脚本
                print(f"\n内联脚本 {i+1}:")
                
                # 查找API调用
                for pattern in [
                    r'fetch\s*\(\s*["\']([^"\']+)["\']',
                    r'\.post\s*\(\s*["\']([^"\']+)["\']',
                    r'["\']([^"\']*api[^"\']*)["\']',
                ]:
                    matches = re.findall(pattern, script, re.IGNORECASE)
                    for match in matches:
                        if 'api' in match.lower() or 'download' in match.lower():
                            print(f"  发现API: {match}")
                            api_calls.append({
                                'source': 'inline_script',
                                'endpoint': match
                            })
        
        return api_calls
        
    except Exception as e:
        print(f"分析失败: {e}")
        return []

def test_discovered_apis(api_calls):
    """测试发现的API端点"""
    
    if not api_calls:
        print("未发现API端点")
        return
    
    print(f"\n=== 测试发现的 {len(api_calls)} 个API端点 ===")
    
    test_url = "https://www.xiaohongshu.com/discovery/item/693a701a000000001e028c47"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Referer': 'https://www.hellotik.app/zh/rednote',
        'Origin': 'https://www.hellotik.app'
    }
    
    # 去重API端点
    unique_endpoints = list(set([call['endpoint'] for call in api_calls]))
    
    for endpoint in unique_endpoints:
        print(f"\n测试端点: {endpoint}")
        
        # 构造完整URL
        if endpoint.startswith('/'):
            full_url = f"https://www.hellotik.app{endpoint}"
        elif endpoint.startswith('http'):
            full_url = endpoint
        else:
            full_url = f"https://www.hellotik.app/{endpoint}"
        
        # 测试不同的请求格式
        payloads = [
            {"url": test_url},
            {"requestURL": test_url},
            {"link": test_url, "platform": "rednote"},
        ]
        
        for payload in payloads:
            try:
                response = requests.post(full_url, json=payload, headers=headers, timeout=10)
                print(f"  POST {json.dumps(payload, ensure_ascii=False)} -> {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"  ✅ JSON响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                        except:
                            print("  JSON解析失败")
                    elif 'video' in content_type:
                        print(f"  ✅ 视频文件: {len(response.content)} 字节")
                    else:
                        print(f"  响应: {response.text[:100]}")
                        
            except Exception as e:
                print(f"  请求失败: {e}")

def main():
    print("=== HelloTik.app JavaScript分析工具 ===")
    
    # 分析JavaScript文件
    api_calls = analyze_javascript_files()
    
    # 测试发现的API
    test_discovered_apis(api_calls)
    
    # 汇总结果
    print(f"\n=== 分析结果汇总 ===")
    if api_calls:
        print(f"发现 {len(api_calls)} 个可能的API调用:")
        for call in api_calls:
            print(f"  - {call['endpoint']} (来源: {call['source']})")
    else:
        print("未发现明显的API调用模式")
        print("建议：")
        print("1. 手动使用浏览器开发者工具抓包")
        print("2. 分析网站可能使用的第三方服务")
        print("3. 检查是否有WebSocket连接")

if __name__ == "__main__":
    main()
