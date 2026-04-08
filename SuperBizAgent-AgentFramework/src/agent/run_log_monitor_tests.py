#!/usr/bin/env python3
"""
运行所有日志监控 Agent 测试
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from logging_system import Logger

logger = Logger("TestRunner")

def run_test(test_file: str, test_name: str) -> bool:
    """运行单个测试"""
    logger.info("="*60)
    logger.info(f"运行测试：{test_name}")
    logger.info(f"文件：{test_file}")
    logger.info("="*60)
    
    try:
        result = subprocess.run(
            ['python', test_file],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 输出日志
        if result.stdout:
            logger.info("输出:\n" + result.stdout)
        
        if result.stderr:
            logger.error("错误:\n" + result.stderr)
        
        success = result.returncode == 0
        
        if success:
            logger.info(f"✅ {test_name} 通过")
        else:
            logger.error(f"❌ {test_name} 失败 (返回码：{result.returncode})")
        
        return success
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {test_name} 超时 (>5 分钟)")
        return False
    except Exception as e:
        logger.error(f"❌ {test_name} 异常：{e}")
        return False

def main():
    """主函数"""
    logger.info("="*60)
    logger.info("日志监控 Agent 测试套件")
    logger.info(f"开始时间：{datetime.now().isoformat()}")
    logger.info("="*60)
    
    # 测试列表
    tests = [
        {
            'file': 'tests/test_log_monitor/test_1_analyze_history_bugs.py',
            'name': '测试 1: 分析历史日志 BUG'
        },
        {
            'file': 'tests/test_log_monitor/test_2_simulate_error_scenarios.py',
            'name': '测试 2: 模拟错误场景'
        }
    ]
    
    # 运行测试
    results = []
    for test in tests:
        test_file = Path(__file__).parent / test['file']
        
        if not test_file.exists():
            logger.warning(f"测试文件不存在：{test_file}")
            results.append({
                'name': test['name'],
                'passed': False,
                'error': '文件不存在'
            })
            continue
        
        passed = run_test(str(test_file), test['name'])
        results.append({
            'name': test['name'],
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
        
        if 'error' in result:
            logger.info(f"   错误：{result['error']}")
    
    # 输出报告
    report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_reports/test_summary_{report_time}.md"
    
    Path("test_reports").mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 日志监控 Agent 测试报告\n\n")
        f.write(f"测试时间：{datetime.now().isoformat()}\n\n")
        
        f.write("## 测试结果\n\n")
        f.write(f"通过：{passed_count}/{total_count}\n")
        f.write(f"成功率：{passed_count/total_count*100:.1f}%\n\n")
        
        f.write("### 详细结果\n\n")
        for result in results:
            status = "✅" if result['passed'] else "❌"
            f.write(f"{status} {result['name']}\n")
            if 'error' in result:
                f.write(f"   错误：{result['error']}\n")
        f.write("\n")
    
    logger.info(f"\n测试报告已保存：{report_file}")
    
    # 返回码
    sys.exit(0 if passed_count == total_count else 1)

if __name__ == "__main__":
    main()
