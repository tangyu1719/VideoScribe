"""
流式聊天API - 仿照豆包/火山引擎官方SSE格式
"""
import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

# 导入主应用的状态
from web_api import chat_sessions, llm_configs

class ChatMessageCreate:
    def __init__(self, content: str, images: list = None, useDeepThinking: bool = False, useWebSearch: bool = False):
        self.content = content
        self.images = images or []
        self.useDeepThinking = useDeepThinking
        self.useWebSearch = useWebSearch

async def stream_chat_response(
    session_id: str,
    user_content: str,
    use_deep_thinking: bool = False,
    use_web_search: bool = False
) -> AsyncGenerator[str, None]:
    """
    流式生成聊天响应
    使用标准的 OpenAI SSE 格式
    """
    
    session = chat_sessions.get(session_id)
    if not session:
        yield f"data: {json.dumps({'error': '会话不存在'}, ensure_ascii=False)}\n\n"
        return
    
    # 添加用户消息
    user_message = {
        "id": str(len(session["messages"])),
        "role": "user",
        "content": user_content,
        "timestamp": datetime.now().isoformat()
    }
    session["messages"].append(user_message)
    
    # 获取LLM配置
    if not llm_configs:
        yield f"data: {json.dumps({'error': '没有可用的LLM配置'}, ensure_ascii=False)}\n\n"
        return
    
    config = list(llm_configs.values())[0]
    api_key = config.get('apiKey', '')
    base_url = config.get('baseUrl', 'https://ark.cn-beijing.volces.com/api/v3')
    model = config.get('model', 'doubao-seed-1.6-flash')
    endpoint_id = config.get('endpointId')
    
    if not api_key:
        yield f"data: {json.dumps({'error': 'API Key未配置'}, ensure_ascii=False)}\n\n"
        return
    
    # 构建API URL
    if endpoint_id:
        api_url = f"{base_url}/ep/{endpoint_id}/chat/completions"
    else:
        api_url = f"{base_url}/chat/completions"
    
    # 构建消息列表
    messages = []
    for msg in session["messages"]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # 构建请求体
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 4096
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    full_content = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", api_url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    yield f"data: {json.dumps({'error': f'API错误: {resp.status_code}'}, ensure_ascii=False)}\n\n"
                    return
                
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    
                    data = line[6:]  # 去掉 "data: " 前缀
                    
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            full_content += content
                            # 直接转发原始格式
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    
                    except json.JSONDecodeError:
                        continue
    
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        return
    
    # 保存AI回复到会话
    if full_content:
        assistant_message = {
            "id": str(len(session["messages"])),
            "role": "assistant",
            "content": full_content,
            "thinking": None,
            "useDeepThinking": use_deep_thinking,
            "useWebSearch": use_web_search,
            "timestamp": datetime.now().isoformat()
        }
        session["messages"].append(assistant_message)
        session["updated_at"] = datetime.now().isoformat()
    
    # 发送结束标记
    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"


@router.post("/chat/sessions/{session_id}/messages/stream")
async def chat_stream(session_id: str, request: dict):
    """
    流式聊天接口
    请求体: {"content": "消息内容", "useDeepThinking": false, "useWebSearch": false}
    """
    content = request.get("content", "")
    use_deep_thinking = request.get("useDeepThinking", False)
    use_web_search = request.get("useWebSearch", False)
    
    return StreamingResponse(
        stream_chat_response(session_id, content, use_deep_thinking, use_web_search),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )
