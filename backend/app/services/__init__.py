#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务模块 - 从本地工具移植的核心功能
"""

from .video_downloader import (
    VideoDownloaderService,
    DownloadResult,
    VideoPlatform,
    create_video_downloader
)

from .speech_to_text import (
    SpeechToTextService,
    TranscriptionResult,
    create_speech_to_text_service
)

from .rag_service import (
    RAGService,
    IntentRecognizer,
    QueryRewriter,
    MetadataManager,
    LLMClient,
    IntentType,
    IntentResult,
    DocumentMetadata,
    RetrievedChunk,
    QueryRewriteResult,
    create_rag_service
)

from .ops_agent import (
    OpsAgentService,
    ErrorAnalysis,
    MaintenanceRecord,
    create_ops_agent_service
)

from .link_analyzer import (
    LinkAnalyzerService,
    LinkAnalysisResult,
    create_link_analyzer_service
)

__all__ = [
    # 视频下载
    'VideoDownloaderService',
    'DownloadResult',
    'VideoPlatform',
    'create_video_downloader',
    
    # 语音转文字
    'SpeechToTextService',
    'TranscriptionResult',
    'create_speech_to_text_service',
    
    # RAG服务
    'RAGService',
    'IntentRecognizer',
    'QueryRewriter',
    'MetadataManager',
    'LLMClient',
    'IntentType',
    'IntentResult',
    'DocumentMetadata',
    'RetrievedChunk',
    'QueryRewriteResult',
    'create_rag_service',
    
    # 运维Agent
    'OpsAgentService',
    'ErrorAnalysis',
    'MaintenanceRecord',
    'create_ops_agent_service',
    
    # 链接分析
    'LinkAnalyzerService',
    'LinkAnalysisResult',
    'create_link_analyzer_service',
]
