#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖安装脚本 - 自动安装RAG知识库所需的所有依赖
"""

import subprocess
import sys
import time

def install_package(package_name, description=""):
    """安装单个包"""
    print(f"\n{'='*60}")
    print(f"正在安装: {package_name}")
    if description:
        print(f"用途: {description}")
    print('='*60)
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def main():
    print("="*60)
    print("RAG知识库依赖安装工具")
    print("="*60)
    print("\n将安装以下依赖：")
    print("1. sentence-transformers - 文本向量嵌入模型")
    print("2. faiss-cpu - Facebook向量检索库")
    print("3. PyPDF2 - PDF文件解析")
    print("4. python-docx - Word文档解析")
    print("5. scikit-learn - 机器学习工具包")
    print("\n")
    
    # 依赖列表
    dependencies = [
        ("sentence-transformers>=2.2.0", "文本向量嵌入，用于生成高质量语义向量"),
        ("faiss-cpu>=1.7.4", "Facebook向量检索库，用于高效相似度搜索"),
        ("PyPDF2>=3.0.0", "PDF文件解析，支持导入PDF文档"),
        ("python-docx>=0.8.11", "Word文档解析，支持导入docx文件"),
        ("scikit-learn>=1.3.0", "机器学习工具包，用于相似度计算"),
    ]
    
    success_count = 0
    fail_count = 0
    
    for package, desc in dependencies:
        if install_package(package, desc):
            success_count += 1
        else:
            fail_count += 1
        time.sleep(1)  # 短暂延迟，避免请求过快
    
    # 安装结果总结
    print("\n" + "="*60)
    print("安装结果总结")
    print("="*60)
    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    
    if fail_count == 0:
        print("\n🎉 所有依赖安装成功！")
        print("\n现在您可以：")
        print("1. 运行 python test_rag.py 测试RAG功能")
        print("2. 运行 python chat_gui.py 启动AI问答系统")
        print("3. 在主程序中点击 '🤖 AI问答' 按钮使用知识库功能")
    else:
        print("\n⚠️ 部分依赖安装失败，请检查错误信息")
        print("您可以尝试手动安装失败的包：")
        print("pip install <package_name>")
    
    print("\n" + "="*60)
    
    # 等待用户按键
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
