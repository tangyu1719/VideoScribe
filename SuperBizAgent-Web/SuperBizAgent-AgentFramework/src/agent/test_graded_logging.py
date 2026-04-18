#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分级日志系统测试脚本
测试三级日志功能：完整原型日志、接口粒度日志、操作粒度日志
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_raw_logs():
    """测试完整原型日志"""
    print_section("测试 1: 完整原型日志查询")
    
    # 查询所有原始日志
    response = requests.get(f"{BASE_URL}/api/logs/raw", params={
        "page": 1,
        "pageSize": 10
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 查询成功，共 {data['data']['total']} 条记录")
        print(f"✓ 返回 {len(data['data']['items'])} 条日志")
        
        if data['data']['items']:
            print("\n最近 3 条原始日志:")
            for item in data['data']['items'][:3]:
                print(f"  - {item['method']} {item['path']} "
                      f"[{item['status_code']}] "
                      f"{item['duration_ms']:.2f}ms")
    else:
        print(f"✗ 查询失败：{response.text}")


def test_api_stats():
    """测试接口粒度统计"""
    print_section("测试 2: 接口粒度统计查询")
    
    # 查询接口统计
    response = requests.get(f"{BASE_URL}/api/logs/api-stats", params={
        "sortBy": "count"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 查询成功，共 {data['data']['total']} 个接口")
        
        if data['data']['items']:
            print("\n接口调用统计 Top 5:")
            for item in data['data']['items'][:5]:
                print(f"  - {item['method']} {item['api_path']}")
                print(f"    调用次数：{item['count']}, "
                      f"平均耗时：{item['avg_duration_ms']:.2f}ms, "
                      f"错误率：{item['error_rate']}%")
    else:
        print(f"✗ 查询失败：{response.text}")


def test_operation_logs():
    """测试操作粒度日志"""
    print_section("测试 3: 操作粒度日志查询")
    
    # 查询操作日志
    response = requests.get(f"{BASE_URL}/api/logs/operations", params={
        "page": 1,
        "pageSize": 10
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 查询成功，共 {data['data']['total']} 条记录")
        print(f"✓ 返回 {len(data['data']['items'])} 条日志")
        
        if data['data']['items']:
            print("\n最近 3 条操作日志:")
            for item in data['data']['items'][:3]:
                print(f"  - {item['operation_type']} "
                      f"[{item['status']}] "
                      f"{item['duration_ms']:.2f}ms")
                if item.get('error_message'):
                    print(f"    错误：{item['error_message']}")
    else:
        print(f"✗ 查询失败：{response.text}")


def test_logs_dashboard():
    """测试日志仪表盘"""
    print_section("测试 4: 日志仪表盘查询")
    
    # 查询仪表盘数据
    response = requests.get(f"{BASE_URL}/api/logs/dashboard")
    
    if response.status_code == 200:
        data = response.json()
        print("✓ 仪表盘数据查询成功")
        
        dashboard = data['data']
        
        # 系统日志统计
        if 'systemLogs' in dashboard:
            print(f"\n系统日志统计:")
            for level, count in dashboard['systemLogs']['byLevel'].items():
                print(f"  - {level}: {count} 条")
        
        # API 调用统计
        if 'apiCalls' in dashboard:
            api = dashboard['apiCalls']
            print(f"\n最近 1 小时 API 调用:")
            print(f"  - 总调用：{api['total_calls']} 次")
            print(f"  - 平均耗时：{api['avg_duration_ms']:.2f}ms")
            print(f"  - 成功：{api['success_count']} 次，失败：{api['error_count']} 次")
        
        # 操作统计
        if 'operations' in dashboard:
            print(f"\n最近 1 小时操作统计:")
            for op_type, stats in dashboard['operations'].items():
                print(f"  - {op_type}: {stats['count']} 次，"
                      f"平均 {stats['avg_duration_ms']:.2f}ms")
        
        # 慢接口
        if 'slowApis' in dashboard:
            print(f"\n慢接口 Top 10:")
            for i, api in enumerate(dashboard['slowApis'][:5], 1):
                print(f"  {i}. {api['method']} {api['api_path']} "
                      f"- {api['avg_duration_ms']:.2f}ms "
                      f"({api['count']} 次调用)")
    else:
        print(f"✗ 查询失败：{response.text}")


def test_filtered_logs():
    """测试日志筛选功能"""
    print_section("测试 5: 日志筛选功能")
    
    # 按方法筛选
    response = requests.get(f"{BASE_URL}/api/logs/raw", params={
        "method": "POST",
        "page": 1,
        "pageSize": 5
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ POST 请求日志：{data['data']['total']} 条")
    
    # 按路径筛选
    response = requests.get(f"{BASE_URL}/api/logs/raw", params={
        "path": "/api/chat",
        "page": 1,
        "pageSize": 5
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ /api/chat 相关日志：{data['data']['total']} 条")
    
    # 按操作类型筛选
    response = requests.get(f"{BASE_URL}/api/logs/operations", params={
        "operationType": "chat_send",
        "page": 1,
        "pageSize": 5
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ chat_send 操作日志：{data['data']['total']} 条")


def simulate_api_calls():
    """模拟一些 API 调用以生成日志数据"""
    print_section("模拟 API 调用以生成日志数据")
    
    print("正在生成测试数据...")
    
    # 调用几个 API 以生成日志
    endpoints = [
        ("GET", "/api/logs"),
        ("GET", "/api/logs/stats"),
        ("GET", "/api/configs/llm"),
    ]
    
    for method, path in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{path}", timeout=5)
            print(f"  ✓ {method} {path} - {response.status_code}")
        except Exception as e:
            print(f"  ✗ {method} {path} - {str(e)}")
        time.sleep(0.5)
    
    print("\n测试数据生成完成")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  分级日志系统测试")
    print(f"  开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 先模拟一些调用
    simulate_api_calls()
    
    # 等待几秒让日志写入数据库
    time.sleep(2)
    
    # 运行测试
    test_raw_logs()
    test_api_stats()
    test_operation_logs()
    test_logs_dashboard()
    test_filtered_logs()
    
    print("\n" + "="*60)
    print("  所有测试完成")
    print(f"  结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n✗ 测试失败：{e}")
        print("\n请确保:")
        print("  1. Web API 服务已启动 (python web_api.py)")
        print("  2. 数据库表已创建 (运行 graded_logging_schema.sql)")
        print(f"  3. API 地址正确 (当前：{BASE_URL})")
