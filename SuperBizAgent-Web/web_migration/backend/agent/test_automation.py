#!/usr/bin/env python3
"""自动化测试脚本 - 测试所有按钮和功能"""
import os
import sys
import time
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 测试问题记录
issues = []
test_count = 0

def log_issue(category, description, severity="中"):
    """记录问题"""
    global issues
    issues.append({
        "id": len(issues) + 1,
        "category": category,
        "description": description,
        "severity": severity,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    print(f"  [问题{len(issues)}] [{severity}] {category}: {description}")

def test_basic_imports():
    """测试基本导入"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 基本模块导入测试")
    
    try:
        import tkinter as tk
        print("  ✓ tkinter导入成功")
    except Exception as e:
        log_issue("导入错误", f"tkinter导入失败: {e}", "高")
    
    try:
        from PIL import Image
        print("  ✓ PIL导入成功")
    except Exception as e:
        log_issue("导入错误", f"PIL导入失败: {e}", "高")
    
    try:
        import numpy
        print("  ✓ numpy导入成功")
    except Exception as e:
        log_issue("导入错误", f"numpy导入失败: {e}", "中")

def test_file_structure():
    """测试文件结构"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 文件结构测试")
    
    required_files = [
        "video_gui.py",
        "rag_knowledge_base.py",
        "rag_manager_gui.py",
        "config.json"
    ]
    
    for file in required_files:
        path = os.path.join(BASE_DIR, file)
        if os.path.exists(path):
            print(f"  ✓ {file} 存在")
        else:
            log_issue("文件缺失", f"{file} 不存在", "高")
    
    # 测试目录结构
    required_dirs = ["output", "knowledge_base"]
    for dir_name in required_dirs:
        path = os.path.join(BASE_DIR, dir_name)
        if os.path.exists(path):
            print(f"  ✓ {dir_name}/ 目录存在")
        else:
            print(f"  ! {dir_name}/ 目录不存在（将自动创建）")

def test_rag_knowledge_base():
    """测试RAG知识库功能"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] RAG知识库功能测试")
    
    try:
        from rag_knowledge_base import RAGKnowledgeBase
        print("  ✓ RAGKnowledgeBase导入成功")
        
        # 测试初始化
        kb = RAGKnowledgeBase()
        print(f"  ✓ RAG知识库初始化成功")
        print(f"    - 嵌入维度: {kb.embedding_dim}")
        print(f"    - 文档片段数: {len(kb.chunks)}")
        
        # 测试搜索功能
        if len(kb.chunks) > 0:
            results = kb.search("测试查询", top_k=3)
            print(f"  ✓ 搜索功能正常，返回{len(results)}个结果")
        else:
            print("  ! 知识库为空，跳过搜索测试")
            
    except Exception as e:
        log_issue("RAG功能", f"RAG知识库测试失败: {e}", "高")
        traceback.print_exc()

def test_config_loading():
    """测试配置加载"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 配置加载测试")
    
    config_file = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                import json
                config = json.load(f)
            print("  ✓ config.json加载成功")
            
            # 检查关键配置项
            required_keys = ["volcengine_api_key", "feishu_webhook_url"]
            for key in required_keys:
                if key in config:
                    print(f"    ✓ {key} 配置存在")
                else:
                    log_issue("配置缺失", f"{key} 未配置", "中")
        except Exception as e:
            log_issue("配置错误", f"config.json加载失败: {e}", "高")
    else:
        log_issue("配置缺失", "config.json不存在", "高")

