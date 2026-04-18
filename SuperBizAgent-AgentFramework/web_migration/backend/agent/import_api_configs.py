#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速导入 API 配置到数据库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
from datetime import datetime

# 导入数据库模块
try:
    import db
    DB_AVAILABLE = True
except ImportError:
    print("数据库模块不可用")
    DB_AVAILABLE = False
    sys.exit(1)

# API 配置
API_CONFIGS = [
    {
        'name': 'GLM-4.7',
        'endpoint_id': 'ep-20260413220727-84n92',
    },
    {
        'name': 'Doubao-Seed-2.0-pro',
        'endpoint_id': 'ep-20260413220538-pbfqw',
    },
]

# 从现有配置中获取 API Key 和 Base URL
print("正在从数据库加载现有配置...")
try:
    results = db.execute_query(
        "SELECT * FROM llm_configs WHERE id='default' OR enabled=TRUE LIMIT 1"
    )
    
    if not results:
        print("未找到现有配置，请先在界面中配置主接入点")
        sys.exit(1)
    
    main_config = results[0]
    api_key = main_config['api_key']
    # 防止把 /responses 当成 base_url 写入备选配置
    base_url = (main_config['base_url'] or '').rstrip('/')
    if base_url.endswith('/responses'):
        base_url = base_url[:-len('/responses')].rstrip('/')
    model = main_config['model']
    
    # Windows 控制台可能是 GBK，避免输出不可编码字符（如 ✓）
    print("OK 主接入点配置:")
    print(f"  API Key: {api_key[:20]}...")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    
except Exception as e:
    print(f"加载配置失败：{e}")
    sys.exit(1)

# 获取现有备份配置
try:
    import json
    backup_configs = json.loads(main_config['backup_configs']) if main_config['backup_configs'] else []
    print(f"OK 现有备选配置数量：{len(backup_configs)}")
except Exception as e:
    print(f"解析备份配置失败：{e}")
    backup_configs = []

# 添加新的 API 配置
print("\n正在添加新的 API 配置...")
for config in API_CONFIGS:
    new_backup = {
        'id': str(uuid.uuid4()),
        'name': config['name'],
        'api_key': api_key,  # 使用相同的 API Key
        'base_url': base_url,  # 使用相同的 Base URL
        'model': config['name'],  # 按配置名写入，便于区分展示
        'endpoint_id': config['endpoint_id'],
        'created_at': datetime.now().isoformat()
    }
    
    # 检查是否已存在
    exists = any(b['endpoint_id'] == config['endpoint_id'] for b in backup_configs)
    if exists:
        print(f"  WARN {config['name']} 已存在，跳过")
    else:
        backup_configs.append(new_backup)
        print(f"  OK 添加 {config['name']} ({config['endpoint_id']})")

# 更新数据库
print("\n正在保存配置到数据库...")
try:
    db.execute_update(
        """UPDATE llm_configs 
           SET backup_configs=%s, updated_at=NOW() 
           WHERE id=%s OR enabled=TRUE""",
        (json.dumps(backup_configs, ensure_ascii=False), 'default')
    )
    print("OK 配置已保存到数据库")
    print(f"OK 总备选配置数量：{len(backup_configs)}")
    
except Exception as e:
    print(f"保存失败：{e}")
    sys.exit(1)

print("\n完成！请重启程序或重新打开 API 配置界面查看新配置。")
