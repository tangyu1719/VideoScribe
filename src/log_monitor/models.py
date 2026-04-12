"""
日志监控 Agent 数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import uuid

@dataclass
class ErrorRecord:
    """错误记录模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_type: str = ""  # 配置 | 网络 | 代码 | 资源 | 其他
    severity: str = ""  # critical|high|medium|low
    error_log: str = ""
    module: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    analysis_result: Optional[Dict[str, Any]] = None
    fix_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    auto_fixed: bool = False
    fix_status: str = "pending"  # pending/running/success/failed/cancelled
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'error_type': self.error_type,
            'severity': self.severity,
            'error_log': self.error_log,
            'module': self.module,
            'timestamp': self.timestamp.isoformat(),
            'context': json.dumps(self.context),
            'analysis_result': json.dumps(self.analysis_result) if self.analysis_result else None,
            'fix_suggestions': json.dumps(self.fix_suggestions),
            'auto_fixed': self.auto_fixed,
            'fix_status': self.fix_status,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ErrorRecord':
        """从字典创建"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            error_type=data.get('error_type', ''),
            severity=data.get('severity', ''),
            error_log=data.get('error_log', ''),
            module=data.get('module', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
            context=json.loads(data.get('context', '{}')) if data.get('context') else {},
            analysis_result=json.loads(data['analysis_result']) if data.get('analysis_result') else None,
            fix_suggestions=json.loads(data.get('fix_suggestions', '[]')) if data.get('fix_suggestions') else [],
            auto_fixed=data.get('auto_fixed', False),
            fix_status=data.get('fix_status', 'pending'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )

@dataclass
class SuccessRule:
    """成功规则模型"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern: str = ""
    diagnosis: str = ""
    solution: str = ""
    auto_fix: bool = False
    confidence: float = 0.5
    learned_from: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'pattern': self.pattern,
            'diagnosis': self.diagnosis,
            'solution': self.solution,
            'auto_fix': self.auto_fix,
            'confidence': self.confidence,
            'learned_from': json.dumps(self.learned_from),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SuccessRule':
        """从字典创建"""
        return cls(
            rule_id=data.get('rule_id', str(uuid.uuid4())),
            pattern=data.get('pattern', ''),
            diagnosis=data.get('diagnosis', ''),
            solution=data.get('solution', ''),
            auto_fix=data.get('auto_fix', False),
            confidence=float(data.get('confidence', 0.5)),
            learned_from=json.loads(data.get('learned_from', '[]')) if data.get('learned_from') else [],
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )

@dataclass
class FixHistory:
    """修复历史模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_record_id: str = ""
    fix_action: str = ""
    fix_result: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    retry_count: int = 0
    execution_time: int = 0  # 毫秒
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'error_record_id': self.error_record_id,
            'fix_action': self.fix_action,
            'fix_result': json.dumps(self.fix_result),
            'success': self.success,
            'retry_count': self.retry_count,
            'execution_time': self.execution_time,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FixHistory':
        """从字典创建"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            error_record_id=data.get('error_record_id', ''),
            fix_action=data.get('fix_action', ''),
            fix_result=json.loads(data.get('fix_result', '{}')) if data.get('fix_result') else {},
            success=data.get('success', False),
            retry_count=data.get('retry_count', 0),
            execution_time=data.get('execution_time', 0),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        )

@dataclass
class ErrorAnalysisResult:
    """错误分析结果"""
    error_id: str
    error_type: str
    severity: str
    root_cause: str
    analysis: str
    auto_fixable: bool
    fix_suggestions: List[Dict[str, Any]]
    retry_recommended: bool
    retry_config: Dict[str, Any]
    confidence_score: float
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'error_id': self.error_id,
            'error_type': self.error_type,
            'severity': self.severity,
            'root_cause': self.root_cause,
            'analysis': self.analysis,
            'auto_fixable': self.auto_fixable,
            'fix_suggestions': self.fix_suggestions,
            'retry_recommended': self.retry_recommended,
            'retry_config': self.retry_config,
            'confidence_score': self.confidence_score
        }
