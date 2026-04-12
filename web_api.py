#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web API服务 - 为前端提供RESTful API接口
连接现有的视频处理、AI对话、知识库功能
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import data_store
import db

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入现有模块
try:
    from rag_knowledge_base import RAGKnowledgeBase
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("[WebAPI] RAG知识库模块未安装")

# 导入Agentic RAG
try:
    from agentic_rag_final import AgenticRAG
    AGENTIC_RAG_AVAILABLE = True
    print("[WebAPI] Agentic RAG模块加载成功")
except ImportError as e:
    AGENTIC_RAG_AVAILABLE = False
    print(f"[WebAPI] Agentic RAG模块未安装: {e}")

# 导入新的知识库管理模块（服务启动时初始化）
try:
    from kb_manager import get_knowledge_base, health_check as kb_health_check
    KB_MANAGER_AVAILABLE = True
    print("[WebAPI] 知识库管理模块加载成功")
except ImportError as e:
    KB_MANAGER_AVAILABLE = False
    print(f"[WebAPI] 知识库管理模块未安装: {e}")

# 导入高级知识库管理模块（P1技术升级）
try:
    from kb_manager_advanced import get_advanced_knowledge_base, health_check_advanced
    KB_ADVANCED_AVAILABLE = True
    print("[WebAPI] 高级知识库管理模块加载成功")
except ImportError as e:
    KB_ADVANCED_AVAILABLE = False
    print(f"[WebAPI] 高级知识库管理模块未安装: {e}")

# 导入ReAct Agent和Agentic RAG（P2）
try:
    from react_agent import ReActAgent, AgenticRAG
    REACT_AGENT_AVAILABLE = True
    print("[WebAPI] ReAct Agent模块加载成功")
except ImportError as e:
    REACT_AGENT_AVAILABLE = False
    print(f"[WebAPI] ReAct Agent模块未安装: {e}")

# 导入分级日志系统
try:
    from logging_system import logging_system, LogLevel
    LOGGING_SYSTEM_AVAILABLE = True
    print("[WebAPI] 分级日志系统加载成功")
except ImportError as e:
    LOGGING_SYSTEM_AVAILABLE = False
    print(f"[WebAPI] 分级日志系统未安装: {e}")

# 导入链接分析追踪器
try:
    from link_analyzer_tracer import link_tracer, trace_link_analysis
    LINK_TRACER_AVAILABLE = True
    print("[WebAPI] 链接分析追踪器加载成功")
except ImportError as e:
    LINK_TRACER_AVAILABLE = False
    print(f"[WebAPI] 链接分析追踪器未安装: {e}")

try:
    from link_analyzer import LinkAnalyzer
    LINK_ANALYZER_AVAILABLE = True
except ImportError:
    LINK_ANALYZER_AVAILABLE = False
    print("[WebAPI] 链接分析模块未安装")

# 导入视频下载模块
try:
    from video_downloader import (
        download_video, download_douyin_video, save_video,
        async_download_video, sync_download_video,
        speech_to_text, summarize_with_llm, VIDEO_DIR
    )
    VIDEO_DOWNLOADER_AVAILABLE = True
    print("[WebAPI] 视频下载模块加载成功")
except ImportError as e:
    VIDEO_DOWNLOADER_AVAILABLE = False
    print(f"[WebAPI] 视频下载模块未安装: {e}")

# 导入多模态文档处理模块
try:
    from document_processor import DocumentProcessor, DocumentType
    DOCUMENT_PROCESSOR_AVAILABLE = True
    print("[WebAPI] 文档处理模块加载成功")
except ImportError as e:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    print(f"[WebAPI] 文档处理模块未安装: {e}")

# 导入统一链接+文档处理模块
try:
    from unified_link_document_processor import (
        UnifiedLinkDocumentProcessor, InputType, ContentType,
        UnifiedProcessingResult
    )
    UNIFIED_PROCESSOR_AVAILABLE = True
    print("[WebAPI] 统一链接+文档处理模块加载成功")
