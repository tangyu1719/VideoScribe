#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高并发处理器 - 支持音视频转写和LLM生成的高并发处理

设计目标：
1. ASR并发：支持多个Whisper实例或批处理
2. LLM并发：支持异步API调用 + 限流控制
3. 任务队列：优先级队列 + 超时控制
"""

import os
import sys
import asyncio
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str  # 'asr', 'llm', 'download'
    priority: int = 5  # 1-10, 数字越小优先级越高
    data: Any = None
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 300  # 秒


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    result: Any = None
    error: str = ""
    duration: float = 0.0


class ASRProcessor:
    """
    ASR处理器 - 支持高并发的语音转文字
    
    并发策略：
    1. 批处理：多个短音频合并处理
    2. 多实例：多个Whisper实例（GPU内存允许）
    3. 分段处理：长音频切分并行处理
    """
    
    def __init__(self, max_workers: int = 2, model_size: str = "tiny"):
        self.max_workers = max_workers
        self.model_size = model_size
        self.models = {}  # 模型池
        self.model_locks = {}  # 每个模型的锁
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.batch_queue = []  # 批处理队列
        self.batch_size = 4  # 每批处理数量
        self.batch_timeout = 5  # 批处理等待时间（秒）
        
        # 初始化模型池
        self._init_model_pool()
    
    def _init_model_pool(self):
        """初始化Whisper模型池"""
        try:
            import whisper
            
            logger.info(f"初始化ASR模型池，大小: {self.max_workers}")
            
            for i in range(self.max_workers):
                model_key = f"model_{i}"
                logger.info(f"加载Whisper模型 {i+1}/{self.max_workers}...")
                self.models[model_key] = whisper.load_model(self.model_size)
                self.model_locks[model_key] = threading.Lock()
            
            logger.info("✅ ASR模型池初始化完成")
            
        except Exception as e:
            logger.error(f"ASR模型池初始化失败: {e}")
            raise
    
    def process_single(self, audio_file: str, **kwargs) -> Dict:
        """处理单个音频文件"""
        # 获取可用模型
        model_key = self._get_available_model()
        if not model_key:
            raise Exception("没有可用的ASR模型")
        
        with self.model_locks[model_key]:
            model = self.models[model_key]
            start_time = time.time()
            
            try:
                result = model.transcribe(
                    audio_file,
                    language=kwargs.get('language', 'zh'),
                    fp16=False,
                    verbose=False,
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    condition_on_previous_text=False,
                )
                
                duration = time.time() - start_time
                
                return {
                    'text': result['text'],
                    'segments': result['segments'],
                    'duration': duration,
                    'model': model_key
                }
            except Exception as e:
                logger.error(f"ASR处理失败: {e}")
                raise
    
    def _get_available_model(self) -> Optional[str]:
        """获取可用的模型（简单轮询）"""
        for model_key, lock in self.model_locks.items():
            if not lock.locked():
                return model_key
        # 如果没有可用模型，返回第一个（会等待）
        return list(self.models.keys())[0] if self.models else None
    
    def process_batch(self, audio_files: List[str], **kwargs) -> List[Dict]:
        """批量处理音频文件"""
        futures = []
        for audio_file in audio_files:
            future = self.executor.submit(self.process_single, audio_file, **kwargs)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                result = future.result(timeout=300)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
    
    async def process_async(self, audio_file: str, **kwargs) -> Dict:
        """异步处理音频"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.process_single, 
            audio_file, 
            **kwargs
        )


