#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库API路由
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.schemas import (
    DocumentUploadRequest, DocumentResponse,
    KnowledgeBaseStats, ResponseBase,
    PaginationParams
)

router = APIRouter()

# 内存存储（生产环境应使用数据库+向量数据库）
documents: Dict[str, Dict[str, Any]] = {}


@router.post("/documents", response_model=ResponseBase)
async def upload_document(
    file: UploadFile = File(...),
    metadata: DocumentUploadRequest = None
):
    """
    上传文档到知识库
    """
    try:
        doc_id = str(uuid.uuid4())
        
        # 保存文件
        import os
        from pathlib import Path
        
        upload_dir = Path("./storage/knowledge_base")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{doc_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 创建文档记录
        documents[doc_id] = {
            "id": doc_id,
            "file_name": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "chunk_count": 0,  # TODO: 处理文档分块
            "metadata": metadata.metadata if metadata else None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        return ResponseBase(
            success=True,
            message="文档上传成功",
            data=DocumentResponse(
                id=doc_id,
                file_name=file.filename,
                file_path=str(file_path),
                file_size=len(content),
                chunk_count=0,
                metadata=metadata.metadata if metadata else None,
                created_at=documents[doc_id]["created_at"],
                updated_at=documents[doc_id]["updated_at"]
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/documents", response_model=ResponseBase)
async def list_documents(params: PaginationParams = None):
    """
    获取文档列表
    """
    if params is None:
        params = PaginationParams()
    
    sorted_docs = sorted(
        documents.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )
    
    total = len(sorted_docs)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    paginated_docs = sorted_docs[start:end]
    
    return ResponseBase(
        success=True,
        message="获取文档列表成功",
        data=[
            DocumentResponse(
                id=d["id"],
                file_name=d["file_name"],
                file_path=d["file_path"],
                file_size=d["file_size"],
                chunk_count=d["chunk_count"],
                metadata=d["metadata"],
                created_at=d["created_at"],
                updated_at=d["updated_at"]
            )
            for d in paginated_docs
        ]
    )


@router.get("/documents/{doc_id}", response_model=ResponseBase)
async def get_document(doc_id: str):
    """
    获取文档详情
    """
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc = documents[doc_id]
    
    return ResponseBase(
        success=True,
        message="获取文档详情成功",
        data=DocumentResponse(
            id=doc["id"],
            file_name=doc["file_name"],
            file_path=doc["file_path"],
            file_size=doc["file_size"],
            chunk_count=doc["chunk_count"],
            metadata=doc["metadata"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )
    )


@router.delete("/documents/{doc_id}", response_model=ResponseBase)
async def delete_document(doc_id: str):
    """
    删除文档
    """
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除文件
    import os
    try:
        os.remove(documents[doc_id]["file_path"])
    except:
        pass
    
    del documents[doc_id]
    
    return ResponseBase(
        success=True,
        message="文档删除成功",
        data=None
    )


@router.get("/stats", response_model=ResponseBase)
async def get_knowledge_base_stats():
    """
    获取知识库统计
    """
    total_size = sum(d["file_size"] for d in documents.values())
    total_chunks = sum(d["chunk_count"] for d in documents.values())
    
    # 收集所有领域、模块、文档类型
    domains = set()
    modules = set()
    doc_types = set()
    
    for doc in documents.values():
        if doc["metadata"]:
            if doc["metadata"].domain:
                domains.add(doc["metadata"].domain)
            if doc["metadata"].module:
                modules.add(doc["metadata"].module)
            if doc["metadata"].doc_type:
                doc_types.add(doc["metadata"].doc_type)
    
    return ResponseBase(
        success=True,
        message="获取统计信息成功",
        data=KnowledgeBaseStats(
            total_documents=len(documents),
            total_chunks=total_chunks,
            total_size=total_size,
            domains=list(domains),
            modules=list(modules),
            doc_types=list(doc_types)
        )
    )
