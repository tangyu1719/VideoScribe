#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传视频分析文档到飞书知识库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feishu_integration import FeishuKnowledgeBase

def upload_video_document():
    """上传视频分析文档"""
    print("=== 开始上传视频分析文档到飞书知识库 ===")
    
    # 应用信息
    APP_ID = "cli_a9b7cc9aba389bc4"
    APP_SECRET = "q3VZTLZZjrsNeiJheqfkocH5ReV6Rmc6"
    
    # 目标知识库URL
    TARGET_URL = "https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b"
    
    # 文档路径
    DOCUMENT_PATH = "F:\\java\\AIOPS\\SuperBizAgent-release-2026-01-02\\demo_wendanghua\\output\\015-02-11-#_百万级Excel数据导出优化（面试导_视频分析.md"
    
    try:
        # 读取文档内容
        print("\n=== 步骤1：读取文档内容 ===")
        if not os.path.exists(DOCUMENT_PATH):
            print(f"❌ 文档不存在: {DOCUMENT_PATH}")
            return False
        
        with open(DOCUMENT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ 成功读取文档")
        print(f"  文档大小: {len(content)} 字符")
        print(f"  文档路径: {DOCUMENT_PATH}")
        
        # 提取文档标题
        print("\n=== 步骤2：提取文档标题 ===")
        lines = content.split('\n')
        title = "视频分析 - 百万级Excel数据导出优化"
        # 尝试从内容中提取标题
        for line in lines[:10]:  # 检查前10行
            if line.startswith('# '):
                title = line[2:].strip()
                break
        print(f"✅ 文档标题: {title}")
        
        # 初始化FeishuKnowledgeBase
        print("\n=== 步骤3：初始化飞书集成 ===")
        feishu = FeishuKnowledgeBase(APP_ID, APP_SECRET)
        
        # 解析节点token
        print("\n=== 步骤4：解析节点token ===")
        node_token = feishu.parse_node_token_from_url(TARGET_URL)
        if not node_token:
            print("❌ 解析节点token失败")
            return False
        print(f"✅ 成功解析到节点token: {node_token}")
        
        # 上传文档（两步流程：先创建空文档，再更新内容）
        print("\n=== 步骤5：上传文档到飞书 ===")
        print("  执行两步流程：1. 创建空文档 2. 更新内容")
        
        # 步骤1：创建空文档
        print("  步骤1：创建空文档...")
        empty_doc_id = feishu.create_empty_document(title, node_token)
        
        if empty_doc_id:
            print(f"  ✅ 空文档创建成功: {empty_doc_id}")
            
            # 步骤2：更新文档内容
            print("  步骤2：更新文档内容...")
            update_success = feishu.update_document_content(empty_doc_id, content)
            
            if update_success:
                print(f"\n🎉 文档上传成功！")
                print(f"  Document ID: {empty_doc_id}")
                print(f"  文档标题: {title}")
                print(f"  目标位置: {TARGET_URL}")
                
                # 智能分类
                folder_path = feishu.auto_classify_content(content)
                print(f"  智能分类: {folder_path}")
                
                return True
            else:
                print("\n❌ 更新文档内容失败")
                return False
        else:
            print("\n❌ 创建空文档失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 上传过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = upload_video_document()
    if success:
        print("\n🎉 视频分析文档上传成功！")
    else:
        print("\n❌ 视频分析文档上传失败，请检查错误信息。")

if __name__ == "__main__":
    main()
