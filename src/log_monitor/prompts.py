"""
日志监控 Agent 提示词模板
"""
from typing import List, Dict

# 错误分析 Prompt 模板
ERROR_ANALYSIS_PROMPT = """# 角色
你是一位资深的系统运维专家，负责分析系统日志中的错误并提供修复方案。

# 任务
分析以下日志错误，完成以下任务：
1. 识别错误的根本原因
2. 判断错误类型（配置问题/网络问题/代码问题/资源问题）
3. 生成详细的错误报告
4. 提供可执行的修复建议
5. 评估自动修复的可行性

# 输入信息
- 错误日志：{error_log}
- 错误发生时间：{timestamp}
- 错误发生模块：{module}
- 相关上下文：{context}
- 历史相似错误：{similar_errors}

# 成功输出规则
{success_rules}

# 输出格式
请严格按照以下 JSON 格式输出，不要包含任何其他内容：
```json
{{
  "error_id": "{error_id}",
  "error_type": "配置 | 网络 | 代码 | 资源 | 其他",
  "severity": "critical|high|medium|low",
  "root_cause": "详细描述根本原因",
  "analysis": "详细的分析过程",
  "auto_fixable": true/false,
  "fix_suggestions": [
    {{
      "step": 1,
      "action": "具体操作",
      "command": "可执行的命令或配置修改",
      "expected_result": "预期结果"
    }}
  ],
  "retry_recommended": true/false,
  "retry_config": {{
    "max_retries": 3,
    "delay_seconds": 10,
    "backoff_multiplier": 2
  }},
  "confidence_score": 0.0-1.0
}}
```

# 约束条件
1. 只分析日志中明确提供的信息，不要臆测
2. 修复建议必须具体、可执行
3. 对于配置问题，提供明确的配置修改步骤
4. 对于代码问题，明确指出问题位置，但不修改代码
5. 评估自动修复风险，高风险操作需要人工确认
6. 必须输出有效的 JSON 格式
"""

# 自学习规则 Prompt 模板
RULE_LEARNING_PROMPT = """# 任务
从历史错误处理记录中学习，完善成功输出规则。

# 输入
- 历史成功处理案例：{success_cases}
- 历史失败处理案例：{failure_cases}
- 当前规则集：{current_rules}

# 输出
请分析历史案例，更新成功输出规则：

## 分析结果
1. 成功案例共同特征：
   - {success_patterns}

2. 失败案例教训：
   - {failure_lessons}

3. 规则优化建议：
   - 新增规则：{new_rules}
   - 修正规则：{modified_rules}
   - 删除规则：{deleted_rules}

## 更新后的规则
请按照以下 JSON 格式输出更新后的规则：
```json
{{
  "rules": [
    {{
      "rule_id": "规则唯一标识",
      "pattern": "错误模式匹配正则表达式",
      "diagnosis": "诊断方法描述",
      "solution": "标准解决方案",
      "auto_fix": true/false,
      "confidence": 0.0-1.0,
      "learned_from": ["案例 ID 列表"],
      "action": "add|update|delete"
    }}
  ]
}}
```

# 规则质量要求
1. 规则必须有明确的错误模式匹配
2. 诊断方法必须具体可操作
3. 解决方案必须经过验证
4. 置信度低于 0.6 的规则不建议保留
5. 自动修复规则必须经过至少 3 次成功验证
"""

