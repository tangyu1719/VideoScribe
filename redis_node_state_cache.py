#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis节点状态缓存管理器
用于单次任务的节点状态快速重试

联合主键设计: task_id + conversation_id + query_seq + node_id
"""

import json
import time
import redis
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import threading


class NodeStatus(Enum):
    """节点状态枚举"""
    PENDING = "pending"           # 等待执行
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败
    RETRYING = "retrying"         # 重试中
    CANCELLED = "cancelled"       # 已取消
    TIMEOUT = "timeout"           # 超时
    CACHE_HIT = "cache_hit"       # 缓存命中
    CACHE_MISS = "cache_miss"     # 缓存未命中


@dataclass
class NodeState:
    """节点状态数据类"""
    # 联合主键
    task_id: str                  # 主任务ID
    conversation_id: str          # 对话ID
    query_seq: int                # 原始Query序号
    node_id: str                  # 节点ID
    
    # 节点信息
    node_type: str                # 节点类型
    status: NodeStatus            # 当前状态
    
    # 输入输出
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 执行信息
    duration_ms: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    # 缓存信息（与常态缓存区分）
    cache_key: Optional[str] = None       # 关联的常态缓存key
    cache_hit: bool = False               # 是否命中常态缓存
    node_cache_enabled: bool = True       # 是否启用节点状态缓存
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NodeState':
        """从字典创建"""
        data = data.copy()
        data['status'] = NodeStatus(data['status'])
        return cls(**data)


class RedisNodeStateCache:
    """
    Redis节点状态缓存管理器
    
    特点:
    1. 联合主键: task_id + conversation_id + query_seq + node_id
    2. 单次任务生命周期，任务完成后自动过期
    3. 支持节点级快速重试
    4. 与常态缓存分离，常态缓存用于全局命中，本缓存用于单次任务状态
    """
    
    # Redis键前缀
    KEY_PREFIX = "node_state"
    TASK_INDEX_PREFIX = "node_state:index:task"
    CONV_INDEX_PREFIX = "node_state:index:conv"
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 password: Optional[str] = None,
                 default_ttl: int = 3600):
        """
        初始化Redis缓存
        
        Args:
            redis_host: Redis主机地址
            redis_port: Redis端口
            redis_db: Redis数据库
            password: Redis密码
            default_ttl: 默认过期时间(秒)
        """
        self._redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=password,
            decode_responses=True
        )
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        
        # 检查连接
        try:
            self._redis.ping()
            print(f"[RedisNodeStateCache] Redis连接成功: {redis_host}:{redis_port}/{redis_db}")
        except redis.ConnectionError as e:
            print(f"[RedisNodeStateCache] Redis连接失败: {e}")
            raise
    
    def _make_key(self, task_id: str, conversation_id: str, query_seq: int, node_id: str) -> str:
        """
        生成Redis键
        格式: node_state:{task_id}:{conversation_id}:{query_seq}:{node_id}
        """
        return f"{self.KEY_PREFIX}:{task_id}:{conversation_id}:{query_seq}:{node_id}"
    
    def _make_task_index_key(self, task_id: str) -> str:
        """生成任务索引键"""
        return f"{self.TASK_INDEX_PREFIX}:{task_id}"
    
    def _make_conv_index_key(self, conversation_id: str) -> str:
        """生成对话索引键"""
        return f"{self.CONV_INDEX_PREFIX}:{conversation_id}"
    
    def _parse_key(self, key: str) -> Optional[Dict[str, Any]]:
        """解析Redis键"""
        parts = key.split(":")
        if len(parts) != 5 or parts[0] != self.KEY_PREFIX:
            return None
        return {
            "task_id": parts[1],
            "conversation_id": parts[2],
            "query_seq": int(parts[3]),
            "node_id": parts[4]
        }
    
    def put(self, state: NodeState, ttl: Optional[int] = None) -> bool:
        """
        存储节点状态
        
        Args:
            state: 节点状态对象
            ttl: 过期时间(秒)，默认使用初始化时的default_ttl
        
        Returns:
            bool: 是否成功
        """
        try:
            key = self._make_key(
                state.task_id,
                state.conversation_id,
                state.query_seq,
                state.node_id
            )
            
            # 序列化
            data = json.dumps(state.to_dict(), default=str)
            
            # 使用管道批量操作
            pipe = self._redis.pipeline()
            
            # 存储状态
            pipe.setex(key, ttl or self._default_ttl, data)
            
            # 添加到任务索引 (Set结构，自动去重)
            task_index_key = self._make_task_index_key(state.task_id)
            pipe.sadd(task_index_key, key)
            pipe.expire(task_index_key, ttl or self._default_ttl)
            
            # 添加到对话索引
            conv_index_key = self._make_conv_index_key(state.conversation_id)
            pipe.sadd(conv_index_key, key)
            pipe.expire(conv_index_key, ttl or self._default_ttl)
            
            pipe.execute()
            
            return True
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 存储失败: {e}")
            return False
    
    def get(self, task_id: str, conversation_id: str, query_seq: int, 
            node_id: str) -> Optional[NodeState]:
        """
        获取节点状态
        
        Args:
            task_id: 主任务ID
            conversation_id: 对话ID
            query_seq: Query序号
            node_id: 节点ID
        
        Returns:
            NodeState或None
        """
        try:
            key = self._make_key(task_id, conversation_id, query_seq, node_id)
            data = self._redis.get(key)
            
            if not data:
                return None
            
            # 延长TTL (LRU策略)
            self._redis.expire(key, self._default_ttl)
            
            # 反序列化
            dict_data = json.loads(data)
            return NodeState.from_dict(dict_data)
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 获取失败: {e}")
            return None
    
    def update_status(self, task_id: str, conversation_id: str, query_seq: int,
                      node_id: str, status: NodeStatus, **kwargs) -> bool:
        """
        更新节点状态
        
        Args:
            task_id: 主任务ID
            conversation_id: 对话ID
            query_seq: Query序号
            node_id: 节点ID
            status: 新状态
            **kwargs: 其他要更新的字段
        
        Returns:
            bool: 是否成功
        """
        try:
            # 先获取当前状态
            state = self.get(task_id, conversation_id, query_seq, node_id)
            if not state:
                return False
            
            # 更新状态
            state.status = status
            
            # 自动更新时间戳
            if status == NodeStatus.RUNNING and not state.started_at:
                state.started_at = time.time()
            
            if status in [NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.CANCELLED]:
                state.completed_at = time.time()
                if state.started_at:
                    state.duration_ms = (state.completed_at - state.started_at) * 1000
            
            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            
            # 重新存储
            return self.put(state)
            
        except Exception as e:
            print(f"[RedisNodeStateCache] 更新失败: {e}")
            return False
    
    def get_task_nodes(self, task_id: str, conversation_id: Optional[str] = None,
                       query_seq: Optional[int] = None) -> Dict[str, NodeState]:
        """
        获取任务的所有节点状态
        
        Args:
            task_id: 主任务ID
            conversation_id: 可选，过滤特定对话
            query_seq: 可选，过滤特定Query序号
        
        Returns:
            Dict[node_id, NodeState]
        """
        try:
            # 从任务索引获取所有键
            task_index_key = self._make_task_index_key(task_id)
            keys = self._redis.smembers(task_index_key)
            
            nodes = {}
            for key in keys:
                # 解析键
                parsed = self._parse_key(key)
                if not parsed:
                    continue
                
                # 过滤条件
                if conversation_id and parsed["conversation_id"] != conversation_id:
                    continue
                if query_seq is not None and parsed["query_seq"] != query_seq:
                    continue
                
                # 获取状态
                data = self._redis.get(key)
                if data:
                    dict_data = json.loads(data)
                    state = NodeState.from_dict(dict_data)
                    nodes[state.node_id] = state
            
            return nodes
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 获取任务节点失败: {e}")
            return {}
    
    def get_conversation_nodes(self, conversation_id: str) -> Dict[str, NodeState]:
        """
        获取对话的所有节点状态
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            Dict[composite_key, NodeState] 
            composite_key格式: "{task_id}:{query_seq}:{node_id}"
        """
        try:
            conv_index_key = self._make_conv_index_key(conversation_id)
            keys = self._redis.smembers(conv_index_key)
            
            nodes = {}
            for key in keys:
                parsed = self._parse_key(key)
                if not parsed:
                    continue
                
                data = self._redis.get(key)
                if data:
                    dict_data = json.loads(data)
                    state = NodeState.from_dict(dict_data)
                    composite_key = f"{state.task_id}:{state.query_seq}:{state.node_id}"
                    nodes[composite_key] = state
            
            return nodes
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 获取对话节点失败: {e}")
            return {}
    
    def clear_task(self, task_id: str) -> int:
        """
        清理任务的所有节点状态
        
        Args:
            task_id: 主任务ID
        
        Returns:
            int: 清理的节点数量
        """
        try:
            task_index_key = self._make_task_index_key(task_id)
            keys = self._redis.smembers(task_index_key)
            
            if not keys:
                return 0
            
            # 使用管道批量删除
            pipe = self._redis.pipeline()
            
            for key in keys:
                pipe.delete(key)
                # 从对话索引中移除
                parsed = self._parse_key(key)
                if parsed:
                    conv_index_key = self._make_conv_index_key(parsed["conversation_id"])
                    pipe.srem(conv_index_key, key)
            
            # 删除任务索引
            pipe.delete(task_index_key)
            
            pipe.execute()
            
            return len(keys)
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 清理任务失败: {e}")
            return 0
    
    def clear_conversation(self, conversation_id: str) -> int:
        """
        清理对话的所有节点状态
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            int: 清理的节点数量
        """
        try:
            conv_index_key = self._make_conv_index_key(conversation_id)
            keys = self._redis.smembers(conv_index_key)
            
            if not keys:
                return 0
            
            pipe = self._redis.pipeline()
            
            for key in keys:
                pipe.delete(key)
                # 从任务索引中移除
                parsed = self._parse_key(key)
                if parsed:
                    task_index_key = self._make_task_index_key(parsed["task_id"])
                    pipe.srem(task_index_key, key)
            
            # 删除对话索引
            pipe.delete(conv_index_key)
            
            pipe.execute()
            
            return len(keys)
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 清理对话失败: {e}")
            return 0
    
    def get_retry_candidates(self, task_id: str, max_retry: int = 3) -> List[NodeState]:
        """
        获取需要重试的节点列表
        
        Args:
            task_id: 主任务ID
            max_retry: 最大重试次数
        
        Returns:
            List[NodeState]: 需要重试的节点列表
        """
        nodes = self.get_task_nodes(task_id)
        
        candidates = []
        for state in nodes.values():
            # 失败且未达到最大重试次数
            if (state.status == NodeStatus.FAILED and 
                state.retry_count < max_retry):
                candidates.append(state)
            
            # 超时的节点
            elif state.status == NodeStatus.TIMEOUT:
                candidates.append(state)
        
        # 按创建时间排序，先创建的优先重试
        candidates.sort(key=lambda x: x.created_at)
        
        return candidates
    
    def batch_update_status(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新节点状态
        
        Args:
            updates: 更新列表，每项包含task_id, conversation_id, query_seq, node_id, status等
        
        Returns:
            int: 成功更新的数量
        """
        success_count = 0
        
        for update in updates:
            try:
                result = self.update_status(
                    task_id=update["task_id"],
                    conversation_id=update["conversation_id"],
                    query_seq=update["query_seq"],
                    node_id=update["node_id"],
                    status=update["status"],
                    **update.get("extra", {})
                )
                if result:
                    success_count += 1
            except Exception as e:
                print(f"[RedisNodeStateCache] 批量更新单项失败: {e}")
        
        return success_count
    
    def get_statistics(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            task_id: 可选，指定任务
        
        Returns:
            统计信息字典
        """
        try:
            if task_id:
                nodes = self.get_task_nodes(task_id)
            else:
                # 获取所有任务
                pattern = f"{self.KEY_PREFIX}:*"
                keys = self._redis.keys(pattern)
                nodes = {}
                for key in keys:
                    data = self._redis.get(key)
                    if data:
                        dict_data = json.loads(data)
                        state = NodeState.from_dict(dict_data)
                        nodes[state.node_id] = state
            
            # 统计
            total = len(nodes)
            status_count = {}
            retry_count = 0
            cache_hit_count = 0
            
            for state in nodes.values():
                status_count[state.status.value] = status_count.get(state.status.value, 0) + 1
                if state.retry_count > 0:
                    retry_count += 1
                if state.cache_hit:
                    cache_hit_count += 1
            
            return {
                "total_nodes": total,
                "status_distribution": status_count,
                "retry_nodes": retry_count,
                "cache_hit_nodes": cache_hit_count,
                "cache_hit_rate": cache_hit_count / total if total > 0 else 0
            }
            
        except redis.RedisError as e:
            print(f"[RedisNodeStateCache] 获取统计失败: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            start = time.time()
            self._redis.ping()
            latency = (time.time() - start) * 1000
            
            info = self._redis.info()
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "total_keys": self._redis.dbsize()
            }
            
        except redis.RedisError as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局单例实例
_node_state_cache: Optional[RedisNodeStateCache] = None


def get_node_state_cache(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    password: Optional[str] = None,
    default_ttl: int = 3600
) -> RedisNodeStateCache:
    """
    获取全局单例
    
    使用示例:
        cache = get_node_state_cache(redis_host="localhost")
        cache.put(node_state)
    """
    global _node_state_cache
    
    if _node_state_cache is None:
        _node_state_cache = RedisNodeStateCache(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            password=password,
            default_ttl=default_ttl
        )
    
    return _node_state_cache


# 便捷函数
def create_node_state(
    task_id: str,
    conversation_id: str,
    query_seq: int,
    node_id: str,
    node_type: str,
    status: NodeStatus = NodeStatus.PENDING,
    inputs: Optional[Dict] = None,
    max_retries: int = 3
) -> NodeState:
    """
    便捷函数：创建节点状态
    """
    return NodeState(
        task_id=task_id,
        conversation_id=conversation_id,
        query_seq=query_seq,
        node_id=node_id,
        node_type=node_type,
        status=status,
        inputs=inputs or {},
        max_retries=max_retries
    )


# 测试代码
if __name__ == "__main__":
    # 测试
    cache = get_node_state_cache()
    
    # 创建节点状态
    state = create_node_state(
        task_id="task-001",
        conversation_id="conv-001",
        query_seq=1,
        node_id="query_embedding_001",
        node_type="query_embedding",
        inputs={"query": "订单同步失败怎么办"}
    )
    
    # 存储
    cache.put(state)
    print(f"存储节点状态: {state.node_id}")
    
    # 获取
    retrieved = cache.get("task-001", "conv-001", 1, "query_embedding_001")
    print(f"获取节点状态: {retrieved.status.value if retrieved else 'None'}")
    
    # 更新状态
    cache.update_status(
        "task-001", "conv-001", 1, "query_embedding_001",
        NodeStatus.RUNNING
    )
    
    # 获取任务所有节点
    nodes = cache.get_task_nodes("task-001")
    print(f"任务节点数: {len(nodes)}")
    
    # 统计
    stats = cache.get_statistics("task-001")
    print(f"统计: {stats}")
    
    # 健康检查
    health = cache.health_check()
    print(f"健康状态: {health}")
    
    # 清理
    count = cache.clear_task("task-001")
    print(f"清理节点数: {count}")
