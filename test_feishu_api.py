#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用飞书官方API创建文档
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

def create_document_api(token, title, folder_token=None):
    """使用飞书API创建文档"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "title": title
    }
    
    if folder_token:
        data["folder_token"] = folder_token
    
    print(f"\n调用创建文档API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") != 0:
        print(f"\n❌ 创建文档失败: {result.get('msg')}")
        return None
    
    doc_token = result.get("data", {}).get("document_token")
    if not doc_token:
        print("\n❌ 未返回document_token")
        return None
    
    print(f"\n✅ 创建文档成功！")
    print(f"  Document Token: {doc_token}")
    print(f"  文档链接: https://www.feishu.cn/docx/{doc_token}")
    
    return doc_token

def update_document_content(token, doc_token, content):
    """更新文档内容"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "requests": [
            {
                "insert_text": {
                    "text": content,
                    "end_of_segment": True
                }
            }
        ]
    }
    
    print(f"\n更新文档内容...")
    print(f"URL: {url}")
    
    response = requests.patch(url, headers=headers, json=data)
    result = response.json()
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") != 0:
        print(f"\n❌ 更新内容失败: {result.get('msg')}")
        return False
    
    print("\n✅ 更新内容成功！")
    return True

def get_wiki_spaces(token):
    """获取wiki空间列表"""
    url = "https://open.feishu.cn/open-apis/wiki/v2/spaces"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n获取wiki空间列表...")
    print(f"URL: {url}")
    
    response = requests.get(url, headers=headers)
    result = response.json()
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") != 0:
        print(f"\n❌ 获取空间列表失败: {result.get('msg')}")
        return None
    
    spaces = result.get("data", {}).get("items", [])
    print(f"\n✅ 获取到 {len(spaces)} 个空间")
    
    for i, space in enumerate(spaces):
        space_id = space.get("space_id")
        space_name = space.get("name")
        print(f"  {i+1}. {space_name} (ID: {space_id})")
    
    return spaces

def get_wiki_nodes(token, space_id):
    """获取wiki空间节点列表"""
    url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n获取wiki空间节点列表...")
    print(f"URL: {url}")
    
    response = requests.get(url, headers=headers)
    result = response.json()
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") != 0:
        print(f"\n❌ 获取节点列表失败: {result.get('msg')}")
        return None
    
    nodes = result.get("data", {}).get("items", [])
    print(f"\n✅ 获取到 {len(nodes)} 个节点")
    
    for i, node in enumerate(nodes[:5]):
        node_token = node.get("node_token")
        node_title = node.get("title")
        node_type = node.get("type")
        print(f"  {i+1}. {node_title} (Type: {node_type}, Token: {node_token})")
    
    if len(nodes) > 5:
        print(f"  ... 等 {len(nodes) - 5} 个节点")
    
    return nodes

def create_wiki_node(token, space_id, parent_token, title, node_type="document"):
    """创建wiki节点"""
    url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "parent_token": parent_token,
        "title": title,
        "type": node_type
    }
    
    print(f"\n创建wiki节点...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") != 0:
        print(f"\n❌ 创建节点失败: {result.get('msg')}")
        return None
    
    node_token = result.get("data", {}).get("node_token")
    if not node_token:
        print("\n❌ 未返回node_token")
        return None
    
    print(f"\n✅ 创建节点成功！")
    print(f"  Node Token: {node_token}")
    
    return node_token

def main():
    """主函数"""
    print("=== 开始测试飞书API ===")
    
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
    
    # 测试1：获取wiki空间列表
    print("\n=== 测试1：获取wiki空间列表 ===")
    spaces = get_wiki_spaces(token)
    
    if spaces:
        # 使用第一个空间进行测试
        test_space = spaces[0]
        space_id = test_space.get("space_id")
        space_name = test_space.get("name")
        print(f"\n选择测试空间: {space_name} (ID: {space_id})")
        
        # 测试2：获取空间节点列表
        print("\n=== 测试2：获取空间节点列表 ===")
        nodes = get_wiki_nodes(token, space_id)
        
        # 测试3：直接创建文档
        print("\n=== 测试3：直接创建文档 ===")
        test_title = f"API测试文档 - {int(time.time())}"
        test_content = f"# API测试文档\n\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n## 测试信息\n- Wiki节点: {wiki_node}\n- 测试空间: {space_name}\n- 测试目的: 直接使用API创建文档\n- 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 先创建空文档
        doc_token = create_document_api(token, test_title)
        
        if doc_token:
            # 更新文档内容
            update_success = update_document_content(token, doc_token, test_content)
            
            if update_success:
                print("\n=== 文档创建成功 ===")
                print(f"✅ 文档创建并更新成功！")
                print(f"  文档标题: {test_title}")
                print(f"  文档链接: https://www.feishu.cn/docx/{doc_token}")
            
        # 测试4：尝试在wiki节点下创建文档
        print("\n=== 测试4：尝试在wiki节点下创建文档 ===")
        wiki_title = f"Wiki测试文档 - {int(time.time())}"
        doc_token_wiki = create_document_api(token, wiki_title, wiki_node)
        
        if doc_token_wiki:
            print("\n=== 测试成功 ===")
            print(f"✅ 成功在wiki节点下创建文档！")
            print(f"  文档链接: https://www.feishu.cn/docx/{doc_token_wiki}")
        else:
            print("\n=== 测试失败 ===")
            print("❌ 无法在wiki节点下创建文档")
            
        # 测试5：创建wiki节点
        print("\n=== 测试5：创建wiki节点 ===")
        wiki_node_title = f"Wiki节点测试 - {int(time.time())}"
        new_node_token = create_wiki_node(token, space_id, wiki_node, wiki_node_title)
        
        if new_node_token:
            print("\n=== 测试成功 ===")
            print(f"✅ 成功在wiki节点下创建新节点！")
            print(f"  节点标题: {wiki_node_title}")
            print(f"  节点Token: {new_node_token}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
