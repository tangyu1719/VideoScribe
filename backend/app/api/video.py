#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理API路由
"""

import uuid
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.schemas import (
    VideoTaskCreate, VideoTaskResponse, VideoTaskListResponse,
    VideoTaskStatus, ResponseBase, PaginationParams
)
from app.services import create_video_downloader, create_speech_to_text_service
from app.core.config import settings

router = APIRouter()

# 内存中的任务存储（生产环境应使用Redis + 数据库）
video_tasks: Dict[str, Dict[str, Any]] = {}

# 服务实例
video_downloader = create_video_downloader()
speech_to_text = create_speech_to_text_service(settings.WHISPER_MODEL_SIZE)


@router.post("/tasks", response_model=ResponseBase)
async def create_video_task(task: VideoTaskCreate, background_tasks: BackgroundTasks):
    """
    创建视频处理任务
    """
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    video_tasks[task_id] = {
        "id": task_id,
        "link": task.link,
        "platform": task.platform,
        "status": VideoTaskStatus.PENDING,
        "progress": 0,
        "progress_message": "等待处理...",
        "video_path": None,
        "transcription": None,
        "ai_summary": None,
        "error_message": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "logs": []
    }
    
    # 后台处理任务
    background_tasks.add_task(process_video_task, task_id, task.link, task.user_prompt)
    
    return ResponseBase(
        success=True,
        message="视频任务创建成功",
        data={"task_id": task_id, "status": VideoTaskStatus.PENDING}
    )


@router.get("/tasks", response_model=ResponseBase)
async def list_video_tasks(params: PaginationParams = None):
    """
    获取视频任务列表
    """
    if params is None:
        params = PaginationParams()
    
    # 排序：最新的在前
    sorted_tasks = sorted(
        video_tasks.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )
    
    # 分页
    total = len(sorted_tasks)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    paginated_tasks = sorted_tasks[start:end]
    
    # 转换为响应格式
    items = [
        VideoTaskResponse(
            id=task["id"],
            link=task["link"],
            platform=task["platform"],
            status=task["status"],
            progress=task["progress"],
            progress_message=task["progress_message"],
            video_path=task["video_path"],
            transcription=task["transcription"],
            ai_summary=task["ai_summary"],
            error_message=task["error_message"],
            created_at=task["created_at"],
            updated_at=task["updated_at"]
        )
        for task in paginated_tasks
    ]
    
    from app.models.schemas import PaginationResponse
    
    return ResponseBase(
        success=True,
        message="获取任务列表成功",
        data=VideoTaskListResponse(
            items=items,
            pagination=PaginationResponse(
                total=total,
                page=params.page,
                page_size=params.page_size,
                total_pages=(total + params.page_size - 1) // params.page_size
            )
        )
    )


@router.get("/tasks/{task_id}", response_model=ResponseBase)
async def get_video_task(task_id: str):
    """
    获取视频任务详情
    """
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = video_tasks[task_id]
    
    return ResponseBase(
        success=True,
        message="获取任务详情成功",
        data=VideoTaskResponse(
            id=task["id"],
            link=task["link"],
            platform=task["platform"],
            status=task["status"],
            progress=task["progress"],
            progress_message=task["progress_message"],
            video_path=task["video_path"],
            transcription=task["transcription"],
            ai_summary=task["ai_summary"],
            error_message=task["error_message"],
            created_at=task["created_at"],
            updated_at=task["updated_at"]
        )
    )


@router.delete("/tasks/{task_id}", response_model=ResponseBase)
async def delete_video_task(task_id: str):
    """
    删除视频任务
    """
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    del video_tasks[task_id]
    
    return ResponseBase(
        success=True,
        message="任务删除成功",
        data=None
    )


@router.post("/tasks/{task_id}/retry", response_model=ResponseBase)
async def retry_video_task(task_id: str, background_tasks: BackgroundTasks):
    """
    重试视频任务
    """
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = video_tasks[task_id]
    
    # 重置任务状态
    task["status"] = VideoTaskStatus.PENDING
    task["progress"] = 0
    task["progress_message"] = "重新处理..."
    task["error_message"] = None
    task["updated_at"] = datetime.now()
    
    # 后台重新处理
    background_tasks.add_task(process_video_task, task_id, task["link"], "")
    
    return ResponseBase(
        success=True,
        message="任务重试成功",
        data={"task_id": task_id, "status": VideoTaskStatus.PENDING}
    )


@router.post("/tasks/{task_id}/stop", response_model=ResponseBase)
async def stop_video_task(task_id: str):
    """
    停止视频任务
    """
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = video_tasks[task_id]
    
    # 只有正在运行的任务才能停止
    if task["status"] in [VideoTaskStatus.PENDING, VideoTaskStatus.DOWNLOADING, 
                          VideoTaskStatus.TRANSCRIBING, VideoTaskStatus.SUMMARIZING]:
        task["status"] = VideoTaskStatus.STOPPED
        task["progress_message"] = "任务已停止"
        task["updated_at"] = datetime.now()
        
        return ResponseBase(
            success=True,
            message="任务已停止",
            data={"task_id": task_id, "status": VideoTaskStatus.STOPPED}
        )
    else:
        return ResponseBase(
            success=False,
            message=f"任务当前状态为 {task['status']}，无法停止",
            data=None
        )


@router.websocket("/ws/tasks")
async def video_tasks_websocket(websocket: WebSocket):
    """
    WebSocket实时推送任务状态
    """
    await websocket.accept()
    
    try:
        while True:
            # 获取所有任务状态
            tasks_data = [
                {
                    "id": task["id"],
                    "status": task["status"],
                    "progress": task["progress"],
                    "progress_message": task["progress_message"]
                }
                for task in video_tasks.values()
            ]
            
            await websocket.send_json({
                "type": "tasks_update",
                "data": tasks_data
            })
            
            # 每秒推送一次
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print("WebSocket连接断开")
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def process_video_task(task_id: str, link: str, user_prompt: str):
    """
    处理视频任务（后台任务）
    """
    task = video_tasks.get(task_id)
    if not task:
        return
    
    def update_progress(progress: int, message: str):
        """更新进度"""
        task["progress"] = progress
        task["progress_message"] = message
        task["updated_at"] = datetime.now()
        task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def log_callback(message: str, level: str = "INFO"):
        """日志回调"""
        task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}")
    
    try:
        # 1. 下载视频
        task["status"] = VideoTaskStatus.DOWNLOADING
        update_progress(10, "开始下载视频...")
        
        download_result = video_downloader.download_video(link, log_callback)
        
        if not download_result.success:
            task["status"] = VideoTaskStatus.FAILED
            task["error_message"] = download_result.error_message or "视频下载失败"
            update_progress(0, f"下载失败: {task['error_message']}")
            return
        
        task["video_path"] = download_result.file_path
        update_progress(40, "视频下载完成")
        
        # 检查任务是否被停止
        if task["status"] == VideoTaskStatus.STOPPED:
            return
        
        # 2. 语音转文字
        task["status"] = VideoTaskStatus.TRANSCRIBING
        update_progress(50, "开始语音转文字...")
        
        llm_config = {
            "apiKey": settings.DEFAULT_LLM_API_KEY,
            "baseUrl": settings.DEFAULT_LLM_BASE_URL,
            "model": settings.DEFAULT_LLM_MODEL
        }
        
        transcription_result = speech_to_text.transcribe(
            video_file=download_result.file_path,
            log_callback=log_callback,
            progress_callback=update_progress,
            llm_config=llm_config,
            user_prompt=user_prompt
        )
        
        if not transcription_result.success:
            task["status"] = VideoTaskStatus.FAILED
            task["error_message"] = transcription_result.error_message or "语音转文字失败"
            update_progress(0, f"转写失败: {task['error_message']}")
            return
        
        task["transcription"] = {
            "segments": transcription_result.segments,
            "full_text": transcription_result.full_text
        }
        task["ai_summary"] = transcription_result.ai_summary
        
        update_progress(90, "语音转文字完成")
        
        # 3. 完成
        task["status"] = VideoTaskStatus.COMPLETED
        update_progress(100, "处理完成")
        
    except Exception as e:
        task["status"] = VideoTaskStatus.FAILED
        task["error_message"] = str(e)
        update_progress(0, f"处理异常: {str(e)}")
        import traceback
        task["logs"].append(traceback.format_exc())
