"""
规则学习器
从历史案例中学习，完善成功规则
"""
import json
from typing import Dict, List, Optional
from datetime import datetime

from .models import SuccessRule, ErrorRecord
from .config import get_agent_config
from db import get_db_connection
from logging_system import Logger

logger = Logger("RuleLearner")

class RuleLearner:
    """规则学习器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_agent_config()
        self.rules_cache: Dict[str, SuccessRule] = {}
        self._load_rules()
    
    def _load_rules(self):
        """从数据库加载规则"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT * FROM success_rules WHERE is_active = TRUE")
            rows = cursor.fetchall()
            
            for row in rows:
                rule = SuccessRule.from_dict(row)
                self.rules_cache[rule.rule_id] = rule
            
            logger.info(f"加载了 {len(self.rules_cache)} 条规则")
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"加载规则失败：{e}")
    
    async def learn_from_success(self, error_record: ErrorRecord, analysis_result: Dict):
        """
        从成功案例学习
        
        Args:
            error_record: 错误记录
            analysis_result: 分析结果
        """
        if not self.config.learning_enabled:
            return
        
        logger.info(f"从成功案例学习：{error_record.id}")
        
        try:
            # 提取规则
            new_rule = self._extract_rule(error_record, analysis_result, success=True)
            
            if new_rule and new_rule.confidence >= self.config.min_confidence:
                # 保存规则
                await self._save_rule(new_rule)
                logger.info(f"学习到新规则：{new_rule.rule_id}")
            
        except Exception as e:
            logger.error(f"从成功案例学习失败：{e}")
    
    async def learn_from_failure(self, error_record: ErrorRecord, analysis_result: Dict):
        """
        从失败案例学习
        
        Args:
            error_record: 错误记录
            analysis_result: 分析结果
        """
        if not self.config.learning_enabled:
            return
        
        logger.info(f"从失败案例学习：{error_record.id}")
        
        try:
            # 分析失败原因
            await self._analyze_failure(error_record, analysis_result)
            
        except Exception as e:
            logger.error(f"从失败案例学习失败：{e}")
    
    def _extract_rule(self, error_record: ErrorRecord, analysis_result: Dict, success: bool) -> Optional[SuccessRule]:
        """
        从案例提取规则
        
        Args:
            error_record: 错误记录
            analysis_result: 分析结果
            success: 是否成功
        
        Returns:
            新规则
        """
        try:
            # 从错误日志提取模式
            error_log = error_record.error_log
            error_type = analysis_result.get('error_type', '其他')
            
            # 生成规则模式（简化版）
            import re
            words = re.findall(r'\b\w+\b', error_log.lower())
            
            # 提取关键词
            keywords = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'with', 'from']]
            pattern = '.*' + '.*'.join(keywords[:3]) + '.*' if keywords else '.*'
            
            # 创建规则
            rule = SuccessRule(
                pattern=pattern,
                diagnosis=analysis_result.get('root_cause', ''),
                solution=str(analysis_result.get('fix_suggestions', [])),
                auto_fix=analysis_result.get('auto_fixable', False),
                confidence=0.7 if success else 0.5,
                learned_from=[error_record.id]
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"提取规则失败：{e}")
            return None
    
    async def _analyze_failure(self, error_record: ErrorRecord, analysis_result: Dict):
        """分析失败原因"""
        # 这里可以调用 LLM 分析失败原因
        # 简化版只记录日志
        logger.warning(f"失败案例：{error_record.id}, 错误类型：{analysis_result.get('error_type')}")
    
    async def _save_rule(self, rule: SuccessRule):
        """保存规则到数据库"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO success_rules 
            (rule_id, pattern, diagnosis, solution, auto_fix, confidence, learned_from)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(sql, (
                rule.rule_id,
                rule.pattern,
                rule.diagnosis,
                rule.solution,
                rule.auto_fix,
                rule.confidence,
                json.dumps(rule.learned_from)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # 更新缓存
            self.rules_cache[rule.rule_id] = rule
            
            logger.info(f"规则已保存：{rule.rule_id}")
            
        except Exception as e:
            logger.error(f"保存规则失败：{e}")
    
    def match_rule(self, error_log: str) -> Optional[SuccessRule]:
        """
        匹配规则
        
        Args:
            error_log: 错误日志
        
        Returns:
            匹配的规则
        """
        import re
        
        for rule in self.rules_cache.values():
            if re.search(rule.pattern, error_log.lower()):
                logger.info(f"匹配规则：{rule.rule_id}")
                return rule
        
        return None


# 单例
_rule_learner_instance: Optional[RuleLearner] = None

def get_rule_learner() -> RuleLearner:
    """获取规则学习器单例"""
    global _rule_learner_instance
    if _rule_learner_instance is None:
        _rule_learner_instance = RuleLearner()
    return _rule_learner_instance
