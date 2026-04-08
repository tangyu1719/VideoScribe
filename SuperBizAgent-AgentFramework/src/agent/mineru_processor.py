#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinerU 文档处理器
基于MinerU技术的PDF/文档解析工具
支持：PDF转Markdown、表格识别、公式识别、OCR
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinerUStatus(Enum):
    """处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class MinerUResult:
    """MinerU处理结果"""
    success: bool
    content: str = ""
    markdown: str = ""
    metadata: Dict = None
    images: List[str] = None
    tables: List[Dict] = None
    error: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.images is None:
            self.images = []
        if self.tables is None:
            self.tables = []


class MinerUProcessor:
    """
    MinerU文档处理器
    
    功能：
    1. PDF转Markdown（保留格式、表格、公式）
    2. 图片OCR识别
    3. 文档结构化提取
    4. 批量处理支持
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化MinerU处理器
        
        Args:
            output_dir: 输出目录，默认为当前目录下的output文件夹
        """
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 检查MinerU是否安装
        self.mineru_available = self._check_mineru()
        
        if self.mineru_available:
            logger.info("[MinerU] 处理器初始化成功")
        else:
            logger.warning("[MinerU] 未安装，将使用备用处理方案")
    
    def _check_mineru(self) -> bool:
        """检查MinerU是否已安装"""
        try:
            # 尝试导入MinerU
            import magic_pdf
            logger.info("[MinerU] magic_pdf模块已安装")
            return True
        except ImportError:
            logger.warning("[MinerU] magic_pdf模块未安装")
            return False
    
    def process_pdf(self, pdf_path: str, method: str = "auto") -> MinerUResult:
        """
        处理PDF文件
        
        Args:
            pdf_path: PDF文件路径
            method: 处理方法 (auto/ocr/txt)
        
        Returns:
            MinerUResult: 处理结果
        """
        if not os.path.exists(pdf_path):
            return MinerUResult(success=False, error=f"文件不存在: {pdf_path}")
        
        if not self.mineru_available:
            # 使用备用方案
            return self._process_pdf_fallback(pdf_path)
        
        try:
            from magic_pdf.data.data_reader_writer import FileBasedDataWriter
            from magic_pdf.data.dataset import PymuDocDataset
            from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
            from magic_pdf.config.enums import SupportedPdfParseMethod
            
            logger.info(f"[MinerU] 开始处理PDF: {pdf_path}")
            
            # 生成输出目录
            file_name = Path(pdf_path).stem
            output_path = os.path.join(self.output_dir, file_name)
            os.makedirs(output_path, exist_ok=True)
            
            # 读取PDF
            pdf_bytes = open(pdf_path, "rb").read()
            
            # 选择解析方法
            if method == "ocr":
                parse_method = SupportedPdfParseMethod.OCR
            elif method == "txt":
                parse_method = SupportedPdfParseMethod.TXT
            else:
                parse_method = SupportedPdfParseMethod.AUTO
            
            # 创建数据集
            dataset = PymuDocDataset(pdf_bytes)
            
            # 解析文档
            parsed_result = dataset.apply(doc_analyze, ocr=True)
            
            # 提取内容
            markdown_content = parsed_result.get_markdown()
            
            # 保存Markdown
            md_path = os.path.join(output_path, f"{file_name}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 提取图片
            images = []
            for img_info in parsed_result.get_images():
                img_path = os.path.join(output_path, "images", img_info["filename"])
                images.append(img_path)
            
            # 提取表格
            tables = parsed_result.get_tables()
            
            logger.info(f"[MinerU] PDF处理完成: {file_name}")
            
            return MinerUResult(
                success=True,
                content=markdown_content,
                markdown=markdown_content,
                metadata={
                    "file_name": file_name,
                    "file_path": pdf_path,
                    "output_path": output_path,
                    "page_count": len(parsed_result),
                    "image_count": len(images),
                    "table_count": len(tables)
                },
                images=images,
                tables=tables
            )
            
        except Exception as e:
            logger.error(f"[MinerU] PDF处理失败: {e}")
            return MinerUResult(success=False, error=str(e))
    
    def _process_pdf_fallback(self, pdf_path: str) -> MinerUResult:
        """PDF处理备用方案（使用PyPDF2）"""
        try:
            import PyPDF2
            
            logger.info(f"[MinerU] 使用备用方案处理PDF: {pdf_path}")
            
            file_name = Path(pdf_path).stem
            text_content = []
            
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"## 第{page_num}页\n\n{text}")
            
            markdown_content = "\n\n".join(text_content)
            
            # 保存Markdown
            output_path = os.path.join(self.output_dir, file_name)
            os.makedirs(output_path, exist_ok=True)
            md_path = os.path.join(output_path, f"{file_name}.md")
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return MinerUResult(
                success=True,
                content=markdown_content,
                markdown=markdown_content,
                metadata={
                    "file_name": file_name,
                    "file_path": pdf_path,
                    "output_path": output_path,
                    "page_count": len(reader.pages),
                    "method": "fallback"
                }
            )
            
        except Exception as e:
            logger.error(f"[MinerU] 备用处理失败: {e}")
            return MinerUResult(success=False, error=str(e))
    
    def process_image(self, image_path: str, ocr: bool = True) -> MinerUResult:
        """
        处理图片（OCR识别）
        
        Args:
            image_path: 图片路径
            ocr: 是否启用OCR
        
        Returns:
            MinerUResult: 处理结果
        """
        if not os.path.exists(image_path):
            return MinerUResult(success=False, error=f"文件不存在: {image_path}")
        
        try:
            logger.info(f"[MinerU] 处理图片: {image_path}")
            
            # 尝试使用PaddleOCR
            try:
                from paddleocr import PaddleOCR
                ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch')
                result = ocr_engine.ocr(image_path, cls=True)
                
                text_lines = []
                for line in result[0]:
                    if line:
                        text_lines.append(line[1][0])
                
                content = "\n".join(text_lines)
                
                return MinerUResult(
                    success=True,
                    content=content,
                    markdown=f"![图片]({image_path})\n\n## OCR识别结果\n\n{content}",
                    metadata={
                        "file_name": Path(image_path).name,
                        "file_path": image_path,
                        "ocr_enabled": True,
                        "text_lines": len(text_lines)
                    }
                )
                
            except ImportError:
                logger.warning("[MinerU] PaddleOCR未安装，跳过OCR")
                return MinerUResult(
                    success=True,
                    content="",
                    markdown=f"![图片]({image_path})",
                    metadata={
                        "file_name": Path(image_path).name,
                        "file_path": image_path,
                        "ocr_enabled": False
                    }
                )
                
        except Exception as e:
            logger.error(f"[MinerU] 图片处理失败: {e}")
            return MinerUResult(success=False, error=str(e))
    
    def process_document(self, file_path: str) -> MinerUResult:
        """
        处理文档（自动识别类型）
        
        Args:
            file_path: 文档路径
        
        Returns:
            MinerUResult: 处理结果
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return self.process_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            return self.process_image(file_path)
        elif ext in ['.docx', '.doc']:
            return self._process_word(file_path)
        elif ext in ['.md', '.markdown']:
            return self._process_markdown(file_path)
        else:
            return MinerUResult(success=False, error=f"不支持的文件类型: {ext}")
    
    def _process_word(self, docx_path: str) -> MinerUResult:
        """处理Word文档"""
        try:
            from docx import Document
            
            logger.info(f"[MinerU] 处理Word文档: {docx_path}")
            
            doc = Document(docx_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            content = "\n\n".join(paragraphs)
            markdown_content = f"# {Path(docx_path).stem}\n\n{content}"
            
            return MinerUResult(
                success=True,
                content=content,
                markdown=markdown_content,
                metadata={
                    "file_name": Path(docx_path).name,
                    "file_path": docx_path,
                    "paragraph_count": len(paragraphs)
                }
            )
            
        except ImportError:
            return MinerUResult(success=False, error="python-docx未安装")
        except Exception as e:
            return MinerUResult(success=False, error=str(e))
    
    def _process_markdown(self, md_path: str) -> MinerUResult:
        """处理Markdown文件"""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return MinerUResult(
                success=True,
                content=content,
                markdown=content,
                metadata={
                    "file_name": Path(md_path).name,
                    "file_path": md_path,
                    "char_count": len(content)
                }
            )
        except Exception as e:
            return MinerUResult(success=False, error=str(e))
    
    def batch_process(self, file_paths: List[str]) -> List[MinerUResult]:
        """批量处理文件"""
        results = []
        for file_path in file_paths:
            result = self.process_document(file_path)
            results.append(result)
        return results
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', 
                '.docx', '.doc', '.md', '.markdown']


# 便捷函数
def process_with_mineru(file_path: str, output_dir: str = None) -> MinerUResult:
    """便捷函数：使用MinerU处理文件"""
    processor = MinerUProcessor(output_dir=output_dir)
    return processor.process_document(file_path)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("MinerU 文档处理器测试")
    print("=" * 60)
    
    processor = MinerUProcessor()
    print(f"MinerU可用: {processor.mineru_available}")
    print(f"支持格式: {processor.get_supported_formats()}")
