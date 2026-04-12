#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web API服务 - 统一配置管理
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 创建FastAPI应用
app = FastAPI(
    title="SuperBizAgent Web API",
    description="SuperBizAgent Web 端 API 服务",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 数据模型 ==============

class LLMAPIConfig(BaseModel):
    id: str
    name: str
    apiKey: str
    baseUrl: str
    model: str
    requestFormat: Optional[str] = "openai"
    enabled: bool = True
    createdAt: str
    updatedAt: str

class AIPersona(BaseModel):
    id: str
    name: str
    description: str
    systemPrompt: str
    thinkingSystemPrompt: Optional[str] = None
    temperature: float = 0.7
    maxTokens: int = 4096
    topP: float = 0.9
    enabled: bool = True
    createdAt: str
    updatedAt: str

class DocumentParser(BaseModel):
    id: str
    name: str
    description: str
    systemPrompt: str
    rules: str = ""
    outputTemplate: str = ""
    userPrompt: str = ""
    fileNamingRule: str = ""
    summaryPrompt: str = ""
    enabled: bool = True
    createdAt: str
    updatedAt: str

class AppConfig(BaseModel):
    currentLLMConfigId: str = ""
    currentAIPersonaId: str = ""
    currentParserId: str = ""
    knowledgeBaseThreshold: float = 0.7
    defaultDeepThinking: bool = False
    defaultWebSearch: bool = False

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

# ============== 全局状态 ==============

llm_configs: Dict[str, Dict] = {}
ai_personas: Dict[str, Dict] = {}
document_parsers: Dict[str, Dict] = {}
app_config: Dict[str, Any] = {}

# 默认配置
DEFAULT_LLM_CONFIG = {
    "id": "default-1",
    "name": "火山引擎",
    "apiKey": "",
    "baseUrl": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "ep-20260411182220-jv5qt",
    "requestFormat": "openai",
    "enabled": True,
    "createdAt": datetime.now().isoformat(),
    "updatedAt": datetime.now().isoformat()
}

DEFAULT_AI_PERSONA = {
    "id": "default-1",
    "name": "默认助手",
    "description": "专业的AI助手",
    "systemPrompt": "你是一个专业的 AI 助手，擅长回答各种问题。",
    "thinkingSystemPrompt": "你是一个善于分析的 AI 助手。",
    "temperature": 0.7,
    "maxTokens": 4096,
    "topP": 0.9,
    "enabled": True,
    "createdAt": datetime.now().isoformat(),
    "updatedAt": datetime.now().isoformat()
}

DEFAULT_PARSER = {
    "id": "default-1",
    "name": "通用解析器",
    "description": "通用的内容解析器",
    "systemPrompt": "你是一个专业的内容分析助手。",
    "rules": "1. 提取关键信息\n2. 结构化呈现",
    "outputTemplate": "# {platform}视频分析\n\n## 分析摘要\n{summary}",
    "userPrompt": "",
    "fileNamingRule": "序号 - 日期 - 标题",
    "summaryPrompt": "请对以下内容进行总结。",
    "enabled": True,
    "createdAt": datetime.now().isoformat(),
    "updatedAt": datetime.now().isoformat()
}

# ============== 初始化 ==============

@app.on_event("startup")
async def startup_event():
    global llm_configs, ai_personas, document_parsers, app_config
    
    # 初始化默认配置
    if not llm_configs:
        llm_configs[DEFAULT_LLM_CONFIG["id"]] = DEFAULT_LLM_CONFIG.copy()
        print(f"[WebAPI] 已加载 {len(llm_configs)} 个 LLM 配置")
    
    if not ai_personas:
        ai_personas[DEFAULT_AI_PERSONA["id"]] = DEFAULT_AI_PERSONA.copy()
        print(f"[WebAPI] 已加载 {len(ai_personas)} 个 AI 形象")
    
    if not document_parsers:
        document_parsers[DEFAULT_PARSER["id"]] = DEFAULT_PARSER.copy()
        print(f"[WebAPI] 已加载 {len(document_parsers)} 个文档解析器")
    
    if not app_config:
        app_config = {
            "currentLLMConfigId": DEFAULT_LLM_CONFIG["id"],
            "currentAIPersonaId": DEFAULT_AI_PERSONA["id"],
            "currentParserId": DEFAULT_PARSER["id"],
            "knowledgeBaseThreshold": 0.7,
            "defaultDeepThinking": False,
            "defaultWebSearch": False
        }
        print("[WebAPI] 应用配置已初始化")

# ============== LLM 配置 API ==============

@app.get("/api/llm-configs")
async def get_llm_configs():
    """获取 LLM 配置列表"""
    configs = list(llm_configs.values())
    # 隐藏 API 密钥
    for cfg in configs:
        cfg["apiKey"] = "***" if cfg["apiKey"] else ""
    return {"success": True, "data": configs}

@app.post("/api/llm-configs")
async def save_llm_config(config: LLMAPIConfig):
    """保存LLM配置"""
    config_dict = config.dict()
    if config.id in llm_configs:
        config_dict["updatedAt"] = datetime.now().isoformat()
    else:
        config_dict["createdAt"] = datetime.now().isoformat()
        config_dict["updatedAt"] = datetime.now().isoformat()
    
    llm_configs[config.id] = config_dict
    return {"success": True, "data": {**config_dict, "apiKey": "***"}}

@app.delete("/api/llm-configs/{config_id}")
async def delete_llm_config(config_id: str):
    """删除LLM配置"""
    if config_id in llm_configs:
        del llm_configs[config_id]
    return {"success": True, "data": None}

@app.post("/api/llm-configs/{config_id}/default")
async def set_default_llm(config_id: str):
    """设为默认LLM配置"""
    if config_id in llm_configs:
        app_config["currentLLMConfigId"] = config_id
    return {"success": True, "data": None}

# ============== AI形象 API ==============

@app.get("/api/ai-personas")
async def get_ai_personas():
    """获取 AI 形象列表"""
    return {"success": True, "data": list(ai_personas.values())}

@app.post("/api/ai-personas")
async def save_ai_persona(persona: AIPersona):
    """保存 AI 形象"""
    persona_dict = persona.dict()
    if persona.id in ai_personas:
        persona_dict["updatedAt"] = datetime.now().isoformat()
    else:
        persona_dict["createdAt"] = datetime.now().isoformat()
        persona_dict["updatedAt"] = datetime.now().isoformat()
    
    ai_personas[persona.id] = persona_dict
    return {"success": True, "data": persona_dict}

@app.delete("/api/ai-personas/{persona_id}")
async def delete_ai_persona(persona_id: str):
    """删除 AI 形象"""
    if persona_id in ai_personas:
        del ai_personas[persona_id]
    return {"success": True, "data": None}

@app.post("/api/ai-personas/{persona_id}/default")
async def set_default_persona(persona_id: str):
    """设为默认 AI 形象"""
    if persona_id in ai_personas:
        app_config["currentAIPersonaId"] = persona_id
    return {"success": True, "data": None}

# ============== 文档解析器 API ==============

@app.get("/api/parsers")
async def get_parsers():
    """获取文档解析器列表"""
    return {"success": True, "data": list(document_parsers.values())}

@app.post("/api/parsers")
async def save_parser(parser: DocumentParser):
    """保存文档解析器"""
    parser_dict = parser.dict()
    if parser.id in document_parsers:
        parser_dict["updatedAt"] = datetime.now().isoformat()
    else:
        parser_dict["createdAt"] = datetime.now().isoformat()
        parser_dict["updatedAt"] = datetime.now().isoformat()
    
    document_parsers[parser.id] = parser_dict
    return {"success": True, "data": parser_dict}

@app.delete("/api/parsers/{parser_id}")
async def delete_parser(parser_id: str):
    """删除文档解析器"""
    if parser_id in document_parsers:
        del document_parsers[parser_id]
    return {"success": True, "data": None}

@app.post("/api/parsers/{parser_id}/default")
async def set_default_parser(parser_id: str):
    """设为默认解析器"""
    if parser_id in document_parsers:
        app_config["currentParserId"] = parser_id
    return {"success": True, "data": None}

# ============== 应用配置 API ==============

@app.get("/api/config")
async def get_app_config():
    """获取应用配置"""
    return {"success": True, "data": app_config}

@app.post("/api/config")
async def update_app_config(config: AppConfig):
    """更新应用配置"""
    config_dict = config.dict(exclude_unset=True)
    app_config.update(config_dict)
    return {"success": True, "data": app_config}

# ============== 主程序入口 ==============

if __name__ == "__main__":
    print("=" * 50)
    print("SuperBizAgent Web API 配置服务启动中...")
    print("=" * 50)
    print("API 文档：http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        "config_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