class LLMProcessor:
    """
    LLM处理器 - 支持高并发的LLM API调用
    
    并发策略：
    1. 异步HTTP客户端
    2. 限流控制（Rate Limiting）
    3. 连接池复用
    4. 批量请求合并
    """
    
    def __init__(self, 
                 api_key: str, 
                 base_url: str, 
                 model: str,
                 max_concurrent: int = 10,
                 rate_limit: int = 20):  # 每分钟请求数
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        
        # 信号量控制并发
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 请求时间记录（用于限流）
        self.request_times = []
        self.request_lock = threading.Lock()
        
        # 异步HTTP客户端
        self.session = None
    
    async def _get_session(self):
        """获取HTTP会话（连接池）"""
        if self.session is None:
            import aiohttp
            connector = aiohttp.TCPConnector(
                limit=100,  # 连接池大小
                limit_per_host=30,
                enable_cleanup_closed=True,
                force_close=False,
            )
            timeout = aiohttp.ClientTimeout(total=120)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session
    
    async def _rate_limit_check(self):
        """限流检查"""
        with self.request_lock:
            now = time.time()
            # 清理1分钟前的记录
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            if len(self.request_times) >= self.rate_limit:
                # 需要等待
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    logger.warning(f"触发限流，等待 {wait_time:.1f} 秒")
                    await asyncio.sleep(wait_time)
            
            self.request_times.append(time.time())
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """异步生成文本"""
        async with self.semaphore:  # 控制并发数
            await self._rate_limit_check()  # 限流检查
            
            session = await self._get_session()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 1500)
            }
            
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        duration = time.time() - start_time
                        logger.info(f"LLM请求完成，耗时: {duration:.2f}s")
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        raise Exception(f"API错误 {response.status}: {error_text}")
                        
            except Exception as e:
                logger.error(f"LLM生成失败: {e}")
                raise
    
    async def generate_batch(self, prompts: List[str], system_prompt: str = "", **kwargs) -> List[str]:
        """批量异步生成"""
        tasks = [
            self.generate(prompt, system_prompt, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None


class TaskScheduler:
    """
    任务调度器 - 管理所有任务的执行
    
    功能：
    1. 优先级队列
    2. 任务超时控制
    3. 资源限制
    4. 进度监控
    """
    
    def __init__(self, 
                 max_concurrent_tasks: int = 5,
                 asr_workers: int = 2,
                 llm_concurrent: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue = queue.PriorityQueue()
        self.running_tasks = {}
        self.results = {}
        
        # 处理器
        self.asr_processor = ASRProcessor(max_workers=asr_workers)
        self.llm_processor = None  # 需要外部配置
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        
        # 运行状态
        self.is_running = False
        self.scheduler_thread = None
    
    def set_llm_config(self, api_key: str, base_url: str, model: str):
        """设置LLM配置"""
        self.llm_processor = LLMProcessor(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
    
    def submit_task(self, task: Task) -> str:
        """提交任务到队列"""
        # 优先级队列：(priority, task_id, task)
        self.task_queue.put((task.priority, task.task_id, task))
        logger.info(f"任务 {task.task_id} 已提交，优先级: {task.priority}")
        return task.task_id
    
    def start(self):
        """启动调度器"""
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("✅ 任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        self.executor.shutdown(wait=True)
        logger.info("⏹️ 任务调度器已停止")
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.is_running:
            try:
                # 获取任务（阻塞）
                priority, task_id, task = self.task_queue.get(timeout=1)
                
                # 提交到线程池执行
                future = self.executor.submit(self._execute_task, task)
                self.running_tasks[task_id] = future
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"调度错误: {e}")
    
    def _execute_task(self, task: Task):
        """执行任务"""
        start_time = time.time()
        
        try:
            if task.task_type == 'asr':
                result = self._process_asr_task(task)
            elif task.task_type == 'llm':
                result = self._process_llm_task(task)
            else:
                result = {'error': f'未知任务类型: {task.task_type}'}
            
            duration = time.time() - start_time
            task_result = TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            task_result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                duration=duration
            )
        
        # 保存结果
        self.results[task.task_id] = task_result
        
        # 回调
        if task.callback:
            task.callback(task_result)
        
        # 清理
        if task.task_id in self.running_tasks:
            del self.running_tasks[task.task_id]
        
        logger.info(f"任务 {task.task_id} 完成，耗时: {duration:.2f}s")
    
    def _process_asr_task(self, task: Task) -> Dict:
        """处理ASR任务"""
        audio_file = task.data.get('audio_file')
        return self.asr_processor.process_single(audio_file)
    
    def _process_llm_task(self, task: Task) -> str:
        """处理LLM任务（同步包装）"""
        if not self.llm_processor:
            raise Exception("LLM处理器未配置")
        
        prompt = task.data.get('prompt')
        system_prompt = task.data.get('system_prompt', '')
        
        # 使用asyncio运行异步函数
        return asyncio.run(self.llm_processor.generate(prompt, system_prompt))
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        return self.results.get(task_id)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.results),
        }


# ============ 使用示例 ============

def example_usage():
    """使用示例"""
    
    # 1. 创建调度器
    scheduler = TaskScheduler(
        max_concurrent_tasks=5,
        asr_workers=2,  # 2个Whisper实例
        llm_concurrent=10  # 10个并发LLM请求
    )
    
    # 2. 配置LLM
    scheduler.set_llm_config(
        api_key="your-api-key",
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo"
    )
    
    # 3. 启动调度器
    scheduler.start()
    
    # 4. 提交ASR任务
    def on_complete(result):
        print(f"任务完成: {result}")
    
    task1 = Task(
        task_id="asr_001",
        task_type="asr",
        priority=1,
        data={'audio_file': 'video1.mp4'},
        callback=on_complete
    )
    scheduler.submit_task(task1)
    
    # 5. 提交LLM任务
    task2 = Task(
        task_id="llm_001",
        task_type="llm",
        priority=2,
        data={
            'prompt': '总结这段文本...',
            'system_prompt': '你是助手'
        }
    )
    scheduler.submit_task(task2)
    
    # 6. 批量ASR处理
    audio_files = ['video1.mp4', 'video2.mp4', 'video3.mp4', 'video4.mp4']
    results = scheduler.asr_processor.process_batch(audio_files)
    print(f"批量处理结果: {results}")
    
    # 7. 查看统计
    stats = scheduler.get_stats()
    print(f"统计: {stats}")
    
    # 8. 停止
    scheduler.stop()


if __name__ == "__main__":
    example_usage()