except ImportError as e:
    UNIFIED_PROCESSOR_AVAILABLE = False
    print(f"[WebAPI] 统一链接+文档处理模块未安装: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="SuperBizAgent Web API",
    description="SuperBizAgent Web端API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
video_tasks: Dict[str, Dict] = {}
link_tasks: Dict[str, Dict] = {}
chat_sessions: Dict[str, Dict] = {}
chat_session_groups: Dict[str, Dict] = {}
llm_configs: Dict[str, Dict] = {}
ai_personas: Dict[str, Dict] = {}
document_parsers: Dict[str, Dict] = {}
system_logs: List[Dict] = []
app_config: Dict[str, Any] = {}
rag_kb = None
agentic_rag = None
link_analyzer = None
unified_processor = None  # 统一链接+文档处理器
agentic_rag = None
link_analyzer = None

# ============== 链接分析任务处理 ==============

class LinkTaskStage:
    DETECT_TYPE = "detect_type"           # 阶段1: 检测链接类型
    EXTRACT_CONTENT = "extract_content"   # 阶段2: 提取内容（图文/视频下载）
    TRANSCRIBE = "transcribe"             # 阶段3: 语音转文字（视频）
    AI_ANALYSIS = "ai_analysis"           # 阶段4: AI分析
    GENERATE_MD = "generate_md"           # 阶段5: 生成Markdown
    EXPORT = "export"                     # 阶段6: 导出/上传


def call_llm_for_analysis(content: str, llm_config: Dict, parser_config: Dict, user_prompt: str = "") -> str:
    """调用LLM进行内容分析"""
    import requests
    
    if not llm_config or not llm_config.get('apiKey'):
        return "未配置LLM API，无法进行分析"
    
    try:
        api_key = llm_config.get('apiKey', '')
        base_url = llm_config.get('baseUrl', 'https://api.openai.com/v1')
        model = llm_config.get('model', 'gpt-3.5-turbo')
        
        # 构建系统提示词
        system_prompt = parser_config.get('systemPrompt', '') if parser_config else ''
        if not system_prompt:
            system_prompt = "你是一个专业的内容分析助手，擅长分析社交媒体内容。请对以下内容进行分析并生成摘要。"
        
        # 构建用户提示词
        if user_prompt:
            user_content = f"{user_prompt}\n\n内容:\n{content[:8000]}"  # 限制内容长度
        else:
            user_content = f"请分析以下内容并生成摘要:\n\n{content[:8000]}"
        
        # 构建请求体
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 发送请求
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return ai_response
        else:
            error_msg = f"API调用失败: {response.status_code} - {response.text[:200]}"
            print(f"[AI分析] {error_msg}")
            return f"AI分析失败: {error_msg}"
            
    except Exception as e:
        error_msg = f"AI分析异常: {str(e)}"
        print(f"[AI分析] {error_msg}")
        return error_msg


async def process_link_task(task_id: str, url: str, config: Dict[str, Any]):
    """后台处理链接分析任务 - 完整流程"""
    import uuid
    import time
    import hashlib
    import re
    
    task = link_tasks.get(task_id)
    if not task:
        return
    
    # 获取配置
    parser_id = config.get("parserId")
    llm_config_id = config.get("llmConfigId")
    output_dir = config.get("outputDir", "OUTPUT")
    user_prompt = config.get("userPrompt", "")
    
    # 获取解析器配置
    parser_config = document_parsers.get(parser_id, {}) if parser_id else {}
    
    # 获取LLM配置
    llm_config = llm_configs.get(llm_config_id, {}) if llm_config_id else {}
    
    def update_stage(stage: str, status: str, progress: int, message: str, result: Any = None):
        """更新任务阶段状态"""
        task["stages"][stage] = {
            "status": status,
            "progress": progress,
            "message": message,
            "result": result,
            "updated_at": datetime.now().isoformat()
        }
        task["overall_progress"] = progress
        task["status"] = "running" if status == "in_progress" else ("completed" if status == "completed" else "failed")
        if status == "completed" and result:
            task["result"] = result
    
    try:
        # ========== 阶段1: 检测链接类型 ==========
        update_stage(LinkTaskStage.DETECT_TYPE, "in_progress", 10, "检测链接类型...")
        
        if not LINK_ANALYZER_AVAILABLE or not link_analyzer:
            raise Exception("链接分析器不可用")
        
        # 分析链接类型
        link_info = link_analyzer._judge_link_type(url)
        
        # 对于小红书，需要进一步检测是视频还是图文
        content_type = link_info
        platform = "unknown"
        
        if 'xiaohongshu.com' in url:
            platform = "小红书"
            # 访问页面检测类型
            try:
                import requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36',
                    'Referer': 'https://www.xiaohongshu.com/'
                }
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    # 检测是视频还是图文
                    if link_analyzer._detect_xiaohongshu_type(response.text) == 'video':
                        content_type = 'video'
                    else:
                        content_type = 'xiaohongshu'
            except Exception as e:
                print(f"检测小红书类型失败: {e}")
                content_type = 'xiaohongshu'  # 默认图文
        elif 'douyin.com' in url:
            platform = "抖音"
            content_type = link_analyzer._detect_douyin_type(url)
        
        update_stage(LinkTaskStage.DETECT_TYPE, "completed", 15, f"检测到{platform} {content_type}", {
            "platform": platform,
            "type": content_type
        })
        
        # ========== 阶段2: 提取内容 ==========
        update_stage(LinkTaskStage.EXTRACT_CONTENT, "in_progress", 20, "提取内容...")
        
        extracted_data = {}
        
        if content_type == 'video':
            # 视频类型 - 使用yt-dlp下载
            update_stage(LinkTaskStage.EXTRACT_CONTENT, "in_progress", 25, "下载视频...")
            
            # 调用真实的视频下载逻辑
            video_file = None
            if VIDEO_DOWNLOADER_AVAILABLE:
                def log_callback(msg, level="INFO"):
                    print(f"[VideoDownload] [{level}] {msg}")
                    update_stage(LinkTaskStage.EXTRACT_CONTENT, "in_progress", 30, msg)
                
                video_file = download_video(url, log_callback)
            
            if video_file and os.path.exists(video_file):
                extracted_data = {
                    "type": "video",
                    "platform": platform,
                    "url": url,
                    "video_file": video_file,
                    "needs_transcribe": True
                }
                update_stage(LinkTaskStage.EXTRACT_CONTENT, "completed", 40, f"视频下载完成: {os.path.basename(video_file)}", extracted_data)
            else:
                # 视频下载失败，但仍然继续流程
                extracted_data = {
                    "type": "video",
                    "platform": platform,
                    "url": url,
                    "video_file": None,
                    "needs_transcribe": False,
                    "download_failed": True
                }
                update_stage(LinkTaskStage.EXTRACT_CONTENT, "completed", 40, "视频下载失败，跳过转写", extracted_data)
            
        elif content_type in ['xiaohongshu', 'douyin_image']:
            # 图文类型 - 提取图片和文本
            update_stage(LinkTaskStage.EXTRACT_CONTENT, "in_progress", 25, "提取图文内容...")
            
            if content_type == 'xiaohongshu':
                result = link_analyzer._analyze_xiaohongshu(url)
            else:
                result = link_analyzer._analyze_douyin_image(url)
            
            if result.get('error'):
                raise Exception(f"内容提取失败: {result.get('error')}")
            
            extracted_data = {
                "type": content_type,
                "platform": platform,
                "url": url,
                "title": result.get('title', ''),
                "text_content": result.get('text_content', ''),
                "image_links": result.get('image_links', []),
                "image_analysis": result.get('image_analysis', []),
                "summary": result.get('summary', ''),
                "needs_transcribe": False
            }
            
            update_stage(LinkTaskStage.EXTRACT_CONTENT, "completed", 50, f"提取到{len(extracted_data['image_links'])}张图片", extracted_data)
        else:
            # 通用链接
            result = link_analyzer._analyze_general(url)
            extracted_data = {
                "type": "general",
                "platform": platform,
                "url": url,
                "title": result.get('title', ''),
                "text_content": result.get('text_content', ''),
                "needs_transcribe": False
            }
            update_stage(LinkTaskStage.EXTRACT_CONTENT, "completed", 50, "内容提取完成", extracted_data)
        
        # ========== 阶段3: 语音转文字（仅视频）==========
        transcript_result = None
        if extracted_data.get("needs_transcribe") and extracted_data.get("video_file"):
            update_stage(LinkTaskStage.TRANSCRIBE, "in_progress", 55, "语音转文字...")
            
            if VIDEO_DOWNLOADER_AVAILABLE:
                def stt_log_callback(msg, level="INFO"):
                    print(f"[SpeechToText] [{level}] {msg}")
                
                def stt_progress_callback(progress, message):
                    update_stage(LinkTaskStage.TRANSCRIBE, "in_progress", 55 + int(progress * 0.05), message)
                
                transcript_result = speech_to_text(
                    extracted_data["video_file"],
                    log_callback=stt_log_callback,
                    progress_callback=stt_progress_callback,
                    llm_config=llm_config,
                    parser_config=parser_config,
                    user_prompt=user_prompt
                )
            
            if transcript_result:
                extracted_data["transcript"] = transcript_result.get("full_text", "")
                extracted_data["transcript_segments"] = transcript_result.get("segments", [])
                update_stage(LinkTaskStage.TRANSCRIBE, "completed", 60, 
                    f"转写完成，共 {len(transcript_result.get('segments', []))} 个片段", 
                    transcript_result)
            else:
                extracted_data["transcript"] = ""
                extracted_data["transcript_segments"] = []
                update_stage(LinkTaskStage.TRANSCRIBE, "completed", 60, "转写失败或跳过", {"transcript": ""})
        
        # ========== 阶段4: AI分析 ==========
        update_stage(LinkTaskStage.AI_ANALYSIS, "in_progress", 65, "AI分析中...")
        
        # 准备分析内容
        if extracted_data.get("type") in ['xiaohongshu', 'douyin_image']:
            analysis_content = extracted_data.get("summary", "")
        elif extracted_data.get("type") == "video":
            analysis_content = extracted_data.get("transcript", "")
        else:
            analysis_content = extracted_data.get("text_content", "")
        
        # 调用AI分析
        ai_summary = ""
        if llm_config and analysis_content:
            try:
                update_stage(LinkTaskStage.AI_ANALYSIS, "in_progress", 68, "正在调用LLM API...")
                ai_summary = call_llm_for_analysis(
                    analysis_content, 
                    llm_config, 
                    parser_config,
                    user_prompt
                )
                print(f"[AI分析] 分析完成，结果长度: {len(ai_summary)}")
            except Exception as e:
                print(f"AI分析失败: {e}")
                ai_summary = f"AI分析失败: {str(e)}"
        elif not llm_config:
            ai_summary = "未配置LLM API，跳过AI分析"
        elif not analysis_content:
            ai_summary = "无内容可供分析"
        
        extracted_data["ai_summary"] = ai_summary
        
        # 提取标题
        title = extracted_data.get("title", "")
        if not title or title == "未知标题":
            # 从AI摘要第一行提取
            lines = ai_summary.strip().split('\n')
            for line in lines:
                line = line.strip().replace('#', '').strip()
                if line and len(line) < 50:
                    title = line
                    break
            if not title:
                title = f"{platform}内容分析"
        
        # 清理标题
        title = re.sub(r'[\\/*?:"<>|]', '', title).replace(' ', '_')[:50]
        extracted_data["title"] = title
        
        update_stage(LinkTaskStage.AI_ANALYSIS, "completed", 75, "AI分析完成", {"summary": ai_summary, "title": title})
        
        # ========== 阶段5: 生成Markdown ==========
        update_stage(LinkTaskStage.GENERATE_MD, "in_progress", 80, "生成Markdown...")
        
        # 生成文件名
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        existing_md = list(output_path.glob("*.md"))
        total_count = len(existing_md) + 1
        current_date = time.strftime('%m-%d')
        
        # 根据类型选择模板
        is_image_content = extracted_data.get("type") in ['xiaohongshu', 'douyin_image']
        
        if is_image_content:
            md_filename = f"{total_count:03d}-{current_date}-{title}_内容分析.md"
        else:
            md_filename = f"{total_count:03d}-{current_date}-{title}_视频分析.md"
        
        md_path = output_path / md_filename
        
        # 构建Markdown内容
        if is_image_content:
            # 图文模板
            original_content = extracted_data.get("summary", "")
            image_analysis = extracted_data.get("image_analysis", [])
            
            # 图片统计
            expected_count = len(extracted_data.get("image_links", []))
            actual_count = len(image_analysis)
            image_stats = ""
            if expected_count > 0:
                image_stats = f"\n## 图片统计\n- 应有图片数: {expected_count}\n- 实际提取: {actual_count}\n- 状态: {'全部提取成功' if actual_count >= expected_count else '部分图片可能未成功提取'}\n\n"
            
            # 图片OCR内容
            image_ocr_content = ""
            if image_analysis and "## 图片内容" not in original_content:
                image_ocr_content = "\n## 图片内容识别\n\n"
                for i, img_data in enumerate(image_analysis, 1):
                    img_url = img_data.get('url', '')
                    img_text = img_data.get('text', '')
                    if img_text:
                        image_ocr_content += f"### 图片 {i}\n"
                        image_ocr_content += f"**图片链接**: {img_url}\n\n"
                        image_ocr_content += f"**识别内容**:\n{img_text}\n\n"
            
            # 组合最终内容
            md_content = f"# {title}\n\n"
            md_content += f"**平台**: {platform}\n\n"
            md_content += f"**原始链接**: {url}\n\n"
            md_content += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md_content += "---\n\n"
            md_content += image_stats
            md_content += "## AI分析摘要\n\n"
            md_content += ai_summary + "\n\n"
            md_content += "## 原始内容\n\n"
            md_content += original_content + "\n\n"
            md_content += image_ocr_content
            
        else:
            # 视频模板
            transcript = extracted_data.get("transcript", "")
            
            md_content = f"# {title}\n\n"
            md_content += f"**平台**: {platform}\n\n"
            md_content += f"**原始链接**: {url}\n\n"
            md_content += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md_content += "---\n\n"
            md_content += "## AI分析摘要\n\n"
            md_content += ai_summary + "\n\n"
            md_content += "## 视频转录内容\n\n"
            md_content += transcript + "\n\n"
        
        # 写入文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        update_stage(LinkTaskStage.GENERATE_MD, "completed", 90, f"Markdown已生成: {md_filename}", {
            "file_path": str(md_path),
            "filename": md_filename,
            "content": md_content
        })
        
        # ========== 阶段6: 导出/完成 ==========
        update_stage(LinkTaskStage.EXPORT, "completed", 100, "分析完成", {
            "file_path": str(md_path),
            "filename": md_filename
        })
        
        # 更新任务最终结果
        task["status"] = "completed"
        task["result"] = {
            "url": url,
            "platform": platform,
            "type": extracted_data.get("type"),
            "title": title,
            "file_path": str(md_path),
            "filename": md_filename,
            "stages": task["stages"]
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[LinkTask] 任务失败: {error_msg}")
        import traceback
        traceback.print_exc()
        
        task["status"] = "failed"
        task["error"] = error_msg
        
        # 更新当前阶段为失败
        for stage_name in task["stages"]:
            if task["stages"][stage_name]["status"] == "in_progress":
                task["stages"][stage_name]["status"] = "failed"
                task["stages"][stage_name]["message"] = f"失败: {error_msg}"
                break

# ============== 分级日志系统 ==============
# 1. 完整原型日志 (Raw Logs) - 记录所有请求的完整流水
# 2. 接口粒度日志 (API Summary) - 按接口聚合统计
# 3. 操作粒度日志 (Operation Details) - 记录每个具体操作的详情

# 完整原型日志存储（内存 + 数据库）
raw_logs: List[Dict[str, Any]] = []

# 接口粒度统计：{api_path: {method: count, total_time, avg_time, last_called, ...}}
api_stats: Dict[str, Dict[str, Any]] = {}

# 操作粒度日志：{operation_id: {operation_type, start_time, end_time, duration, inputs, outputs, status, ...}}
operation_logs: List[Dict[str, Any]] = []

# 初始化组件
@app.on_event("startup")
async def startup_event():
    global rag_kb, agentic_rag, link_analyzer, llm_configs, ai_personas, document_parsers, app_config
    
    # 加载历史日志
    load_logs_from_db()
    add_log("info", "system", "WebAPI服务启动", {"version": "1.0.0"})
    
    # 从 MariaDB 初始化 LLM 配置
    try:
        results = db.execute_query("SELECT * FROM llm_configs ORDER BY created_at")
        for row in results:
            llm_configs[row['id']] = dict(row)
        if len(llm_configs) > 0:
            add_log("info", "config", f"加载 {len(llm_configs)} 个 LLM 配置")
    except Exception as e:
        add_log("error", "config", f"加载 LLM 配置失败: {e}")

    # 从 MariaDB 初始化 AI 形象
    try:
        results = db.execute_query("SELECT * FROM ai_personas ORDER BY created_at")
        for row in results:
            ai_personas[row['id']] = dict(row)
        if len(ai_personas) > 0:
            add_log("info", "config", f"加载 {len(ai_personas)} 个 AI 形象")
    except Exception as e:
        add_log("error", "config", f"加载 AI 形象失败: {e}")

    # 从 MariaDB 初始化解析器
    try:
        results = db.execute_query("SELECT * FROM document_parsers ORDER BY created_at")
        for row in results:
            document_parsers[row['id']] = dict(row)
        if len(document_parsers) > 0:
            add_log("info", "config", f"加载 {len(document_parsers)} 个解析器")
    except Exception as e:
        add_log("error", "config", f"加载解析器失败: {e}")

    # 从 MariaDB 初始化应用配置
    try:
        results = db.execute_query("SELECT * FROM app_config WHERE id=1")
        if results:
            app_config = dict(results[0])
    except Exception as e:
        add_log("error", "config", f"加载应用配置失败: {e}")

    # 从 MariaDB 初始化会话分组
    try:
        results = db.execute_query("SELECT * FROM session_groups ORDER BY created_at")
        for row in results:
            chat_session_groups[row['id']] = dict(row)
    except Exception as e:
        add_log("error", "chat", f"加载会话分组失败: {e}")

    # 从 MariaDB 初始化会话
    try:
        results = db.execute_query("SELECT * FROM chat_sessions ORDER BY created_at")
        for row in results:
            session_data = dict(row)
            session_data['messages'] = []
            chat_sessions[row['id']] = session_data

        # 加载每个会话的消息
        for session_id in chat_sessions:
            msg_results = db.execute_query(
                "SELECT * FROM chat_messages WHERE session_id=%s ORDER BY timestamp",
                (session_id,)
            )
            chat_sessions[session_id]['messages'] = [dict(msg) for msg in msg_results]

        if len(chat_sessions) > 0:
            add_log("info", "chat", f"加载 {len(chat_sessions)} 个会话")
    except Exception as e:
        add_log("error", "chat", f"加载会话失败: {e}")
    
    # 初始化新的知识库管理器（服务启动时初始化，解决点击时才初始化的问题）
    if KB_MANAGER_AVAILABLE:
        try:
            from kb_manager import get_knowledge_base
            kb_manager = get_knowledge_base()
            stats = kb_manager.get_stats()
            add_log("info", "knowledge_base", 
                   f"知识库管理器初始化成功: {stats['total_chunks']} chunks, model_loaded={stats['model_loaded']}")
            print(f"[WebAPI] 知识库管理器初始化成功: {stats['total_chunks']} chunks")
        except Exception as e:
            add_log("error", "knowledge_base", f"知识库管理器初始化失败: {e}")
            print(f"[WebAPI] 知识库管理器初始化失败: {e}")
    
    # 初始化高级知识库管理器（P1技术升级：递归分割+ChromaDB+Hybrid RAG+BGE-Large）
    if KB_ADVANCED_AVAILABLE:
        try:
            from kb_manager_advanced import get_advanced_knowledge_base
            kb_advanced = get_advanced_knowledge_base()
            stats = kb_advanced.get_stats()
            add_log("info", "knowledge_base", 
                   f"高级知识库管理器初始化成功: {stats['total_chunks']} chunks, dim={stats['embedding_dim']}, store={stats['vector_store_type']}")
            print(f"[WebAPI] 高级知识库管理器初始化成功: {stats['total_chunks']} chunks, dim={stats['embedding_dim']}")
        except Exception as e:
            add_log("error", "knowledge_base", f"高级知识库管理器初始化失败: {e}")
            print(f"[WebAPI] 高级知识库管理器初始化失败: {e}")
    
    # 初始化ReAct Agent和Agentic RAG（P2：ReAct框架+自适应多次检索）
    if REACT_AGENT_AVAILABLE and KB_ADVANCED_AVAILABLE:
        try:
            from react_agent import AgenticRAG
            from kb_manager_advanced import get_advanced_knowledge_base
            kb_advanced = get_advanced_knowledge_base()
            agentic_rag = AgenticRAG(kb_manager=kb_advanced)
            add_log("info", "agentic_rag", "Agentic RAG初始化成功（ReAct框架）")
            print("[WebAPI] Agentic RAG初始化成功（ReAct框架）")
        except Exception as e:
            add_log("error", "agentic_rag", f"Agentic RAG初始化失败: {e}")
            print(f"[WebAPI] Agentic RAG初始化失败: {e}")
    
    # 初始化RAG知识库（旧版，保留兼容）
    if RAG_AVAILABLE:
        try:
            rag_kb = RAGKnowledgeBase()
            print("[WebAPI] RAG知识库初始化成功")
        except Exception as e:
            print(f"[WebAPI] RAG知识库初始化失败: {e}")
    
    # 初始化Agentic RAG知识库（旧版，保留兼容）
    if AGENTIC_RAG_AVAILABLE:
        try:
            agentic_rag = AgenticRAG()
            print("[WebAPI] Agentic RAG知识库初始化成功")
        except Exception as e:
            print(f"[WebAPI] Agentic RAG知识库初始化失败: {e}")
    
    # 初始化链接分析器
    if LINK_ANALYZER_AVAILABLE:
        try:
            link_analyzer = LinkAnalyzer()
            print("[WebAPI] 链接分析器初始化成功")
        except Exception as e:
            print(f"[WebAPI] 链接分析器初始化失败: {e}")
    
    # 初始化统一链接+文档处理器
    global unified_processor
    if UNIFIED_PROCESSOR_AVAILABLE:
        try:
            unified_processor = UnifiedLinkDocumentProcessor()
            print("[WebAPI] 统一链接+文档处理器初始化成功")
        except Exception as e:
            print(f"[WebAPI] 统一链接+文档处理器初始化失败: {e}")

# ============== 数据模型 ==============

class VideoTaskCreate(BaseModel):
    url: str
    platform: str

class ChatMessageCreate(BaseModel):
    content: str
    images: Optional[List[str]] = None

class AIConfigUpdate(BaseModel):
    thinking_system_prompt: Optional[str] = None
    response_system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

class LinkAnalyzeRequest(BaseModel):
    url: str
    config: Optional[Dict[str, Any]] = None

class ChatMessageCreate(BaseModel):
    content: str
    images: Optional[List[str]] = None
    useDeepThinking: Optional[bool] = False
    useWebSearch: Optional[bool] = False
    useKnowledgeBase: Optional[bool] = False  # 是否使用知识库

class RenameSessionRequest(BaseModel):
    title: str

class MoveSessionRequest(BaseModel):
    groupId: Optional[str] = None

class CreateGroupRequest(BaseModel):
    name: str

class LLMConfig(BaseModel):
    id: str
    name: str
    apiKey: str
    baseUrl: str
    model: str
    endpointId: Optional[str] = None
    requestFormat: Optional[str] = "openai"
    headers: Optional[Dict[str, str]] = None

class AIConfigUpdate(BaseModel):
    llmConfigs: Optional[List[LLMConfig]] = None
    currentLLMConfigId: Optional[str] = None
    knowledgeBaseThreshold: Optional[float] = 0.7
    defaultDeepThinking: Optional[bool] = False
    defaultWebSearch: Optional[bool] = False
    thinkingSystemPrompt: Optional[str] = None
    responseSystemPrompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    maxTokens: Optional[int] = 4096
    topP: Optional[float] = 0.9

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

# ============== 视频任务API ==============

@app.get("/api/video/tasks")
async def get_video_tasks(page: int = 1, page_size: int = 20):
    """获取视频任务列表"""
    tasks_list = list(video_tasks.values())
    total = len(tasks_list)
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    items = tasks_list[start:end]
    
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }

