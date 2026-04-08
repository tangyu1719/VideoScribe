#!/usr/bin/env python3
"""
测试SSE接口，抓包分析数据格式
"""
import requests
import json
import time
import uuid

def create_session():
    """创建测试会话"""
    url = "http://localhost:8000/api/chat/sessions"
    
    data = {
        "title": "测试会话",
        "groupId": None
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('data', {}).get('id')
            print(f"✓ 创建会话成功: {session_id}")
            return session_id
        else:
            print(f"✗ 创建会话失败: {response.status_code}")
            print(response.text[:500])
            return None
    except Exception as e:
        print(f"✗ 创建会话错误: {e}")
        return None

def test_sse_stream(session_id):
    """测试SSE流式接口"""
    url = f"http://localhost:8000/api/chat/sessions/{session_id}/messages/stream"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    data = {
        "content": "你好",
        "useDeepThinking": False,
        "useWebSearch": False
    }
    
    print("\n" + "=" * 60)
    print("测试SSE接口")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    print("-" * 60)
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print("-" * 60)
        
        if response.status_code == 200:
            print("开始接收SSE数据:\n")
            
            chunk_count = 0
            full_content = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk_count += 1
                    print(f"[{chunk_count}] 原始数据: {repr(line)}")
                    
                    # 解析SSE格式
                    if line.startswith("data: "):
                        data_str = line[6:]
                        print(f"      解析后: {data_str}")
                        
                        try:
                            parsed = json.loads(data_str)
                            print(f"      JSON: {parsed}")
                            
                            # 收集内容
                            if 'content' in parsed:
                                full_content += parsed['content']
                            elif 'done' in parsed:
                                print(f"\n      [完成标记]")
                            elif 'error' in parsed:
                                print(f"\n      [错误: {parsed['error']}]")
                        except json.JSONDecodeError as e:
                            print(f"      JSON解析错误: {e}")
                    
                    print()
                    
                    # 限制输出数量
                    if chunk_count >= 50:
                        print("... (已达到显示上限)")
                        break
            
            print(f"\n共接收 {chunk_count} 个数据块")
            print(f"完整内容: {full_content[:200]}...")
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text[:500])
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 创建会话
    session_id = create_session()
    
    if session_id:
        # 测试SSE
        test_sse_stream(session_id)
    else:
        print("无法创建会话，测试中止")
