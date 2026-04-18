import requests
import json

base_url = "http://localhost:8000/api"

# 1. 先创建会话
print("=" * 60)
print("步骤 1: 创建会话")
print("=" * 60)
create_url = f"{base_url}/chat/sessions"
session_data = {
    "title": "测试会话",
    "messages": []
}

response = requests.post(create_url, json=session_data)
print(f"创建会话状态码：{response.status_code}")
session_info = response.json()
print(f"响应：{json.dumps(session_info, ensure_ascii=False)}")

if response.status_code == 200:
    session_id = session_info['data']['id']
    print(f"\n✓ 会话创建成功，ID: {session_id}\n")
    
    # 2. 发送流式消息
    print("=" * 60)
    print("步骤 2: 发送流式消息")
    print("=" * 60)
    stream_url = f"{base_url}/chat/sessions/{session_id}/messages/stream"
    message_data = {
        "content": "你好，请用一句话介绍你自己",
        "images": None,
        "useDeepThinking": False,
        "useWebSearch": False
    }
    
    print(f"发送请求：{stream_url}")
    print(f"消息内容：{message_data['content']}\n")
    
    response = requests.post(stream_url, json=message_data, stream=True, timeout=60)
    print(f"流式响应状态码：{response.status_code}\n")
    print("接收内容:")
    print("-" * 60)
    
    full_content = ""
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            print(decoded)
            if decoded.startswith('data: '):
                data_str = decoded[6:]
                try:
                    data = json.loads(data_str)
                    if data.get('type') == 'chunk':
                        full_content += data.get('content', '')
                except:
                    pass
    
    print("\n" + "=" * 60)
    print("完整回复:")
    print("=" * 60)
    print(full_content)
else:
    print("创建会话失败！")
