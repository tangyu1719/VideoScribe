#!/usr/bin/env python3
"""
测试API URL是否正确
"""
import requests
import json

def test_api():
    """直接测试火山引擎API"""
    
    # 从数据库读取配置
    import sys
    sys.path.insert(0, 'F:\\java\\AIOPS\\SuperBizAgent-release-2026-01-02\\demo_wendanghua')
    import db
    
    results = db.execute_query("SELECT * FROM llm_configs LIMIT 1")
    if not results:
        print("数据库中没有配置")
        return
    
    config = results[0]
    print("=" * 60)
    print("数据库配置:")
    print("=" * 60)
    for key, value in config.items():
        if 'key' in key.lower():
            print(f"{key}: {'*' * 10}")
        else:
            print(f"{key}: {value}")
    print("-" * 60)
    
    # 构建API URL
    base_url = config.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3')
    endpoint_id = config.get('endpoint_id', '')
    
    # 清理base_url，移除末尾的/responses等路径
    base_url = base_url.rstrip('/')
    if base_url.endswith('/responses'):
        base_url = base_url[:-10]  # 移除 /responses
    elif base_url.endswith('/chat/completions'):
        base_url = base_url[:-17]  # 移除 /chat/completions
    
    if endpoint_id:
        api_url = f"{base_url}/ep/{endpoint_id}/chat/completions"
    else:
        api_url = f"{base_url}/chat/completions"
    
    print(f"\nAPI URL: {api_url}")
    
    # 测试API是否可访问
    api_key = config.get('api_key', '')
    if not api_key:
        print("API Key为空，无法测试")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.get('model', 'doubao-seed-1.6-flash'),
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False,
        "max_tokens": 100
    }
    
    print(f"\n发送测试请求...")
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ API调用成功!")
            print(f"回复: {result['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"✗ API调用失败")
            print(f"响应: {response.text[:500]}")
    
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_api()
