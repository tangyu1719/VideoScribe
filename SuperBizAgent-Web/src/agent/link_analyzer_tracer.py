#!/usr/bin/env python3
"""
链接分析流程追踪器
详细记录链接分析的每个步骤，包括：
1. 链接类型检测
2. 页面内容获取
3. 图片/视频提取
4. OCR文字识别
5. 结果生成
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from logging_system import logging_system, LogLevel, OperationStatus

class LinkAnalysisTracer:
    """链接分析流程追踪器"""
    
    # 定义标准流程步骤
    STANDARD_STEPS = {
        'xiaohongshu': [
            ('detect_type', '检测内容类型'),
            ('fetch_page', '获取页面内容'),
            ('extract_images', '提取图片链接'),
            ('download_images', '下载图片'),
            ('ocr_recognition', 'OCR文字识别'),
            ('extract_text', '提取文本内容'),
            ('generate_result', '生成分析结果')
        ],
        'douyin_image': [
            ('detect_type', '检测内容类型'),
            ('fetch_page', '获取页面内容'),
            ('extract_images', '提取图片链接'),
            ('download_images', '下载图片'),
            ('ocr_recognition', 'OCR文字识别'),
            ('extract_text', '提取文本内容'),
            ('generate_result', '生成分析结果')
        ],
        'video': [
            ('detect_type', '检测内容类型'),
            ('analyze_video', '分析视频信息'),
            ('generate_result', '生成分析结果')
        ],
        'general': [
            ('detect_type', '检测内容类型'),
            ('fetch_page', '获取页面内容'),
            ('extract_content', '提取通用内容'),
            ('generate_result', '生成分析结果')
        ]
    }
    
    def __init__(self):
        self.active_traces: Dict[str, Dict] = {}
    
    def start_analysis(self, url: str, request_id: str) -> str:
        """开始链接分析追踪"""
        trace_id = logging_system.start_operation(
            operation_type='link_analysis',
            operation_name=f'链接分析: {url[:50]}...',
            request_id=request_id,
            inputs={'url': url}
        )
        
        self.active_traces[trace_id] = {
            'url': url,
            'request_id': request_id,
            'start_time': datetime.now().isoformat(),
            'steps': {},
            'current_step': 0
        }
        
        # 记录原始日志
        logging_system.log_raw(
            level=LogLevel.INFO,
            module='link_analyzer',
            api_path='/api/link/analyze',
            method='POST',
            request_id=request_id,
            message=f'开始分析链接: {url}',
            request_data={'url': url}
        )
        
        return trace_id
    
    def add_step(self, trace_id: str, step_key: str, step_name: str, 
                 inputs: Dict = None) -> int:
        """添加分析步骤"""
        if trace_id not in self.active_traces:
            return -1
        
        trace = self.active_traces[trace_id]
        step_order = len(trace['steps']) + 1
        
        # 记录到日志系统
        logging_system.add_operation_step(
            operation_id=trace_id,
            step_name=step_name,
            step_order=step_order,
            inputs=inputs
        )
        
        # 记录到本地追踪
        trace['steps'][step_key] = {
            'order': step_order,
            'name': step_name,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'inputs': inputs,
            'outputs': None,
            'error': None
        }
        trace['current_step'] = step_order
        
        # 记录原始日志
        logging_system.log_raw(
            level=LogLevel.DEBUG,
            module='link_analyzer',
            api_path='/api/link/analyze',
            method='POST',
            request_id=trace['request_id'],
            message=f'步骤 {step_order}: {step_name} - 开始',
            request_data={'step': step_key, 'inputs': inputs}
        )
        
        return step_order
    
    def complete_step(self, trace_id: str, step_key: str, 
                     outputs: Dict = None, error: str = None):
        """完成分析步骤"""
        if trace_id not in self.active_traces:
            return
        
        trace = self.active_traces[trace_id]
        
        if step_key in trace['steps']:
            step = trace['steps'][step_key]
            step['status'] = 'failed' if error else 'success'
            step['end_time'] = datetime.now().isoformat()
            step['outputs'] = outputs
            step['error'] = error
            
            # 计算耗时
            if step.get('start_time'):
                start = datetime.fromisoformat(step['start_time'])
                end = datetime.fromisoformat(step['end_time'])
                step['duration_ms'] = (end - start).total_seconds() * 1000
        
        # 记录到日志系统
        step_order = trace['steps'][step_key]['order'] if step_key in trace['steps'] else 0
        logging_system.complete_operation_step(
            operation_id=trace_id,
            step_order=step_order,
            outputs=outputs,
            error=error
        )
        
        # 记录原始日志
        level = LogLevel.ERROR if error else LogLevel.DEBUG
        message = f'步骤 {step_order}: {trace["steps"][step_key]["name"]} - {"失败" if error else "完成"}'
        logging_system.log_raw(
            level=level,
            module='link_analyzer',
            api_path='/api/link/analyze',
            method='POST',
            request_id=trace['request_id'],
            message=message,
            request_data={'step': step_key, 'outputs': outputs, 'error': error},
            error=error
        )
    
    def complete_analysis(self, trace_id: str, result: Dict = None, 
                         error_message: str = None):
        """完成链接分析"""
        if trace_id not in self.active_traces:
            return
        
        trace = self.active_traces[trace_id]
        trace['end_time'] = datetime.now().isoformat()
        trace['status'] = 'failed' if error_message else 'success'
        trace['result'] = result
        trace['error'] = error_message
        
        # 计算总耗时
        if trace.get('start_time'):
            start = datetime.fromisoformat(trace['start_time'])
            end = datetime.fromisoformat(trace['end_time'])
            trace['duration_ms'] = (end - start).total_seconds() * 1000
        
        # 记录到日志系统
        logging_system.complete_operation(
            operation_id=trace_id,
            outputs=result,
            error_message=error_message
        )
        
        # 记录原始日志
        level = LogLevel.ERROR if error_message else LogLevel.INFO
        message = f'链接分析完成 - {"失败" if error_message else "成功"}: {trace["url"]}'
        logging_system.log_raw(
            level=level,
            module='link_analyzer',
            api_path='/api/link/analyze',
            method='POST',
            request_id=trace['request_id'],
            message=message,
            request_data={'url': trace['url'], 'result': result, 'error': error_message},
            error=error_message
        )
        
        # 清理
        del self.active_traces[trace_id]
    
    def get_trace_info(self, trace_id: str) -> Optional[Dict]:
        """获取追踪信息"""
        return self.active_traces.get(trace_id)


# 装饰器：自动追踪链接分析函数
def trace_link_analysis(func: Callable) -> Callable:
    """装饰器：自动追踪链接分析函数的执行流程"""
    @wraps(func)
    def wrapper(self, url: str, *args, **kwargs):
        import uuid
        request_id = str(uuid.uuid4())
        
        # 创建追踪器
        tracer = LinkAnalysisTracer()
        trace_id = tracer.start_analysis(url, request_id)
        
        # 将追踪器附加到实例
        self._current_tracer = tracer
        self._current_trace_id = trace_id
        
        try:
            # 执行原函数
            result = func(self, url, *args, **kwargs)
            
            # 完成追踪
            tracer.complete_analysis(trace_id, result)
            
            return result
        except Exception as e:
            # 记录错误
            tracer.complete_analysis(trace_id, error_message=str(e))
            raise
    
    return wrapper


# 全局追踪器实例
link_tracer = LinkAnalysisTracer()
