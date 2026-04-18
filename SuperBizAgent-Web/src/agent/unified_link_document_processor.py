#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一链接+文档处理模块
将链接分析和多模态文档处理集成到统一的文字分析流程

功能：
1. 链接输入：支持网页链接、小红书、抖音等
2. 文档上传：支持图片、PDF、Word、Markdown、CSV、音频、视频
3. 统一处理流程：类型识别 → 内容提取 → 文字分析 → AI摘要
"""

import os
import re
import json
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import requests

# 导入现有模块
try:
    from link_analyzer import LinkAnalyzer
    LINK_ANALYZER_AVAILABLE = True
except ImportError:
    LINK_ANALYZER_AVAILABLE = False
    print("[UnifiedProcessor] 链接分析器未安装")

try:
    from document_processor import DocumentProcessor, DocumentType, ProcessingResult, ExtractedContent
    DOC_PROCESSOR_AVAILABLE = True
except ImportError:
    DOC_PROCESSOR_AVAILABLE = False
    print("[UnifiedProcessor] 文档处理器未安装")

try:
    from video_downloader import download_video, speech_to_text
    VIDEO_DOWNLOADER_AVAILABLE = True
except ImportError:
    VIDEO_DOWNLOADER_AVAILABLE = False
    print("[UnifiedProcessor] 视频下载器未安装")


class InputType(Enum):
    """输入类型"""
    URL = "url"                     # 网页链接
    LOCAL_FILE = "local_file"       # 本地文件


class ContentType(Enum):
    """内容类型"""
    VIDEO = "video"                 # 视频
    AUDIO = "audio"                 # 音频
    IMAGE = "image"                 # 图片
    DOCUMENT = "document"           # 文档(PDF/Word/Markdown)
    WEB_PAGE = "web_page"           # 网页
    SOCIAL_MEDIA = "social_media"   # 社交媒体(小红书/抖音图文)
    UNKNOWN = "unknown"


@dataclass
class ProcessingStage:
    """处理阶段"""
    name: str
    status: str = "pending"  # pending, in_progress, completed, failed
    progress: int = 0
    message: str = ""
    result: Any = None


@dataclass
class UnifiedProcessingResult:
    """统一处理结果"""
    success: bool = False
    input_type: InputType = InputType.URL
    content_type: ContentType = ContentType.UNKNOWN
    source: str = ""  # URL或文件路径
    title: str = ""
    text_content: str = ""  # 提取的文本内容
    extracted_images: List[Dict] = field(default_factory=list)
    extracted_tables: List[List[List[str]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ai_summary: str = ""
    output_file: str = ""
    stages: Dict[str, ProcessingStage] = field(default_factory=dict)
    error: Optional[str] = None
    processing_time: float = 0.0


class UnifiedLinkDocumentProcessor:
    """统一链接+文档处理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 初始化子处理器
        self.link_analyzer = LinkAnalyzer() if LINK_ANALYZER_AVAILABLE else None
        self.doc_processor = DocumentProcessor() if DOC_PROCESSOR_AVAILABLE else None
        
        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.log_callback: Optional[Callable] = None
        
    def set_callbacks(self, progress_callback: Callable = None, log_callback: Callable = None):
        """设置回调函数"""
        self.progress_callback = progress_callback
        self.log_callback = log_callback
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message, level)
        print(f"[UnifiedProcessor] [{level}] {message}")
    
    def _update_progress(self, stage: str, progress: int, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(stage, progress, message)
        self._log(f"[{stage}] {progress}% - {message}")
    
    def process(self, input_source: str, **kwargs) -> UnifiedProcessingResult:
        """
        统一处理入口
        
        Args:
            input_source: URL或本地文件路径
            **kwargs: 额外参数
                - is_url: 是否为URL（自动检测）
                - llm_config: LLM配置
                - output_dir: 输出目录
                - user_prompt: 用户自定义提示词
        
        Returns:
            UnifiedProcessingResult: 处理结果
        """
        start_time = time.time()
        
        # 判断输入类型
        is_url = kwargs.get('is_url', self._is_url(input_source))
        input_type = InputType.URL if is_url else InputType.LOCAL_FILE
        
        result = UnifiedProcessingResult(
            input_type=input_type,
            source=input_source
        )
        
        try:
            if input_type == InputType.URL:
                # 处理链接
                result = self._process_url(input_source, result, **kwargs)
            else:
                # 处理本地文件
                result = self._process_local_file(input_source, result, **kwargs)
            
            # 如果处理成功，进行AI分析
            if result.success and result.text_content:
                result = self._perform_ai_analysis(result, **kwargs)
            
            # 生成输出文件
            if result.success:
                result = self._generate_output(result, **kwargs)
                
        except Exception as e:
            result.success = False
            result.error = str(e)
            self._log(f"处理失败: {e}", "ERROR")
        
        result.processing_time = time.time() - start_time
        return result
    
    def _is_url(self, source: str) -> bool:
        """判断是否为URL"""
        url_patterns = [
            r'^https?://',
            r'^www\.'
        ]
        for pattern in url_patterns:
            if re.match(pattern, source, re.IGNORECASE):
                return True
        return False
    
    def _process_url(self, url: str, result: UnifiedProcessingResult, **kwargs) -> UnifiedProcessingResult:
        """处理URL链接"""
        self._update_progress("detect_type", 10, "检测链接类型...")
        
        # 使用link_analyzer分析链接
        if not self.link_analyzer:
            result.success = False
            result.error = "链接分析器不可用"
            return result
        
        # 判断链接类型
        link_type = self.link_analyzer._judge_link_type(url)
        self._log(f"检测到链接类型: {link_type}")
        
        # 根据类型处理
        if link_type in ['xiaohongshu', 'douyin_image']:
            # 社交媒体图文
            result.content_type = ContentType.SOCIAL_MEDIA
            result = self._process_social_media(url, link_type, result)
        elif link_type == 'video' or self._is_video_url(url):
            # 视频链接
            result.content_type = ContentType.VIDEO
            result = self._process_video_url(url, result, **kwargs)
        else:
            # 通用网页
            result.content_type = ContentType.WEB_PAGE
            result = self._process_web_page(url, result)
        
        return result
    
    def _is_video_url(self, url: str) -> bool:
        """判断是否为视频链接"""
        video_indicators = [
            'youtube.com', 'youtu.be', 'bilibili.com', 'v.qq.com',
            'youku.com', 'iqiyi.com', 'vimeo.com', 'dailymotion.com'
        ]
        return any(indicator in url for indicator in video_indicators)
    
    def _process_social_media(self, url: str, platform: str, result: UnifiedProcessingResult) -> UnifiedProcessingResult:
        """处理社交媒体链接（小红书/抖音图文）"""
        self._update_progress("extract_content", 30, f"提取{platform}内容...")
        
        try:
            if platform == 'xiaohongshu':
                analysis = self.link_analyzer._analyze_xiaohongshu(url)
            else:  # douyin_image
                analysis = self.link_analyzer._analyze_douyin_image(url)
            
            if 'error' in analysis:
                result.success = False
                result.error = analysis['error']
                return result
            
            # 填充结果
            result.title = analysis.get('title', '')
            result.text_content = analysis.get('text_content', '')
            result.extracted_images = [
                {"url": img, "type": "remote"} 
                for img in analysis.get('image_links', [])
            ]
            result.metadata = {
                'platform': platform,
                'image_count': len(analysis.get('image_links', [])),
                'image_analysis': analysis.get('image_analysis', [])
            }
            result.success = True
            
            self._update_progress("extract_content", 60, f"提取完成，共{len(result.extracted_images)}张图片")
            
        except Exception as e:
            result.success = False
            result.error = f"社交媒体处理失败: {e}"
        
        return result
    
    def _process_video_url(self, url: str, result: UnifiedProcessingResult, **kwargs) -> UnifiedProcessingResult:
        """处理视频链接"""
        self._update_progress("download", 20, "下载视频...")
        
        try:
            # 下载视频
            if VIDEO_DOWNLOADER_AVAILABLE:
                video_file = download_video(url, self._log)
                
                if video_file and os.path.exists(video_file):
                    self._update_progress("transcribe", 50, "语音转文字...")
                    
                    # 语音转文字
                    transcript_result = speech_to_text(
                        video_file,
                        log_callback=self._log,
                        progress_callback=lambda p, m: self._update_progress("transcribe", 50 + p//2, m)
                    )
                    
                    if transcript_result:
                        result.text_content = transcript_result.get('full_text', '')
                        result.metadata = {
                            'video_file': video_file,
                            'segments': transcript_result.get('segments', [])
                        }
                        result.success = True
                        self._update_progress("transcribe", 90, "语音转文字完成")
                    else:
                        result.error = "语音转文字失败"
                else:
                    result.error = "视频下载失败"
            else:
                result.error = "视频下载器不可用"
                
        except Exception as e:
            result.success = False
            result.error = f"视频处理失败: {e}"
        
        return result
    
    def _process_web_page(self, url: str, result: UnifiedProcessingResult) -> UnifiedProcessingResult:
        """处理通用网页"""
        self._update_progress("extract_content", 30, "提取网页内容...")
        
        try:
            analysis = self.link_analyzer._analyze_general(url)
            
            if 'error' in analysis:
                result.success = False
                result.error = analysis['error']
                return result
            
            result.title = analysis.get('title', '')
            result.text_content = analysis.get('text_content', '')
            result.extracted_images = [
                {"url": img, "type": "remote"} 
                for img in analysis.get('image_links', [])
            ]
            result.metadata = {
                'platform': 'web',
                'image_count': len(analysis.get('image_links', []))
            }
            result.success = True
            
            self._update_progress("extract_content", 60, "网页内容提取完成")
            
        except Exception as e:
            result.success = False
            result.error = f"网页处理失败: {e}"
        
        return result
    
    def _process_local_file(self, file_path: str, result: UnifiedProcessingResult, **kwargs) -> UnifiedProcessingResult:
        """处理本地文件"""
        self._update_progress("detect_type", 10, "检测文件类型...")
        
        if not self.doc_processor:
            result.success = False
            result.error = "文档处理器不可用"
            return result
        
        try:
            # 使用文档处理器处理
            doc_result = self.doc_processor.process(file_path)
            
            if not doc_result.success:
                result.success = False
                result.error = doc_result.error
                return result
            
            # 映射文档类型到内容类型
            type_mapping = {
                DocumentType.IMAGE: ContentType.IMAGE,
                DocumentType.PDF: ContentType.DOCUMENT,
                DocumentType.DOCX: ContentType.DOCUMENT,
                DocumentType.MD: ContentType.DOCUMENT,
                DocumentType.CSV: ContentType.DOCUMENT,
                DocumentType.AUDIO: ContentType.AUDIO,
                DocumentType.VIDEO: ContentType.VIDEO,
            }
            result.content_type = type_mapping.get(doc_result.doc_type, ContentType.UNKNOWN)
            
            # 填充结果
            result.title = os.path.basename(file_path)
            result.text_content = doc_result.content.text
            result.extracted_images = doc_result.content.images
            result.extracted_tables = doc_result.content.tables
            result.metadata = {
                'file_type': doc_result.doc_type.value,
                'file_size': doc_result.file_size,
                **doc_result.content.metadata
            }
            result.success = True
            
            self._update_progress("extract_content", 60, f"文件处理完成，提取{len(result.text_content)}字符")
            
        except Exception as e:
            result.success = False
            result.error = f"文件处理失败: {e}"
        
        return result
    
    def _perform_ai_analysis(self, result: UnifiedProcessingResult, **kwargs) -> UnifiedProcessingResult:
        """执行AI分析"""
        self._update_progress("ai_analysis", 70, "AI分析中...")
        
        try:
            llm_config = kwargs.get('llm_config', {})
            user_prompt = kwargs.get('user_prompt', '')
            
            # 构建分析内容
            content = result.text_content
            if len(content) > 8000:
                content = content[:8000] + "..."
            
            # 调用AI分析
            ai_summary = self._call_llm(content, llm_config, user_prompt)
            result.ai_summary = ai_summary
            result.success = True
            
            self._update_progress("ai_analysis", 90, "AI分析完成")
            
        except Exception as e:
            self._log(f"AI分析失败: {e}", "WARNING")
            result.ai_summary = f"AI分析失败: {e}"
        
        return result
    
    def _call_llm(self, content: str, llm_config: Dict, user_prompt: str = "") -> str:
        """调用LLM进行分析"""
        try:
            api_key = llm_config.get('apiKey', '')
            base_url = llm_config.get('baseUrl', 'https://api.openai.com/v1')
            model = llm_config.get('model', 'gpt-3.5-turbo')
            
            if not api_key:
                return "未配置LLM API密钥"
            
            system_prompt = """你是一个专业的内容分析助手，擅长分析各种文档和媒体内容。
请对以下内容进行分析并生成结构化的摘要，包括：
1. 内容概览
2. 核心要点
3. 详细分析
4. 总结"""
            
            user_content = user_prompt + "\n\n" if user_prompt else ""
            user_content += f"请分析以下内容:\n\n{content}"
            
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
            
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API调用失败: {response.status_code}"
                
        except Exception as e:
            return f"AI分析异常: {e}"
    
    def _generate_output(self, result: UnifiedProcessingResult, **kwargs) -> UnifiedProcessingResult:
        """生成输出文件"""
        self._update_progress("generate_output", 95, "生成输出文件...")
        
        try:
            output_dir = kwargs.get('output_dir', 'OUTPUT')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成文件名
            timestamp = time.strftime('%m-%d', time.localtime())
            title = result.title or 'untitled'
            clean_title = re.sub(r'[^\w\u4e00-\u9fa5]', '_', title)[:30]
            
            # 确定前缀序号
            existing_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
            prefix = f"{len(existing_files) + 1:03d}"
            
            # 确定后缀
            if result.content_type == ContentType.VIDEO:
                suffix = '_视频分析.md'
            elif result.content_type == ContentType.AUDIO:
                suffix = '_音频分析.md'
            elif result.content_type == ContentType.SOCIAL_MEDIA:
                suffix = '_社媒分析.md'
            else:
                suffix = '_文档分析.md'
            
            filename = f"{prefix}-{timestamp}-{clean_title}{suffix}"
            output_path = os.path.join(output_dir, filename)
            
            # 生成Markdown内容
            md_content = self._generate_markdown(result)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            result.output_file = output_path
            self._update_progress("generate_output", 100, f"输出文件: {filename}")
            
        except Exception as e:
            self._log(f"生成输出文件失败: {e}", "WARNING")
        
        return result
    
    def _generate_markdown(self, result: UnifiedProcessingResult) -> str:
        """生成Markdown内容"""
        md = f"""# {result.title or '内容分析'}

## 基本信息
- 分析时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
- 内容类型: {result.content_type.value}
- 输入来源: {result.source}

"""
        
        # 添加提取的文本内容
        if result.text_content:
            md += f"""## 提取内容

{result.text_content}

"""
        
        # 添加图片信息
        if result.extracted_images:
            md += f"""## 图片信息
共提取 {len(result.extracted_images)} 张图片

"""
            for i, img in enumerate(result.extracted_images[:5], 1):  # 最多显示5张
                img_url = img.get('url', img.get('path', '未知'))
                md += f"- 图片{i}: {img_url}\n"
            if len(result.extracted_images) > 5:
                md += f"- ... 还有 {len(result.extracted_images) - 5} 张图片\n"
            md += "\n"
        
        # 添加AI分析摘要
        if result.ai_summary:
            md += f"""## AI分析摘要

{result.ai_summary}

"""
        
        # 添加元数据
        if result.metadata:
            md += """## 元数据

"""
            for key, value in result.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    md += f"- {key}: {value}\n"
            md += "\n"
        
        return md


# 便捷函数
def process_input(input_source: str, **kwargs) -> UnifiedProcessingResult:
    """
    便捷函数：处理输入（链接或文件）
    
    Args:
        input_source: URL或文件路径
        **kwargs: 额外参数
    
    Returns:
        UnifiedProcessingResult: 处理结果
    """
    processor = UnifiedLinkDocumentProcessor()
    return processor.process(input_source, **kwargs)


# 测试
if __name__ == "__main__":
    # 测试本地文件处理
    test_file = "test.pdf"  # 替换为实际测试文件
    if os.path.exists(test_file):
        result = process_input(test_file)
        print(json.dumps({
            'success': result.success,
            'content_type': result.content_type.value,
            'text_length': len(result.text_content),
            'output_file': result.output_file
        }, ensure_ascii=False, indent=2))
