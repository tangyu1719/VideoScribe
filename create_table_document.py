#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建包含表格的飞书文档
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feishu_integration import FeishuKnowledgeBase

def create_table_document():
    """创建包含表格的文档"""
    print("=== 开始创建包含表格的飞书文档 ===")
    
    # 应用信息
    APP_ID = "cli_a9b7cc9aba389bc4"
    APP_SECRET = "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    
    # 目标知识库URL
    TARGET_URL = "https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b"
    TABLE_PARAM = "ldxw4epjpmvLng8S"  # 从URL参数中提取
    
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
        print(f"  Table 参数: {TABLE_PARAM}")
        
        # 步骤1：创建空文档
        print("\n=== 步骤3：创建空文档 ===")
        title = f"表格测试文档 - {TABLE_PARAM}"
        empty_doc_id = feishu.create_empty_document(title, node_token)
        
        if empty_doc_id:
            print(f"✅ 空文档创建成功: {empty_doc_id}")
            
            # 步骤2：创建包含表格的内容
            print("\n=== 步骤4：创建包含表格的内容 ===")
            import time
            table_content = f"# 表格测试文档\n\n## 测试表格\n\n| 姓名 | 年龄 | 职业 | 城市 |\n|------|------|------|------|\n| 张三 | 25 | 工程师 | 北京 |\n| 李四 | 30 | 设计师 | 上海 |\n| 王五 | 28 | 产品经理 | 深圳 |\n| 赵六 | 32 | 销售 | 广州 |\n\n## 表格说明\n- 这是一个测试表格\n- 包含基本个人信息\n- 用于验证表格创建功能\n\n## 技术信息\n- Table 参数: {TABLE_PARAM}\n- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n- 文档ID: {empty_doc_id}\n"
            
            print(f"✅ 表格内容已生成")
            print(f"  内容长度: {len(table_content)} 字符")
            
            # 步骤3：更新文档内容
            print("\n=== 步骤5：更新文档内容 ===")
            update_success = feishu.update_document_content(empty_doc_id, table_content)
            
            if update_success:
                print(f"\n🎉 表格文档创建成功！")
                print(f"  Document ID: {empty_doc_id}")
                print(f"  文档标题: {title}")
                print(f"  目标位置: {TARGET_URL}")
                print(f"  Table 参数: {TABLE_PARAM}")
                
                return True
            else:
                print("\n❌ 更新文档内容失败")
                return False
        else:
            print("\n❌ 创建空文档失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 创建表格文档异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    import time
    success = create_table_document()
    if success:
        print("\n🎉 表格文档创建成功！")
    else:
        print("\n❌ 表格文档创建失败，请检查错误信息。")

if __name__ == "__main__":
    main()