@app.post("/api/video/tasks")
async def create_video_task(task: VideoTaskCreate):
    """创建视频下载任务"""
    import uuid
    
    task_id = str(uuid.uuid4())
    video_tasks[task_id] = {
        "id": task_id,
        "url": task.url,
        "platform": task.platform,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "title": None,
        "transcript": None,
        "summary": None,
        "error": None
    }
    
    # 启动后台任务处理
    asyncio.create_task(process_video_task(task_id, task.url, task.platform))
    
    return {
        "success": True,
        "data": video_tasks[task_id]
    }

async def process_video_task(task_id: str, url: str, platform: str):
    """后台处理视频任务"""
    task = video_tasks[task_id]
    
    try:
        # 这里调用现有的视频处理逻辑
        # 模拟处理过程
        task["status"] = "downloading"
        task["progress"] = 20
        await asyncio.sleep(2)
        
        task["status"] = "transcribing"
        task["progress"] = 50
        await asyncio.sleep(2)
        
        task["status"] = "analyzing"
        task["progress"] = 80
        await asyncio.sleep(2)
        
        task["status"] = "completed"
        task["progress"] = 100
        task["completed_at"] = datetime.now().isoformat()
        task["title"] = ""
        task["transcript"] = ""
        task["summary"] = ""
        
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)

@app.get("/api/video/tasks/{task_id}")
async def get_video_task(task_id: str):
    """获取任务详情"""
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "data": video_tasks[task_id]
    }

@app.delete("/api/video/tasks/{task_id}")
async def delete_video_task(task_id: str):
    """删除任务"""
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    del video_tasks[task_id]
    
    return {
        "success": True,
        "data": None
    }

@app.post("/api/video/tasks/{task_id}/retry")
async def retry_video_task(task_id: str):
    """重试任务"""
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = video_tasks[task_id]
    task["status"] = "pending"
    task["progress"] = 0
    task["error"] = None
    
    asyncio.create_task(process_video_task(task_id, task["url"], task["platform"]))
    
    return {
        "success": True,
        "data": task
    }

# ============== AI对话API ==============

@app.get("/api/chat/sessions")
async def get_chat_sessions():
    """获取会话列表"""
    sessions = list(chat_sessions.values())
    return {
        "success": True,
        "data": sessions
    }

@app.post("/api/chat/sessions")
async def create_chat_session():
    """创建新会话"""
    import uuid
    
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        "id": session_id,
        "title": "新会话",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "group_id": None,
        "context_length": 0,
        "max_context_length": 8192
    }
    
    return {
        "success": True,
        "data": chat_sessions[session_id]
    }

@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """获取会话详情"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "success": True,
        "data": chat_sessions[session_id]
    }

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """删除会话"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    del chat_sessions[session_id]
    
    return {
        "success": True,
        "data": None
    }

@app.post("/api/chat/sessions/{session_id}/rename")
async def rename_chat_session(session_id: str, request: RenameSessionRequest):
    """重命名会话"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    chat_sessions[session_id]["title"] = request.title
    chat_sessions[session_id]["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": chat_sessions[session_id]
    }

@app.post("/api/chat/sessions/{session_id}/move")
async def move_chat_session(session_id: str, request: MoveSessionRequest):
    """移动会话到分组"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    chat_sessions[session_id]["group_id"] = request.groupId
    chat_sessions[session_id]["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": chat_sessions[session_id]
    }

# ============== 会话分组API ==============

@app.get("/api/chat/session-groups")
async def get_session_groups():
    """获取会话分组列表"""
    groups = list(chat_session_groups.values())
    return {
        "success": True,
        "data": groups
    }

@app.post("/api/chat/session-groups")
async def create_session_group(request: CreateGroupRequest):
    """创建会话分组"""
    import uuid
    
    group_id = str(uuid.uuid4())
    chat_session_groups[group_id] = {
        "id": group_id,
        "name": request.name,
        "created_at": datetime.now().isoformat(),
        "sessions": []
    }
    
    return {
        "success": True,
        "data": chat_session_groups[group_id]
    }

@app.post("/api/chat/sessions/{session_id}/messages")
async def send_message(session_id: str, message: ChatMessageCreate):
    """发送消息（非流式）"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = chat_sessions[session_id]
    
    # 添加用户消息
    user_message = {
        "id": str(len(session["messages"])),
        "role": "user",
        "content": message.content,
        "images": message.images,
        "timestamp": datetime.now().isoformat()
    }
    session["messages"].append(user_message)
    
    # 更新上下文长度
    session["context_length"] = sum(len(m["content"]) for m in session["messages"])
    
    # 模拟AI回复（支持深度思考）
    thinking_content = None
    if message.useDeepThinking:
        thinking_content = f"深度思考过程：分析用户问题'{message.content}'...\n1. 理解问题核心\n2. 检索相关知识\n3. 构建回答框架"
    
    assistant_message = {
        "id": str(len(session["messages"])),
        "role": "assistant",
        "content": "",
        "thinking": thinking_content,
        "useDeepThinking": message.useDeepThinking,
        "useWebSearch": message.useWebSearch,
        "knowledgeReferences": [
            {"content": "相关知识片段1", "source": "文档A", "similarity": 0.85},
            {"content": "相关知识片段2", "source": "文档B", "similarity": 0.78}
        ] if message.useWebSearch else None,
        "timestamp": datetime.now().isoformat()
    }
    session["messages"].append(assistant_message)
    session["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": assistant_message
    }

@app.post("/api/chat/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: str, 
    request: ChatMessageCreate
):
    """发送消息（流式）- 支持知识库问答"""
    print(f"\n[Stream API] 收到请求 - 会话：{session_id}")
    print(f"[Stream API] 使用知识库: {request.useKnowledgeBase}")
    
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = chat_sessions[session_id]
    content = request.content
    useDeepThinking = request.useDeepThinking
    useWebSearch = request.useWebSearch
    useKnowledgeBase = request.useKnowledgeBase
    
    # 添加用户消息
    user_message = {
        "id": str(len(session["messages"])),
        "role": "user",
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    session["messages"].append(user_message)
    
    async def generate():
        # 如果使用知识库，先进行知识库检索
        kb_results = []
        kb_context = ""
        
        if useKnowledgeBase:
            print("[Stream API] 开始知识库检索...")
            yield f"data: {json.dumps({'type': 'kb_search', 'content': '🔍 正在检索知识库...'}, ensure_ascii=False)}\n\n"
            
            try:
                # 使用高级知识库
                if KB_ADVANCED_AVAILABLE:
                    kb = get_advanced_knowledge_base()
                    if kb and kb.is_ready():
                        kb_results = kb.search(content, top_k=5)
                        print(f"[Stream API] 知识库检索完成，找到 {len(kb_results)} 条结果")
                        
                        if kb_results:
                            yield f"data: {json.dumps({'type': 'kb_result', 'content': f'✅ 找到 {len(kb_results)} 个相关文档片段'}, ensure_ascii=False)}\n\n"
                            
                            # 构建知识库上下文
                            context_parts = []
                            for i, result in enumerate(kb_results, 1):
                                source = result.get('source_file', '未知来源')
                                doc_content = result.get('content', '')
                                score = result.get('score', 0)
                                context_parts.append(f"[文档{i}] 来源: {source} (相关度: {score:.2f})\n{doc_content}")
                                
                                # 发送检索结果摘要
                                yield f"data: {json.dumps({'type': 'kb_reference', 'content': f'📄 {source} (相关度: {score:.2f})'}, ensure_ascii=False)}\n\n"
                            
                            kb_context = "\n\n".join(context_parts)
                            yield f"data: {json.dumps({'type': 'kb_done', 'content': '---'}, ensure_ascii=False)}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'kb_empty', 'content': '⚠️ 知识库中未找到相关内容，将基于通用知识回答'}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'kb_error', 'content': '⚠️ 知识库未就绪'}, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'kb_error', 'content': '⚠️ 知识库模块未加载'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"[Stream API] 知识库检索失败: {e}")
                yield f"data: {json.dumps({'type': 'kb_error', 'content': f'⚠️ 知识库检索失败: {str(e)}'}, ensure_ascii=False)}\n\n"
        
        # 获取LLM配置
        if not llm_configs:
            yield f"data: {json.dumps({'error': '没有可用的LLM配置'}, ensure_ascii=False)}\n\n"
            return
        
        config = list(llm_configs.values())[0]
        # 支持两种字段命名：数据库使用下划线，代码使用驼峰
        api_key = config.get('api_key', '') or config.get('apiKey', '')
        base_url = config.get('base_url', '') or config.get('baseUrl', 'https://ark.cn-beijing.volces.com/api/v3')
        model = config.get('model', '') or config.get('model', 'doubao-seed-1.6-flash')
        endpoint_id = config.get('endpoint_id', '') or config.get('endpointId', '')
        
        if not api_key:
            yield f"data: {json.dumps({'error': 'API Key未配置'}, ensure_ascii=False)}\n\n"
            return
        
        # 清理base_url，移除末尾的/responses等路径
        base_url = base_url.rstrip('/')
        if base_url.endswith('/responses'):
            base_url = base_url[:-10]  # 移除 /responses
        elif base_url.endswith('/chat/completions'):
            base_url = base_url[:-17]  # 移除 /chat/completions
        
        # 构建API URL - 火山引擎使用 /chat/completions，不使用 /ep/{endpoint_id}
        api_url = f"{base_url}/chat/completions"
        
        # 使用 endpoint_id 作为 model 名称（如果存在）
        if endpoint_id:
            model = endpoint_id
        
        print(f"[Stream API] 调用URL: {api_url}, 模型: {model}")
        
        # 构建系统提示词（包含知识库上下文）
        system_prompt = """你是一位资深的Java和AI应用开发专家，拥有以下专业背景：

