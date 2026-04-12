#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI对话API路由
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse,
    ChatMessageRole, ResponseBase
)

router = APIRouter()

# 内存存储（生产环境应使用数据库）
chat_sessions: Dict[str, Dict[str, Any]] = {}
chat_messages: Dict[str, List[Dict[str, Any]]] = {}


@router.post("/sessions", response_model=ResponseBase)
async def create_chat_session(session: ChatSessionCreate):
    """
    创建聊天会话
    """
    session_id = str(uuid.uuid4())
    
    chat_sessions[session_id] = {
        "id": session_id,
        "title": session.title or "新会话",
        "persona_id": session.persona_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    chat_messages[session_id] = []
    
    return ResponseBase(
        success=True,
        message="会话创建成功",
        data=ChatSessionResponse(
            id=session_id,
            title=chat_sessions[session_id]["title"],
            persona_id=session.persona_id,
            created_at=chat_sessions[session_id]["created_at"],
            updated_at=chat_sessions[session_id]["updated_at"]
        )
    )


@router.get("/sessions", response_model=ResponseBase)
async def list_chat_sessions():
    """
    获取聊天会话列表
    """
    sessions = sorted(
        chat_sessions.values(),
        key=lambda x: x["updated_at"],
        reverse=True
    )
    
    return ResponseBase(
        success=True,
        message="获取会话列表成功",
        data=[
            ChatSessionResponse(
                id=s["id"],
                title=s["title"],
                persona_id=s["persona_id"],
                created_at=s["created_at"],
                updated_at=s["updated_at"]
            )
            for s in sessions
        ]
    )


@router.get("/sessions/{session_id}", response_model=ResponseBase)
async def get_chat_session(session_id: str):
    """
    获取聊天会话详情
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = chat_sessions[session_id]
    messages = chat_messages.get(session_id, [])
    
    return ResponseBase(
        success=True,
        message="获取会话详情成功",
        data={
            "session": ChatSessionResponse(
                id=session["id"],
                title=session["title"],
                persona_id=session["persona_id"],
                created_at=session["created_at"],
                updated_at=session["updated_at"]
            ),
            "messages": [
                ChatMessageResponse(
                    id=m["id"],
                    session_id=m["session_id"],
                    role=m["role"],
                    content=m["content"],
                    thinking_content=m.get("thinking_content"),
                    retrieved_chunks=m.get("retrieved_chunks"),
                    intent_result=m.get("intent_result"),
                    created_at=m["created_at"]
                )
                for m in messages
            ]
        }
    )


@router.delete("/sessions/{session_id}", response_model=ResponseBase)
async def delete_chat_session(session_id: str):
    """
    删除聊天会话
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    del chat_sessions[session_id]
    if session_id in chat_messages:
        del chat_messages[session_id]
    
    return ResponseBase(
        success=True,
        message="会话删除成功",
        data=None
    )


@router.post("/sessions/{session_id}/messages", response_model=ResponseBase)
async def create_chat_message(session_id: str, message: ChatMessageCreate):
    """
    创建聊天消息
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 保存用户消息
    user_message_id = str(uuid.uuid4())
    user_message = {
        "id": user_message_id,
        "session_id": session_id,
        "role": ChatMessageRole.USER,
        "content": message.content,
        "created_at": datetime.now()
    }
    
    chat_messages[session_id].append(user_message)
    
    # 更新会话时间
    chat_sessions[session_id]["updated_at"] = datetime.now()
    
    # TODO: 调用AI生成回复（需要集成RAG和LLM）
    # 这里返回模拟回复
    assistant_message_id = str(uuid.uuid4())
    assistant_message = {
        "id": assistant_message_id,
        "session_id": session_id,
        "role": ChatMessageRole.ASSISTANT,
        "content": f"这是AI的回复：{message.content}",
        "thinking_content": None,
        "retrieved_chunks": None,
        "intent_result": None,
        "created_at": datetime.now()
    }
    
    chat_messages[session_id].append(assistant_message)
    
    return ResponseBase(
        success=True,
        message="消息发送成功",
        data={
            "user_message": ChatMessageResponse(
                id=user_message["id"],
                session_id=user_message["session_id"],
                role=user_message["role"],
                content=user_message["content"],
                created_at=user_message["created_at"]
            ),
            "assistant_message": ChatMessageResponse(
                id=assistant_message["id"],
                session_id=assistant_message["session_id"],
                role=assistant_message["role"],
                content=assistant_message["content"],
                thinking_content=assistant_message.get("thinking_content"),
                retrieved_chunks=assistant_message.get("retrieved_chunks"),
                intent_result=assistant_message.get("intent_result"),
                created_at=assistant_message["created_at"]
            )
        }
    )


@router.get("/sessions/{session_id}/messages", response_model=ResponseBase)
async def list_chat_messages(session_id: str):
    """
    获取聊天消息列表
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = chat_messages.get(session_id, [])
    
    return ResponseBase(
        success=True,
        message="获取消息列表成功",
        data=[
            ChatMessageResponse(
                id=m["id"],
                session_id=m["session_id"],
                role=m["role"],
                content=m["content"],
                thinking_content=m.get("thinking_content"),
                retrieved_chunks=m.get("retrieved_chunks"),
                intent_result=m.get("intent_result"),
                created_at=m["created_at"]
            )
            for m in messages
        ]
    )
