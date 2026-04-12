#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI主应用入口
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import video, chat, rag, knowledge_base, link_analyzer, ops, config

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("=" * 50)
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 50)
    
    # 创建必要的目录
    import os
    from pathlib import Path
    
    directories = [
        settings.VIDEO_STORAGE_PATH,
        settings.MAINTENANCE_STORAGE_PATH,
        settings.KNOWLEDGE_BASE_PATH,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"确保目录存在: {directory}")
    
    yield
    
    # 关闭时执行
    logger.info("=" * 50)
    logger.info(f"关闭 {settings.APP_NAME}")
    logger.info("=" * 50)


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SuperBizAgent Web Backend API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None
        }
    )


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "success": True,
        "message": "服务正常运行",
        "data": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG
        }
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "success": True,
        "message": f"欢迎使用 {settings.APP_NAME} API",
        "data": {
            "version": settings.APP_VERSION,
            "docs_url": "/docs" if settings.DEBUG else None
        }
    }


# 注册路由
app.include_router(
    video.router,
    prefix="/api/video",
    tags=["视频处理"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["AI对话"]
)

app.include_router(
    rag.router,
    prefix="/api/rag",
    tags=["RAG检索"]
)

app.include_router(
    knowledge_base.router,
    prefix="/api/kb",
    tags=["知识库"]
)

app.include_router(
    link_analyzer.router,
    prefix="/api/link",
    tags=["链接分析"]
)

app.include_router(
    ops.router,
    prefix="/api/ops",
    tags=["运维Agent"]
)

app.include_router(
    config.router,
    prefix="/api/config",
    tags=["配置管理"]
)

# 静态文件服务
app.mount("/storage", StaticFiles(directory="./storage"), name="storage")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
