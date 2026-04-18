#!/usr/bin/env python3
"""
检查数据库中的LLM配置
"""
import sys
sys.path.insert(0, 'F:\\java\\AIOPS\\SuperBizAgent-release-2026-01-02\\demo_wendanghua')

import db

def check_llm_configs():
    """检查LLM配置"""
    print("=" * 60)
    print("检查数据库中的LLM配置")
    print("=" * 60)
    
    try:
        results = db.execute_query("SELECT * FROM llm_configs")
        
        if results:
            print(f"\n找到 {len(results)} 个LLM配置:\n")
            for row in results:
                print(f"ID: {row.get('id')}")
                print(f"名称: {row.get('name')}")
                print(f"API Key: {'*' * 10 if row.get('api_key') else '未设置'}")
                print(f"Base URL: {row.get('base_url')}")
                print(f"Model: {row.get('model')}")
                print(f"Endpoint ID: {row.get('endpoint_id')}")
                print(f"Enabled: {row.get('enabled')}")
                print("-" * 60)
        else:
            print("\n数据库中没有LLM配置")
            print("需要添加配置到 llm_configs 表")
    
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_llm_configs()