【技术专长】
1. Java生态：精通Spring Boot、Spring Cloud、JVM调优、高并发架构设计
2. AI应用开发：熟悉LangChain、向量数据库、RAG系统、模型微调
3. 高并发系统：精通分布式架构、缓存策略、消息队列、微服务
4. 工程实践：代码重构、性能优化、系统设计、技术选型

【回答风格】
1. 技术深度：提供具体的技术细节和最佳实践
2. 实用性：给出可落地的代码示例和架构建议
3. 系统性：从架构层面分析问题，提供完整解决方案
4. 前瞻性：结合最新技术趋势，提供演进建议

【知识库引用规范】
当使用知识库内容回答时，请：
1. 明确标注引用来源（文档名称）
2. 结合知识库内容和你的专业知识综合回答
3. 如果知识库内容不足，补充你的专业见解

请基于以上角色设定回答用户问题。"""
        
        # 构建用户提示词（包含知识库上下文）
        user_content = content
        if kb_context:
            user_content = f"【知识库参考内容】\n{kb_context}\n\n【用户问题】\n{content}\n\n请基于以上知识库内容回答用户问题，如果知识库内容不足以完整回答，请补充你的专业知识。"
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        full_content = ""
        
        # 发送开始生成标记
        yield f"data: {json.dumps({'type': 'generating', 'content': '🤖 生成回答...'}, ensure_ascii=False)}\n\n"
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", api_url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        print(f"[Stream API] API错误: {resp.status_code} - {error_body[:200]}")
                        yield f"data: {json.dumps({'error': f'API错误: {resp.status_code}'}, ensure_ascii=False)}\n\n"
                        return
                    
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data = line[6:]  # 去掉 "data: " 前缀
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                            
                            delta = choices[0].get("delta", {})
                            content_chunk = delta.get("content", "")
                            
                            if content_chunk:
                                full_content += content_chunk
                                # 发送内容片段
                                yield f"data: {json.dumps({'type': 'content', 'content': content_chunk}, ensure_ascii=False)}\n\n"
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            print(f"[Stream API] 异常: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return
        
        # 保存AI回复
        if full_content:
            assistant_message = {
                "id": str(len(session["messages"])),
                "role": "assistant",
                "content": full_content,
                "thinking": None,
                "useDeepThinking": useDeepThinking,
                "useWebSearch": useWebSearch,
                "useKnowledgeBase": useKnowledgeBase,
                "knowledgeReferences": [
                    {
                        "content": r.get('content', '')[:200] + "...",
                        "source": r.get('source_file', '未知'),
                        "similarity": r.get('score', 0)
                    } for r in kb_results[:3]
                ] if kb_results else None,
                "timestamp": datetime.now().isoformat()
            }
            session["messages"].append(assistant_message)
            session["updated_at"] = datetime.now().isoformat()
            print(f"[Stream API] 回复已保存，长度: {len(full_content)}")
        
        # 发送结束标记
        yield f"data: {json.dumps({'type': 'done', 'done': True}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/chat/config")
async def get_ai_config():
    """获取AI配置"""
    return {
        "success": True,
        "data": {
            "llmConfigs": list(llm_configs.values()),
            "currentLLMConfigId": list(llm_configs.keys())[0] if llm_configs else "",
            "knowledgeBaseThreshold": 0.7,
            "defaultDeepThinking": False,
            "defaultWebSearch": False,
            "thinking_system_prompt": "你是一个善于分析的AI助手，请深入思考问题后再回答...",
            "response_system_prompt": "你是一个专业的AI助手，请提供准确、有用的回答...",
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9
        }
    }

@app.post("/api/chat/config")
async def update_ai_config(config: AIConfigUpdate):
    """更新AI配置"""
    # 这里保存配置到文件或数据库
    return {
        "success": True,
        "data": config.dict(exclude_unset=True)
    }

# ============== LLM配置管理API ==============

@app.get("/api/chat/llm-configs")
async def get_llm_configs():
    """获取LLM配置列表"""
    configs = list(llm_configs.values())
    # 隐藏API密钥
    for cfg in configs:
        cfg["apiKey"] = "***"
    return {
        "success": True,
        "data": configs
    }

@app.post("/api/chat/llm-configs")
async def save_llm_config(config: LLMConfig):
    """保存LLM配置"""
    llm_configs[config.id] = config.dict()
    return {
        "success": True,
        "data": {**config.dict(), "apiKey": "***"}
    }

@app.delete("/api/chat/llm-configs/{config_id}")
async def delete_llm_config(config_id: str):
    """删除LLM配置"""
    if config_id in llm_configs:
        del llm_configs[config_id]
    return {
        "success": True,
        "data": None
    }

# ============== 知识库API ==============

@app.get("/api/kb/health")
async def get_kb_health():
    """知识库健康检查 - 用于验证服务启动时初始化是否成功"""
    if KB_MANAGER_AVAILABLE:
        try:
            health = kb_health_check()
            return {
                "success": True,
                "data": health
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"健康检查失败: {str(e)}"
            }
    else:
        return {
            "success": False,
            "error": "知识库管理模块不可用"
        }

@app.get("/api/kb/stats")
async def get_kb_stats():
    """获取知识库统计"""
    global agentic_rag
    
    # 优先使用新的知识库管理器
    if KB_MANAGER_AVAILABLE:
        try:
            from kb_manager import get_knowledge_base
            kb = get_knowledge_base()
            stats = kb.get_stats()
            return {
                "success": True,
                "data": {
                    "total_files": stats['total_files'],
                    "indexed_files": stats['total_files'],
                    "total_chunks": stats['total_chunks'],
                    "total_size": 0,
                    "embedding_dim": stats['embedding_dim'],
                    "model_loaded": stats['model_loaded'],
                    "initialized": stats['initialized'],
                    "type": "kb_manager_v2"
                }
            }
        except Exception as e:
            logger.error(f"[API] 获取知识库统计失败: {e}")
    
    # 回退到旧版
    try:
        # 从数据库获取统计
        result = db.execute_query("""
            SELECT 
                COUNT(*) as total_files,
                SUM(CASE WHEN status = 'indexed' THEN 1 ELSE 0 END) as indexed_files,
                SUM(file_size) as total_size,
                SUM(chunk_count) as total_chunks
            FROM kb_files
        """)
        
        stats = result[0] if result else {}
        
        return {
            "success": True,
            "data": {
                "total_files": stats.get('total_files', 0),
                "indexed_files": stats.get('indexed_files', 0),
                "total_size": stats.get('total_size', 0) or 0,
                "total_chunks": stats.get('total_chunks', 0) or 0,
                "type": "agentic_rag"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取统计失败: {str(e)}"
        }

# 允许的文件类型
ALLOWED_KB_EXTENSIONS = {'.txt', '.md', '.markdown'}

def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()

@app.get("/api/kb/files")
async def get_kb_files(page: int = 1, page_size: int = 20):
    """获取文件列表 - 从数据库读取"""
    try:
        # 获取总数
        count_result = db.execute_query("SELECT COUNT(*) as total FROM kb_files")
        total = count_result[0]['total'] if count_result else 0
        
        # 获取分页数据
        results = db.execute_query(
            """SELECT id, file_name, file_size, file_type, status, chunk_count, created_at 
               FROM kb_files ORDER BY created_at DESC LIMIT %s OFFSET %s""",
            (page_size, (page - 1) * page_size)
        )
        
        items = []
        for row in results:
            items.append({
                "id": str(row['id']),
                "name": row['file_name'],
                "size": row['file_size'],
                "type": row['file_type'],
                "status": row['status'],
                "chunkCount": row['chunk_count'],
                "createdAt": row['created_at'].isoformat() if row['created_at'] else datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取文件列表失败: {str(e)}"
        }

@app.post("/api/kb/files")
async def upload_kb_file(file: UploadFile = File(...)):
    """上传文件到知识库 - 仅支持txt和md文件"""
    global agentic_rag
    
    if not AGENTIC_RAG_AVAILABLE or not agentic_rag:
        if not RAG_AVAILABLE or not rag_kb:
            raise HTTPException(status_code=503, detail="知识库服务不可用")
    
    # 检查文件类型
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_KB_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {ext}。仅支持: {', '.join(ALLOWED_KB_EXTENSIONS)}"
        )
    
    # 保存上传的文件
    upload_dir = Path("uploads/knowledge_base")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    try:
        # 保存文件
        content = await file.read()
        file_size = len(content)
        
        # 检查文件大小（限制10MB）
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小超过10MB限制")
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 先插入数据库记录（pending状态）
        db.execute_update(
            """INSERT INTO kb_files (file_name, file_path, file_size, file_type, status, chunk_count) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (file.filename, str(file_path), file_size, ext, 'processing', 0)
        )
        
        # 获取刚插入的记录ID
        result = db.execute_query(
            "SELECT id FROM kb_files WHERE file_name = %s ORDER BY created_at DESC LIMIT 1",
            (file.filename,)
        )
        file_id = result[0]['id'] if result else None
        
        # 使用Agentic RAG添加文档
        if AGENTIC_RAG_AVAILABLE and agentic_rag:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                # 添加到Agentic RAG
                success = agentic_rag.add_document(str(file_path))
                
                if success:
                    chunk_count = len(agentic_rag.local_chunks) if hasattr(agentic_rag, 'local_chunks') else 0
                    
                    # 更新数据库状态
                    if file_id:
                        db.execute_update(
                            "UPDATE kb_files SET status = %s, chunk_count = %s WHERE id = %s",
                            ('indexed', chunk_count, file_id)
                        )
                    
                    # 记录日志
                    add_log("info", "knowledge_base", f"文件导入成功: {file.filename}", {
                        "file_id": file_id,
                        "file_name": file.filename,
                        "file_size": file_size,
                        "chunk_count": chunk_count
                    })
                    
                    return {
                        "success": True,
                        "data": {
                            "id": file_id,
                            "name": file.filename,
                            "size": file_size,
                            "status": "indexed",
                            "type": "agentic_rag",
                            "chunkCount": chunk_count
                        }
                    }
                else:
                    # 更新失败状态
                    if file_id:
                        db.execute_update(
                            "UPDATE kb_files SET status = %s WHERE id = %s",
                            ('failed', file_id)
                        )
                    
                    add_log("error", "knowledge_base", f"文档索引失败: {file.filename}")
                    return {
                        "success": False,
                        "error": "文档索引失败"
                    }
            except Exception as e:
                # 更新失败状态
                if file_id:
                    db.execute_update(
                        "UPDATE kb_files SET status = %s WHERE id = %s",
                        ('failed', file_id)
                    )
                
                add_log("error", "knowledge_base", f"处理文档失败: {file.filename}", {"error": str(e)})
                return {
                    "success": False,
                    "error": f"处理文档失败: {str(e)}"
                }
        
        # 回退到旧版RAG
        return {
            "success": True,
            "data": {
                "id": "file_id",
                "name": file.filename,
                "size": len(content),
                "status": "pending"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.delete("/api/kb/files/{file_id}")
async def delete_kb_file(file_id: str):
    """删除知识库文件"""
    try:
        # 获取文件信息
        result = db.execute_query(
            "SELECT file_path, file_name FROM kb_files WHERE id = %s",
            (file_id,)
        )
        
        if result:
            file_path = result[0]['file_path']
            file_name = result[0]['file_name']
            
            # 删除物理文件
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除数据库记录
            db.execute_update(
                "DELETE FROM kb_files WHERE id = %s",
                (file_id,)
            )
            
            add_log("info", "knowledge_base", f"文件已删除: {file_name}", {"file_id": file_id})
        
        return {
            "success": True,
            "data": None
        }
    except Exception as e:
        add_log("error", "knowledge_base", f"删除文件失败: {str(e)}", {"file_id": file_id})
        return {
            "success": False,
            "error": f"删除文件失败: {str(e)}"
        }

@app.post("/api/kb/rebuild")
async def rebuild_kb_index():
    """重建知识库索引"""
    if not RAG_AVAILABLE or not rag_kb:
        raise HTTPException(status_code=503, detail="知识库服务不可用")
    
    return {
        "success": True,
        "data": None
    }

@app.get("/api/kb/search")
async def search_kb(query: str, top_k: int = 5, threshold: float = 0.5):
    """搜索知识库 - 使用新的知识库管理器"""
    global agentic_rag
    
    # 优先使用新的知识库管理器（服务启动时已初始化）
    if KB_MANAGER_AVAILABLE:
        try:
            from kb_manager import get_knowledge_base
            kb = get_knowledge_base()
            
            if not kb.is_ready():
                return {
                    "success": False,
                    "error": "知识库尚未就绪"
                }
            
            results = kb.search(query, top_k=top_k)
            
            # 格式化返回结果
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "content": item['content'],
                    "source": {
                        "file_name": item['source_file'],
                        "chunk_index": item['chunk_id'],
                        "position": f"{item['start_pos']}-{item['end_pos']}"
                    },
                    "scores": {
                        "semantic": item['score'],
                        "final": item['score']
                    },
                    "relevance": item['score']
                })
            
            return {
                "success": True,
                "data": formatted_results,
                "meta": {
                    "query": query,
                    "top_k": len(results),
                    "threshold": threshold,
                    "type": "kb_manager_v2"
                }
            }
        except Exception as e:
            logger.error(f"[API] 知识库搜索失败: {e}")
            # 出错时回退到旧版
    
    # 回退到Agentic RAG
    if AGENTIC_RAG_AVAILABLE and agentic_rag:
        try:
            result = agentic_rag.search(query, threshold=threshold)
            
            # 格式化返回结果
            formatted_results = []
            for item in result['results']:
                formatted_results.append({
                    "content": item['content'],
                    "source": {
                        "file_name": item['source']['file_name'],
                        "page_number": item['source']['page_number'],
                        "chunk_index": item['source']['chunk_index'],
                        "position": item['source']['position']
                    },
                    "scores": item['scores'],
                    "relevance": item['scores']['rrf']
                })
            
            return {
                "success": True,
                "data": formatted_results,
                "meta": {
                    "query": result['query'],
                    "top_k": result['top_k'],
                    "total_chunks": result['total_chunks'],
                    "threshold": result['threshold'],
                    "type": "agentic_rag"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}"
            }
    
    # 回退到旧版RAG
    if not RAG_AVAILABLE or not rag_kb:
        return {
            "success": True,
            "data": []
        }
    
    # 这里调用实际的搜索功能
    return {
        "success": True,
        "data": []
    }

