#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态解析工具 - @tool 形式
支持：文本、图片、音频、视频、网页链接的多模态解析

使用方法：
    from multimodal_tool import MultimodalTool
    
    tool = MultimodalTool()
    result = tool.parse("path/to/file.jpg")  # 自动识别类型并解析
    result = tool.parse("https://example.com")  # 解析网页
"""

import os
import io
import base64
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    WEBPAGE = "webpage"
    PDF = "pdf"
    UNKNOWN = "unknown"


@dataclass
class ParsedContent:
    """解析后的内容"""
    content_type: ContentType
    text: str = ""                    # 文本内容（OCR/ASR/转录结果）
    raw_data: bytes = None            # 原始二进制数据
    base64_data: str = ""            # Base64编码数据
    metadata: Dict[str, Any] = None   # 元数据（尺寸、时长等）
    description: str = ""             # AI生成的描述
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MultimodalTool:
    """
    多模态解析工具
    
    支持解析：
    - 文本文件：.txt, .md, .doc, .docx
    - 图片：.jpg, .jpeg, .png, .gif, .bmp, .webp
    - 音频：.mp3, .wav, .m4a, .flac, .ogg
    - 视频：.mp4, .avi, .mov, .mkv, .flv
    - 网页：http://, https://
    - PDF：.pdf
    """
    
    # 支持的文件类型映射
    SUPPORTED_TYPES = {
        # 文本
        '.txt': ContentType.TEXT,
        '.md': ContentType.TEXT,
        '.doc': ContentType.TEXT,
        '.docx': ContentType.TEXT,
        '.json': ContentType.TEXT,
        '.xml': ContentType.TEXT,
        '.html': ContentType.TEXT,
        '.htm': ContentType.TEXT,
        
        # 图片
        '.jpg': ContentType.IMAGE,
        '.jpeg': ContentType.IMAGE,
        '.png': ContentType.IMAGE,
        '.gif': ContentType.IMAGE,
        '.bmp': ContentType.IMAGE,
        '.webp': ContentType.IMAGE,
        '.svg': ContentType.IMAGE,
        
        # 音频
        '.mp3': ContentType.AUDIO,
        '.wav': ContentType.AUDIO,
        '.m4a': ContentType.AUDIO,
        '.flac': ContentType.AUDIO,
        '.ogg': ContentType.AUDIO,
        '.aac': ContentType.AUDIO,
        
        # 视频
        '.mp4': ContentType.VIDEO,
        '.avi': ContentType.VIDEO,
        '.mov': ContentType.VIDEO,
        '.mkv': ContentType.VIDEO,
        '.flv': ContentType.VIDEO,
        '.wmv': ContentType.VIDEO,
        
        # PDF
        '.pdf': ContentType.PDF,
    }
    
    def __init__(self, llm_client=None):
        """
        初始化多模态工具
        
        Args:
            llm_client: LLM客户端（用于图片/音频/视频的描述生成）
        """
        self.llm_client = llm_client
        self._init_parsers()
        logger.info("[MultimodalTool] 多模态工具初始化完成")
    
    def _init_parsers(self):
        """初始化各种解析器"""
        self.parsers = {
            ContentType.TEXT: self._parse_text,
            ContentType.IMAGE: self._parse_image,
            ContentType.AUDIO: self._parse_audio,
            ContentType.VIDEO: self._parse_video,
            ContentType.PDF: self._parse_pdf,
            ContentType.WEBPAGE: self._parse_webpage,
        }
    
    def parse(self, source: str, **kwargs) -> ParsedContent:
        """
        解析多模态内容（主入口）
        
        Args:
            source: 文件路径或URL
            **kwargs: 额外参数
                - ocr: 是否对图片使用OCR（默认True）
                - asr: 是否对音频使用ASR（默认True）
                - describe: 是否生成AI描述（默认True）
        
        Returns:
            ParsedContent: 解析后的内容
        """
        # 检测内容类型
        content_type = self._detect_type(source)
        logger.info(f"[MultimodalTool] 解析 {source}，类型: {content_type.value}")
        
        # 调用对应的解析器
        parser = self.parsers.get(content_type, self._parse_unknown)
        return parser(source, **kwargs)
    
    def _detect_type(self, source: str) -> ContentType:
        """检测内容类型"""
        # 检查是否是URL
        if source.startswith(('http://', 'https://')):
            return ContentType.WEBPAGE
        
        # 检查文件扩展名
        ext = os.path.splitext(source.lower())[1]
        return self.SUPPORTED_TYPES.get(ext, ContentType.UNKNOWN)
    
    def _parse_text(self, file_path: str, **kwargs) -> ParsedContent:
        """解析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return ParsedContent(
                content_type=ContentType.TEXT,
                text=text,
                metadata={
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'char_count': len(text)
                }
            )
        except Exception as e:
            logger.error(f"[MultimodalTool] 文本解析失败: {e}")
            return ParsedContent(content_type=ContentType.TEXT, text="")
    
    def _parse_image(self, file_path: str, ocr: bool = True, describe: bool = True, **kwargs) -> ParsedContent:
        """解析图片"""
        try:
            from PIL import Image
            
            # 读取图片
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # 获取图片信息
            img = Image.open(io.BytesIO(raw_data))
            width, height = img.size
            format_type = img.format
            
            # Base64编码
            base64_data = base64.b64encode(raw_data).decode('utf-8')
            
            # OCR识别（如果启用）
            ocr_text = ""
            if ocr:
                ocr_text = self._ocr_image(raw_data)
            
            # AI描述（如果启用且有LLM客户端）
            description = ""
            if describe and self.llm_client:
                description = self._describe_image(base64_data, format_type)
            
            return ParsedContent(
                content_type=ContentType.IMAGE,
                text=ocr_text,
                raw_data=raw_data,
                base64_data=base64_data,
                description=description,
                metadata={
                    'file_path': file_path,
                    'width': width,
                    'height': height,
                    'format': format_type,
                    'has_ocr': bool(ocr_text),
                    'has_description': bool(description)
                }
            )
        except Exception as e:
            logger.error(f"[MultimodalTool] 图片解析失败: {e}")
            return ParsedContent(content_type=ContentType.IMAGE)
    
    def _parse_audio(self, file_path: str, asr: bool = True, **kwargs) -> ParsedContent:
        """解析音频"""
        try:
            # 读取音频文件
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # 获取音频信息
            file_size = len(raw_data)
            
            # ASR识别（如果启用）
            asr_text = ""
            if asr:
                asr_text = self._asr_audio(file_path, raw_data)
            
            return ParsedContent(
                content_type=ContentType.AUDIO,
                text=asr_text,
                raw_data=raw_data,
                metadata={
                    'file_path': file_path,
                    'file_size': file_size,
                    'duration': self._get_audio_duration(file_path),
                    'has_asr': bool(asr_text)
                }
            )
        except Exception as e:
            logger.error(f"[MultimodalTool] 音频解析失败: {e}")
            return ParsedContent(content_type=ContentType.AUDIO)
    
    def _parse_video(self, file_path: str, **kwargs) -> ParsedContent:
        """解析视频"""
        try:
            # 提取视频关键帧和音频
            frames = self._extract_video_frames(file_path)
            audio_text = self._extract_video_audio(file_path)
            
            # 合并文本
            text = audio_text
            if frames and self.llm_client:
                # 对关键帧进行描述
                frame_descriptions = []
                for frame in frames[:3]:  # 最多处理3帧
                    desc = self._describe_image(frame, 'JPEG')
                    frame_descriptions.append(desc)
                text = f"视频音频内容：{audio_text}\n\n视频画面描述：\n" + "\n".join(frame_descriptions)
            
            return ParsedContent(
                content_type=ContentType.VIDEO,
                text=text,
                metadata={
                    'file_path': file_path,
                    'duration': self._get_video_duration(file_path),
                    'frame_count': len(frames),
                    'has_audio': bool(audio_text)
                }
            )
        except Exception as e:
            logger.error(f"[MultimodalTool] 视频解析失败: {e}")
            return ParsedContent(content_type=ContentType.VIDEO)
    
    def _parse_pdf(self, file_path: str, **kwargs) -> ParsedContent:
        """解析PDF"""
        try:
            # 尝试使用PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    
                    return ParsedContent(
                        content_type=ContentType.PDF,
                        text=text,
                        metadata={
                            'file_path': file_path,
                            'page_count': len(reader.pages),
                            'char_count': len(text)
                        }
                    )
            except ImportError:
                logger.warning("[MultimodalTool] PyPDF2未安装，PDF解析受限")
                return ParsedContent(
                    content_type=ContentType.PDF,
                    text=f"[PDF文件: {file_path}]",
                    metadata={'file_path': file_path}
                )
        except Exception as e:
            logger.error(f"[MultimodalTool] PDF解析失败: {e}")
            return ParsedContent(content_type=ContentType.PDF)
    
    def _parse_webpage(self, url: str, **kwargs) -> ParsedContent:
        """解析网页"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # 获取网页内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题和正文
            title = soup.title.string if soup.title else ""
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            # 清理空白
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return ParsedContent(
                content_type=ContentType.WEBPAGE,
                text=text,
                metadata={
                    'url': url,
                    'title': title,
                    'char_count': len(text)
                }
            )
        except Exception as e:
            logger.error(f"[MultimodalTool] 网页解析失败: {e}")
            return ParsedContent(
                content_type=ContentType.WEBPAGE,
                text=f"[网页链接: {url}]",
                metadata={'url': url}
            )
    
    def _parse_unknown(self, source: str, **kwargs) -> ParsedContent:
        """解析未知类型"""
        logger.warning(f"[MultimodalTool] 未知类型: {source}")
        return ParsedContent(
            content_type=ContentType.UNKNOWN,
            text=f"[未知类型文件: {source}]",
            metadata={'source': source}
        )
    
    # ========== 辅助方法 ==========
    
    def _ocr_image(self, image_data: bytes) -> str:
        """OCR识别图片文字"""
        try:
            # 尝试使用easyocr
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'])
            
            # 保存临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(image_data)
                temp_path = f.name
            
            result = reader.readtext(temp_path)
            text = ' '.join([item[1] for item in result])
            
            os.remove(temp_path)
            return text
        except ImportError:
            logger.warning("[MultimodalTool] easyocr未安装，OCR功能不可用")
            return ""
        except Exception as e:
            logger.error(f"[MultimodalTool] OCR失败: {e}")
            return ""
    
    def _describe_image(self, base64_data: str, format_type: str) -> str:
        """使用LLM描述图片"""
        if not self.llm_client:
            return ""
        
        try:
            # 构建多模态提示
            prompt = f"请描述这张图片的内容。图片格式: {format_type}"
            
            # 这里应该调用支持多模态的LLM API
            # 例如：GPT-4V、Claude 3、Gemini等
            # 示例代码：
            # response = self.llm_client.chat.completions.create(
            #     model="gpt-4-vision-preview",
            #     messages=[{
            #         "role": "user",
            #         "content": [
            #             {"type": "text", "text": prompt},
            #             {"type": "image_url", "image_url": f"data:image/{format_type.lower()};base64,{base64_data}"}
            #         ]
            #     }]
            # )
            # return response.choices[0].message.content
            
            return "[图片描述：需要配置多模态LLM]"
        except Exception as e:
            logger.error(f"[MultimodalTool] 图片描述失败: {e}")
            return ""
    
    def _asr_audio(self, file_path: str, audio_data: bytes) -> str:
        """ASR语音识别"""
        try:
            # 尝试使用whisper
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(file_path)
            return result["text"]
        except ImportError:
            logger.warning("[MultimodalTool] whisper未安装，ASR功能不可用")
            return ""
        except Exception as e:
            logger.error(f"[MultimodalTool] ASR失败: {e}")
            return ""
    
    def _get_audio_duration(self, file_path: str) -> float:
        """获取音频时长"""
        try:
            from mutagen.mp3 import MP3
            audio = MP3(file_path)
            return audio.info.length
        except:
            return 0.0
    
    def _extract_video_frames(self, file_path: str, num_frames: int = 5) -> List[str]:
        """提取视频关键帧（返回base64编码的帧）"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(file_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frames = []
            for i in range(num_frames):
                frame_idx = int(total_frames * (i + 1) / (num_frames + 1))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    # 编码为JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    base64_frame = base64.b64encode(buffer).decode('utf-8')
                    frames.append(base64_frame)
            
            cap.release()
            return frames
        except ImportError:
            logger.warning("[MultimodalTool] opencv未安装，视频帧提取不可用")
            return []
        except Exception as e:
            logger.error(f"[MultimodalTool] 视频帧提取失败: {e}")
            return []
    
    def _extract_video_audio(self, file_path: str) -> str:
        """提取视频音频并ASR"""
        try:
            import subprocess
            import tempfile
            
            # 提取音频到临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_audio = f.name
            
            # 使用ffmpeg提取音频
            subprocess.run([
                'ffmpeg', '-i', file_path, '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '16000', '-ac', '1', temp_audio
            ], check=True, capture_output=True)
            
            # ASR识别
            with open(temp_audio, 'rb') as f:
                audio_data = f.read()
            text = self._asr_audio(temp_audio, audio_data)
            
            os.remove(temp_audio)
            return text
        except Exception as e:
            logger.error(f"[MultimodalTool] 视频音频提取失败: {e}")
            return ""
    
    def _get_video_duration(self, file_path: str) -> float:
        """获取视频时长"""
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            return frame_count / fps if fps > 0 else 0.0
        except:
            return 0.0
    
    # ========== 便捷方法 ==========
    
    def parse_text(self, source: str) -> str:
        """便捷方法：只获取文本内容"""
        result = self.parse(source)
        return result.text
    
    def parse_batch(self, sources: List[str], **kwargs) -> List[ParsedContent]:
        """批量解析"""
        return [self.parse(source, **kwargs) for source in sources]
    
    def is_supported(self, source: str) -> bool:
        """检查是否支持该类型"""
        content_type = self._detect_type(source)
        return content_type != ContentType.UNKNOWN


# ========== 工具函数 ==========

def multimodal_parse(source: str, **kwargs) -> ParsedContent:
    """
    便捷函数：直接解析多模态内容
    
    使用示例：
        result = multimodal_parse("path/to/image.jpg")
        print(result.text)  # OCR结果
        print(result.description)  # AI描述
    """
    tool = MultimodalTool()
    return tool.parse(source, **kwargs)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("多模态工具测试")
    print("=" * 60)
    
    tool = MultimodalTool()
    
    # 测试文本解析
    test_file = "test.txt"
    if os.path.exists(test_file):
        result = tool.parse(test_file)
        print(f"\n文本解析: {test_file}")
        print(f"类型: {result.content_type.value}")
        print(f"内容长度: {len(result.text)}")
    
    # 测试网页解析
    result = tool.parse("https://www.example.com")
    print(f"\n网页解析: example.com")
    print(f"类型: {result.content_type.value}")
    print(f"标题: {result.metadata.get('title', 'N/A')}")
    print(f"内容长度: {len(result.text)}")