# 成功输出规则模板（初始版本）
INITIAL_SUCCESS_RULES = """
## 当前成功输出规则

### 规则 1: 网络超时处理
- **模式**: `.*timeout.*`
- **诊断**: 检查是否为网络超时或服务器响应慢
- **解决方案**: 
  1. 增加超时时间配置
  2. 执行重试机制（最多 3 次，指数退避）
  3. 检查网络连接状态
- **自动修复**: 是
- **置信度**: 0.85

### 规则 2: 连接拒绝处理
- **模式**: `.*connection refused.*`
- **诊断**: 目标服务未启动或网络不通
- **解决方案**:
  1. 检查目标服务状态
  2. 验证网络连接
  3. 检查防火墙配置
- **自动修复**: 是
- **置信度**: 0.90

### 规则 3: API 密钥过期处理
- **模式**: `.*API.*key.*expired.*|.*401.*unauthorized.*`
- **诊断**: API 密钥过期或无效
- **解决方案**:
  1. 从备用配置切换 API 密钥
  2. 更新认证信息
  3. 联系管理员获取新密钥
- **自动修复**: 是
- **置信度**: 0.95

### 规则 4: 权限不足处理
- **模式**: `.*403.*forbidden.*|.*permission denied.*`
- **诊断**: 权限配置不足
- **解决方案**:
  1. 检查当前权限配置
  2. 申请相应权限
  3. 联系管理员授权
- **自动修复**: 否（需要人工确认）
- **置信度**: 0.85

### 规则 5: 资源不存在处理
- **模式**: `.*404.*not found.*|.*file.*not found.*`
- **诊断**: 请求的资源或文件不存在
- **解决方案**:
  1. 检查 URL 或文件路径
  2. 验证资源是否存在
  3. 创建缺失的资源（如适用）
- **自动修复**: 否
- **置信度**: 0.90

### 规则 6: 服务器错误处理
- **模式**: `.*500.*internal server error.*|.*502.*bad gateway.*|.*503.*service unavailable.*`
- **诊断**: 服务器端错误或不可用
- **解决方案**:
  1. 稍后重试（最多 3 次）
  2. 检查服务状态
  3. 联系服务提供方
- **自动修复**: 是
- **置信度**: 0.80

### 规则 7: 资源不足处理
- **模式**: `.*out of memory.*|.*disk space.*`
- **诊断**: 系统资源不足
- **解决方案**:
  1. 清理临时文件
  2. 释放内存
  3. 扩容资源
- **自动修复**: 部分（清理操作可自动）
- **置信度**: 0.90

### 规则 8: 数据库连接问题
- **模式**: `.*database.*connection.*|.*MySQL.*connection.*`
- **诊断**: 数据库连接失败
- **解决方案**:
  1. 检查数据库服务状态
  2. 验证连接配置
  3. 重试连接（最多 3 次）
- **自动修复**: 是
- **置信度**: 0.85

### 规则 9: 请求频率限制
- **模式**: `.*rate limit.*|.*too many requests.*`
- **诊断**: 请求频率超过限制
- **解决方案**:
  1. 降低请求频率
  2. 等待后重试
  3. 申请提高限额
- **自动修复**: 是
- **置信度**: 0.90
"""

def format_error_analysis_prompt(
    error_log: str,
    timestamp: str,
    module: str,
    context: Dict = None,
    similar_errors: List[str] = None,
    success_rules: str = None,
    error_id: str = None
) -> str:
    """
    格式化错误分析 Prompt
    
    Args:
        error_log: 错误日志
        timestamp: 时间戳
        module: 模块名称
        context: 上下文信息
        similar_errors: 历史相似错误
        success_rules: 成功输出规则
        error_id: 错误 ID
    
    Returns:
        格式化后的 Prompt
    """
    import uuid
    
    return ERROR_ANALYSIS_PROMPT.format(
        error_log=error_log,
        timestamp=timestamp,
        module=module,
        context=str(context) if context else "无",
        similar_errors='\n'.join(similar_errors) if similar_errors else "无",
        success_rules=success_rules or INITIAL_SUCCESS_RULES,
        error_id=error_id or str(uuid.uuid4())
    )

def format_rule_learning_prompt(
    success_cases: List[Dict],
    failure_cases: List[Dict],
    current_rules: List[Dict]
) -> str:
    """
    格式化规则学习 Prompt
    
    Args:
        success_cases: 成功案例列表
        failure_cases: 失败案例列表
        current_rules: 当前规则列表
    
    Returns:
        格式化后的 Prompt
    """
    return RULE_LEARNING_PROMPT.format(
        success_cases=str(success_cases),
        failure_cases=str(failure_cases),
        current_rules=str(current_rules)
    )
