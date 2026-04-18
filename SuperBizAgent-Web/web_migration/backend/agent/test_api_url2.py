#!/usr/bin/env python3
"""
测试不同的API URL格式
"""
import requests
import sys
sys.path.insert(0, 'F:\\java\\AIOPS\\SuperBizAgent-release-2026-01-02\\demo_wendanghua')
import db

def test_api_url(api_url, api_key, model):
    """测试单个API URL"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False,
        "max_tokens": 100
    }
    
    print(f"\n测试URL: {api_url}")
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 成功!")
            print(f"回复: {result['choices'][0]['message']['content'][:50]}...")
            return True
        else:
            print(f"✗ 失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def main():
    # 从数据库读取配置
    results = db.execute_query("SELECT * FROM llm_configs LIMIT 1")
    if not results:
        print("数据库中没有配置")
        return
    
    config = results[0]
    api_key = config.get('api_key', '')
    endpoint_id = config.get('endpoint_id', '')
    model = config.get('model', '')
    
    print("=" * 60)
    print("测试不同的API URL格式")
    print("=" * 60)
    print(f"API Key: {'*' * 10}")
    print(f"Endpoint ID: {endpoint_id}")
    print(f"Model: {model}")
    
    base_urls = [
        "https://ark.cn-beijing.volces.com/api/v3",
        "https://ark.cn-beijing.volces.com/api/v3/responses",
    ]
    
    # 测试不同的URL格式
    for base in base_urls:
        # 格式1: /ep/{endpoint_id}/chat/completions
        if endpoint_id:
            test_api_url(f"{base}/ep/{endpoint_id}/chat/completions", api_key, model)
        
        # 格式2: /chat/completions (使用model作为endpoint)
        test_api_url(f"{base}/chat/completions", api_key, model)
        
        # 格式3: 直接使用endpoint_id作为model
        if endpoint_id:
            test_api_url(f"{base}/chat/completions", api_key, endpoint_id)

if __name__ == "__main__":
    main()
