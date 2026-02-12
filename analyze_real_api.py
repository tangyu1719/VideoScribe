#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析hellotik.app的真实工作方式
通过分析JavaScript代码找到正确的API调用方法
"""

import requests
import re
import json

def analyze_hellotik_website():
    """分析网站的真实工作方式"""
    
    print("=== 分析hellotik.app网站 ===")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    })
    
    try:
        # 1. 获取主页面
        print("1. 获取主页面...")
        response = session.get("https://www.hellotik.app/zh/rednote", timeout=15)
        
        if response.status_code != 200:
            print(f"❌ 获取主页面失败: {response.status_code}")
            return
            
        html_content = response.text
        print(f"✅ 主页面获取成功，长度: {len(html_content)}")
        
        # 2. 分析JavaScript文件
        print("\n2. 分析JavaScript文件...")
        
        # 提取所有JavaScript文件URL
        js_urls = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html_content)
        
        print(f"找到 {len(js_urls)} 个JavaScript文件")
        
        # 分析主要的JS文件
        for i, js_url in enumerate(js_urls[:5]):  # 只分析前5个
            if js_url.startswith('/'):
                full_js_url = f"https://www.hellotik.app{js_url}"
            else:
                full_js_url = js_url
                
            print(f"\n分析JS文件 {i+1}: {full_js_url}")
            
            try:
                js_response = session.get(full_js_url, timeout=10)
                if js_response.status_code == 200:
                    js_content = js_response.text
                    
                    # 查找API调用模式
                    api_patterns = [
                        r'fetch\s*\(\s*["\']([^"\']+)["\']',
                        r'axios\s*\.\s*post\s*\(\s*["\']([^"\']+)["\']',
                        r'\.post\s*\(\s*["\']([^"\']+)["\']',
                        r'/api/[^"\s\']+',
                        r'endpoint\s*:\s*["\']([^"\']+)["\']',
                    ]
                    
                    found_apis = set()
                    for pattern in api_patterns:
                        matches = re.findall(pattern, js_content, re.IGNORECASE)
                        for match in matches:
                            if 'api' in match.lower() or 'download' in match.lower():
                                found_apis.add(match)
                    
                    if found_apis:
                        print(f"  发现API端点: {list(found_apis)}")
                    
                    # 查找请求参数模式
                    param_patterns = [
                        r'\{\s*["\']?url["\']?\s*:\s*[^,}]+[,}]',
                        r'\{\s*["\']?requestURL["\']?\s*:\s*[^,}]+[,}]',
                        r'JSON\.stringify\s*\(\s*\{[^}]+\}',
                    ]
                    
                    for pattern in param_patterns:
                        matches = re.findall(pattern, js_content, re.IGNORECASE)
                        if matches:
                            print(f"  发现参数模式: {matches[:3]}")  # 只显示前3个
                    
                    # 查找关键函数
                    function_patterns = [
                        r'function\s+(\w*download\w*)\s*\(',
                        r'const\s+(\w*download\w*)\s*=',
                        r'(\w*download\w*)\s*:\s*function',
                    ]
                    
                    for pattern in function_patterns:
                        matches = re.findall(pattern, js_content, re.IGNORECASE)
                        if matches:
                            print(f"  发现下载函数: {matches}")
                            
            except Exception as e:
                print(f"  分析失败: {e}")
        
        # 3. 查找表单和按钮
        print("\n3. 分析表单结构...")
        
        # 查找表单
        forms = re.findall(r'<form[^>]*>(.*?)</form>', html_content, re.DOTALL | re.IGNORECASE)
        print(f"找到 {len(forms)} 个表单")
        
        for i, form in enumerate(forms):
            action = re.search(r'action=["\']([^"\']+)["\']', form, re.IGNORECASE)
            method = re.search(r'method=["\']([^"\']+)["\']', form, re.IGNORECASE)
            
            if action:
                print(f"  表单 {i+1}: action={action.group(1)}, method={method.group(1) if method else 'GET'}")
        
        # 查找按钮和点击事件
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', html_content, re.DOTALL | re.IGNORECASE)
        print(f"找到 {len(buttons)} 个按钮")
        
        for i, button in enumerate(buttons[:3]):  # 只显示前3个
            button_text = re.sub(r'<[^>]+>', '', button).strip()
            if button_text:
                print(f"  按钮 {i+1}: {button_text}")
        
        # 4. 查找内联JavaScript
        print("\n4. 分析内联JavaScript...")
        
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
        
        for i, script in enumerate(script_blocks):
            if len(script.strip()) > 100 and 'api' in script.lower():  # 只分析包含api的较长脚本
                print(f"\n内联脚本 {i+1} (包含API):")
                
                # 查找API调用
                api_calls = re.findall(r'fetch\s*\(\s*["\']([^"\']+)["\']', script, re.IGNORECASE)
                for call in api_calls:
                    print(f"  API调用: {call}")
                
                # 查找配置对象
                configs = re.findall(r'\{[^}]*["\']?url["\']?[^}]*\}', script)
                for config in configs[:2]:  # 只显示前2个
                    print(f"  配置对象: {config}")
        
        print("\n=== 分析完成 ===")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    analyze_hellotik_website()