@app.post("/api/kb/agentic-query")
async def agentic_kb_query(request: Dict[str, Any]):
    """
    Agentic RAG查询 - 使用ReAct框架进行自适应多次检索
    
    支持：
    - 多次RAG检索（根据信息充分性自适应）
    - 查询重写优化
    - 思考过程可视化
    """
    global agentic_rag
    
    question = request.get('question', '')
    stream = request.get('stream', False)
    
    if not question:
        return {
            "success": False,
            "error": "问题不能为空"
        }
    
    # 使用新的Agentic RAG（ReAct框架）
    if REACT_AGENT_AVAILABLE and agentic_rag:
        try:
            result = agentic_rag.query(question, stream=stream)
            
            return {
                "success": True,
                "data": {
                    "answer": result['answer'],
                    "sources": result['sources'],
                    "retrieval_count": result['retrieval_count'],
                    "iterations": result['iterations'],
                    "thought_process": result['thought_process']
                },
                "meta": {
                    "type": "agentic_rag_react",
                    "question": question
                }
            }
        except Exception as e:
            logger.error(f"[API] Agentic RAG查询失败: {e}")
            return {
                "success": False,
                "error": f"Agentic RAG查询失败: {str(e)}"
            }
    
    # 回退到高级知识库管理器
    if KB_ADVANCED_AVAILABLE:
        try:
            from kb_manager_advanced import get_advanced_knowledge_base
            kb = get_advanced_knowledge_base()
            
            if not kb.is_ready():
                return {
                    "success": False,
                    "error": "知识库尚未就绪"
                }
            
            results = kb.search(question, top_k=5)
            
            # 构建简单答案
            answer = f"基于知识库检索结果：\n\n"
            for i, item in enumerate(results, 1):
                answer += f"[{i}] {item['content'][:200]}...\n"
            
            return {
                "success": True,
                "data": {
                    "answer": answer,
                    "sources": [{"file": r['source_file'], "relevance": "high"} for r in results],
                    "retrieval_count": 1,
                    "iterations": 1,
                    "thought_process": "单次检索模式"
                },
                "meta": {
                    "type": "kb_advanced",
                    "question": question
                }
            }
        except Exception as e:
            logger.error(f"[API] 高级知识库查询失败: {e}")
            return {
                "success": False,
                "error": f"查询失败: {str(e)}"
            }
    
    return {
        "success": False,
        "error": "Agentic RAG服务不可用"
    }

# ============== 链接分析API ==============

@app.post("/api/link/analyze")
async def analyze_link(request: LinkAnalyzeRequest):
    """分析链接 - 支持解析器选择"""
    import uuid
    
    # 获取配置
    config = request.config or {}
    llm_config_id = config.get("llmConfigId")
    parser_id = config.get("parserId")  # 解析器ID
    user_prompt = config.get("userPrompt", "")
    
    request_id = str(uuid.uuid4())
    url = request.url
    
    # 开始链接分析追踪
    trace_id = None
    if LINK_TRACER_AVAILABLE:
        trace_id = link_tracer.start_analysis(url, request_id)
    
    try:
        # 获取解析器配置
        parser_config = None
        if parser_id and parser_id in document_parsers:
            parser_config = document_parsers[parser_id]
        
        # 使用LinkAnalyzer进行实际分析
        if LINK_ANALYZER_AVAILABLE and link_analyzer:
            # 添加步骤：检测链接类型
            if LINK_TRACER_AVAILABLE and trace_id:
                link_tracer.add_step(trace_id, 'detect_type', '检测链接类型', {'url': url})
            
            # 分析链接
            analysis_result = link_analyzer.analyze_link(url)
            
            # 完成步骤
            if LINK_TRACER_AVAILABLE and trace_id:
                link_tracer.complete_step(trace_id, 'detect_type', 
                    {'platform': analysis_result.get('platform'), 'type': analysis_result.get('type')})
            
            # 构建结果
            result = {
                "url": url,
                "platform": analysis_result.get('platform', ''),
                "type": analysis_result.get('type', ''),
                "title": analysis_result.get('title', ''),
                "content": analysis_result.get('content', ''),
                "images": analysis_result.get('images', []),
                "author": analysis_result.get('author', ''),
                "publish_time": analysis_result.get('publish_time', datetime.now().isoformat()),
                "aiAnalysis": analysis_result.get('ai_analysis', {
                    "summary": "",
                    "keyPoints": [],
                    "sentiment": "neutral",
                    "tags": []
                }),
                "parser_used": parser_config.get('name') if parser_config else None,
                "trace_id": trace_id
            }
        else:
            # 链接分析器不可用，返回模拟结果
            result = {
                "url": url,
                "platform": "unknown",
                "type": "text",
                "title": "",
                "content": "链接分析功能暂不可用",
                "images": [],
                "author": "",
                "publish_time": datetime.now().isoformat(),
                "aiAnalysis": {
                    "summary": "",
                    "keyPoints": [],
                    "sentiment": "neutral",
                    "tags": []
                },
                "parser_used": None,
                "trace_id": trace_id
            }
        
        # 完成链接分析追踪
        if LINK_TRACER_AVAILABLE and trace_id:
            link_tracer.complete_analysis(trace_id, result)
        
        # 记录日志
        if LOGGING_SYSTEM_AVAILABLE:
            logging_system.log_raw(
                level=LogLevel.INFO,
                module='link_analyzer',
                api_path='/api/link/analyze',
                method='POST',
                request_id=request_id,
                message=f'链接分析完成: {url}',
                request_data={'url': url, 'parser_id': parser_id},
                response_data={'platform': result['platform'], 'type': result['type']}
            )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # 记录失败
        if LINK_TRACER_AVAILABLE and trace_id:
            link_tracer.complete_analysis(trace_id, error_message=error_msg)
        
        if LOGGING_SYSTEM_AVAILABLE:
            logging_system.log_raw(
                level=LogLevel.ERROR,
                module='link_analyzer',
                api_path='/api/link/analyze',
                method='POST',
                request_id=request_id,
                message=f'链接分析失败: {url}',
                request_data={'url': url, 'parser_id': parser_id},
                error=error_msg
            )
        
        return {
            "success": False,
            "error": f"链接分析失败: {error_msg}"
        }

@app.get("/api/link/parsers")
async def get_link_parsers():
    """获取可用的链接分析解析器列表"""
    try:
        # 从document_parsers中获取启用的解析器
        parsers = []
        for parser_id, parser in document_parsers.items():
            if parser.get('enabled', True):
                parsers.append({
                    "id": parser_id,
                    "name": parser.get('name', '未命名解析器'),
                    "description": parser.get('description', ''),
                    "systemPrompt": parser.get('system_prompt', ''),
                    "rules": parser.get('rules', ''),
                    "outputTemplate": parser.get('output_template', '')
                })
        
        return {
            "success": True,
            "data": parsers
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取解析器列表失败: {str(e)}"
        }

@app.get("/api/link/history")
async def get_link_history(page: int = 1, page_size: int = 20):
    """获取分析历史"""
    return {
        "success": True,
        "data": {
            "items": [],
            "total": 0
        }
    }

