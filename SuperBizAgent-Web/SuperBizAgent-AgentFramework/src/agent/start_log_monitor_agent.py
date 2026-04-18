#!/usr/bin/env python3
"""
日志监控 Agent 启动脚本
初始化并启动 Agent 服务
"""
import sys
import asyncio
import signal
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.log_monitor import get_log_monitor_agent, get_error_detector
from logging_system import Logger

logger = Logger("LogMonitorStarter")

# 全局变量
agent = None
detector = None
running = True

def signal_handler(sig, frame):
    """信号处理"""
    global running
    logger.info("收到停止信号，正在关闭...")
    running = False

def init_agent():
    """初始化 Agent"""
    global agent, detector
    
    logger.info("="*60)
    logger.info("日志监控 Agent 启动")
    logger.info("="*60)
    
    try:
        # 初始化 Agent
        logger.info("初始化日志监控 Agent...")
        agent = get_log_monitor_agent()
        logger.info("✓ Agent 初始化完成")
        
        # 初始化错误检测器
        logger.info("初始化错误检测器...")
        detector = get_error_detector()
        logger.info("✓ 错误检测器初始化完成")
        
        # 添加错误回调
        logger.info("注册错误回调...")
        
        def on_error_detected(error_record):
            """错误检测回调"""
            logger.info(f"检测到错误：{error_record.module} - {error_record.error_log[:50]}...")
            
            # 异步调用 Agent 分析
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    agent.analyze_error(
                        error_log=error_record.error_log,
                        timestamp=error_record.timestamp,
                        module=error_record.module,
                        context=error_record.context,
                        trigger_type='log_alert'
                    )
                )
                
                if result:
                    logger.info(f"分析完成：{result.error_type} - {result.severity}")
                else:
                    logger.warning("分析失败")
                
            except Exception as e:
                logger.error(f"分析错误失败：{e}")
            finally:
                loop.close()
        
        detector.add_error_callback(on_error_detected)
        logger.info("✓ 错误回调注册完成")
        
        return True
        
    except Exception as e:
        logger.error(f"初始化失败：{e}", exc_info=True)
        return False

def start_listening():
    """开始监听"""
    logger.info("="*60)
    logger.info("开始监听日志数据库")
    logger.info("按 Ctrl+C 停止")
    logger.info("="*60)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 开始监听
    detector.start_listening(db_poll_interval=5)
    
    # 主循环
    while running:
        try:
            import time
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号")
            break
    
    # 关闭
    shutdown()

def shutdown():
    """关闭服务"""
    logger.info("关闭日志监控 Agent...")
    
    if agent:
        agent.shutdown()
    
    logger.info("✓ Agent 已关闭")
    logger.info("="*60)
    logger.info("服务已停止")
    logger.info("="*60)

def main():
    """主函数"""
    logger.info(f"启动时间：{datetime.now().isoformat()}")
    
    # 初始化
    if not init_agent():
        logger.error("初始化失败，退出")
        return
    
    # 开始监听
    start_listening()

if __name__ == "__main__":
    main()
