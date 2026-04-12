"""
日志监控 Agent 配置模块
独立 LLM 配置，从备用 API 配置读取
"""
import os
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """LLM 配置类"""
    api_key: str
    base_url: str
    model: str
    timeout: int = 300
    max_retries: int = 3
    temperature: float = 0.1
    max_tokens: int = 2000

@dataclass
class AgentConfig:
    """Agent 配置类"""
    enabled: bool = True
    name: str = "日志监控 Agent"
    version: str = "1.0.0"
    
    # 异步执行配置
    thread_pool_size: int = 5
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    
    # 错误检测配置
    error_levels: List[str] = None
    warning_patterns: List[str] = None
    ignore_patterns: List[str] = None
    
    # 自动修复配置
    auto_fix_enabled: bool = True
    max_retries: int = 3
    require_confirmation: bool = False
    
    # 学习配置
    learning_enabled: bool = True
    min_confidence: float = 0.8
    
    def __post_init__(self):
        if self.error_levels is None:
            self.error_levels = ["ERROR", "CRITICAL"]
        if self.warning_patterns is None:
            self.warning_patterns = ["timeout", "retry failed", "connection refused"]
        if self.ignore_patterns is None:
            self.ignore_patterns = ["debug test", "expected error"]

# 日志监控 Agent 专用 LLM 配置（从备用 API 读取）
LOG_AGENT_LLM_CONFIG = LLMConfig(
    api_key=os.getenv('LOG_AGENT_API_KEY', ''),
    base_url=os.getenv('LOG_AGENT_BASE_URL', 'https://api.openai.com/v1'),
    model=os.getenv('LOG_AGENT_MODEL', 'gpt-4'),
    timeout=int(os.getenv('LOG_AGENT_TIMEOUT', '300')),
    max_retries=int(os.getenv('LOG_AGENT_MAX_RETRIES', '3')),
    temperature=0.1,
    max_tokens=2000
)

# 备用 API 配置（多套配置轮换）
BACKUP_API_CONFIGS: List[Dict[str, str]] = [
    {
        'name': '备用 API 1',
        'api_key': os.getenv('BACKUP_API_KEY_1', ''),
        'base_url': os.getenv('BACKUP_BASE_URL_1', ''),
        'model': os.getenv('BACKUP_MODEL_1', 'gpt-3.5-turbo')
    },
    {
        'name': '备用 API 2',
        'api_key': os.getenv('BACKUP_API_KEY_2', ''),
        'base_url': os.getenv('BACKUP_BASE_URL_2', ''),
        'model': os.getenv('BACKUP_MODEL_2', 'gpt-3.5-turbo')
    },
    {
        'name': '备用 API 3',
        'api_key': os.getenv('BACKUP_API_KEY_3', ''),
        'base_url': os.getenv('BACKUP_BASE_URL_3', ''),
        'model': os.getenv('BACKUP_MODEL_3', 'gpt-3.5-turbo')
    }
]

def get_llm_config(use_backup: bool = True, api_index: int = 0) -> LLMConfig:
    """
    获取 LLM 配置
    
    Args:
        use_backup: 是否使用备用 API
        api_index: 备用 API 索引
    
    Returns:
        LLMConfig 配置对象
    """
    if use_backup and BACKUP_API_CONFIGS:
        # 从备用 API 中选择
        index = api_index % len(BACKUP_API_CONFIGS)
        backup_config = BACKUP_API_CONFIGS[index]
        return LLMConfig(
            api_key=backup_config['api_key'],
            base_url=backup_config['base_url'],
            model=backup_config['model'],
            timeout=300,
            max_retries=3
        )
    else:
        return LOG_AGENT_LLM_CONFIG

def get_agent_config() -> AgentConfig:
    """获取 Agent 配置"""
    return AgentConfig(
        enabled=os.getenv('AGENT_ENABLED', 'true').lower() == 'true',
        thread_pool_size=int(os.getenv('AGENT_THREAD_POOL_SIZE', '5')),
        max_concurrent_tasks=int(os.getenv('AGENT_MAX_CONCURRENT_TASKS', '10')),
        task_timeout=int(os.getenv('AGENT_TASK_TIMEOUT', '300')),
        auto_fix_enabled=os.getenv('AGENT_AUTO_FIX_ENABLED', 'true').lower() == 'true',
        max_retries=int(os.getenv('AGENT_MAX_RETRIES', '3')),
        learning_enabled=os.getenv('AGENT_LEARNING_ENABLED', 'true').lower() == 'true',
        min_confidence=float(os.getenv('AGENT_MIN_CONFIDENCE', '0.8'))
    )
