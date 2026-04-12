#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic模型定义 - 请求和响应Schema
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 通用Schema ====================

class ResponseBase(BaseModel):
    """基础响应"""
    success: bool = True
    message: str = ""
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginationResponse(BaseModel):
    """分页响应"""
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 视频处理Schema ====================

class VideoTaskStatus(str, Enum):
    """视频任务状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class VideoTaskCreate(BaseModel):
    """创建视频任务请求"""
    link: str = Field(..., description="视频链接")
    platform: Optional[str] = Field(default=None, description="平台类型")
    user_prompt: Optional[str] = Field(default="", description="用户自定义提示词")


class VideoTaskResponse(BaseModel):
    """视频任务响应"""
    id: str
    link: str
    platform: Optional[str]
    status: VideoTaskStatus
    progress: int = Field(default=0, ge=0, le=100)
    progress_message: str = ""
    video_path: Optional[str] = None
    transcription: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VideoTaskListResponse(BaseModel):
    """视频任务列表响应"""
    items: List[VideoTaskResponse]
    pagination: PaginationResponse


# ==================== AI对话Schema ====================

class ChatMessageRole(str, Enum):
    """聊天消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSessionCreate(BaseModel):
    """创建聊天会话请求"""
    title: Optional[str] = Field(default=None, description="会话标题")
    persona_id: Optional[str] = Field(default=None, description="AI形象ID")


class ChatSessionResponse(BaseModel):
    """聊天会话响应"""
    id: str
    title: str
    persona_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    """创建聊天消息请求"""
    content: str = Field(..., description="消息内容")
    use_rag: bool = Field(default=True, description="是否使用RAG")
    use_deep_thinking: bool = Field(default=False, description="是否使用深度思考")


class ChatMessageResponse(BaseModel):
    """聊天消息响应"""
    id: str
    session_id: str
    role: ChatMessageRole
    content: str
    thinking_content: Optional[str] = None
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None
    intent_result: Optional[Dict[str, Any]] = None
    created_at: datetime


class ChatStreamResponse(BaseModel):
    """聊天流式响应"""
    type: str  # "thinking", "content", "chunk", "complete"
    data: Any


# ==================== RAG Schema ====================

class IntentType(str, Enum):
    """意图类型"""
    QUESTION = "question"
    CHAT = "chat"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    THANKS = "thanks"
    UNKNOWN = "unknown"
    NEED_RAG = "need_rag"
    NO_RAG = "no_rag"


class DocumentMetadata(BaseModel):
    """文档元数据"""
    domain: str = Field(..., description="领域")
    module: str = Field(..., description="模块")
    doc_type: str = Field(..., description="文档类型")
    keyword1: Optional[str] = Field(default="", description="关键词1")
    keyword2: Optional[str] = Field(default="", description="关键词2")


class IntentRecognitionRequest(BaseModel):
    """意图识别请求"""
    query: str = Field(..., description="用户查询")


class IntentRecognitionResponse(BaseModel):
    """意图识别响应"""
    intent: IntentType
    confidence: float
    needs_rag: bool
    reason: str
    suggested_tags: Optional[DocumentMetadata] = None


class QueryRewriteRequest(BaseModel):
    """Query改写请求"""
    query: str = Field(..., description="原始查询")
    intent_result: Optional[IntentRecognitionResponse] = None


class QueryRewriteResponse(BaseModel):
    """Query改写响应"""
    original_query: str
    rewritten_query: str
    keywords: List[str]
    suggested_tags: DocumentMetadata
    needs_clarification: bool
    clarification_question: str = ""
    reason: str = ""


class RAGSearchRequest(BaseModel):
    """RAG搜索请求"""
    query: str = Field(..., description="查询文本")
    metadata_filter: Optional[DocumentMetadata] = None
    top_k: int = Field(default=5, ge=1, le=20)
    skip_intent: bool = Field(default=False)


class RetrievedChunk(BaseModel):
    """召回的文档片段"""
    content: str
    metadata: DocumentMetadata
    similarity: float
    doc_id: str
    chunk_id: str


class RAGSearchResponse(BaseModel):
    """RAG搜索响应"""
    intent_result: IntentRecognitionResponse
    chunks: List[RetrievedChunk]
    total_found: int


# ==================== 知识库Schema ====================

class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    metadata: Optional[DocumentMetadata] = None
    auto_extract_metadata: bool = Field(default=True)


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    file_name: str
    file_path: str
    file_size: int
    chunk_count: int
    metadata: DocumentMetadata
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseStats(BaseModel):
    """知识库统计"""
    total_documents: int
    total_chunks: int
    total_size: int
    domains: List[str]
    modules: List[str]
    doc_types: List[str]


# ==================== 运维Agent Schema ====================

class MaintenanceRecordResponse(BaseModel):
    """维护记录响应"""
    id: str
    timestamp: datetime
    link: str
    task_id: str
    status: str
    error_type: str
    error_message: str
    root_cause: str
    priority: str
    estimated_fix_time: str
    md_file_path: str


class MaintenanceSummary(BaseModel):
    """维护摘要"""
    total_records: int
    period_days: int
    error_types: Dict[str, int]
    priorities: Dict[str, int]


# ==================== 链接分析Schema ====================

class LinkAnalysisRequest(BaseModel):
    """链接分析请求"""
    url: str = Field(..., description="链接URL")
    use_ocr: bool = Field(default=False, description="是否使用OCR")


class LinkAnalysisResponse(BaseModel):
    """链接分析响应"""
    success: bool
    link_type: str
    title: Optional[str]
    content: Optional[str]
    images: List[str]
    ocr_text: Optional[str] = None
    error_message: Optional[str] = None


# ==================== 配置Schema ====================

class LLMConfigCreate(BaseModel):
    """创建LLM配置请求"""
    name: str
    api_key: str
    base_url: str
    model: str
    is_default: bool = False


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    id: str
    name: str
    base_url: str
    model: str
    is_default: bool
    created_at: datetime


class PersonaCreate(BaseModel):
    """创建AI形象请求"""
    name: str
    description: Optional[str] = None
    system_prompt: str
    avatar: Optional[str] = None


class PersonaResponse(BaseModel):
    """AI形象响应"""
    id: str
    name: str
    description: Optional[str]
    system_prompt: str
    avatar: Optional[str]
    created_at: datetime


class ParserConfigCreate(BaseModel):
    """创建解析器配置请求"""
    name: str
    parser_type: str
    config: Dict[str, Any]


class ParserConfigResponse(BaseModel):
    """解析器配置响应"""
    id: str
    name: str
    parser_type: str
    config: Dict[str, Any]
    created_at: datetime