@app.post("/api/link/tasks")
async def create_link_task(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """创建链接分析任务 - 启动完整的多阶段处理流程"""
    import uuid
    
    task_id = str(uuid.uuid4())
    url = request.get('url', '')
    config = request.get('config', {})
    
    # 创建任务记录
    task = {
        "id": task_id,
        "url": url,
        "status": "pending",
        "overall_progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "config": config,
        "stages": {
            LinkTaskStage.DETECT_TYPE: {
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "result": None,
                "updated_at": datetime.now().isoformat()
            },
            LinkTaskStage.EXTRACT_CONTENT: {
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "result": None,
                "updated_at": datetime.now().isoformat()
            },
            LinkTaskStage.TRANSCRIBE: {
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "result": None,
                "updated_at": datetime.now().isoformat()
            },
            LinkTaskStage.AI_ANALYSIS: {
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "result": None,
                "updated_at": datetime.now().isoformat()
            },
            LinkTaskStage.GENERATE_MD: {
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "result": None,
                "updated_at": datetime.now().isoformat()
            },
            LinkTaskStage.EXPORT: {
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "result": None,
                "updated_at": datetime.now().isoformat()
            }
        },
        "result": None,
        "error": None
    }
    
    link_tasks[task_id] = task
    
    # 启动后台任务
    background_tasks.add_task(process_link_task, task_id, url, config)
    
    print(f"[LinkTask] 创建任务: {task_id}, URL: {url}")
    
    return {
        "success": True,
        "data": {
            "taskId": task_id,
            "status": "pending",
            "message": "任务已创建，开始处理"
        }
    }

@app.get("/api/link/tasks/{task_id}")
async def get_link_task(task_id: str):
    """获取链接分析任务状态"""
    task = link_tasks.get(task_id)
    
    if not task:
        return {
            "success": False,
            "error": "任务不存在"
        }
    
    return {
        "success": True,
        "data": task
    }

@app.get("/api/link/tasks")
async def list_link_tasks():
    """获取所有链接分析任务列表"""
    tasks = list(link_tasks.values())
    
    # 按创建时间倒序
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {
        "success": True,
        "data": tasks
    }

@app.delete("/api/link/tasks/{task_id}")
async def delete_link_task(task_id: str):
    """删除链接分析任务"""
    if task_id in link_tasks:
        del link_tasks[task_id]
        return {
            "success": True,
            "data": None
        }
    
    return {
        "success": False,
        "error": "任务不存在"
    }


# ============== 多模态文档处理 API ==============

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    parser_id: Optional[str] = Form(None),
    llm_config_id: Optional[str] = Form(None),
    output_dir: Optional[str] = Form(None),
    user_prompt: Optional[str] = Form(None)
):
    """上传并处理文档（支持图片、PDF、DOCX、MD、CSV、音频、视频）"""
    import uuid
    import shutil
    
    if not DOCUMENT_PROCESSOR_AVAILABLE:
        return {
            "success": False,
            "error": "文档处理模块未安装"
        }
    
    task_id = str(uuid.uuid4())
    
    try:
        # 保存上传的文件
        upload_dir = Path(__file__).parent / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 创建处理任务
        task = {
            "id": task_id,
            "type": "document",
            "filename": file.filename,
            "file_path": str(file_path),
            "status": "processing",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "result": None,
            "error": None
        }
        
        # 启动后台处理
        # TODO: 实现异步处理
        
        return {
            "success": True,
            "data": {
                "taskId": task_id,
                "filename": file.filename,
                "status": "processing",
                "message": "文件已上传，开始处理"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"上传失败: {str(e)}"
        }


@app.get("/api/documents/supported-types")
async def get_supported_document_types():
    """获取支持的文档类型列表"""
    if not DOCUMENT_PROCESSOR_AVAILABLE:
        return {
            "success": False,
            "error": "文档处理模块未安装"
        }
    
    types = {
        "images": {
            "label": "图片",
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "description": "支持OCR文字识别"
        },
        "documents": {
            "label": "文档",
            "extensions": [".pdf", ".docx", ".doc", ".md", ".markdown"],
            "description": "PDF、Word、Markdown文档"
        },
        "spreadsheets": {
            "label": "表格",
            "extensions": [".csv"],
            "description": "CSV表格文件"
        },
        "audio": {
            "label": "音频",
            "extensions": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"],
            "description": "支持语音转文字"
        },
        "video": {
            "label": "视频",
            "extensions": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"],
            "description": "支持提取音频并转文字"
        }
    }
    
    return {
        "success": True,
        "data": types
    }


@app.post("/api/link/export")
async def export_link_result(request: Dict[str, Any]):
    """导出分析结果为MD文件到指定位置"""
    import os
    import re
    from pathlib import Path

    try:
        result = request.get('result', {})
        output_dir = request.get('outputDir', '')
        parser_id = request.get('parserId', '')

        # 获取解析器配置
        parser_config = None
        if parser_id and parser_id in document_parsers:
            parser_config = document_parsers[parser_id]

        # 获取文件命名规则
        file_naming_rule = parser_config.get('fileNamingRule', '序号 - 日期 - 标题') if parser_config else '序号 - 日期 - 标题'
        output_template = parser_config.get('outputTemplate', '') if parser_config else ''

        # 提取基本信息
        url = result.get('url', '')
        title = result.get('title', '未命名')
        platform = result.get('platform', '未知平台')
        content = result.get('content', '')
        author = result.get('author', '')
        publish_time = result.get('publish_time', '')
        ai_analysis = result.get('aiAnalysis', {})

        # 生成文件名
        date_str = datetime.now().strftime('%m-%d')
        clean_title = re.sub(r'[^\w\u4e00-\u9fa5]', '_', title)[:30].strip('_') or 'untitled'

        # 计算序号（基于输出目录中的现有文件数）
        if output_dir and os.path.exists(output_dir):
            existing_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
            prefix_num = len(existing_files) + 1
        else:
            prefix_num = 1
        prefix = f"{prefix_num:03d}"

        # 根据命名规则生成文件名
        filename = file_naming_rule.replace('序号', prefix).replace('日期', date_str).replace('标题', clean_title)
        if not filename.endswith('.md'):
            filename += '.md'

        # 确定输出路径
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path / filename
        else:
            # 默认输出到项目目录下的OUTPUT文件夹
            output_path = Path(__file__).parent / 'OUTPUT'
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path / filename

        # 生成Markdown内容
        if output_template:
            # 使用解析器的输出模板
            md_content = output_template.replace('{platform}', platform) \
                .replace('{datetime}', datetime.now().strftime('%Y-%m-%d %H:%M:%S')) \
                .replace('{link}', url) \
                .replace('{transcript}', content) \
                .replace('{summary}', ai_analysis.get('summary', '')) \
                .replace('{title}', title) \
                .replace('{author}', author)
        else:
            # 使用默认模板
            md_content = f"# {title}\n\n"
            md_content += f"**平台**: {platform}\n\n"
            md_content += f"**作者**: {author}\n\n" if author else ""
            md_content += f"**发布时间**: {publish_time}\n\n" if publish_time else ""
            md_content += f"**原始链接**: {url}\n\n"
            md_content += "---\n\n"

            if content:
                md_content += "## 内容\n\n"
                md_content += content + "\n\n"

            if ai_analysis:
                md_content += "## AI分析\n\n"
                if ai_analysis.get('summary'):
                    md_content += f"### 摘要\n{ai_analysis['summary']}\n\n"
                if ai_analysis.get('keyPoints'):
                    md_content += "### 关键点\n"
                    for point in ai_analysis['keyPoints']:
                        md_content += f"- {point}\n"
                    md_content += "\n"
                if ai_analysis.get('tags'):
                    md_content += "### 标签\n"
                    for tag in ai_analysis['tags']:
                        md_content += f"#{tag} "
                    md_content += "\n"

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"[API] Markdown文件已生成: {file_path}")

        return {
            "success": True,
            "data": {
                "filePath": str(file_path),
                "filename": filename,
                "content": md_content
            }
        }
    except Exception as e:
        print(f"[API] 导出Markdown失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"导出失败: {str(e)}"
        }

# ============== 统一链接+文档处理 API ==============

class UnifiedProcessRequest(BaseModel):
    """统一处理请求"""
    source: str  # URL或文件路径
    isUrl: Optional[bool] = None  # 是否为URL（自动检测）
    llmConfigId: Optional[str] = None
    outputDir: Optional[str] = None
    userPrompt: Optional[str] = None


class UnifiedProcessResponse(BaseModel):
    """统一处理响应"""
    success: bool
    taskId: Optional[str] = None
    inputType: Optional[str] = None
    contentType: Optional[str] = None
    title: Optional[str] = None
    textContent: Optional[str] = None
    aiSummary: Optional[str] = None
    outputFile: Optional[str] = None
    error: Optional[str] = None
    processingTime: Optional[float] = None


# 统一处理任务存储
unified_tasks: Dict[str, Dict] = {}


@app.post("/api/unified/process", response_model=ApiResponse)
async def unified_process(request: UnifiedProcessRequest):
    """
    统一处理链接或文档
    支持：链接（小红书、抖音、网页等）和本地文件（PDF、Word、图片、音频、视频）
    """
    import uuid
    
    if not UNIFIED_PROCESSOR_AVAILABLE or not unified_processor:
        return {
            "success": False,
            "error": "统一处理器模块未安装或初始化失败"
        }
    
    task_id = str(uuid.uuid4())
    
    # 创建任务
    task = {
        "id": task_id,
        "source": request.source,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "result": None,
        "error": None
    }
    unified_tasks[task_id] = task
    
    # 获取LLM配置
    llm_config = llm_configs.get(request.llmConfigId, {}) if request.llmConfigId else {}
    
    # 启动后台处理
    asyncio.create_task(process_unified_task(
        task_id=task_id,
        source=request.source,
        is_url=request.isUrl,
        llm_config=llm_config,
        output_dir=request.outputDir,
        user_prompt=request.userPrompt
    ))
    
    return {
        "success": True,
        "data": {
            "taskId": task_id,
            "status": "pending",
            "message": "任务已创建，开始处理"
        }
    }


async def process_unified_task(
    task_id: str,
    source: str,
    is_url: Optional[bool],
    llm_config: Dict,
    output_dir: Optional[str],
    user_prompt: Optional[str]
):
    """后台处理统一任务"""
    task = unified_tasks.get(task_id)
    if not task:
        return
    
    try:
        task["status"] = "processing"
        task["progress"] = 10
        
        # 执行处理
        result = unified_processor.process(
            source,
            is_url=is_url,
            llm_config=llm_config,
            output_dir=output_dir or "OUTPUT",
            user_prompt=user_prompt or ""
        )
        
        # 更新任务结果
        if result.success:
            task["status"] = "completed"
            task["progress"] = 100
            task["result"] = {
                "inputType": result.input_type.value,
                "contentType": result.content_type.value,
                "title": result.title,
                "textContent": result.text_content[:1000] if result.text_content else "",  # 限制返回长度
                "textContentLength": len(result.text_content),
                "aiSummary": result.ai_summary[:500] if result.ai_summary else "",  # 限制返回长度
                "outputFile": result.output_file,
                "extractedImages": len(result.extracted_images),
                "processingTime": result.processing_time
            }
        else:
            task["status"] = "failed"
            task["error"] = result.error
            
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        print(f"[UnifiedProcess] 任务失败: {e}")
        import traceback
        traceback.print_exc()


@app.get("/api/unified/tasks/{task_id}", response_model=ApiResponse)
async def get_unified_task(task_id: str):
    """获取统一处理任务状态"""
    if task_id not in unified_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "data": unified_tasks[task_id]
    }


@app.get("/api/unified/tasks", response_model=ApiResponse)
async def list_unified_tasks(page: int = 1, page_size: int = 20):
    """获取统一处理任务列表"""
    tasks_list = list(unified_tasks.values())
    total = len(tasks_list)
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    items = tasks_list[start:end]
    
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@app.post("/api/unified/detect-type", response_model=ApiResponse)
async def detect_input_type(source: str):
    """
    检测输入类型
    返回：是否为URL、内容类型预测
    """
    if not UNIFIED_PROCESSOR_AVAILABLE or not unified_processor:
        return {
            "success": False,
            "error": "统一处理器模块未安装"
        }
    
    try:
        is_url = unified_processor._is_url(source)
        
        result = {
            "isUrl": is_url,
            "source": source
        }
        
        if is_url:
            # 尝试判断链接类型
            if unified_processor.link_analyzer:
                link_type = unified_processor.link_analyzer._judge_link_type(source)
                result["linkType"] = link_type
                
                # 映射到内容类型
                type_mapping = {
                    'xiaohongshu': 'social_media',
                    'douyin_image': 'social_media',
                    'video': 'video',
                    'general': 'web_page'
                }
                result["predictedContentType"] = type_mapping.get(link_type, 'unknown')
        else:
            # 本地文件，检测文件类型
            if os.path.exists(source):
                from pathlib import Path
                ext = Path(source).suffix.lower()
                
                type_mapping = {
                    '.jpg': 'image', '.jpeg': 'image', '.png': 'image',
                    '.pdf': 'document', '.docx': 'document', '.doc': 'document',
                    '.md': 'document', '.csv': 'document',
                    '.mp3': 'audio', '.wav': 'audio', '.m4a': 'audio',
                    '.mp4': 'video', '.avi': 'video', '.mov': 'video'
                }
                result["predictedContentType"] = type_mapping.get(ext, 'unknown')
                result["fileExtension"] = ext
            else:
                result["predictedContentType"] = 'unknown'
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"类型检测失败: {str(e)}"
        }


@app.get("/api/unified/supported-types", response_model=ApiResponse)
async def get_unified_supported_types():
    """获取支持的输入类型列表"""
    return {
        "success": True,
        "data": {
            "urlTypes": {
                "social_media": {
                    "label": "社交媒体",
                    "platforms": ["小红书", "抖音", "B站"],
                    "description": "支持图文和视频内容提取"
                },
                "video": {
                    "label": "视频平台",
                    "platforms": ["YouTube", "腾讯视频", "优酷", "爱奇艺"],
                    "description": "支持视频下载和语音转文字"
                },
                "web_page": {
                    "label": "网页",
                    "description": "通用网页内容提取"
                }
            },
            "fileTypes": {
                "image": {
                    "label": "图片",
                    "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
                    "description": "支持OCR文字识别"
                },
                "document": {
                    "label": "文档",
                    "extensions": [".pdf", ".docx", ".doc", ".md", ".markdown", ".csv"],
                    "description": "PDF、Word、Markdown、CSV文档"
                },
                "audio": {
                    "label": "音频",
                    "extensions": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"],
                    "description": "支持语音转文字"
                },
                "video": {
                    "label": "视频",
                    "extensions": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"],
                    "description": "支持提取音频并转文字"
                }
            }
        }
    }


# ============== 系统配置API ==============

@app.get("/api/config")
async def get_app_config():
    """获取应用配置（统一配置）"""
    return {
        "success": True,
        "data": app_config
    }

@app.post("/api/config")
async def update_app_config(config: Dict[str, Any]):
    """更新应用配置（统一配置）"""
    app_config.update(config)
    return {
        "success": True,
        "data": app_config
    }

# ============== LLM 配置 API ==============

@app.get("/api/llm-configs")
async def get_llm_configs():
    """获取 LLM 配置列表"""
    configs = list(llm_configs.values())
    for cfg in configs:
        cfg["apiKey"] = "***" if cfg["apiKey"] else ""
    return {"success": True, "data": configs}

