#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎方舟LLM并发处理器

针对火山引擎的特殊优化：
1. 预扣机制：请求时预扣除TPM配额
2. 默认限流：RPM和TPM双限制
3. 429/503专门处理：服务过载时等待重试
4. 自适应调整：根据错误率动态调整并发

官方文档：https://www.volcengine.com/docs/82379/1359411
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VolcengineConfig:
    """火山引擎配置"""
    api_key: str
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model: str = "ep-20260411182220-jv5qt"  # 主接入点 Doubao-Seed-2.0-mini
    
    # 火山引擎默认限流（根据账号等级调整）
    # 免费/试用账号：RPM较低
    # 付费账号：RPM较高，具体在开通管理页查看
    rpm_limit: int = 60  # 默认每分钟60请求，建议根据实际账号调整
    tpm_limit: int = 60000  # 默认每分钟6万token
    
    # 并发控制
    max_concurrent: int = 5  # 保守设置，避免触发限流
    
    # 重试策略（针对429/503）
    max_retries: int = 10  # 火山引擎建议多次重试
    base_wait_time: float = 2.0  # 基础等待时间
    max_wait_time: float = 120.0  # 最大等待时间
    
    # 自适应调整
    enable_adaptive: bool = True  # 启用自适应限流
    adaptive_window: int = 20  # 每20次请求调整一次


class VolcengineLLMProcessor:
    """
    火山引擎LLM处理器
    
    特点：
    1. TPM预扣机制-aware：控制token使用量
    2. 双限流：RPM + TPM同时控制
    3. 专门处理429/503：服务过载时智能等待
    4. 自适应：根据成功率动态调整速率
    """
    
    def __init__(self, config: VolcengineConfig):
        self.config = config
        
        # RPM控制（令牌桶）
        self.rpm_bucket = TokenBucket(
            rate=config.rpm_limit / 60.0,
            capacity=config.rpm_limit
        )
        
        # TPM控制（滑动窗口）
        self.tpm_window = TPMWindow(
            limit=config.tpm_limit,
            window_seconds=60
        )
        
        # 并发控制
        self.concurrency_semaphore = asyncio.Semaphore(config.max_concurrent)
        
        # HTTP会话
        self.session = None
        
        # 统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'rate_limited_429': 0,  # 429错误
            'overloaded_503': 0,    # 503错误
            'retried_requests': 0,
            'total_wait_time': 0.0,
        }
        
        # 自适应控制
        self.current_rpm = config.rpm_limit
        self.success_count = 0
        self.error_count = 0
    
    async def generate(self, 
                       prompt: str,
                       system_prompt: str = "",
                       max_tokens: int = 1500,
                       temperature: float = 0.7,
                       **kwargs) -> Dict[str, Any]:
        """
        生成文本 - 带火山引擎专门优化
        
        流程：
        1. 检查TPM配额（预扣机制）
        2. 获取RPM令牌
        3. 获取并发槽位
        4. 发送请求
        5. 处理429/503（专门等待重试）
        """
        start_time = time.time()
        prompt_tokens = self._estimate_tokens(prompt)
        
        async with self._get_stats_lock():
            self.stats['total_requests'] += 1
        
        for attempt in range(self.config.max_retries):
            try:
                # 1. TPM预扣检查
                total_tokens = prompt_tokens + max_tokens
                if not await self.tpm_window.try_acquire(total_tokens, timeout=30):
                    raise ServiceOverloadedError("TPM配额不足，等待中...")
                
                # 2. RPM限流
                if not await self.rpm_bucket.acquire(timeout=30):
                    raise RateLimitError("RPM限制，等待中...")
                
                # 3. 并发控制
                async with self.concurrency_semaphore:
                    # 4. 发送请求
                    result = await self._send_request(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    # 成功
                    await self._report_success()
                    
                    total_time = time.time() - start_time
                    return {
                        'success': True,
                        'text': result,
                        'duration': total_time,
                        'attempts': attempt + 1
                    }
                    
            except (RateLimitError, ServiceOverloadedError) as e:
                # 429/503错误 - 专门等待重试
                await self._report_rate_limited()
                
                wait_time = self._calculate_wait_time(attempt)
                logger.warning(
                    f"火山引擎限流（{type(e).__name__}），"
                    f"等待 {wait_time:.2f} 秒后重试 "
                    f"（{attempt+1}/{self.config.max_retries}）"
                )
                
                async with self._get_stats_lock():
                    if '429' in str(type(e)):
                        self.stats['rate_limited_429'] += 1
                    else:
                        self.stats['overloaded_503'] += 1
                    self.stats['retried_requests'] += 1
                    self.stats['total_wait_time'] += wait_time
                
                await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                # 其他错误
                logger.error(f"请求失败: {e}")
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
    
    async def _send_request(self, **kwargs) -> str:
        """发送请求到火山引擎"""
        # 这里使用volcenginesdkarkruntime或aiohttp
        # 示例使用官方SDK
        from volcenginesdkarkruntime import Ark
        
        client = Ark(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": kwargs.get('system_prompt', '')},
                {"role": "user", "content": kwargs['prompt']}
            ],
            max_tokens=kwargs.get('max_tokens', 1500),
            temperature=kwargs.get('temperature', 0.7)
        )
        
        return response.choices[0].message.content
    
    def _calculate_wait_time(self, attempt: int) -> float:
        """计算等待时间（指数退避 + 抖动）"""
        base = self.config.base_wait_time * (2 ** attempt)
        jitter = random.uniform(0, base * 0.1)  # 10%抖动
        return min(base + jitter, self.config.max_wait_time)
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数（简单实现）"""
        # 中文约1.5字符/token，英文约4字符/token
        # 简化计算：总字符数 / 2
        return len(text) // 2
    
    async def _report_success(self):
        """报告成功"""
        self.success_count += 1
        if self.config.enable_adaptive:
            await self._maybe_adjust_rate()
    
    async def _report_rate_limited(self):
        """报告被限流"""
        self.error_count += 1
        if self.config.enable_adaptive:
            await self._maybe_adjust_rate()
    
    async def _maybe_adjust_rate(self):
        """自适应调整速率"""
        total = self.success_count + self.error_count
        if total >= self.config.adaptive_window:
            success_rate = self.success_count / total
            
            if success_rate < 0.8:
                # 成功率低，降低RPM
                new_rpm = max(10, int(self.current_rpm * 0.8))
                if new_rpm < self.current_rpm:
                    logger.warning(
                        f"成功率 {success_rate:.1%}，降低RPM: "
                        f"{self.current_rpm} → {new_rpm}"
                    )
                    self.current_rpm = new_rpm
                    self.rpm_bucket = TokenBucket(
                        rate=new_rpm / 60.0,
                        capacity=new_rpm
                    )
            
            # 重置计数
            self.success_count = 0
            self.error_count = 0
    
    def _get_stats_lock(self):
        """获取统计锁"""
        if not hasattr(self, '_stats_lock'):
            self._stats_lock = asyncio.Lock()
        return self._stats_lock


class TokenBucket:
    """令牌桶 - RPM控制"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        start_time = time.time()
        
        while True:
            async with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                new_tokens = elapsed * self.rate
                self.tokens = min(self.capacity, self.tokens + new_tokens)
                self.last_update = now
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                wait_time = (1 - self.tokens) / self.rate
            
            if timeout is not None:
                elapsed_total = time.time() - start_time
                if elapsed_total + wait_time > timeout:
                    return False
                wait_time = min(wait_time, timeout - elapsed_total)
            
            await asyncio.sleep(wait_time)