def test_output_files():
    """测试输出文件"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 输出文件测试")
    
    output_dir = os.path.join(BASE_DIR, "output")
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        txt_files = [f for f in files if f.endswith('.txt')]
        print(f"  ✓ output目录存在，包含{len(txt_files)}个txt文件")
        
        for file in txt_files[:3]:  # 只显示前3个
            file_path = os.path.join(output_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"    ✓ {file} ({len(content)}字符)")
            except Exception as e:
                log_issue("文件读取", f"{file}读取失败: {e}", "中")
    else:
        log_issue("目录缺失", "output目录不存在", "中")

def test_kb_index():
    """测试知识库索引"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 知识库索引测试")
    
    index_file = os.path.join(BASE_DIR, "knowledge_base", "real_index.json")
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                import json
                index_data = json.load(f)
            
            chunk_count = index_data.get('count', 0)
            embedding_dim = index_data.get('embedding_dim', 0)
            model_name = index_data.get('model', 'unknown')
            
            print(f"  ✓ 索引文件存在")
            print(f"    - 文档片段: {chunk_count}")
            print(f"    - 嵌入维度: {embedding_dim}")
            print(f"    - 模型: {model_name}")
            
            if chunk_count == 0:
                log_issue("索引为空", "知识库索引为空", "中")
            if embedding_dim != 384:
                log_issue("维度异常", f"嵌入维度{embedding_dim}不等于384", "中")
                
        except Exception as e:
            log_issue("索引错误", f"索引文件读取失败: {e}", "高")
    else:
        log_issue("索引缺失", "real_index.json不存在", "中")

def test_imports_detailed():
    """详细测试所有导入"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 详细导入测试")
    
    modules = [
        ("tkinter", "GUI框架"),
        ("PIL", "图像处理"),
        ("requests", "HTTP请求"),
        ("numpy", "数值计算"),
        ("json", "JSON处理"),
        ("os", "系统操作"),
        ("sys", "系统参数"),
        ("threading", "多线程"),
        ("concurrent.futures", "并发执行"),
        ("hashlib", "哈希计算"),
        ("datetime", "日期时间"),
    ]
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name} ({description})")
        except Exception as e:
            log_issue("导入错误", f"{module_name}导入失败: {e}", "中")

def test_performance():
    """性能测试"""
    global test_count
    test_count += 1
    print(f"\n[测试{test_count}] 性能测试")
    
    # 测试RAG搜索性能
    try:
        from rag_knowledge_base import RAGKnowledgeBase
        kb = RAGKnowledgeBase()
        
        if len(kb.chunks) > 0:
            start_time = time.time()
            for _ in range(10):
                kb.search("性能测试", top_k=5)
            elapsed = time.time() - start_time
            avg_time = elapsed / 10
            
            print(f"  ✓ RAG搜索性能: {avg_time:.3f}s/次")
            
            if avg_time > 1.0:
                log_issue("性能问题", f"RAG搜索过慢: {avg_time:.3f}s/次", "中")
        else:
            print("  ! 知识库为空，跳过性能测试")
            
    except Exception as e:
        log_issue("性能测试", f"性能测试失败: {e}", "低")

def generate_report():
    """生成测试报告"""
    print("\n" + "="*70)
    print("测试报告")
    print("="*70)
    
    print(f"\n总测试数: {test_count}")
    print(f"发现问题: {len(issues)}个")
    
    if issues:
        # 按严重程度分类
        high_issues = [i for i in issues if i['severity'] == '高']
        medium_issues = [i for i in issues if i['severity'] == '中']
        low_issues = [i for i in issues if i['severity'] == '低']
        
        print(f"\n严重问题: {len(high_issues)}个")
        for issue in high_issues:
            print(f"  [{issue['id']}] {issue['category']}: {issue['description']}")
        
        print(f"\n中等问题: {len(medium_issues)}个")
        for issue in medium_issues:
            print(f"  [{issue['id']}] {issue['category']}: {issue['description']}")
        
        print(f"\n轻微问题: {len(low_issues)}个")
        for issue in low_issues:
            print(f"  [{issue['id']}] {issue['category']}: {issue['description']}")
    else:
        print("\n✓ 未发现明显问题")
    
    print("\n" + "="*70)

def main():
    """主测试函数"""
    print("="*70)
    print("开始自动化测试")
    print("="*70)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_basic_imports()
        test_imports_detailed()
        test_file_structure()
        test_config_loading()
        test_output_files()
        test_kb_index()
        test_rag_knowledge_base()
        test_performance()
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        traceback.print_exc()
    
    generate_report()
    
    print(f"\n结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {time.time() - start_time:.1f}秒")

if __name__ == "__main__":
    start_time = time.time()
    main()
