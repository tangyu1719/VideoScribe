#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析wiki节点挂载失败的原因
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

def test_wiki_node_properties(token, wiki_node_token):
    """测试wiki节点属性"""
    print(f"\n=== 测试wiki节点属性: {wiki_node_token} ===")
    
    # 测试1：尝试作为folder_token使用
    print("\n1. 测试作为folder_token创建文档...")
    create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    create_data = {
        "title": f"测试文档 - folder_token - {int(time.time())}",
        "folder_token": wiki_node_token
    }
    
    create_response = requests.post(create_url, headers=headers, json=create_data)
    create_result = create_response.json()
    
    print(f"响应: {json.dumps(create_result, ensure_ascii=False, indent=2)}")
    
    if create_result.get("code") == 0:
        print("✓ 成功！wiki节点可以作为folder_token使用")
        doc_token = create_result.get("data", {}).get("document_token")
        print(f"  Document Token: {doc_token}")
        print(f"  文档链接: https://www.feishu.cn/docx/{doc_token}")
        return doc_token
    else:
        print(f"✗ 失败: {create_result.get('msg')}")
    
    # 测试2：尝试使用wiki API获取节点信息
    print("\n2. 测试使用wiki API获取节点信息...")
    
    # 尝试不同的API端点
    test_endpoints = [
        f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{wiki_node_token}",
        f"https://open.feishu.cn/open-apis/wiki/v2/nodes/{wiki_node_token}",
        f"https://open.feishu.cn/open-apis/wiki/v1/spaces/{wiki_node_token}"
    ]
    
    for endpoint in test_endpoints:
        print(f"\n尝试端点: {endpoint}")
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 测试3：检查应用权限
    print("\n3. 检查应用权限...")
    permission_url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    permission_response = requests.post(permission_url, headers={"Content-Type": "application/json"}, json={
        "app_id": "cli_a9b7cc9aba389bc4",
        "app_secret": "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    })
    permission_result = permission_response.json()
    print(f"App Access Token响应: {json.dumps(permission_result, ensure_ascii=False, indent=2)}")
    
    # 测试4：分析节点token格式
    print("\n4. 分析节点token格式...")
    print(f"Token: {wiki_node_token}")
    print(f"长度: {len(wiki_node_token)}")
    print(f"字符集: {set(wiki_node_token)}")
    print(f"是否纯数字: {wiki_node_token.isdigit()}")
    print(f"是否字母数字混合: {wiki_node_token.isalnum()}")
    
    # 测试5：尝试解析URL结构
    print("\n5. 解析URL结构...")
    wiki_url = f"https://dvnrviz26l5.feishu.cn/wiki/{wiki_node_token}"
    print(f"完整URL: {wiki_url}")
    print(f"域名: dvnrviz26l5.feishu.cn")
    print(f"路径: /wiki/{wiki_node_token}")
    
    # 测试6：尝试使用MCP list-docs工具
    print("\n6. 测试MCP list-docs工具...")
    mcp_url = "https://mcp.feishu.cn/mcp"
    mcp_headers = {
        "Content-Type": "application/json",
        "X-Lark-MCP-TAT": token,
        "X-Lark-MCP-Allowed-Tools": "list-docs"
    }
    
    mcp_data = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {
            "name": "list-docs",
            "arguments": {
                "my_library": True
            }
        }
    }
    
    mcp_response = requests.post(mcp_url, headers=mcp_headers, json=mcp_data)
    mcp_result = mcp_response.json()
    print(f"响应: {json.dumps(mcp_result, ensure_ascii=False, indent=2)}")
    
    return None

def analyze_wiki_issue():
    """分析wiki节点挂载失败的原因"""
    print("=== 开始详细分析wiki节点挂载失败原因 ===")
    
    # 应用凭证
    APP_ID = "cli_a9b7cc9aba389bc4"
    APP_SECRET = "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    
    # Wiki节点信息
    wiki_node_token = "YhzqwByshiRNWKk0T1GcxFHmn6b"
    wiki_url = f"https://dvnrviz26l5.feishu.cn/wiki/{wiki_node_token}"
    
    print(f"Wiki节点: {wiki_url}")
    print(f"Node Token: {wiki_node_token}")
    
    # 获取TAT
    token = get_tenant_access_token(APP_ID, APP_SECRET)
    if not token:
        print("✗ 获取TAT失败，退出测试")
        return False
    print(f"✓ 获取TAT成功: {token[:20]}...")
    
    # 测试wiki节点属性
    doc_token = test_wiki_node_properties(token, wiki_node_token)
    
    # 综合分析
    print("\n=== 综合分析结果 ===")
    print("\n可能的原因:")
    print("1. 节点类型问题: wiki节点可能不是标准的folder_token")
    print("2. 权限问题: 应用可能没有权限在该wiki节点下创建文档")
    print("3. API限制: 某些API可能不支持wiki节点作为父节点")
    print("4. 网络问题: 可能存在网络延迟或缓存问题")
    print("5. 配置问题: 应用可能需要额外的配置")
    
    print("\n建议的解决方案:")
    print("1. 手动测试: 尝试在飞书客户端中在该wiki节点下创建文档")
    print("2. 权限检查: 确认应用有wiki:node:create权限")
    print("3. 直接使用: 使用已创建的文档，通过链接访问")
    print("4. 手动移动: 创建文档后手动移动到wiki节点")
    print("5. 联系支持: 联系飞书开发者支持获取帮助")
    
    if doc_token:
        print("\n=== 测试成功 ===")
        print(f"✓ 成功在wiki节点下创建文档！")
        print(f"  文档链接: https://www.feishu.cn/docx/{doc_token}")
        print(f"  请在飞书客户端中验证文档是否在wiki节点中: {wiki_url}")
    else:
        print("\n=== 测试失败 ===")
        print("✗ 无法在wiki节点下创建文档")
    
    print("\n=== 分析完成 ===")

if __name__ == "__main__":
    analyze_wiki_issue()
