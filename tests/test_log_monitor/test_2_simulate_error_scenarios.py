#!/usr/bin/env python3
"""
测试用例 2: 模拟错误场景
创建各种错误场景，验证 Agent 分析能力
"""
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.log_monitor import get_log_monitor_agent
from logging_system import Logger

logger = Logger("TestErrorScenarios")

# 测试场景数据
TEST_SCENARIOS = [
    {
        'name': 'API 密钥过期',
        'error_log': '[ERROR] API request failed: 401 Unauthorized - API key expired. Please update your API credentials.',
        'module': 'video_downloader',
        'expected_type': '配置',
        'expected_severity': 'high',
        'expected_auto_fix': True
    },
    {
        'name': '网络超时',
        'error_log': '[ERROR] Request timeout: Connection timed out after 30 seconds. Host: api.example.com',
        'module': 'web_api',
        'expected_type': '网络',
        'expected_severity': 'medium',
        'expected_auto_fix': True
    },
    {
        'name': '数据库连接失败',
        'error_log': '[ERROR] MySQL connection failed: Can\'t connect to MySQL server on \'localhost\' (10061)',
        'module': 'db',
        'expected_type': '配置',
        'expected_severity': 'critical',
        'expected_auto_fix': True
    },
    {
        'name': '文件不存在',
        'error_log': '[ERROR] FileNotFoundError: [Errno 2] No such file or directory: \'/path/to/file.txt\'',
        'module': 'document_processor',
        'expected_type': '资源',
        'expected_severity': 'high',
        'expected_auto_fix': False
    },
    {
        'name': '内存不足',
        'error_log': '[CRITICAL] Out of memory: Unable to allocate 512MB for tensor operation. Current usage: 95%',
        'module': 'ai_model',
        'expected_type': '资源',
        'expected_severity': 'critical',
        'expected_auto_fix': False
    },
    {
        'name': '权限被拒绝',
        'error_log': '[ERROR] Permission denied: Access denied to resource /admin/config. Required role: admin',
        'module': 'auth',
        'expected_type': '配置',
        'expected_severity': 'high',
        'expected_auto_fix': False
    },
    {
        'name': '服务器内部错误',
        'error_log': '[ERROR] HTTP 500 Internal Server Error: Unexpected error occurred while processing request',
        'module': 'web_api',
        'expected_type': '网络',
        'expected_severity': 'high',
        'expected_auto_fix': True
    },
    {
        'name': '连接被拒绝',
        'error_log': '[ERROR] Connection refused: Cannot connect to service at http://localhost:8080. Service may not be running.',
        'module': 'service_client',
        'expected_type': '网络',
        'expected_severity': 'high',
        'expected_auto_fix': True
    }
]

async def test_scenario(scenario: dict, agent):
    """测试单个场景"""
    logger.info(f"\n测试场景：{scenario['name']}")
    logger.info("-" * 60)
    
    try:
        # 调用 Agent 分析
        result = await agent.analyze_error(
            error_log=scenario['error_log'],
            timestamp=datetime.now(),
            module=scenario['module'],
            context={'test': True},
            trigger_type='test'
        )
        
        if result:
            # 验证结果
            passed = True
            issues = []
            
            # 检查错误类型
            if result.error_type != scenario['expected_type']:
                passed = False
                issues.append(f"错误类型不匹配：期望 {scenario['expected_type']}, 实际 {result.error_type}")
            
            # 检查严重程度
            if result.severity != scenario['expected_severity']:
                passed = False
                issues.append(f"严重程度不匹配：期望 {scenario['expected_severity']}, 实际 {result.severity}")
            
            # 检查自动修复
            if result.auto_fixable != scenario['expected_auto_fix']:
                passed = False
                issues.append(f"自动修复不匹配：期望 {scenario['expected_auto_fix']}, 实际 {result.auto_fixable}")
            
            # 输出结果
            if passed:
                logger.info(f"✅ 测试通过")
            else:
                logger.warning(f"❌ 测试失败")
                for issue in issues:
                    logger.warning(f"  - {issue}")
            
            # 输出分析结果
            logger.info(f"  错误类型：{result.error_type}")
            logger.info(f"  严重程度：{result.severity}")
            logger.info(f"  自动修复：{result.auto_fixable}")
            logger.info(f"  置信度：{result.confidence_score:.2f}")
            
            return passed
            
        else:
            logger.error("❌ Agent 返回空结果")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试异常：{e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    logger.info("="*60)
    logger.info("测试用例 2: 模拟错误场景")
    logger.info("="*60)
    
    # 初始化 Agent
    logger.info("初始化日志监控 Agent...")
    agent = get_log_monitor_agent()
    
    # 运行测试
    results = []
    for scenario in TEST_SCENARIOS:
        passed = await test_scenario(scenario, agent)
        results.append({
            'name': scenario['name'],
            'passed': passed
        })
    
    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("测试结果汇总")
    logger.info("="*60)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    logger.info(f"通过：{passed_count}/{total_count}")
    logger.info(f"成功率：{passed_count/total_count*100:.1f}%")
    
    for result in results:
        status = "✅" if result['passed'] else "❌"
        logger.info(f"{status} {result['name']}")
    
    return passed_count == total_count

def main():
    """主函数"""
    try:
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(run_all_tests())
        
        loop.close()
        
        if success:
            logger.info("\n🎉 所有测试通过！")
        else:
            logger.warning("\n⚠️ 部分测试失败")
        
    except Exception as e:
        logger.error(f"测试失败：{e}", exc_info=True)

if __name__ == "__main__":
    main()
