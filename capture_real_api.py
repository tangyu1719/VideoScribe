#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取hellotik.app的真实API调用
使用Selenium监听网络请求，获取真实的API端点和请求格式
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def capture_hellotik_api():
    """抓取hellotik.app的真实API调用"""
    
    # Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 启用性能日志
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = None
    try:
        print("启动Chrome浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 启用网络域
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Runtime.enable', {})
        
        print("访问hellotik.app小红书页面...")
        driver.get("https://www.hellotik.app/zh/rednote")
        
        # 等待页面加载
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        print("查找输入框...")
        input_element = None
        
        # 尝试多种选择器
        selectors = [
            'input[type="text"]',
            'input[placeholder*="链接"]',
            'input[placeholder*="URL"]',
            'input[placeholder*="url"]',
            'textarea'
        ]
        
        for selector in selectors:
            try:
                input_element = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"找到输入框: {selector}")
                break
            except:
                continue
                
        if not input_element:
            print("未找到输入框，查看页面结构...")
            print("页面标题:", driver.title)
            print("页面URL:", driver.current_url)
            
            # 查找所有input元素
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"找到 {len(inputs)} 个input元素")
            for i, inp in enumerate(inputs):
                print(f"Input {i}: type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}")
                if inp.get_attribute('type') in ['text', 'url'] or inp.is_displayed():
                    input_element = inp
                    print(f"使用Input {i}")
                    break
                    
        if not input_element:
            raise Exception("未找到可用的输入框")
            
        # 输入测试链接
        test_url = "https://www.xiaohongshu.com/discovery/item/693a701a000000001e028c47"
        print(f"输入测试链接: {test_url}")
        input_element.clear()
        input_element.send_keys(test_url)
        
        print("查找下载按钮...")
        button_element = None
        
        # 尝试多种按钮选择器
        button_selectors = [
            'button[type="submit"]',
            'button:contains("下载")',
            'button:contains("Download")',
            '.download-btn',
            '#download-btn'
        ]
        
        for selector in button_selectors:
            try:
                if ':contains(' in selector:
                    xpath = "//button[contains(text(), '下载') or contains(text(), 'Download') or contains(text(), 'download')]"
                    button_element = driver.find_element(By.XPATH, xpath)
                else:
                    button_element = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"找到按钮: {selector}")
                break
            except:
                continue
                
        if not button_element:
            # 查找所有按钮
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"找到 {len(buttons)} 个button元素")
            for i, btn in enumerate(buttons):
                text = btn.text.lower()
                print(f"Button {i}: text='{btn.text}', visible={btn.is_displayed()}")
                if btn.is_displayed() and any(word in text for word in ['下载', 'download', '获取', 'get', '解析']):
                    button_element = btn
                    print(f"使用Button {i}: {btn.text}")
                    break
                    
        if not button_element:
            raise Exception("未找到下载按钮")
            
        print("开始监听网络请求...")
        
        # 清空之前的日志
        driver.get_log('performance')
        
        # 点击下载按钮
        print("点击下载按钮...")
        driver.execute_script("arguments[0].click();", button_element)
        
        # 等待网络请求
        print("等待网络请求...")
        time.sleep(5)
        
        # 获取网络日志
        logs = driver.get_log('performance')
        
        api_requests = []
        for log in logs:
            try:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.requestWillBeSent':
                    request = message['message']['params']['request']
                    url = request['url']
                    method = request['method']
                    
                    # 过滤API请求
                    if ('api' in url.lower() or 
                        'download' in url.lower() or 
                        ('hellotik' in url and method == 'POST')):
                        
                        api_info = {
                            'url': url,
                            'method': method,
                            'headers': request.get('headers', {}),
                            'postData': request.get('postData', '')
                        }
                        api_requests.append(api_info)
                        print(f"\n发现API请求:")
                        print(f"URL: {url}")
                        print(f"Method: {method}")
                        if 'postData' in request:
                            print(f"POST Data: {request['postData']}")
                            
            except Exception as e:
                continue
                
        # 获取响应
        for log in logs:
            try:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response['url']
                    
                    if ('api' in url.lower() or 'download' in url.lower()):
                        print(f"\nAPI响应:")
                        print(f"URL: {url}")
                        print(f"Status: {response['status']}")
                        print(f"Headers: {response.get('headers', {})}")
                        
            except Exception as e:
                continue
                
        if api_requests:
            print(f"\n✅ 找到 {len(api_requests)} 个API请求")
            return api_requests
        else:
            print("\n❌ 未找到API请求")
            
            # 尝试查看页面变化
            print("检查页面变化...")
            time.sleep(2)
            
            # 查找可能的下载链接
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and ('.mp4' in href or 'video' in href.lower()):
                    print(f"找到可能的下载链接: {href}")
                    
            return None
            
    except Exception as e:
        print(f"抓取失败: {e}")
        return None
    finally:
        if driver:
            print("关闭浏览器")
            driver.quit()

if __name__ == "__main__":
    print("=== 抓取hellotik.app真实API调用 ===")
    api_requests = capture_hellotik_api()
    
    if api_requests:
        print("\n=== 抓取结果 ===")
        for i, req in enumerate(api_requests):
            print(f"\nAPI请求 {i+1}:")
            print(json.dumps(req, indent=2, ensure_ascii=False))
    else:
        print("\n未能抓取到API请求，可能需要手动分析网站")