class TPMWindow:
    """TPM滑动窗口 - TPM控制（预扣机制）"""
    
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window = window_seconds
        self.usage_history = []  # [(timestamp, tokens), ...]
        self.lock = asyncio.Lock()
    
    async def try_acquire(self, tokens: int, timeout: float = 30) -> bool:
        """尝试获取TPM配额"""
        start_time = time.time()
        
        while True:
            async with self.lock:
                now = time.time()
                
                # 清理过期记录
                cutoff = now - self.window
                self.usage_history = [
                    (t, tok) for t, tok in self.usage_history
                    if t > cutoff
                ]
                
                # 计算当前使用
                current_usage = sum(tok for _, tok in self.usage_history)
                
                # 检查是否足够
                if current_usage + tokens <= self.limit:
                    # 预扣除
                    self.usage_history.append((now, tokens))
                    return True
                
                # 计算需要等待的时间
                if self.usage_history:
                    oldest_time = min(t for t, _ in self.usage_history)
                    wait_time = self.window - (now - oldest_time)
                else:
                    wait_time = self.window
            
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed + wait_time > timeout:
                return False
            
            await asyncio.sleep(min(wait_time, 1.0))  # 最多等1秒再检查


class RateLimitError(Exception):
    """速率限制错误"""
    pass


class ServiceOverloadedError(Exception):
    """服务过载错误"""
    pass


# ============ 使用示例 ============

async def example():
    """使用示例"""
    
    config = VolcengineConfig(
        api_key="your-api-key",
        model="ep-20260411182220-jv5qt",
        rpm_limit=60,  # 根据你的账号等级调整
        tpm_limit=60000,
        max_concurrent=5,
        enable_adaptive=True
    )
    
    processor = VolcengineLLMProcessor(config)
    
    # 单个请求
    result = await processor.generate(
        prompt="总结这段文本...",
        system_prompt="你是专业助手"
    )
    print(f"结果: {result}")
    
    # 批量请求
    prompts = [f"总结文本{i}..." for i in range(10)]
    tasks = [processor.generate(p) for p in prompts]
    results = await asyncio.gather(*tasks)
    print(f"批量结果: {results}")


if __name__ == "__main__":
    asyncio.run(example())