@app.post("/api/llm-configs")
async def save_llm_config(config: Dict[str, Any]):
    """保存 LLM 配置（MariaDB）"""
    config_id = config.get("id")
    if config_id:
        config["updatedAt"] = datetime.now().isoformat()
        llm_configs[config_id] = config
        
        # 保存到 MariaDB
        try:
            sql = """
                INSERT INTO llm_configs (id, name, api_key, base_url, model, endpoint_id, request_format, headers, enabled, backup_configs, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name=%s, api_key=%s, base_url=%s, model=%s, endpoint_id=%s, request_format=%s, headers=%s, enabled=%s, backup_configs=%s, updated_at=%s
            """
            params = (
                config_id, config.get('name'), config.get('apiKey'), config.get('baseUrl'),
                config.get('model'), config.get('endpointId'), config.get('requestFormat'),
                json.dumps(config.get('headers')), config.get('enabled', True),
                json.dumps(config.get('backupConfigs', [])), config["updatedAt"],
                config.get('name'), config.get('apiKey'), config.get('baseUrl'),
                config.get('model'), config.get('endpointId'), config.get('requestFormat'),
                json.dumps(config.get('headers')), config.get('enabled', True),
                json.dumps(config.get('backupConfigs', [])), config["updatedAt"]
            )
            db.execute_update(sql, params)
            print(f"[API] LLM 配置已保存到 MariaDB: {config_id}")
        except Exception as e:
            print(f"[API] 保存到 MariaDB 失败：{e}")
            # 回退到文件存储
            data_store.save_llm_config(config)
            
    return {"success": True, "data": {**config, "apiKey": "***"}}

@app.delete("/api/llm-configs/{config_id}")
async def delete_llm_config(config_id: str):
    """删除 LLM 配置（MariaDB）"""
    if config_id in llm_configs:
        del llm_configs[config_id]
        
        # 从 MariaDB 删除
        try:
            sql = "DELETE FROM llm_configs WHERE id=%s"
            db.execute_update(sql, (config_id,))
            print(f"[API] LLM 配置已从 MariaDB 删除：{config_id}")
        except Exception as e:
            print(f"[API] 从 MariaDB 删除失败：{e}")
            # 回退到文件删除
            data_store.delete_llm_config(config_id)
            
    return {"success": True, "data": None}

# ============== AI 形象 API ==============

@app.get("/api/ai-personas")
async def get_ai_personas():
    """获取 AI 形象列表"""
    return {"success": True, "data": list(ai_personas.values())}

@app.post("/api/ai-personas")
async def save_ai_persona(persona: Dict[str, Any]):
    """保存 AI 形象"""
    persona_id = persona.get("id")
    if persona_id:
        persona["updatedAt"] = datetime.now().isoformat()
        ai_personas[persona_id] = persona
    return {"success": True, "data": persona}

@app.delete("/api/ai-personas/{persona_id}")
async def delete_ai_persona(persona_id: str):
    """删除 AI 形象"""
    if persona_id in ai_personas:
        del ai_personas[persona_id]
    return {"success": True, "data": None}

# ============== 文档解析器 API ==============

@app.get("/api/parsers")
async def get_parsers():
    """获取文档解析器列表 - 从MariaDB读取"""
    try:
        results = db.execute_query("SELECT * FROM document_parsers ORDER BY created_at")
        parsers = []
        for row in results:
            parsers.append({
                "id": row['id'],
                "name": row['name'],
                "description": row['description'] or '',
                "systemPrompt": row['system_prompt'] or '',
                "rules": row['rules'] or '',
                "outputTemplate": row['output_template'] or '',
                "userPrompt": row['user_prompt'] or '',
                "fileNamingRule": row['file_naming_rule'] or '',
                "summaryPrompt": row['summary_prompt'] or '',
                "enabled": bool(row['enabled']),
                "createdAt": row['created_at'].isoformat() if row['created_at'] else datetime.now().isoformat(),
                "updatedAt": row['updated_at'].isoformat() if row['updated_at'] else datetime.now().isoformat()
            })
        return {"success": True, "data": parsers}
    except Exception as e:
        print(f"[API] 获取解析器列表失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/parsers")
