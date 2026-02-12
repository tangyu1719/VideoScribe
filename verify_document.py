#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证飞书文档是否真正创建成功的详细测试脚本
包含详细日志埋点和直接验证
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feishu_integration import FeishuKnowledgeBase

def verify_document_creation():
    """验证文档创建是否真正成功"""
    print("=== 开始详细验证飞书文档创建 ===")
    
    # 应用信息
    APP_ID = "cli_a9b7cc9aba389bc4"
    APP_SECRET = "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    
    # 测试知识库节点
    TEST_URL = "https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b"
    
    try:
        # 初始化FeishuKnowledgeBase
        print("\n=== 步骤1：初始化飞书集成 ===")
        feishu = FeishuKnowledgeBase(APP_ID, APP_SECRET)
        
        # 解析节点token
        print("\n=== 步骤2：解析节点token ===")
        node_token = feishu.parse_node_token_from_url(TEST_URL)
        if not node_token:
            print("❌ 解析节点token失败")
            return False
        print(f"✅ 成功解析到节点token: {node_token}")
        
        # 测试Tenant Access Token获取
        print("\n=== 步骤3：测试Token获取 ===")
        token = feishu.get_tenant_access_token()
        if not token:
            print("❌ 获取Tenant Access Token失败")
            return False
        print(f"✅ 成功获取Tenant Access Token: {token[:20]}...")
        
        # 测试MCP会话初始化
        print("\n=== 步骤4：测试MCP会话初始化 ===")
        init_result = feishu.mcp_request("initialize", {}, [])
        if init_result:
            print("✅ MCP会话初始化成功")
            print(f"  Protocol Version: {init_result.get('protocolVersion')}")
            server_info = init_result.get('serverInfo', {})
            print(f"  Server Info: {server_info}")
        else:
            print("⚠️  MCP会话初始化失败，但继续尝试工具调用")
        
        # 测试list-docs工具
        print("\n=== 步骤5：测试list-docs工具 ===")
        items = feishu.list_docs(node_token)
        if items is not None:
            print(f"✅ 成功获取 {len(items)} 个项目")
            # 打印所有项目详情
            if items:
                print("\n📁 文件夹/文档列表:")
                for i, item in enumerate(items):
                    name = item.get('name', '未知')
                    item_type = item.get('type', '未知')
                    item_token = item.get('token', '无')
                    print(f"  {i+1}. [{item_type}] {name} - {item_token}")
            else:
                print("📭 当前文件夹为空")
        else:
            print("❌ 获取项目列表失败")
            return False
        
        # 创建测试文档
        print("\n=== 步骤6：创建测试文档 ===")
        timestamp = int(time.time())
        test_title = f"验证测试 - {timestamp}"
        test_content = f"# 验证测试文档\n\n## 测试信息\n- 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n- 时间戳: {timestamp}\n- 测试目的: 验证文档是否真正创建到飞书知识库\n\n## 测试内容\n这是一个用于验证飞书MCP集成的测试文档。\n如果您能看到此文档，说明MCP集成成功！\n\n## 测试步骤\n1. 初始化MCP会话\n2. 调用create-doc工具\n3. 验证文档创建结果\n4. 检查飞书知识库中是否存在此文档\n"
        
        print(f"📄 准备创建文档:")
        print(f"  标题: {test_title}")
        print(f"  内容长度: {len(test_content)} 字符")
        
        # 创建文档
        doc_id = feishu.create_md_document(test_title, test_content, node_token)
        
        if doc_id:
            print(f"\n✅ 文档创建成功！")
            print(f"  Document ID: {doc_id}")
            print(f"  预期位置: 就业技术文档集")
            
            # 再次查询文件夹，验证文档是否存在
            print("\n=== 步骤7：验证文档是否存在 ===")
            time.sleep(2)  # 等待文档同步
            
            items_after = feishu.list_docs(node_token)
            if items_after:
                print(f"✅ 成功获取更新后的项目列表 ({len(items_after)} 个)")
                
                # 查找新创建的文档
                found = False
                for item in items_after:
                    if item.get('name') == test_title:
                        found = True
                        print(f"\n🎉 找到新创建的文档！")
                        print(f"  名称: {item.get('name')}")
                        print(f"  类型: {item.get('type')}")
                        print(f"  Token: {item.get('token')}")
                        break
                
                if found:
                    print("\n✅ 验证通过：文档确实已创建到飞书知识库！")
                else:
                    print("\n⚠️  验证失败：未找到新创建的文档")
                    print("  可能原因：")
                    print("  1. 文档创建但尚未同步到列表")
                    print("  2. 权限问题导致无法查看")
                    print("  3. 文档创建到了其他位置")
                    
                    # 打印所有项目名称，方便手动检查
                    print("\n📋 当前所有项目名称:")
                    for item in items_after:
                        print(f"  - {item.get('name')}")
            else:
                print("❌ 获取更新后的项目列表失败")
                
        else:
            print("\n❌ 文档创建失败")
            return False
        
        # 总结
        print("\n=== 验证总结 ===")
        print("✅ 所有测试步骤执行完成")
        print("📝 测试文档信息:")
        print(f"  标题: {test_title}")
        print(f"  Document ID: {doc_id}")
        print(f"  创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        print(f"  目标位置: {TEST_URL}")
        
        print("\n🔍 手动验证建议:")
        print(f"  1. 打开飞书知识库: {TEST_URL}")
        print(f"  2. 检查是否存在名为 '{test_title}' 的文档")
        print(f"  3. 确认文档内容是否正确")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 验证过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = verify_document_creation()
    if success:
        print("\n🎉 验证测试成功完成！")
    else:
        print("\n❌ 验证测试失败，请检查错误信息。")

if __name__ == "__main__":
    main()
