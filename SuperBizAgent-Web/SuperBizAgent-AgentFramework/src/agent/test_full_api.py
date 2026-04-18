import requests
import json

base_url = "http://localhost:8000/api"

print("=" * 80)
print("完整 API 测试流程")
print("=" * 80)

# 测试 1: 获取 LLM 配置列表
print("\n【测试 1】获取 LLM 配置列表")
print("-" * 80)
response = requests.get(f"{base_url}/llm-configs")
print(f"GET /api/llm-configs")
print(f"状态码：{response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"成功：{data.get('success')}")
    configs = data.get('data', [])
    print(f"配置数量：{len(configs)}")
    for cfg in configs:
        print(f"  - {cfg['name']}: {cfg['model']} (API Key: {cfg['apiKey'][:10]}... if not empty)")
else:
    print(f"失败：{response.text}")

# 测试 2: 保存 LLM 配置
print("\n【测试 2】保存 LLM 配置")
print("-" * 80)
test_config = {
    "id": "test-123456",
    "name": "测试火山引擎",
    "apiKey": "sk-test-key-123456",  # 测试用假 key
    "baseUrl": "https://ark.cn-beijing.volces.com/api/v3/responses",
    "model": "doubao-seed-1.6-flash",
    "endpointId": "ep-test-123",
    "requestFormat": "custom",
    "enabled": True,
    "backupConfigs": []
}

response = requests.post(f"{base_url}/llm-configs", json=test_config)
print(f"POST /api/llm-configs")
print(f"请求数据：{json.dumps(test_config, indent=2)}")
print(f"状态码：{response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ 保存成功")
    print(f"响应：{json.dumps(data, indent=2, ensure_ascii=False)}")
else:
    print(f"✗ 保存失败：{response.text}")

# 测试 3: 再次获取配置，验证保存
print("\n【测试 3】验证配置已保存")
print("-" * 80)
response = requests.get(f"{base_url}/llm-configs")
print(f"GET /api/llm-configs")
print(f"状态码：{response.status_code}")
if response.status_code == 200:
    data = response.json()
    configs = data.get('data', [])
    print(f"当前配置数量：{len(configs)}")
    for cfg in configs:
        print(f"  ✓ {cfg['name']} - {cfg['model']}")
        print(f"    API Key: {cfg['apiKey'][:15]}... (长度：{len(cfg['apiKey'])})")
        print(f"    Endpoint ID: {cfg.get('endpointId', '无')}")
else:
    print(f"失败：{response.text}")

# 测试 4: 创建会话
print("\n【测试 4】创建会话")
print("-" * 80)
session_data = {"title": "API 测试会话", "messages": []}
response = requests.post(f"{base_url}/chat/sessions", json=session_data)
print(f"POST /api/chat/sessions")
print(f"状态码：{response.status_code}")
if response.status_code == 200:
    data = response.json()
    session_id = data['data']['id']
    print(f"✓ 会话创建成功")
    print(f"  ID: {session_id}")
    print(f"  标题：{data['data']['title']}")
else:
    print(f"✗ 失败：{response.text}")
    session_id = None

# 测试 5: 发送流式消息（如果有配置）
if session_id and len(configs) > 0 and configs[0].get('apiKey'):
    print("\n【测试 5】发送流式消息")
    print("-" * 80)
    message_data = {
        "content": "你好，请用一句话介绍你自己",
        "useDeepThinking": False,
        "useWebSearch": False
    }
    stream_url = f"{base_url}/chat/sessions/{session_id}/messages/stream"
    print(f"POST {stream_url}")
    print(f"消息：{message_data['content']}")
    
    try:
        response = requests.post(stream_url, json=message_data, stream=True, timeout=30)
        print(f"状态码：{response.status_code}")
        print(f"\n流式回复内容:")
        print("-" * 80)
        
        full_content = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    try:
                        data = json.loads(decoded[6:])
                        if data.get('type') == 'chunk':
                            content = data.get('content', '')
                            full_content += content
                            print(content, end='', flush=True)
                        elif data.get('type') == 'error':
                            print(f"\n✗ 错误：{data.get('message')}")
                    except:
                        pass
        
        print(f"\n\n完整回复：{full_content}")
        
    except Exception as e:
        print(f"\n✗ 流式请求失败：{e}")
else:
    print("\n【测试 5】跳过 - 没有有效的 API Key 配置")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
