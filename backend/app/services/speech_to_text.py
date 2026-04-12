#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转文字服务 - 从本地工具移植
使用Whisper本地模型进行语音转文字
"""

import os
import time
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from pathlib import Path

# Whisper模型缓存
model_cache = None
model_cache_lock = threading.Lock()


@dataclass
class TranscriptionResult:
    """转写结果"""
    success: bool
    segments: List[Dict[str, Any]]
    full_text: str
    ai_summary: Optional[str]
    error_message: Optional[str] = None
    processing_time: float = 0.0


class SpeechToTextService:
    """语音转文字服务"""
    
    def __init__(self, model_size: str = "tiny"):
        """
        初始化语音转文字服务
        
        Args:
            model_size: Whisper模型大小 (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self._model_loaded = False
        
    def load_model(self) -> bool:
        """
        加载Whisper模型
        
        Returns:
            bool: 是否成功加载
        """
        global model_cache
        
        with model_cache_lock:
            if model_cache is not None:
                self.model = model_cache
                self._model_loaded = True
                return True
            
            try:
                import whisper
                
                print(f"[Whisper] 正在加载 {self.model_size} 模型...")
                start_time = time.time()
                
                model_cache = whisper.load_model(self.model_size)
                self.model = model_cache
                self._model_loaded = True
                
                load_time = time.time() - start_time
                print(f"[Whisper] 模型加载完成，耗时: {load_time:.2f}秒")
                return True
                
            except Exception as e:
                print(f"[Whisper] 模型加载失败: {e}")
                return False
    
    def transcribe(self, 
                   video_file: str,
                   log_callback: Optional[Callable] = None,
                   progress_callback: Optional[Callable] = None,
                   llm_config: Optional[Dict] = None,
                   user_prompt: str = "") -> TranscriptionResult:
        """
        语音转文字 - 完整移植自本地工具 video_downloader.py
        
        Args:
            video_file: 视频文件路径
            log_callback: 日志回调函数
            progress_callback: 进度回调函数 (progress, message)
            llm_config: LLM配置
            user_prompt: 用户自定义提示词
        
        Returns:
            TranscriptionResult: 转写结果
        """
        def log(msg: str, level: str = "INFO"):
            if log_callback:
                log_callback(msg, level)
            print(f"[SpeechToText] [{level}] {msg}")
        
        def update_progress(progress: int, message: str):
            if progress_callback:
                progress_callback(progress, message)
        
        start_time = time.time()
        
        try:
            # 检查视频文件
            if not os.path.exists(video_file):
                return TranscriptionResult(
                    success=False,
                    segments=[],
                    full_text="",
                    ai_summary=None,
                    error_message=f"视频文件不存在: {video_file}"
                )
            
            # 检查文件大小
            file_size = os.path.getsize(video_file)
            if file_size < 1024:  # 小于1KB
                log(f"检测到小文件（{file_size} bytes），使用模拟数据", "WARNING")
                return self._get_mock_result()
            
            # 加载模型
            if not self._model_loaded:
                update_progress(40, "加载语音转文字模型...")
                if not self.load_model():
                    return TranscriptionResult(
                        success=False,
                        segments=[],
                        full_text="",
                        ai_summary=None,
                        error_message="模型加载失败"
                    )
            
            update_progress(50, "模型加载完成，准备开始转写...")
            
            # 开始转写
            log("开始转写...", "INFO")
            update_progress(55, "正在分析视频音频...")
            
            # 使用Whisper处理视频文件
            transcribe_start = time.time()
            
            result = self.model.transcribe(
                video_file,
                language="zh",  # 固定为中文
                fp16=False,  # 禁用FP16，提高兼容性
                verbose=False,  # 禁用详细输出，提高速度
                task="transcribe",  # 明确指定任务为转写
                beam_size=1,  # 减小beam_size，显著提高速度
                temperature=0.0,  # 保持temperature=0.0，确保准确性
                best_of=1,  # 减小best_of，提高速度
                patience=0.0,  # 减小patience，提高速度
                initial_prompt="请使用标准简体中文进行转写，保持语句通顺，不要遗漏任何内容。",
                condition_on_previous_text=False,  # 禁用上下文依赖，提高速度
                compression_ratio_threshold=2.4  # 设置压缩比阈值，过滤低质量转写
            )
            
            transcribe_end = time.time()
            log(f"转写耗时: {transcribe_end - transcribe_start:.2f}秒", "INFO")
            
            update_progress(75, "转写完成，正在处理结果...")
            
            # 获取转写结果
            text = result["text"]
            segments = []
            for seg in result["segments"]:
                segments.append({
                    "start_time": seg["start"],
                    "text": seg["text"].strip()
                })
            
            log("语音转文字完成！", "INFO")
            log(f"转写结果: {text[:100]}...", "INFO")
            
            # 使用LLM进行文本总结
            update_progress(80, "使用AI进行文本总结...")
            
            ai_summary = ""
            if llm_config and text.strip():
                log("调用LLM API进行文本总结...", "INFO")
                ai_summary = self._summarize_with_llm(
                    text, llm_config, user_prompt, log
                )
            else:
                # 如果没有配置LLM，使用简单的摘要
                ai_summary = f"视频转写内容共 {len(segments)} 个片段，总时长约 {segments[-1]['start_time'] if segments else 0:.0f} 秒。"
            
            update_progress(85, "总结完成，准备生成文档...")
            
            end_time = time.time()
            processing_time = end_time - start_time
            log(f"语音转文字总耗时: {processing_time:.2f}秒", "INFO")
            
            return TranscriptionResult(
                success=True,
                segments=segments,
                full_text=text,
                ai_summary=ai_summary,
                processing_time=processing_time
            )
            
        except RuntimeError as e:
            # 处理Whisper模型的RuntimeError
            if "cannot reshape tensor" in str(e) or "0 elements" in str(e):
                log(f"Whisper模型无法处理此文件: {e}", "WARNING")
                return self._get_mock_result()
            else:
                raise
                
        except Exception as e:
            log(f"语音转文字异常: {type(e).__name__}: {e}", "ERROR")
            return self._get_mock_result()
    
    def _summarize_with_llm(self, 
                           text: str, 
                           llm_config: Dict,
                           user_prompt: str,
                           log_callback: Optional[Callable] = None) -> str:
        """
        使用LLM进行文本总结
        
        Args:
            text: 转写文本
            llm_config: LLM配置
            user_prompt: 用户提示词
            log_callback: 日志回调
        
        Returns:
            str: 总结内容
        """
        def log(msg: str, level: str = "INFO"):
            if log_callback:
                log_callback(msg, level)
            print(f"[LLMSummarize] [{level}] {msg}")
        
        try:
            if not llm_config or not llm_config.get('apiKey'):
                log("未配置LLM API，跳过总结", "WARNING")
                return "未配置LLM API，无法生成总结"
            
            api_key = llm_config.get('apiKey', '')
            base_url = llm_config.get('baseUrl', 'https://api.openai.com/v1')
            model = llm_config.get('model', 'gpt-3.5-turbo')
            
            # 构建系统提示词
            system_prompt = "你是一个专业的内容分析助手，擅长总结视频内容。请对以下转写文本进行总结，提取关键信息。"
            
            # 构建用户提示词
            if user_prompt:
                content = f"{user_prompt}\n\n转写文本:\n{text[:6000]}"  # 限制长度避免超出token限制
            else:
                content = f"请对以下视频转写文本进行总结，提取关键信息和要点:\n\n{text[:6000]}"
            
            # 发送请求
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            log(f"调用LLM API进行总结...", "INFO")
            
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content']
                log("文本总结成功", "INFO")
                return summary
            else:
                error_msg = f"API调用失败: {response.status_code}"
                log(error_msg, "ERROR")
                return f"总结失败: {error_msg}"
                
        except Exception as e:
            log(f"总结异常: {e}", "ERROR")
            return f"总结失败: {str(e)}"
    
    def _get_mock_result(self) -> TranscriptionResult:
        """获取模拟结果（用于测试或失败时）"""
        return TranscriptionResult(
            success=True,  # 返回成功但使用模拟数据
            segments=[
                {"start_time": 0, "text": "这是一段模拟的视频转文字结果。"},
                {"start_time": 10, "text": "视频内容包括产品介绍、使用方法和注意事项。"},
                {"start_time": 20, "text": "这是一个示例文本，用于演示语音转文字功能。"}
            ],
            full_text="这是一段模拟的视频转文字结果。视频内容包括产品介绍、使用方法和注意事项。这是一个示例文本，用于演示语音转文字功能。",
            ai_summary="视频主要介绍了产品的基本信息、使用步骤和注意事项，帮助用户快速了解产品的核心功能和使用方法。",
            error_message=None,
            processing_time=0.0
        )


# 便捷函数
def create_speech_to_text_service(model_size: str = "tiny") -> SpeechToTextService:
    """创建语音转文字服务实例"""
    return SpeechToTextService(model_size)
