#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运维Agent API路由
"""

from typing import List
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    MaintenanceRecordResponse, MaintenanceSummary,
    ResponseBase
)
from app.services import create_ops_agent_service
from app.core.config import settings

router = APIRouter()

# 运维Agent服务实例
ops_agent = create_ops_agent_service(
    api_key=settings.DEFAULT_LLM_API_KEY,
    api_model=settings.DEFAULT_LLM_MODEL,
    maintenance_dir=settings.MAINTENANCE_STORAGE_PATH
)


@router.get("/maintenance", response_model=ResponseBase)
async def list_maintenance_records(days: int = 7):
    """
    获取维护记录列表
    """
    try:
        records = ops_agent.get_all_records()
        
        # 过滤最近N天的记录
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_records = [
            r for r in records
            if datetime.fromisoformat(r.timestamp) > cutoff_date
        ]
        
        return ResponseBase(
            success=True,
            message="获取维护记录成功",
            data=[
                MaintenanceRecordResponse(
                    id=r.task_id,
                    timestamp=r.timestamp,
                    link=r.link,
                    task_id=r.task_id,
                    status=r.status,
                    error_type=r.error_analysis.error_type,
                    error_message=r.error_analysis.error_message,
                    root_cause=r.error_analysis.root_cause,
                    priority=r.error_analysis.priority,
                    estimated_fix_time=r.error_analysis.estimated_fix_time,
                    md_file_path=r.md_file_path
                )
                for r in recent_records
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取维护记录失败: {str(e)}")


@router.get("/maintenance/{task_id}", response_model=ResponseBase)
async def get_maintenance_record(task_id: str):
    """
    获取维护记录详情
    """
    try:
        record = ops_agent.get_record_by_id(task_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="维护记录不存在")
        
        return ResponseBase(
            success=True,
            message="获取维护记录成功",
            data=MaintenanceRecordResponse(
                id=record.task_id,
                timestamp=record.timestamp,
                link=record.link,
                task_id=record.task_id,
                status=record.status,
                error_type=record.error_analysis.error_type,
                error_message=record.error_analysis.error_message,
                root_cause=record.error_analysis.root_cause,
                priority=record.error_analysis.priority,
                estimated_fix_time=record.error_analysis.estimated_fix_time,
                md_file_path=record.md_file_path
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取维护记录失败: {str(e)}")


@router.get("/summary", response_model=ResponseBase)
async def get_maintenance_summary(days: int = 7):
    """
    获取维护摘要统计
    """
    try:
        summary = ops_agent.get_maintenance_summary(days)
        
        return ResponseBase(
            success=True,
            message="获取维护摘要成功",
            data=MaintenanceSummary(
                total_records=summary["total_records"],
                period_days=summary["period_days"],
                error_types=summary["error_types"],
                priorities=summary["priorities"]
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取维护摘要失败: {str(e)}")
