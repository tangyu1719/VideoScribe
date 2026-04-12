#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链接分析服务 - 从本地工具移植
包含链接解析、OCR识别、内容提取等功能
"""

import os
import re
import json
import time
import base64
import hashlib
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from pathlib import Path
import requests
from urllib.parse import urlparse


@dataclass
class LinkAnalysisResult:
    """链接分析结果"""
    success: bool
    link_type: str
    title: Optional[str]
    content: Optional[str]
    images: List[str]
    error_message: Optional[str] = None
    ocr_text: Optional[str] = None


class LinkAnalyzerService:
    """链接分析服务"""
    
    def __init__(self, ocr_api_key: Optional[str] = None):
        """
        初始化链接分析器
        
        Args:
            ocr_api_key: OCR API密钥（可选）
        """
        self.ocr_api_key = ocr_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_link(self, url: str) -> LinkAnalysisResult:
        """
        分析链接内容
        
        Args:
            url: 链接URL
        
        Returns:
            LinkAnalysisResult: 分析结果
        """
        try:
            # 判断链接类型
            link_type = self._judge_link_type(url)
            
            if link_type == "douyin_video":
                return self._analyze_video(url)
            elif link_type == "xiaohongshu":
                return self._analyze_xiaohongshu(url)
            elif link_type == "douyin_image":
                return self._analyze_douyin_image(url)
            else:
                return self._analyze_general(url)
                
        except Exception as e:
            return LinkAnalysisResult(
                success=False,
                link_type="unknown",
                title=None,
                content=None,
                images=[],
                error_message=str(e)
            )
    
    def _judge_link_type(self, url: str) -> str:
        """
        判断链接类型
        
        Args:
            url: 链接URL
        
        Returns:
            str: 链接类型
        """
        url_lower = url.lower()
        
        # 抖音链接
        if 'douyin.com' in url_lower or 'iesdouyin.com' in url_lower:
            return self._detect_douyin_type(url)
        
        # 小红书链接
        if 'xiaohongshu.com' in url_lower or 'xhslink.com' in url_lower:
            return "xiaohongshu"
        
        # B站链接
        if 'bilibili.com' in url_lower or 'b23.tv' in url_lower:
            return "bilibili"
        
        # YouTube链接
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return "youtube"
        
        return "general"
    
    def _detect_douyin_type(self, url: str) -> str:
        """
        检测抖音链接类型
        
        Args:
            url: 抖音链接
        
        Returns:
            str: 类型(video/image)
        """
        try:
            # 访问链接获取页面信息
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15'
            }
            response = self.session.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            if 'video' in response.url or '/v.' in response.url:
                return "douyin_video"
            elif 'note' in response.url or '/n.' in response.url:
                return "douyin_image"
            else:
                # 通过内容判断
                if 'video' in response.text[:5000]:
                    return "douyin_video"
                else:
                    return "douyin_image"
                    
        except:
            return "douyin_video"  # 默认视频
    
    def _analyze_video(self, url: str) -> LinkAnalysisResult:
        """
        分析视频链接
        
        Args:
            url: 视频链接
        
        Returns:
            LinkAnalysisResult: 分析结果
        """
        try:
            # 使用yt-dlp获取视频信息
            import subprocess
            
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--skip-download",
                "--quiet",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout:
                video_info = json.loads(result.stdout.strip().split('\n')[0])
                
                return LinkAnalysisResult(
                    success=True,
                    link_type="video",
                    title=video_info.get('title'),
                    content=video_info.get('description'),
                    images=[video_info.get('thumbnail', '')],
                    ocr_text=None
                )
            else:
                return LinkAnalysisResult(
                    success=False,
                    link_type="video",
                    title=None,
                    content=None,
                    images=[],
                    error_message="无法获取视频信息"
                )
                
        except Exception as e:
            return LinkAnalysisResult(
                success=False,
                link_type="video",
                title=None,
                content=None,
                images=[],
                error_message=str(e)
            )
    
    def _analyze_xiaohongshu(self, url: str) -> LinkAnalysisResult:
        """
        分析小红书链接
        
        Args:
            url: 小红书链接
        
        Returns:
            LinkAnalysisResult: 分析结果
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.DOTALL)
            title = title_match.group(1).strip() if title_match else None
            
            # 提取内容
            content_match = re.search(r'desc":"(.*?)"', response.text)
            content = content_match.group(1) if content_match else None
            
            # 提取图片
            images = re.findall(r'https://[^"\s]+\.jpg', response.text)
            
            # OCR识别
            ocr_text = None
            if images and self.ocr_api_key:
                # 下载第一张图片进行OCR
                image_data = self._download_image(images[0])
                if image_data:
                    ocr_result = self._ocr_image(image_data)
                    if ocr_result:
                        ocr_text = self._extract_text_from_ocr(ocr_result)
            
            return LinkAnalysisResult(
                success=True,
                link_type="xiaohongshu",
                title=title,
                content=content,
                images=images[:5],  # 最多5张图片
                ocr_text=ocr_text
            )
            
        except Exception as e:
            return LinkAnalysisResult(
                success=False,
                link_type="xiaohongshu",
                title=None,
                content=None,
                images=[],
                error_message=str(e)
            )
    
    def _analyze_douyin_image(self, url: str) -> LinkAnalysisResult:
        """
        分析抖音图文
        
        Args:
            url: 抖音图文链接
        
        Returns:
            LinkAnalysisResult: 分析结果
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.DOTALL)
            title = title_match.group(1).strip() if title_match else None
            
            # 提取内容（描述）
            content_match = re.search(r'desc":"(.*?)"', response.text)
            content = content_match.group(1) if content_match else None
            
            # 提取图片
            images = re.findall(r'https://[^"\s]+\.jpg', response.text)
            
            # OCR识别
            ocr_text = None
            if images and self.ocr_api_key:
                # 下载第一张图片进行OCR
                image_data = self._download_image(images[0])
                if image_data:
                    ocr_result = self._ocr_image(image_data)
                    if ocr_result:
                        ocr_text = self._extract_text_from_ocr(ocr_result)
            
            return LinkAnalysisResult(
                success=True,
                link_type="douyin_image",
                title=title,
                content=content,
                images=images[:5],
                ocr_text=ocr_text
            )
            
        except Exception as e:
            return LinkAnalysisResult(
                success=False,
                link_type="douyin_image",
                title=None,
                content=None,
                images=[],
                error_message=str(e)
            )
    
    def _analyze_general(self, url: str) -> LinkAnalysisResult:
        """
        通用链接分析
        
        Args:
            url: 通用链接
        
        Returns:
            LinkAnalysisResult: 分析结果
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.DOTALL)
            title = title_match.group(1).strip() if title_match else None
            
            # 提取meta描述
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', 
                                  response.text, re.IGNORECASE)
            content = desc_match.group(1) if desc_match else None
            
            # 提取图片
            images = re.findall(r'<img[^>]*src=["\']([^"\']+)', response.text)
            
            return LinkAnalysisResult(
                success=True,
                link_type="general",
                title=title,
                content=content,
                images=images[:3]
            )
            
        except Exception as e:
            return LinkAnalysisResult(
                success=False,
                link_type="general",
                title=None,
                content=None,
                images=[],
                error_message=str(e)
            )
    
    def _download_image(self, url: str) -> Optional[bytes]:
        """
        下载图片
        
        Args:
            url: 图片URL
        
        Returns:
            Optional[bytes]: 图片数据
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except:
            return None
    
    def _ocr_image(self, image_data: bytes, max_retries: int = 3) -> Optional[Dict]:
        """
        OCR识别图片
        
        Args:
            image_data: 图片数据
            max_retries: 最大重试次数
        
        Returns:
            Optional[Dict]: OCR结果
        """
        if not self.ocr_api_key:
            return None
        
        # 这里使用示例OCR API，实际使用时需要替换为真实的OCR服务
        # 例如：百度OCR、腾讯OCR、阿里云OCR等
        
        try:
            # 示例：使用百度OCR API
            # 实际实现需要根据具体的OCR服务提供商进行调整
            
            # 将图片转为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 这里只是一个示例，实际使用时需要替换为真实的API调用
            # 返回模拟结果
            return {
                "words_result": [
                    {"words": "示例OCR文本"}
                ]
            }
            
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return None
    
    def _extract_text_from_ocr(self, ocr_result: Dict) -> str:
        """
        从OCR结果提取文本
        
        Args:
            ocr_result: OCR结果
        
        Returns:
            str: 提取的文本
        """
        try:
            if 'words_result' in ocr_result:
                texts = [item.get('words', '') for item in ocr_result['words_result']]
                return '\n'.join(texts)
            return ""
        except:
            return ""


# 便捷函数
def create_link_analyzer_service(ocr_api_key: Optional[str] = None) -> LinkAnalyzerService:
    """创建链接分析服务实例"""
    return LinkAnalyzerService(ocr_api_key)
