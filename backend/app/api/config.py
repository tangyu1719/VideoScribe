#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理API路由
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    LLMConfigCreate, LLMConfigResponse,
    PersonaCreate, PersonaResponse,
    ParserConfigCreate, ParserConfigResponse,
    ResponseBase
)

router = APIRouter()

# 内存存储（生产环境应使用数据库）
llm_configs: Dict[str, Dict[str, Any]] = {}
personas: Dict[str, Dict[str, Any]] = {}
parser_configs: Dict[str, Dict[str, Any]] = {}


# ==================== LLM配置 ====================

@router.post("/llm", response_model=ResponseBase)
async def create_llm_config(config: LLMConfigCreate):
    """
    创建LLM配置
    """
    config_id = str(uuid.uuid4())
    
    llm_configs[config_id] = {
        "id": config_id,
        "name": config.name,
        "base_url": config.base_url,
        "model": config.model,
        "is_default": config.is_default,
        "created_at": datetime.now()
    }
    
    return ResponseBase(
        success=True,
        message="LLM配置创建成功",
        data=LLMConfigResponse(
            id=config_id,
            name=config.name,
            base_url=config.base_url,
            model=config.model,
            is_default=config.is_default,
            created_at=llm_configs[config_id]["created_at"]
        )
    )


@router.get("/llm", response_model=ResponseBase)
async def list_llm_configs():
    """
    获取LLM配置列表
    """
    return ResponseBase(
        success=True,
        message="获取LLM配置列表成功",
        data=[
            LLMConfigResponse(
                id=c["id"],
                name=c["name"],
                base_url=c["base_url"],
                model=c["model"],
                is_default=c["is_default"],
                created_at=c["created_at"]
            )
            for c in llm_configs.values()
        ]
    )


@router.delete("/llm/{config_id}", response_model=ResponseBase)
async def delete_llm_config(config_id: str):
    """
    删除LLM配置
    """
    if config_id not in llm_configs:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    del llm_configs[config_id]
    
    return ResponseBase(
        success=True,
        message="LLM配置删除成功",
        data=None
    )


# ==================== AI形象配置 ====================

@router.post("/personas", response_model=ResponseBase)
async def create_persona(persona: PersonaCreate):
    """
    创建AI形象
    """
    persona_id = str(uuid.uuid4())
    
    personas[persona_id] = {
        "id": persona_id,
        "name": persona.name,
        "description": persona.description,
        "system_prompt": persona.system_prompt,
        "avatar": persona.avatar,
        "created_at": datetime.now()
    }
    
    return ResponseBase(
        success=True,
        message="AI形象创建成功",
        data=PersonaResponse(
            id=persona_id,
            name=persona.name,
            description=persona.description,
            system_prompt=persona.system_prompt,
            avatar=persona.avatar,
            created_at=personas[persona_id]["created_at"]
        )
    )


@router.get("/personas", response_model=ResponseBase)
async def list_personas():
    """
    获取AI形象列表
    """
    return ResponseBase(
        success=True,
        message="获取AI形象列表成功",
        data=[
            PersonaResponse(
                id=p["id"],
                name=p["name"],
                description=p["description"],
                system_prompt=p["system_prompt"],
                avatar=p["avatar"],
                created_at=p["created_at"]
            )
            for p in personas.values()
        ]
    )


@router.delete("/personas/{persona_id}", response_model=ResponseBase)
async def delete_persona(persona_id: str):
    """
    删除AI形象
    """
    if persona_id not in personas:
        raise HTTPException(status_code=404, detail="形象不存在")
    
    del personas[persona_id]
    
    return ResponseBase(
        success=True,
        message="AI形象删除成功",
        data=None
    )


# ==================== 解析器配置 ====================

@router.post("/parsers", response_model=ResponseBase)
async def create_parser_config(config: ParserConfigCreate):
    """
    创建解析器配置
    """
    config_id = str(uuid.uuid4())
    
    parser_configs[config_id] = {
        "id": config_id,
        "name": config.name,
        "parser_type": config.parser_type,
        "config": config.config,
        "created_at": datetime.now()
    }
    
    return ResponseBase(
        success=True,
        message="解析器配置创建成功",
        data=ParserConfigResponse(
            id=config_id,
            name=config.name,
            parser_type=config.parser_type,
            config=config.config,
            created_at=parser_configs[config_id]["created_at"]
        )
    )


@router.get("/parsers", response_model=ResponseBase)
async def list_parser_configs():
    """
    获取解析器配置列表
    """
    return ResponseBase(
        success=True,
        message="获取解析器配置列表成功",
        data=[
            ParserConfigResponse(
                id=c["id"],
                name=c["name"],
                parser_type=c["parser_type"],
                config=c["config"],
                created_at=c["created_at"]
            )
            for c in parser_configs.values()
        ]
    )


@router.delete("/parsers/{config_id}", response_model=ResponseBase)
async def delete_parser_config(config_id: str):
    """
    删除解析器配置
    """
    if config_id not in parser_configs:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    del parser_configs[config_id]
    
    return ResponseBase(
        success=True,
        message="解析器配置删除成功",
        data=None
    )
