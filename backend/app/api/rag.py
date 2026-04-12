#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG检索API路由
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    IntentRecognitionRequest, IntentRecognitionResponse,
    QueryRewriteRequest, QueryRewriteResponse,
    RAGSearchRequest, RAGSearchResponse,
    ResponseBase
)
from app.services import create_rag_service
from app.core.config import settings

router = APIRouter()

# RAG服务实例
llm_config = {
    "api_key": settings.DEFAULT_LLM_API_KEY,
    "base_url": settings.DEFAULT_LLM_BASE_URL,
    "model": settings.DEFAULT_LLM_MODEL
}
rag_service = create_rag_service(kb_manager=None, llm_config=llm_config)


@router.post("/intent", response_model=ResponseBase)
async def recognize_intent(request: IntentRecognitionRequest):
    """
    意图识别
    """
    try:
        result = rag_service.intent_recognizer.recognize(request.query)
        
        return ResponseBase(
            success=True,
            message="意图识别成功",
            data=IntentRecognitionResponse(
                intent=result.intent,
                confidence=result.confidence,
                needs_rag=result.needs_rag,
                reason=result.reason,
                suggested_tags=result.suggested_tags
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"意图识别失败: {str(e)}")


@router.post("/rewrite", response_model=ResponseBase)
async def rewrite_query(request: QueryRewriteRequest):
    """
    Query改写
    """
    try:
        # 先进行意图识别
        intent_result = rag_service.intent_recognizer.recognize(request.query)
        
        # 改写查询
        result = rag_service.query_rewriter.rewrite(
            request.query,
            intent_result
        )
        
        from app.services.rag_service import DocumentMetadata
        
        return ResponseBase(
            success=True,
            message="Query改写成功",
            data=QueryRewriteResponse(
                original_query=result.original_query,
                rewritten_query=result.rewritten_query,
                keywords=result.keywords,
                suggested_tags=DocumentMetadata(
                    domain=result.suggested_tags.domain,
                    module=result.suggested_tags.module,
                    doc_type=result.suggested_tags.doc_type,
                    keyword1=result.suggested_tags.keyword1,
                    keyword2=result.suggested_tags.keyword2
                ),
                needs_clarification=result.needs_clarification,
                clarification_question=result.clarification_question,
                reason=result.reason
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query改写失败: {str(e)}")


@router.post("/search", response_model=ResponseBase)
async def rag_search(request: RAGSearchRequest):
    """
    RAG检索
    """
    try:
        intent_result, chunks = rag_service.search(
            query=request.query,
            metadata_filter=request.metadata_filter,
            top_k=request.top_k,
            skip_intent=request.skip_intent
        )
        
        from app.services.rag_service import DocumentMetadata
        
        return ResponseBase(
            success=True,
            message="RAG检索成功",
            data=RAGSearchResponse(
                intent_result=IntentRecognitionResponse(
                    intent=intent_result.intent,
                    confidence=intent_result.confidence,
                    needs_rag=intent_result.needs_rag,
                    reason=intent_result.reason,
                    suggested_tags=intent_result.suggested_tags
                ),
                chunks=[
                    {
                        "content": chunk.content,
                        "metadata": DocumentMetadata(
                            domain=chunk.metadata.domain,
                            module=chunk.metadata.module,
                            doc_type=chunk.metadata.doc_type,
                            keyword1=chunk.metadata.keyword1,
                            keyword2=chunk.metadata.keyword2
                        ),
                        "similarity": chunk.similarity,
                        "doc_id": chunk.doc_id,
                        "chunk_id": chunk.chunk_id
                    }
                    for chunk in chunks
                ],
                total_found=len(chunks)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG检索失败: {str(e)}")


@router.get("/metadata/options", response_model=ResponseBase)
async def get_metadata_options():
    """
    获取元数据选项
    """
    return ResponseBase(
        success=True,
        message="获取元数据选项成功",
        data={
            "domains": rag_service.metadata_manager.DOMAINS,
            "modules": rag_service.metadata_manager.MODULES,
            "doc_types": rag_service.metadata_manager.DOC_TYPES
        }
    )
