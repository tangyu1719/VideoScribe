#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链接分析API路由
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    LinkAnalysisRequest, LinkAnalysisResponse,
    ResponseBase
)
from app.services import create_link_analyzer_service
from app.core.config import settings

router = APIRouter()

# 链接分析服务实例
link_analyzer = create_link_analyzer_service(settings.OCR_API_KEY)


@router.post("/analyze", response_model=ResponseBase)
async def analyze_link(request: LinkAnalysisRequest):
    """
    分析链接
    """
    try:
        result = link_analyzer.analyze_link(request.url)
        
        return ResponseBase(
            success=result.success,
            message="链接分析成功" if result.success else result.error_message,
            data=LinkAnalysisResponse(
                success=result.success,
                link_type=result.link_type,
                title=result.title,
                content=result.content,
                images=result.images,
                ocr_text=result.ocr_text if request.use_ocr else None,
                error_message=result.error_message
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"链接分析失败: {str(e)}")


@router.get("/detect-type")
async def detect_link_type(url: str):
    """
    检测链接类型
    """
    try:
        link_type = link_analyzer._judge_link_type(url)
        return ResponseBase(
            success=True,
            message="链接类型检测成功",
            data={"url": url, "type": link_type}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"链接类型检测失败: {str(e)}")
