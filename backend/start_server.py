#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的启动脚本
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"启动 {settings.APP_NAME}...")
    print(f"访问地址: http://localhost:{settings.PORT}")
    print(f"API文档: http://localhost:{settings.PORT}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
