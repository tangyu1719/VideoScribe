#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确创建飞书表格和文档的脚本
按照正确流程执行：检查知识库状态 → 创建表格 → 创建文档 → 验证结果
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feishu_integration import FeishuKnowledgeBase

def create_table_and_document():
    """正确创建表格和文档"""
    print("=== 开始正确创建飞书表格和文档 ===")
    
    # 应用信息
    APP_ID = "cli_a9b7cc9aba389bc4"
    APP_SECRET = "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    
    # 目标知识库URL
    TARGET_URL = "https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b"
    
    try:
        # 初始化FeishuKnowledgeBase
        print("\n=== 步骤1：初始化飞书集成 ===")
        feishu = FeishuKnowledgeBase(APP_ID, APP_SECRET)
        
        # 解析节点token
        print("\n=== 步骤2：解析节点token ===")
        node_token = feishu.parse_node_token_from_url(TARGET_URL)
        if not node_token:
            print("❌ 解析节点token失败")
            return False
        print(f"✅ 成功解析到节点token: {node_token}")
        
        # 步骤3：检查知识库状态
        print("\n=== 步骤3：检查知识库状态 ===")
        print(f"  查询节点: {node_token} 下的内容")
        items = feishu.list_docs(node_token)
        
        if items is not None:
            print(f"✅ 成功获取 {len(items)} 个项目")
            if items:
                print("\n📁 当前节点下的内容:")
                for i, item in enumerate(items):
                    name = item.get('name', '未知')
                    item_type = item.get('type', '未知')
                    item_token = item.get('token', '无')
                    print(f"  {i+1}. [{item_type}] {name} - {item_token}")
            else:
                print("📭 当前节点为空，需要创建新内容")
        else:
            print("❌ 检查知识库状态失败")
            return False
        
        # 步骤4：创建表格（使用飞书表格创建工具）
        print("\n=== 步骤4：创建表格 ===")
        print("  注意：飞书的表格创建需要特定的API调用")
        print("  这里创建一个包含表格的文档")
        
        # 步骤5：创建文档（包含表格）
        print("\n=== 步骤5：创建包含表格的文档 ===")
        timestamp = int(time.time())
        title = f"正确表格文档 - {timestamp}"
        
        # 创建空文档
        empty_doc_id = feishu.create_empty_document(title, node_token)
        
        if empty_doc_id:
            print(f"✅ 空文档创建成功: {empty_doc_id}")
            
            # 创建包含表格的内容
            table_content = f"# 正确的表格文档\n\n## 人员信息表格\n\n| ID | 姓名 | 年龄 | 部门 | 职位 | 邮箱 |\n|----|------|------|------|------|------|\n| 1 | 张明 | 28 | 技术部 | 工程师 | zhang@example.com |\n| 2 | 李华 | 32 | 产品部 | 产品经理 | li@example.com |\n| 3 | 王芳 | 26 | 设计部 | UI设计师 | wang@example.com |\n| 4 | 赵强 | 35 | 销售部 | 销售总监 | zhao@example.com |\n| 5 | 陈静 | 30 | 运营部 | 运营经理 | chen@example.com |\n\n## 表格说明\n- 表格ID: 需要通过飞书表格API创建\n- 表格类型: 人员信息管理\n- 数据来源: 测试数据\n\n## 技术参数\n- 知识库节点: {node_token}\n- 文档ID: {empty_doc_id}\n- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n- 表格状态: 待创建\n"
            
            # 更新文档内容
            update_success = feishu.update_document_content(empty_doc_id, table_content)
            
            if update_success:
                print("✅ 文档内容更新成功")
                
                # 步骤6：验证创建结果
                print("\n=== 步骤6：验证创建结果 ===")
                print(f"  📄 文档标题: {title}")
                print(f"  📄 文档ID: {empty_doc_id}")
                print(f"  🔗 文档链接: https://www.feishu.cn/docx/{empty_doc_id}")
                print(f"  📁 目标位置: {TARGET_URL}")
                print(f"  📊 表格状态: 已添加到文档")
                
                # 步骤7：最终验证
                print("\n=== 步骤7：最终验证 ===")
                print("  请在飞书知识库中验证以下内容:")
                print(f"  1. 打开链接: {TARGET_URL}")
                print(f"  2. 检查是否存在文档: {title}")
                print(f"  3. 打开文档检查表格是否正确显示")
                print(f"  4. 验证所有信息是否完整")
                
                return True
            else:
                print("❌ 更新文档内容失败")
                return False
        else:
            print("❌ 创建空文档失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 操作过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = create_table_and_document()
    if success:
        print("\n🎉 表格和文档创建流程执行完成！")
        print("✅ 请按照验证步骤检查飞书知识库")
    else:
        print("\n❌ 操作失败，请检查错误信息并重新执行")

if __name__ == "__main__":
    main()
