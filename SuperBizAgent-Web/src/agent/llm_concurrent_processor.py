#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM高并发处理器 - 真正的并发控制解决方案

核心问题：
1. LLM API有RPM（每分钟请求数）限制
2. 有并发请求数限制（同时处理的请求数）
3. 达到限制时返回429错误，需要等待重试而非错误重试

解决方案：
1. 令牌桶算法 - 平滑控制请求速率
2. 双限流 - 同时控制RPM和并发数
3. 429专门处理 - 等待重试而非失败
4. 连接池复用 - 减少连接开销
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """速率限制错误（429）"""
    pass


class ConcurrencyLimitError(Exception):
    """并发限制错误"""
    pass


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str
    base_url: str
    model: str
    
    # 速率限制配置（根据你的API Tier调整）
    rpm_limit: int = 60  # 每分钟最大请求数
    tpm_limit: int = 60000  # 每分钟最大token数
    max_concurrent: int = 10  # 最大并发请求数
    
    # 重试配置
    max_retries: int = 5
    base_wait_time: float = 1.0  # 基础等待时间（秒）
    max_wait_time: float = 60.0  # 最大等待时间（秒）


class TokenBucket:
    """
    令牌桶算法 - 平滑速率限制
    
    原理：
    - 桶以固定速率（rpm）产生令牌
    - 每个请求消耗1个令牌
    - 桶满时停止产生令牌
    - 没令牌时请求等待
    
    优点：
    - 平滑流量，避免突发
    - 允许一定程度的突发（桶容量）
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 令牌产生速率（每秒）
            capacity: 桶容量（最大突发数）
        """
        self.rate = rate  # 每秒产生多少令牌
        self.capacity = capacity  # 桶容量
        self.tokens = capacity  # 当前令牌数
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取令牌
        
        Args:
            timeout: 最大等待时间（秒），None表示一直等待
        
        Returns:
            是否成功获取令牌
        """
        start_time = time.time()
        
        while True:
            async with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                
                # 计算新产生的令牌
                new_tokens = elapsed * self.rate
                self.tokens = min(self.capacity, self.tokens + new_tokens)
                self.last_update = now
                
                # 检查是否有可用令牌
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                # 计算需要等待的时间
                wait_time = (1 - self.tokens) / self.rate
            
            # 检查超时
            if timeout is not None:
                elapsed_total = time.time() - start_time
                if elapsed_total + wait_time > timeout:
                    return False
                wait_time = min(wait_time, timeout - elapsed_total)
            
            # 等待后重试
            logger.debug(f"令牌桶为空，等待 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)
    
    async def acquire_or_raise(self, timeout: Optional[float] = None):
        """获取令牌，失败则抛出异常"""
        if not await self.acquire(timeout):
            raise RateLimitError("获取令牌超时")


class LLMConcurrentProcessor:
    """
    LLM并发处理器 - 真正的并发控制
    
    三层防护：
    1. 令牌桶 - 控制RPM（每分钟请求数）
    2. 信号量 - 控制并发数（同时处理的请求数）
    3. 429重试 - 遇到限流时等待重试
    
    工作流程：
    请求 → 获取令牌（RPM控制）→ 获取信号量（并发控制）→ 发送请求
          ↓ 没令牌则等待          ↓ 达到并发则等待
        等待令牌补充              等待其他请求完成
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        
        # 1. 令牌桶 - 控制RPM
        # rate = rpm / 60 = 每秒产生的令牌数
        self.token_bucket = TokenBucket(
            rate=config.rpm_limit / 60.0,
            capacity=config.rpm_limit  # 桶容量等于RPM，允许一分钟的突发
        )
        
        # 2. 信号量 - 控制并发数
        self.concurrency_semaphore = asyncio.Semaphore(config.max_concurrent)
        
        # 3. HTTP会话（连接池）
        self.session = None
        self.session_lock = asyncio.Lock()
        
        # 统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'rate_limited_requests': 0,  # 被限流的请求数
            'retried_requests': 0,  # 重试的请求数
            'total_wait_time': 0.0,  # 总等待时间
        }
        self.stats_lock = asyncio.Lock()
    
    async def _get_session(self):
        """获取HTTP会话（连接池）"""
        if self.session is None:
            async with self.session_lock:
                if self.session is None:
                    import aiohttp
                    connector = aiohttp.TCPConnector(
                        limit=100,
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
    
    async def generate(self, 
                       prompt: str, 
                       system_prompt: str = "",
                       max_tokens: int = 1500,
                       temperature: float = 0.7,
                       **kwargs) -> Dict[str, Any]:
        """
        生成文本 - 带完整并发控制
        
        流程：
        1. 获取令牌（RPM限流）
        2. 获取信号量（并发限流）
        3. 发送请求
        4. 如果遇到429，等待后重试（不是错误重试）
        """
        start_time = time.time()
        
        async with self.stats_lock:
            self.stats['total_requests'] += 1
        
        # 尝试发送请求（带重试）
        for attempt in range(self.config.max_retries):
            try:
                # 1. 获取令牌（RPM控制）- 可能等待
                logger.debug(f"请求令牌（尝试 {attempt+1}/{self.config.max_retries}）...")
                token_acquired = await self.token_bucket.acquire(timeout=60)
                if not token_acquired:
                    raise RateLimitError("获取令牌超时（RPM限制）")
                
                # 2. 获取信号量（并发控制）- 可能等待
                logger.debug("获取并发槽位...")
                async with self.concurrency_semaphore:
                    # 3. 发送请求
                    result = await self._send_request(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                    
                    # 成功
                    async with self.stats_lock:
                        self.stats['successful_requests'] += 1
                    
                    total_time = time.time() - start_time
                    logger.info(f"LLM请求成功，总耗时: {total_time:.2f}s")
                    
                    return {
                        'success': True,
                        'text': result,
                        'duration': total_time,
                        'attempts': attempt + 1
                    }
                    
            except RateLimitError as e:
                # 429错误 - 这是并发等待重试，不是错误重试
                async with self.stats_lock:
                    self.stats['rate_limited_requests'] += 1
                    self.stats['retried_requests'] += 1
                
                # 计算等待时间（指数退避 + 随机抖动）
                wait_time = min(
                    self.config.base_wait_time * (2 ** attempt) + random.uniform(0, 1),
                    self.config.max_wait_time
                )
                
                logger.warning(
                    f"遇到速率限制（429），等待 {wait_time:.2f} 秒后重试 "
                    f"（尝试 {attempt+1}/{self.config.max_retries}）"
                )
                
                async with self.stats_lock:
                    self.stats['total_wait_time'] += wait_time
                
                await asyncio.sleep(wait_time)
                continue  # 重试
                
            except Exception as e:
                # 其他错误 - 真正的错误，不重试
                logger.error(f"LLM请求失败: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - start_time,
                    'attempts': attempt + 1
                }
        
        # 重试次数用完
        return {
            'success': False,
            'error': f'达到最大重试次数（{self.config.max_retries}）',
            'duration': time.time() - start_time,
            'attempts': self.config.max_retries
        }
    
    async def _send_request(self, 
                           prompt: str, 
                           system_prompt: str,
                           max_tokens: int,
                           temperature: float,
                           **kwargs) -> str:
        """发送实际请求"""
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 429:
                # 429 Too Many Requests - 速率限制
                raise RateLimitError("API返回429 - 速率限制")
            elif response.status == 503:
                # 503 Service Unavailable - 服务过载
                raise RateLimitError("API返回503 - 服务过载")
            elif response.status != 200:
                error_text = await response.text()
                raise Exception(f"API错误 {response.status}: {error_text}")
            
            result = await response.json()
            return result['choices'][0]['message']['content']
    
    async def generate_batch(self, 
                            prompts: List[str], 
                            system_prompt: str = "",
                            max_concurrent: Optional[int] = None,
                            **kwargs) -> List[Dict[str, Any]]:
        """
        批量生成 - 自动并发控制
        
        Args:
            prompts: 提示词列表
            max_concurrent: 本次批处理的最大并发数（默认使用配置值）
        """
        semaphore = asyncio.Semaphore(max_concurrent or self.config.max_concurrent)
        
        async def process_one(prompt: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs
                )
        
        # 并发执行所有任务
        tasks = [process_one(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    async def generate_with_priority(self,
                                    prompt: str,
                                    priority: int = 5,
                                    **kwargs) -> Dict[str, Any]:
        """
        带优先级的生成（数字越小优先级越高）
        
        注意：这里简化实现，真实场景需要优先级队列
        """
        # 高优先级请求可以稍微降低等待时间
        timeout = 60 if priority <= 3 else 30
        
        # 可以添加优先级相关的逻辑
        return await self.generate(prompt, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'avg_wait_time': (
                self.stats['total_wait_time'] / self.stats['retried_requests']
                if self.stats['retried_requests'] > 0 else 0
            ),
            'success_rate': (
                self.stats['successful_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'rate_limit_rate': (
                self.stats['rate_limited_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
        }
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None


class AdaptiveRateLimiter:
    """
    自适应速率限制器
    
    根据API响应动态调整速率：
    - 如果频繁遇到429，降低速率
    - 如果长时间没有429，提高速率
    """
    
    def __init__(self, initial_rpm: int = 60, min_rpm: int = 10):
        self.current_rpm = initial_rpm
        self.min_rpm = min_rpm
        self.max_rpm = initial_rpm
        
        self.success_count = 0
        self.rate_limit_count = 0
        self.adjustment_interval = 10  # 每10次请求调整一次
        
        self.token_bucket = None
        self._update_bucket()
    
    def _update_bucket(self):
        """更新令牌桶"""
        self.token_bucket = TokenBucket(
            rate=self.current_rpm / 60.0,
            capacity=self.current_rpm
        )
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取令牌"""
        return await self.token_bucket.acquire(timeout)
    
    def report_success(self):
        """报告成功"""
        self.success_count += 1
        self._maybe_adjust()
    
    def report_rate_limit(self):
        """报告被限流"""
        self.rate_limit_count += 1
        self._maybe_adjust()
    
    def _maybe_adjust(self):
        """可能需要调整速率"""
        total = self.success_count + self.rate_limit_count
        
        if total >= self.adjustment_interval:
            # 计算成功率
            success_rate = self.success_count / total
            
            if success_rate < 0.8:
                # 成功率低，降低速率
                new_rpm = max(self.min_rpm, int(self.current_rpm * 0.8))
                if new_rpm < self.current_rpm:
                    logger.warning(f"成功率 {success_rate:.1%}，降低RPM: {self.current_rpm} → {new_rpm}")
                    self.current_rpm = new_rpm
                    self._update_bucket()
            elif success_rate > 0.95 and self.current_rpm < self.max_rpm:
                # 成功率高，尝试提高速率
                new_rpm = min(self.max_rpm, int(self.current_rpm * 1.1))
                if new_rpm > self.current_rpm:
                    logger.info(f"成功率 {success_rate:.1%}，提高RPM: {self.current_rpm} → {new_rpm}")
                    self.current_rpm = new_rpm
                    self._update_bucket()
            
            # 重置计数
            self.success_count = 0
            self.rate_limit_count = 0


# ============ 使用示例 ============

async def example():
    """使用示例"""
    
    # 配置（根据你的API Tier调整）
    config = LLMConfig(
        api_key="your-api-key",
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo",
        rpm_limit=60,  # 每分钟60个请求
        max_concurrent=10,  # 最多10个并发
        max_retries=5,
        base_wait_time=1.0,
    )
    
    # 创建处理器
    processor = LLMConcurrentProcessor(config)
    
    # 单个请求
    result = await processor.generate(
        prompt="总结这段文本...",
        system_prompt="你是专业助手"
    )
    print(f"结果: {result}")
    
    # 批量请求（自动并发控制）
    prompts = [
        "总结文本1...",
        "总结文本2...",
        "总结文本3...",
        # ... 100个提示词
    ]
    
    results = await processor.generate_batch(prompts)
    print(f"批量结果: {results}")
    
    # 查看统计
    stats = processor.get_stats()
    print(f"统计: {stats}")
    
    # 关闭
    await processor.close()


if __name__ == "__main__":
    asyncio.run(example())