async def save_parser(parser: Dict[str, Any]):
    """保存文档解析器 - 持久化到MariaDB"""
    parser_id = parser.get("id")
    if not parser_id:
        return {"success": False, "error": "解析器ID不能为空"}

    try:
        # 检查是否存在
        existing = db.execute_query("SELECT id FROM document_parsers WHERE id=%s", (parser_id,))

        if existing:
            # 更新
            sql = """
                UPDATE document_parsers SET
                    name=%s, description=%s, system_prompt=%s, rules=%s,
                    file_naming_rule=%s, output_template=%s, user_prompt=%s,
                    summary_prompt=%s, enabled=%s, updated_at=%s
                WHERE id=%s
            """
            params = (
                parser.get('name', ''),
                parser.get('description', ''),
                parser.get('systemPrompt', ''),
                parser.get('rules', ''),
                parser.get('fileNamingRule', ''),
                parser.get('outputTemplate', ''),
                parser.get('userPrompt', ''),
                parser.get('summaryPrompt', ''),
                parser.get('enabled', True),
                datetime.now(),
                parser_id
            )
        else:
            # 插入
            sql = """
                INSERT INTO document_parsers
                (id, name, description, system_prompt, rules, file_naming_rule,
                 output_template, user_prompt, summary_prompt, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                parser_id,
                parser.get('name', ''),
                parser.get('description', ''),
                parser.get('systemPrompt', ''),
                parser.get('rules', ''),
                parser.get('fileNamingRule', ''),
                parser.get('outputTemplate', ''),
                parser.get('userPrompt', ''),
                parser.get('summaryPrompt', ''),
                parser.get('enabled', True),
                datetime.now(),
                datetime.now()
            )

        db.execute_update(sql, params)
        print(f"[API] 解析器已保存到MariaDB: {parser_id}")

        # 同时更新内存缓存
        parser["updatedAt"] = datetime.now().isoformat()
        document_parsers[parser_id] = parser

        return {"success": True, "data": parser}
    except Exception as e:
        print(f"[API] 保存解析器失败: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/parsers/{parser_id}")
async def delete_parser(parser_id: str):
    """删除文档解析器 - 从MariaDB删除"""
    try:
        db.execute_update("DELETE FROM document_parsers WHERE id=%s", (parser_id,))
        if parser_id in document_parsers:
            del document_parsers[parser_id]
        print(f"[API] 解析器已删除: {parser_id}")
        return {"success": True, "data": None}
    except Exception as e:
        print(f"[API] 删除解析器失败: {e}")
        return {"success": False, "error": str(e)}

# ============== 日志 API ==============

@app.get("/api/logs")
async def get_logs(
    level: Optional[str] = None,
    module: Optional[str] = None,
    search: Optional[str] = None,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None,
    page: int = 1,
    pageSize: int = 50
):
    """获取日志列表 - 支持时间范围、搜索、筛选"""
    try:
        # 构建查询
        where_clause = []
        params = []

        if level:
            where_clause.append("level = %s")
            params.append(level)
        if module:
            where_clause.append("module = %s")
            params.append(module)
        if search:
            where_clause.append("(message LIKE %s OR details LIKE %s)")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        if startTime:
            where_clause.append("created_at >= %s")
            params.append(startTime)
        if endTime:
            where_clause.append("created_at <= %s")
            params.append(endTime)

        where_sql = ""
        if where_clause:
            where_sql = "WHERE " + " AND ".join(where_clause)

        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM system_logs {where_sql}"
        count_result = db.execute_query(count_sql, tuple(params) if params else None)
        total = count_result[0]['total'] if count_result else 0

        # 获取分页数据
        sql = f"""SELECT id, level, module, message, details, created_at
                  FROM system_logs {where_sql}
                  ORDER BY created_at DESC
                  LIMIT %s OFFSET %s"""
        params.extend([pageSize, (page - 1) * pageSize])

        results = db.execute_query(sql, tuple(params))

        items = []
        for row in results:
            items.append({
                "id": str(row['id']),
                "level": row['level'],
                "module": row['module'],
                "message": row['message'],
                "timestamp": row['created_at'].isoformat() if row['created_at'] else datetime.now().isoformat(),
                "details": json.loads(row['details']) if row['details'] else None
            })

        return {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "totalPages": (total + pageSize - 1) // pageSize
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取日志失败: {str(e)}"
        }

@app.get("/api/logs/stats")
async def get_log_stats():
    """获取日志统计"""
    try:
        # 从数据库统计
        results = db.execute_query("""
            SELECT level, COUNT(*) as count 
            FROM system_logs 
            GROUP BY level
        """)
        by_level = {row['level']: row['count'] for row in results}
        
        results = db.execute_query("""
            SELECT module, COUNT(*) as count 
            FROM system_logs 
            GROUP BY module
        """)
        by_module = {row['module']: row['count'] for row in results}
        
        return {
            "success": True,
            "data": {
                "byLevel": by_level,
                "byModule": by_module
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取统计失败: {str(e)}"
        }

@app.post("/api/logs/clear")
async def clear_logs(olderThan: Optional[str] = None):
    """清理日志"""
    global system_logs
    try:
        if olderThan:
            # 清理特定时间之前的日志
            cutoff = datetime.fromisoformat(olderThan)
            db.execute_update(
                "DELETE FROM system_logs WHERE created_at < %s",
                (cutoff,)
            )
            system_logs = [log for log in system_logs if log['timestamp'] > olderThan]
        else:
            # 清理所有日志
            db.execute_update("DELETE FROM system_logs", ())
            system_logs = []
        
        return {
            "success": True,
            "message": "清理日志成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"清理日志失败：{str(e)}"
        }


# ============== 分级日志查询 API ==============

@app.get("/api/logs/raw")
async def get_raw_logs(
    requestId: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    level: Optional[str] = None,
    module: Optional[str] = None,
    page: int = 1,
    pageSize: int = 50
):
    """
    查询完整原型日志 - 所有请求的完整流水（使用新的日志系统）
    
    Args:
        requestId: 请求 ID（精确匹配）
        method: HTTP 方法
        path: 请求路径（支持模糊匹配）
        level: 日志级别
        module: 模块名称
        page: 页码
        pageSize: 每页数量
    """
    try:
        if LOGGING_SYSTEM_AVAILABLE:
            # 使用新的日志系统
            result = logging_system.get_raw_logs(
                level=level,
                module=module,
                api_path=path,
                request_id=requestId,
                page=page,
                page_size=pageSize
            )
            return {
                "success": True,
                "data": result
            }
        else:
            # 回退到旧系统
            return {
                "success": True,
                "data": {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": pageSize
                }
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"查询原始日志失败：{str(e)}"
        }


@app.get("/api/logs/api-stats")
async def get_api_stats(
    apiPath: Optional[str] = None,
    method: Optional[str] = None,
    sortBy: str = "total_calls"
):
    """
    查询接口粒度统计 - 按接口聚合统计（使用新的日志系统）
    
    Args:
        apiPath: API 路径（支持模糊匹配）
        method: HTTP 方法
        sortBy: 排序字段
    """
    try:
        if LOGGING_SYSTEM_AVAILABLE:
            # 使用新的日志系统
            items = logging_system.get_api_summary(api_path=apiPath)
            
            # 计算错误率
            for item in items:
                total = item.get('total_calls', 0)
                failed = item.get('failed_calls', 0)
                item['error_rate'] = round((failed / total * 100), 2) if total > 0 else 0
            
            # 排序
            if sortBy == 'error_rate':
                items.sort(key=lambda x: x['error_rate'], reverse=True)
            elif sortBy == 'avg_duration':
                items.sort(key=lambda x: x.get('avg_duration_ms', 0), reverse=True)
            else:  # default: total_calls
                items.sort(key=lambda x: x.get('total_calls', 0), reverse=True)
            
            return {
                "success": True,
                "data": {
                    "items": items,
                    "total": len(items)
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "items": [],
                    "total": 0
                }
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"查询接口统计失败：{str(e)}"
        }


@app.get("/api/logs/operations")
async def get_operation_logs(
    operationType: Optional[str] = None,
    operationId: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    pageSize: int = 50
):
    """
    查询操作粒度日志 - 具体业务操作的详情（使用新的日志系统）
    
    Args:
        operationType: 操作类型（如 video_download, chat_send, link_analysis）
        operationId: 操作 ID
        status: 状态（success/failed）
        page: 页码
        pageSize: 每页数量
    """
    try:
        if LOGGING_SYSTEM_AVAILABLE:
            # 使用新的日志系统
            result = logging_system.get_operation_logs(
                operation_type=operationType,
                status=status,
                request_id=operationId,
                page=page,
                page_size=pageSize
            )
            return {
                "success": True,
                "data": result
            }
        else:
            return {
                "success": True,
                "data": {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": pageSize
                }
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"查询操作日志失败：{str(e)}"
        }


@app.get("/api/logs/dashboard")
async def get_logs_dashboard():
    """
    获取日志仪表盘数据 - 综合统计信息
    """
    try:
        # 系统日志统计
        system_logs_stats = db.execute_query("""
            SELECT level, COUNT(*) as count 
            FROM system_logs 
            GROUP BY level
        """)
        by_level = {row['level']: row['count'] for row in system_logs_stats}
        
        # 接口调用统计（最近 1 小时）
        api_stats_result = db.execute_query("""
            SELECT 
                COUNT(*) as total_calls,
                AVG(duration_ms) as avg_duration,
                SUM(CASE WHEN status_code >= 200 AND status_code < 400 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM api_stats_log
            WHERE called_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        
        api_stats = api_stats_result[0] if api_stats_result else {}
        
        # 操作统计（最近 1 小时）
        operation_stats_result = db.execute_query("""
            SELECT 
                operation_type,
                COUNT(*) as count,
                AVG(duration_ms) as avg_duration,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM operation_logs
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY operation_type
        """)
        
        by_operation = {}
        for row in operation_stats_result:
            by_operation[row['operation_type']] = {
                "count": row['count'],
                "avg_duration_ms": float(row['avg_duration_ms']) if row['avg_duration_ms'] else 0,
                "success_count": row['success_count']
            }
        
        # 慢接口 Top 10
        slow_apis_result = db.execute_query("""
            SELECT 
                api_path,
                method,
                AVG(duration_ms) as avg_duration,
                COUNT(*) as count
            FROM api_stats_log
            WHERE called_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY api_path, method
            HAVING COUNT(*) >= 5
            ORDER BY avg_duration DESC
            LIMIT 10
        """)
        
        slow_apis = []
        for row in slow_apis_result:
            slow_apis.append({
                "api_path": row['api_path'],
                "method": row['method'],
                "avg_duration_ms": float(row['avg_duration']) if row['avg_duration'] else 0,
                "count": row['count']
            })
        
        return {
            "success": True,
            "data": {
                "systemLogs": {
                    "byLevel": by_level
                },
                "apiCalls": {
                    "total_calls": api_stats.get('total_calls', 0),
                    "avg_duration_ms": float(api_stats.get('avg_duration', 0)) if api_stats.get('avg_duration') else 0,
                    "success_count": api_stats.get('success_count', 0),
                    "error_count": api_stats.get('error_count', 0)
                },
                "operations": by_operation,
                "slowApis": slow_apis
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取仪表盘数据失败：{str(e)}"
        }


# 添加日志的工具函数
def add_log(level: str, module: str, message: str, details: Optional[Dict] = None):
    """添加系统日志 - 持久化到数据库（向后兼容）"""
    global system_logs
    
    try:
        # 插入到数据库 - 使用 execute_update
        db.execute_update(
            """INSERT INTO system_logs (level, module, message, details, created_at) 
               VALUES (%s, %s, %s, %s, %s)""",
            (level, module, message, json.dumps(details) if details else None, datetime.now())
        )
    except Exception as e:
        print(f"[日志记录失败] {e}")
    
    # 同时添加到内存（用于快速访问）
    log = {
        "id": f"log-{len(system_logs) if 'system_logs' in globals() else 0}-{datetime.now().timestamp()}",
        "level": level,
        "module": module,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    system_logs.append(log)
    # 限制日志数量
    if len(system_logs) > 1000:
        system_logs = system_logs[-1000:]


def log_raw_request(request_id: str, method: str, path: str, headers: Dict, body: Optional[Dict], 
                   start_time: datetime, client_ip: str = ""):
    """
    记录完整原型日志 - 所有请求的完整流水
    
    Args:
        request_id: 请求唯一标识
        method: HTTP 方法
        path: 请求路径
        headers: 请求头
        body: 请求体
        start_time: 请求开始时间
        client_ip: 客户端 IP
    """
    global raw_logs
    
    raw_log = {
        "request_id": request_id,
        "type": "raw_request",
        "method": method,
        "path": path,
        "headers": headers,
        "body": body,
        "start_time": start_time.isoformat(),
        "client_ip": client_ip,
        "timestamp": start_time.isoformat()
    }
    
    raw_logs.append(raw_log)
    
    # 限制内存中的日志数量
    if len(raw_logs) > 5000:
        raw_logs = raw_logs[-5000:]
    
    # 持久化到数据库
    try:
        db.execute_update(
            """INSERT INTO raw_logs 
               (request_id, method, path, headers, body, start_time, client_ip, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (request_id, method, path, json.dumps(headers), json.dumps(body) if body else None,
             start_time, client_ip, datetime.now())
        )
    except Exception as e:
        print(f"[记录原始日志失败] {e}")


def log_raw_response(request_id: str, status_code: int, response_body: Optional[Dict], 
                    end_time: datetime, duration_ms: float):
    """
    记录完整响应日志 - 与请求对应
    
    Args:
        request_id: 请求唯一标识（与 log_raw_request 的 request_id 对应）
        status_code: HTTP 状态码
        response_body: 响应体
        end_time: 响应结束时间
        duration_ms: 耗时（毫秒）
    """
    global raw_logs
    
    # 查找对应的请求日志并更新
    for log in reversed(raw_logs):
        if log.get("request_id") == request_id:
            log.update({
                "status_code": status_code,
                "response_body": response_body,
                "end_time": end_time.isoformat(),
                "duration_ms": duration_ms,
                "complete": True
            })
            break
    
    # 持久化到数据库
    try:
        db.execute_update(
            """UPDATE raw_logs SET status_code=%s, response_body=%s, end_time=%s, duration_ms=%s, complete=1
               WHERE request_id=%s""",
            (status_code, json.dumps(response_body) if response_body else None,
             end_time, duration_ms, request_id)
        )
    except Exception as e:
        print(f"[记录响应日志失败] {e}")


def log_api_summary(api_path: str, method: str, status_code: int, duration_ms: float, 
                   timestamp: datetime, extra_info: Optional[Dict] = None):
    """
    记录接口粒度日志 - 按接口聚合统计
    
    Args:
        api_path: API 路径
        method: HTTP 方法
        status_code: 状态码
        duration_ms: 耗时（毫秒）
        timestamp: 调用时间
        extra_info: 额外信息
    """
    global api_stats
    
    # 初始化统计
    key = f"{method}:{api_path}"
    if key not in api_stats:
        api_stats[key] = {
            "api_path": api_path,
            "method": method,
            "count": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0,
            "min_duration_ms": float('inf'),
            "max_duration_ms": 0,
            "success_count": 0,
            "error_count": 0,
            "last_called": None,
            "recent_calls": []  # 最近 100 次调用详情
        }
    
    # 更新统计
    stats = api_stats[key]
    stats["count"] += 1
    stats["total_duration_ms"] += duration_ms
    stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
    stats["min_duration_ms"] = min(stats["min_duration_ms"], duration_ms)
    stats["max_duration_ms"] = max(stats["max_duration_ms"], duration_ms)
    stats["last_called"] = timestamp.isoformat()
    
    if 200 <= status_code < 400:
        stats["success_count"] += 1
    else:
        stats["error_count"] += 1
    
    # 记录最近调用
    call_detail = {
        "timestamp": timestamp.isoformat(),
        "status_code": status_code,
        "duration_ms": duration_ms,
        "extra_info": extra_info
    }
    stats["recent_calls"].append(call_detail)
    if len(stats["recent_calls"]) > 100:
        stats["recent_calls"] = stats["recent_calls"][-100:]
    
    # 持久化到数据库
    try:
        db.execute_update(
            """INSERT INTO api_stats_log 
               (api_path, method, status_code, duration_ms, called_at, extra_info) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (api_path, method, status_code, duration_ms, timestamp, 
             json.dumps(extra_info) if extra_info else None)
        )
    except Exception as e:
        print(f"[记录接口统计失败] {e}")


def log_operation(operation_type: str, operation_id: str, inputs: Dict, outputs: Optional[Dict],
                 start_time: datetime, end_time: datetime, status: str, 
                 error_message: Optional[str] = None, extra_details: Optional[Dict] = None):
    """
    记录操作粒度日志 - 具体业务操作的详情
    
    Args:
        operation_type: 操作类型（如：video_download, chat_send, knowledge_base_query）
        operation_id: 操作唯一标识
        inputs: 关键输入参数
        outputs: 输出结果（精简版，避免过大）
        start_time: 开始时间
        end_time: 结束时间
        status: 状态（success/failed）
        error_message: 错误消息
        extra_details: 额外详情
    """
    global operation_logs
    
    duration_ms = (end_time - start_time).total_seconds() * 1000
    
    operation_log = {
        "operation_type": operation_type,
        "operation_id": operation_id,
        "inputs": inputs,
        "outputs": outputs,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_ms": duration_ms,
        "status": status,
        "error_message": error_message,
        "extra_details": extra_details,
        "timestamp": start_time.isoformat()
    }
    
    operation_logs.append(operation_log)
    
    # 限制内存中的日志数量
    if len(operation_logs) > 2000:
        operation_logs = operation_logs[-2000:]
    
    # 持久化到数据库
    try:
        db.execute_update(
            """INSERT INTO operation_logs 
               (operation_type, operation_id, inputs, outputs, start_time, end_time, 
                duration_ms, status, error_message, extra_details, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (operation_type, operation_id, json.dumps(inputs), 
             json.dumps(outputs) if outputs else None,
             start_time, end_time, duration_ms, status, 
             error_message, json.dumps(extra_details) if extra_details else None,
             datetime.now())
        )
    except Exception as e:
        print(f"[记录操作日志失败] {e}")


# 装饰器：自动记录 API 日志
def log_api_endpoint(operation_type: str):
    """
    API 日志装饰器 - 自动记录接口粒度日志和操作粒度日志
    
    Usage:
        @app.post("/api/video/download")
        @log_api_endpoint("video_download")
        async def download_video(request: VideoRequest):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            from fastapi import Request
            
            # 获取 request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # 记录开始时间
            start_time = datetime.now()
            start_timestamp = time.time()
            
            # 生成请求 ID
            request_id = f"req-{int(start_timestamp * 1000)}-{id(request) if request else 0}"
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 计算耗时
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                # 确定状态码
                status_code = 200
                
                # 记录接口统计日志
                log_api_summary(
                    api_path=request.path if request else func.__name__,
                    method=request.method if request else "CALL",
                    status_code=status_code,
                    duration_ms=duration_ms,
                    timestamp=end_time
                )
                
                # 记录操作日志
                log_operation(
                    operation_type=operation_type,
                    operation_id=request_id,
                    inputs={},  # 可以从 kwargs 提取
                    outputs={"status": "success"},
                    start_time=start_time,
                    end_time=end_time,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                # 异常情况
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                # 记录操作日志（失败）
                log_operation(
                    operation_type=operation_type,
                    operation_id=request_id,
                    inputs={},
                    outputs=None,
                    start_time=start_time,
                    end_time=end_time,
                    status="failed",
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator

# 从数据库加载日志
def load_logs_from_db(limit: int = 1000):
    """从数据库加载日志"""
    global system_logs
    try:
        results = db.execute_query(
            """SELECT id, level, module, message, details, created_at 
               FROM system_logs ORDER BY created_at DESC LIMIT %s""",
            (limit,)
        )
        system_logs = []
        for row in results:
            system_logs.append({
                "id": str(row['id']),
                "level": row['level'],
                "module": row['module'],
                "message": row['message'],
                "timestamp": row['created_at'].isoformat() if row['created_at'] else datetime.now().isoformat(),
                "details": json.loads(row['details']) if row['details'] else None
            })
        print(f"[WebAPI] 从数据库加载 {len(system_logs)} 条日志")
    except Exception as e:
        print(f"[WebAPI] 加载日志失败: {e}")
        system_logs = []

# ============== 主程序入口 ==============

if __name__ == "__main__":
    print("=" * 50)
    print("SuperBizAgent Web API 服务启动中...")
    print("=" * 50)
    print("API文档: http://localhost:8000/docs")
    print("前端地址: http://localhost:3000")
    print("=" * 50)
    
    uvicorn.run(
        "web_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
