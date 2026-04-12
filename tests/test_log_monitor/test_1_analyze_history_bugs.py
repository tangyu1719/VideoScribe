#!/usr/bin/env python3
"""
测试用例 1: 分析历史日志 BUG
读取历史错误日志，调用 Agent 分析，生成报错文档
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.log_monitor import get_log_monitor_agent, ErrorRecord
from db import get_db_connection
from logging_system import Logger

logger = Logger("TestHistoryBugs")

def get_history_errors(limit: int = 10):
    """从数据库获取历史错误日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(as_dict=True)
        
        sql = """
        SELECT * FROM logs 
        WHERE level IN ('ERROR', 'CRITICAL')
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"获取历史错误失败：{e}")
        return []

def analyze_error(error_log: dict, agent):
    """分析单个错误"""
    logger.info(f"分析错误：{error_log.get('message', '')[:100]}...")
    
    try:
        import asyncio
        
        # 调用 Agent 分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            agent.analyze_error(
                error_log=error_log.get('message', ''),
                timestamp=datetime.fromisoformat(error_log.get('timestamp', datetime.now().isoformat())),
                module=error_log.get('module', 'unknown'),
                context={
                    'level': error_log.get('level', ''),
                    'file': error_log.get('file', ''),
                    'line': error_log.get('line', '')
                },
                trigger_type='test'
            )
        )
        
        loop.close()
        
        return result
        
    except Exception as e:
        logger.error(f"分析失败：{e}")
        return None

def generate_error_report(error_log: dict, analysis_result, output_dir: str = "test_reports"):
    """生成错误报告"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{output_dir}/error_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 错误分析报告\n\n")
        f.write(f"生成时间：{datetime.now().isoformat()}\n\n")
        
        f.write("## 错误信息\n\n")
        f.write(f"- **错误 ID**: {error_log.get('id', 'N/A')}\n")
        f.write(f"- **时间**: {error_log.get('timestamp', 'N/A')}\n")
        f.write(f"- **模块**: {error_log.get('module', 'N/A')}\n")
        f.write(f"- **级别**: {error_log.get('level', 'N/A')}\n")
        f.write(f"- **文件**: {error_log.get('file', 'N/A')}\n")
        f.write(f"- **行号**: {error_log.get('line', 'N/A')}\n\n")
        
        f.write("## 错误日志\n\n```text\n")
        f.write(error_log.get('message', '') + "\n")
        f.write("```\n\n")
        
        if analysis_result:
            f.write("## 分析结果\n\n")
            f.write(f"- **错误类型**: {analysis_result.error_type}\n")
            f.write(f"- **严重程度**: {analysis_result.severity}\n")
            f.write(f"- **根本原因**: {analysis_result.root_cause}\n")
            f.write(f"- **置信度**: {analysis_result.confidence_score:.2f}\n\n")
            
            f.write("### 分析详情\n\n")
            f.write(analysis_result.analysis + "\n\n")
            
            f.write("### 修复建议\n\n")
            for i, suggestion in enumerate(analysis_result.fix_suggestions, 1):
                f.write(f"{i}. **{suggestion.get('action', '')}**\n")
                f.write(f"   - 操作：{suggestion.get('command', '')}\n")
                f.write(f"   - 预期结果：{suggestion.get('expected_result', '')}\n\n")
            
            f.write(f"### 自动修复：{'支持' if analysis_result.auto_fixable else '不支持'}\n\n")
            f.write(f"### 建议重试：{'是' if analysis_result.retry_recommended else '否'}\n\n")
        else:
            f.write("## 分析结果\n\n")
            f.write("分析失败，未能获取结果\n\n")
    
    logger.info(f"报告已生成：{report_file}")
    return report_file

def main():
    """主函数"""
    logger.info("="*60)
    logger.info("测试用例 1: 分析历史日志 BUG")
    logger.info("="*60)
    
    # 1. 获取历史错误
    logger.info("获取历史错误日志...")
    history_errors = get_history_errors(limit=5)
    
    if not history_errors:
        logger.warning("未找到历史错误日志")
        return
    
    logger.info(f"找到 {len(history_errors)} 条历史错误")
    
    # 2. 初始化 Agent
    logger.info("初始化日志监控 Agent...")
    agent = get_log_monitor_agent()
    
    # 3. 分析每个错误
    reports = []
    for error_log in history_errors:
        logger.info(f"分析错误：{error_log.get('id', 'N/A')}")
        
        analysis_result = analyze_error(error_log, agent)
        
        # 4. 生成报告
        report_file = generate_error_report(error_log, analysis_result)
        reports.append(report_file)
        
        logger.info(f"报告生成：{report_file}")
    
    # 5. 汇总
    logger.info("="*60)
    logger.info(f"分析完成，生成了 {len(reports)} 份报告")
    logger.info("报告位置：test_reports/")
    logger.info("="*60)

if __name__ == "__main__":
    main()
