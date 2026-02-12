#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析hellotik.app网站的真实API调用
通过模拟浏览器行为获取真实的API端点和请求格式
"""

import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def analyze_hellotik_api():
    """分析hellotik.app的真实API调用"""
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # 访问小红书下载页面
        print("访问hellotik.app小红书页面...")
        driver.get("https://www.hellotik.app/zh/rednote")
        
        # 等待页面加载
        time.sleep(3)
        
        # 查找输入框和按钮
        print("查找页面元素...")
        
        # 可能的输入框选择器
        input_selectors = [
            'input[type="text"]',
            'input[placeholder*="链接"]',
            'input[placeholder*="URL"]',
            'textarea',
            '#url-input',
            '.url-input'
        ]
        
        input_element = None
        for selector in input_selectors:
            try:
                input_element = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"找到输入框: {selector}")
                break
            except:
                continue
                
        if not input_element:
            print("未找到输入框")
            return None
            
        # 输入测试URL
        test_url = "https://www.xiaohongshu.com/explore/693a701a000000001e028c47"
        input_element.clear()
        input_element.send_keys(test_url)
        print(f"输入测试URL: {test_url}")
        
        # 查找提交按钮
        button_selectors = [
            'button[type="submit"]',
            'button:contains("下载")',
            'button:contains("Download")',
            '.download-btn',
            '#download-btn'
        ]
        
        button_element = None
        for selector in button_selectors:
            try:
                if ':contains(' in selector:
                    # XPath查找
                    xpath = f"//button[contains(text(), '下载') or contains(text(), 'Download')]"
                    button_element = driver.find_element(By.XPATH, xpath)
                else:
                    button_element = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"找到按钮: {selector}")
                break
            except:
                continue
                
        if not button_element:
            print("未找到下载按钮")
            return None
            
        # 监听网络请求
        print("开始监听网络请求...")
        
        # 启用网络日志
        driver.execute_cdp_cmd('Network.enable', {})
        
        # 点击下载按钮
        button_element.click()
        print("点击下载按钮")
        
        # 等待网络请求
        time.sleep(5)
        
        # 获取网络日志
        logs = driver.get_log('performance')
        
        api_calls = []
        for log in logs:
            message = json.loads(log['message'])
            if message['message']['method'] == 'Network.responseReceived':
                response = message['message']['params']['response']
                url = response['url']
                
                # 查找API调用
                if 'api' in url.lower() or 'download' in url.lower():
                    api_calls.append({
                        'url': url,
                        'method': response.get('method', 'GET'),
                        'status': response['status'],
                        'headers': response['headers']
                    })
                    print(f"发现API调用: {url}")
                    
        return api_calls
        
    except Exception as e:
        print(f"分析失败: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

def manual_api_analysis():
    """手动分析API调用模式"""
    print("手动分析hellotik.app API调用模式...")
    
    # 基于观察到的网络请求模式
    test_url = "https://www.xiaohongshu.com/explore/693a701a000000001e028c47"
    
    # 可能的API端点
    potential_apis = [
        "https://api.hellotik.app/download",
        "https://hellotik.app/api/v1/download", 
        "https://hellotik.app/api/rednote/download",
        "https://www.hellotik.app/api/download",
        "https://backend.hellotik.app/download"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Referer': 'https://www.hellotik.app/zh/rednote',
        'Origin': 'https://www.hellotik.app'
    }
    
    # 不同的请求格式
    payloads = [
        {"url": test_url},
        {"requestURL": test_url},
        {"link": test_url},
        {"videoUrl": test_url},
        {
            "url": test_url,
            "platform": "xiaohongshu"
        },
        {
            "requestURL": test_url,
            "isMobile": False,
            "platform": "rednote"
        }
    ]
    
    for api in potential_apis:
        for payload in payloads:
            try:
                print(f"\n尝试API: {api}")
                print(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
                
                response = requests.post(api, json=payload, headers=headers, timeout=10)
                
                print(f"状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"JSON响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                        except:
                            print("JSON解析失败")
                    elif 'video' in content_type or 'octet-stream' in content_type:
                        print(f"检测到视频文件，大小: {len(response.content)} 字节")
                        return {
                            'api': api,
                            'payload': payload,
                            'response_type': 'video_file',
                            'size': len(response.content)
                        }
                    else:
                        print(f"响应内容: {response.text[:200]}")
                        
                elif response.status_code == 404:
                    print("API端点不存在")
                else:
                    print(f"请求失败: {response.status_code}")
                    
            except Exception as e:
                print(f"请求异常: {e}")
                
    return None

if __name__ == "__main__":
    print("=== 分析hellotik.app真实API调用 ===")
    
    # 方法1: 使用Selenium分析
    print("\n方法1: 使用浏览器自动化分析...")
    try:
        api_calls = analyze_hellotik_api()
        if api_calls:
            print("发现的API调用:")
            for call in api_calls:
                print(json.dumps(call, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"浏览器分析失败: {e}")
    
    # 方法2: 手动尝试不同API格式
    print("\n方法2: 手动尝试不同API格式...")
    result = manual_api_analysis()
    
    if result:
        print(f"\n✅ 找到有效API:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n❌ 未找到有效的API端点")
