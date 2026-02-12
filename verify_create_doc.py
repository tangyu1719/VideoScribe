#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证create-doc工具的父节点和返回链接
"""

import requests
import json
import time

def get_tenant_access_token(app_id, app_secret):
    """获取Tenant Access Token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        print(f"获取TAT失败: {result}")
        return None

def verify_create_doc(token, parent_node, title, content):
    """验证create-doc工具"""
    mcp_url = "https://mcp.feishu.cn/mcp"
    headers = {
        "Content-Type": "application/json",
        "X-Lark-MCP-TAT": token,
        "X-Lark-MCP-Allowed-Tools": "create-doc"
    }
    
    request_body = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {
            "name": "create-doc",
            "arguments": {
                "parent_node": parent_node,
                "title": title,
                "content": content
            }
        }
    }
    
    print(f"\n=== 验证create-doc工具 ===")
    print(f"父节点: {parent_node}")
    print(f"标题: {title}")
    
    response = requests.post(mcp_url, headers=headers, json=request_body)
    result = response.json()
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if "error" in result:
        print(f"\n❌ 失败: {result['error']}")
        return None
    else:
        print(f"\n✅ 成功")
        
        # 解析结果
        content = result.get('result', {}).get('content', [])
        doc_info = None
        for item in content:
            if item.get('type') == 'text':
                try:
                    doc_info = json.loads(item.get('text', '{}'))
                    print(f"\n文档信息:")
                    print(f"  doc_id: {doc_info.get('doc_id')}")
                    print(f"  doc_url: {doc_info.get('doc_url')}")
                    print(f"  message: {doc_info.get('message')}")
                    print(f"  log_id: {doc_info.get('log_id')}")
                    
                    # 分析链接
                    doc_url = doc_info.get('doc_url')
                    if doc_url:
                        print(f"\n链接分析:")
                        print(f"  链接类型: {'docx链接' if 'docx' in doc_url else '其他链接'}")
                        print(f"  是否包含wiki: {'wiki' in doc_url}")
                        print(f"  是否包含parent_node: {parent_node in doc_url}")
                except Exception as e:
                    print(f"  解析失败: {e}")
                    print(f"  原始文本: {item.get('text')}")
        
        return doc_info

def main():
    """主函数"""
    print("=== 开始验证create-doc工具 ===")
    
    # 应用凭证
    APP_ID = "cli_a9b7cc9aba389bc4"
    APP_SECRET = "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    
    # Wiki节点信息
    wiki_node = "YhzqwByshiRNWKk0T1GcxFHmn6b"
    wiki_url = f"https://dvnrviz26l5.feishu.cn/wiki/{wiki_node}"
    
    print(f"Wiki节点: {wiki_url}")
    print(f"Parent Node: {wiki_node}")
    
    # 获取TAT
    token = get_tenant_access_token(APP_ID, APP_SECRET)
    if not token:
        print("❌ 获取TAT失败，退出测试")
        return
    print(f"✅ 获取TAT成功")
    
    # 验证create-doc
    test_title = f"验证文档 - {int(time.time())}"
    test_content = f"# 验证文档\n\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n## 验证信息\n- **父节点**: {wiki_node}\n- **测试目的**: 验证create-doc工具的父节点和返回链接\n- **测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    doc_info = verify_create_doc(token, wiki_node, test_title, test_content)
    
    if doc_info:
        print("\n=== 验证结果 ===")
        print(f"✅ 文档创建成功")
        print(f"📄 文档链接: {doc_info.get('doc_url')}")
        print(f"🆔 文档ID: {doc_info.get('doc_id')}")
        
        # 验证文档是否可访问
        doc_url = doc_info.get('doc_url')
        if doc_url:
            print(f"\n🔗 请验证:")
            print(f"1. 直接访问文档: {doc_url}")
            print(f"2. 查看wiki节点: {wiki_url}")
            print(f"3. 确认文档是否存在于目标节点")
    else:
        print("\n❌ 验证失败")
    
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    main()
