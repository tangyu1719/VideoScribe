"""
数据持久化模块
使用 JSON 文件存储数据，确保服务重启后数据不丢失
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LLM_CONFIGS_FILE = os.path.join(DATA_DIR, 'llm_configs.json')
AI_PERSONAS_FILE = os.path.join(DATA_DIR, 'ai_personas.json')
PARSERS_FILE = os.path.join(DATA_DIR, 'parsers.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'chat_sessions.json')
SESSION_GROUPS_FILE = os.path.join(DATA_DIR, 'session_groups.json')
APP_CONFIG_FILE = os.path.join(DATA_DIR, 'app_config.json')
VIDEO_TASKS_FILE = os.path.join(DATA_DIR, 'video_tasks.json')
LINK_TASKS_FILE = os.path.join(DATA_DIR, 'link_tasks.json')

def ensure_data_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"[Data] 创建数据目录：{DATA_DIR}")

def load_json(filepath: str, default: Any = None) -> Any:
    """加载 JSON 文件"""
    ensure_data_dir()
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Data] 加载 {filepath} 失败：{e}")
        return default if default is not None else {}

def save_json(filepath: str, data: Any):
    """保存 JSON 文件"""
    ensure_data_dir()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"[Data] 保存数据到 {filepath}")
    except Exception as e:
        print(f"[Data] 保存 {filepath} 失败：{e}")

# LLM 配置
def load_llm_configs() -> Dict[str, Any]:
    return load_json(LLM_CONFIGS_FILE, {})

def save_llm_config(config: Dict[str, Any]):
    configs = load_llm_configs()
    configs[config['id']] = config
    save_json(LLM_CONFIGS_FILE, configs)

def delete_llm_config(config_id: str):
    configs = load_llm_configs()
    if config_id in configs:
        del configs[config_id]
        save_json(LLM_CONFIGS_FILE, configs)

# AI 形象配置
def load_ai_personas() -> Dict[str, Any]:
    return load_json(AI_PERSONAS_FILE, {})

def save_ai_persona(persona: Dict[str, Any]):
    personas = load_ai_personas()
    personas[persona['id']] = persona
    save_json(AI_PERSONAS_FILE, personas)

def delete_ai_persona(persona_id: str):
    personas = load_ai_personas()
    if persona_id in personas:
        del personas[persona_id]
        save_json(AI_PERSONAS_FILE, personas)

# 解析器配置
def load_parsers() -> Dict[str, Any]:
    return load_json(PARSERS_FILE, {})

def save_parser(parser: Dict[str, Any]):
    parsers = load_parsers()
    parsers[parser['id']] = parser
    save_json(PARSERS_FILE, parsers)

def delete_parser(parser_id: str):
    parsers = load_parsers()
    if parser_id in parsers:
        del parsers[parser_id]
        save_json(PARSERS_FILE, parsers)

# 会话配置
def load_sessions() -> Dict[str, Any]:
    return load_json(SESSIONS_FILE, {})

def save_session(session: Dict[str, Any]):
    sessions = load_sessions()
    sessions[session['id']] = session
    save_json(SESSIONS_FILE, sessions)

def delete_session(session_id: str):
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_json(SESSIONS_FILE, sessions)

# 会话分组
def load_session_groups() -> Dict[str, Any]:
    return load_json(SESSION_GROUPS_FILE, {})

def save_session_group(group: Dict[str, Any]):
    groups = load_session_groups()
    groups[group['id']] = group
    save_json(SESSION_GROUPS_FILE, groups)

def delete_session_group(group_id: str):
    groups = load_session_groups()
    if group_id in groups:
        del groups[group_id]
        save_json(SESSION_GROUPS_FILE, groups)

# 应用配置
def load_app_config() -> Dict[str, Any]:
    return load_json(APP_CONFIG_FILE, {})

def save_app_config(config: Dict[str, Any]):
    save_json(APP_CONFIG_FILE, config)

# 视频任务
def load_video_tasks() -> Dict[str, Any]:
    return load_json(VIDEO_TASKS_FILE, {})

def save_video_task(task: Dict[str, Any]):
    tasks = load_video_tasks()
    tasks[task['id']] = task
    save_json(VIDEO_TASKS_FILE, tasks)

def delete_video_task(task_id: str):
    tasks = load_video_tasks()
    if task_id in tasks:
        del tasks[task_id]
        save_json(VIDEO_TASKS_FILE, tasks)

# 链接分析任务
def load_link_tasks() -> Dict[str, Any]:
    return load_json(LINK_TASKS_FILE, {})

def save_link_task(task: Dict[str, Any]):
    tasks = load_link_tasks()
    tasks[task['id']] = task
    save_json(LINK_TASKS_FILE, tasks)

def delete_link_task(task_id: str):
    tasks = load_link_tasks()
    if task_id in tasks:
        del tasks[task_id]
        save_json(LINK_TASKS_FILE, tasks)

# 初始化
print("[Data] 数据持久化模块已加载")
ensure_data_dir()
