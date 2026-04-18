#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI对话记忆系统 - 带Memory机制和任务管理
功能：
1. 存储对话上下文记忆
2. 任务自动命名和管理
3. 上下文压缩和归档
4. 左侧导航栏任务列表
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re


class ChatSession:
    """对话会话类"""
    
    def __init__(self, session_id: str = None, name: str = None):
        self.session_id = session_id or self._generate_id()
        self.name = name or f"新对话 {datetime.now().strftime('%m-%d %H:%M')}"
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.messages: List[Dict] = []
        self.summary = ""  # 对话摘要
        self.token_count = 0
        self.is_archived = False
        
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
    
    def add_message(self, role: str, content: str, tokens: int = 0):
        """添加消息"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'tokens': tokens
        })
        self.updated_at = datetime.now().isoformat()
        self.token_count += tokens
        
        # 自动更新会话名称（基于第一条用户消息）
        if len(self.messages) == 1 and role == 'user':
            self.name = self._auto_name(content)
    
    def _auto_name(self, first_message: str) -> str:
        """基于第一条消息自动生成名称"""
        # 提取前20个字符作为名称
        name = first_message[:30].strip()
        # 去除特殊字符
        name = re.sub(r'[\\/*?":<>|]', '', name)
        # 添加时间戳
        time_str = datetime.now().strftime('%m-%d')
        if len(name) > 20:
            name = name[:20] + "..."
        return f"{name} ({time_str})"
    
    def get_context(self, max_messages: int = 10) -> str:
        """获取对话上下文"""
        recent_messages = self.messages[-max_messages:]
        context = []
        for msg in recent_messages:
            role_name = "用户" if msg['role'] == 'user' else "助手"
            context.append(f"{role_name}: {msg['content'][:200]}")
        return "\n".join(context)
    
    def compress(self) -> str:
        """压缩对话内容为摘要"""
        if len(self.messages) < 3:
            return self.get_context()
        
        # 提取关键信息
        key_points = []
        user_questions = [m['content'][:100] for m in self.messages if m['role'] == 'user']
        assistant_answers = [m['content'][:100] for m in self.messages if m['role'] == 'assistant']
        
        summary = f"对话主题: {self.name}\n"
        summary += f"问题数: {len(user_questions)}\n"
        summary += f"主要问题: {'; '.join(user_questions[:3])}\n"
        summary += f"关键回答: {'; '.join(assistant_answers[:3])}"
        
        self.summary = summary
        self.is_archived = True
        return summary
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'messages': self.messages,
            'summary': self.summary,
            'token_count': self.token_count,
            'is_archived': self.is_archived
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatSession':
        session = cls(data['session_id'], data['name'])
        session.created_at = data.get('created_at', datetime.now().isoformat())
        session.updated_at = data.get('updated_at', session.created_at)
        session.messages = data.get('messages', [])
        session.summary = data.get('summary', '')
        session.token_count = data.get('token_count', 0)
        session.is_archived = data.get('is_archived', False)
        return session


class ChatMemoryManager:
    """对话记忆管理器"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.memory_dir = os.path.join(self.base_dir, "chat_memory")
        self.active_session_file = os.path.join(self.memory_dir, "active_session.json")
        self.sessions_dir = os.path.join(self.memory_dir, "sessions")
        self.archive_dir = os.path.join(self.memory_dir, "archive")
        
        # 创建目录
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        
        # 当前会话
        self.current_session: Optional[ChatSession] = None
        self.sessions: Dict[str, ChatSession] = {}
        
        # 加载历史会话
        self._load_sessions()
        
        # 最大消息数限制
        self.max_messages_per_session = 50
        self.max_tokens_per_session = 4000
    
    def _load_sessions(self):
        """加载所有会话"""
        if os.path.exists(self.sessions_dir):
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.sessions_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            session = ChatSession.from_dict(data)
                            self.sessions[session.session_id] = session
                    except Exception as e:
                        print(f"加载会话失败 {filename}: {e}")
        
        print(f"已加载 {len(self.sessions)} 个历史会话")
    
    def create_new_session(self) -> ChatSession:
        """创建新会话"""
        # 保存当前会话
        if self.current_session:
            self._save_session(self.current_session)
        
        # 创建新会话
        self.current_session = ChatSession()
        self.sessions[self.current_session.session_id] = self.current_session
        self._save_session(self.current_session)
        
        print(f"创建新会话: {self.current_session.name}")
        return self.current_session
    
    def switch_session(self, session_id: str) -> Optional[ChatSession]:
        """切换到指定会话"""
        # 保存当前会话
        if self.current_session:
            self._save_session(self.current_session)
        
        # 加载目标会话
        if session_id in self.sessions:
            self.current_session = self.sessions[session_id]
            print(f"切换到会话: {self.current_session.name}")
            return self.current_session
        
        # 尝试从文件加载
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = ChatSession.from_dict(data)
                    self.sessions[session_id] = session
                    self.current_session = session
                    return session
            except Exception as e:
                print(f"加载会话失败: {e}")
        
        return None
    
    def add_message(self, role: str, content: str, tokens: int = 0):
        """添加消息到当前会话"""
        if not self.current_session:
            self.create_new_session()
        
        # 检查是否需要压缩
        if len(self.current_session.messages) >= self.max_messages_per_session:
            self._compress_current_session()
        
        self.current_session.add_message(role, content, tokens)
        self._save_session(self.current_session)
    
    def _compress_current_session(self):
        """压缩当前会话"""
        if not self.current_session:
            return
        
        print(f"压缩会话: {self.current_session.name}")
        
        # 生成摘要
        summary = self.current_session.compress()
        
        # 保存到归档
        archive_path = os.path.join(
            self.archive_dir,
            f"{self.current_session.session_id}_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_session.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 清空消息，保留摘要
        self.current_session.messages = []
        self.current_session.add_message('system', f"[历史对话摘要]\n{summary}")
        
        print(f"会话已压缩并归档: {archive_path}")
    
    def _save_session(self, session: ChatSession):
        """保存会话到文件"""
        filepath = os.path.join(self.sessions_dir, f"{session.session_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话列表"""
        sessions = []
        for session_id, session in self.sessions.items():
            sessions.append({
                'session_id': session_id,
                'name': session.name,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'message_count': len(session.messages),
                'is_current': self.current_session and self.current_session.session_id == session_id
            })
        
        # 按更新时间排序
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
            # 删除文件
            filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # 如果删除的是当前会话，创建新会话
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
                self.create_new_session()
            
            return True
        return False
    
    def get_current_context(self, max_messages: int = 10) -> str:
        """获取当前会话的上下文"""
        if not self.current_session:
            return ""
        return self.current_session.get_context(max_messages)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        total_tokens = sum(s.token_count for s in self.sessions.values())
        
        return {
            'total_sessions': len(self.sessions),
            'total_messages': total_messages,
            'total_tokens': total_tokens,
            'current_session': self.current_session.name if self.current_session else None,
            'memory_dir': self.memory_dir
        }


# 测试代码
if __name__ == "__main__":
    print("="*60)
    print("对话记忆系统测试")
    print("="*60)
    
    manager = ChatMemoryManager()
    
    # 创建新会话
    session = manager.create_new_session()
    print(f"\n创建会话: {session.name}")
    
    # 添加消息
    manager.add_message('user', '如何优化Java高并发系统？')
    manager.add_message('assistant', '优化Java高并发系统可以从以下几个方面入手：1. 线程池优化 2. 锁优化 3. 缓存策略')
    manager.add_message('user', '能详细说一下线程池优化吗？')
    
    # 显示统计
    stats = manager.get_stats()
    print(f"\n统计信息:")
    print(f"- 总会话数: {stats['total_sessions']}")
    print(f"- 总消息数: {stats['total_messages']}")
    print(f"- 当前会话: {stats['current_session']}")
    
    # 显示所有会话
    print(f"\n所有会话:")
    for s in manager.get_all_sessions():
        print(f"- {s['name']} ({s['message_count']}条消息)")
    
    print("\n" + "="*60)
