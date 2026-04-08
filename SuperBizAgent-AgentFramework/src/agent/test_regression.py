#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试脚本 - 全面测试所有功能模块
"""

import sys
import traceback
from datetime import datetime

# 测试报告
report = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test_case(name):
    """测试装饰器"""
    def decorator(func):
        def wrapper():
            report["total"] += 1
            try:
                print(f"\n{'='*60}")
                print(f"测试: {name}")
                print('='*60)
                func()
                report["passed"] += 1
                report["tests"].append({"name": name, "status": "✅ 通过"})
                print(f"✅ 测试通过: {name}")
                return True
            except Exception as e:
                report["failed"] += 1
                report["tests"].append({"name": name, "status": "❌ 失败", "error": str(e)})
                print(f"❌ 测试失败: {name}")
                print(f"错误: {e}")
                traceback.print_exc()
                return False
        return wrapper
    return decorator

# ========== P0: 初始化逻辑测试 ==========

@test_case("P0-1: 知识库管理器初始化")
def test_kb_manager_init():
    """测试知识库管理器服务启动时初始化"""
    from kb_manager import get_knowledge_base, health_check
    
    kb = get_knowledge_base()
    assert kb.is_ready(), "知识库未就绪"
    
    health = health_check()
    assert health['status'] == 'healthy', f"健康检查失败: {health}"
    assert health['initialized'] == True, "未初始化"
    
    print(f"健康状态: {health}")

@test_case("P0-2: 高级知识库管理器初始化")
def test_advanced_kb_init():
    """测试高级知识库管理器初始化"""
    from kb_manager_advanced import get_advanced_knowledge_base, health_check_advanced
    
    kb = get_advanced_knowledge_base()
    assert kb.is_ready(), "高级知识库未就绪"
    
    health = health_check_advanced()
    assert health['status'] == 'healthy', f"健康检查失败: {health}"
    assert health['initialized'] == True, "未初始化"
    
    print(f"健康状态: {health}")

# ========== P1: 知识库技术升级测试 ==========

@test_case("P1-1: 递归文本分割器")
def test_recursive_splitter():
    """测试递归文本分割器"""
    from kb_manager_advanced import RecursiveTextSplitter
    
    splitter = RecursiveTextSplitter(chunk_size=100, chunk_overlap=20)
    
    text = """第一段内容。这是第一段的内容。

第二段内容。这是第二段的内容。

第三段内容。这是第三段的内容。"""
    
    chunks = splitter.split_text(text, "test.txt")
    
    assert len(chunks) > 0, "没有生成分块"
    assert all(len(c.content) > 0 for c in chunks), "存在空内容分块"
    
    print(f"生成了 {len(chunks)} 个分块")
    for i, c in enumerate(chunks):
        print(f"  [{i}] {c.content[:50]}...")

@test_case("P1-2: BGE嵌入模型")
def test_bge_embedding():
    """测试BGE嵌入模型"""
    from kb_manager_advanced import BGEEmbeddingModel
    
    model = BGEEmbeddingModel()
    
    texts = ["这是一个测试句子", "这是另一个测试句子"]
    embeddings = model.encode(texts)
    
    assert embeddings.shape[0] == 2, "嵌入数量不匹配"
    assert embeddings.shape[1] > 0, "嵌入维度为0"
    
    print(f"嵌入形状: {embeddings.shape}")
    print(f"嵌入维度: {model.dimension}")

@test_case("P1-3: 知识库搜索")
def test_kb_search():
    """测试知识库搜索功能"""
    from kb_manager import get_knowledge_base
    
    kb = get_knowledge_base()
    
    # 搜索（即使知识库为空也应该正常返回）
    results = kb.search("测试查询", top_k=5)
    
    assert isinstance(results, list), "返回结果不是列表"
    
    print(f"搜索结果数量: {len(results)}")

@test_case("P1-4: 高级知识库搜索(Hybrid RAG)")
def test_advanced_kb_search():
    """测试高级知识库搜索（混合检索）"""
    from kb_manager_advanced import get_advanced_knowledge_base
    
    kb = get_advanced_knowledge_base()
    
    # 搜索
    results = kb.search("测试查询", top_k=5)
    
    assert isinstance(results, list), "返回结果不是列表"
    
    print(f"搜索结果数量: {len(results)}")
    if results:
        print(f"第一个结果: {results[0]}")

# ========== P2: ReAct Agent测试 ==========

@test_case("P2-1: ReAct Agent初始化")
def test_react_agent_init():
    """测试ReAct Agent初始化"""
    from react_agent import ReActAgent
    from kb_manager import get_knowledge_base
    
    kb = get_knowledge_base()
    agent = ReActAgent(max_iterations=3, kb_manager=kb)
    
    assert agent.max_iterations == 3, "迭代次数设置失败"
    assert len(agent.tools) > 0, "工具未注册"
    
    print(f"Agent工具: {list(agent.tools.keys())}")

@test_case("P2-2: ReAct Agent执行")
def test_react_agent_run():
    """测试ReAct Agent执行"""
    from react_agent import ReActAgent
    from kb_manager import get_knowledge_base
    
    kb = get_knowledge_base()
    agent = ReActAgent(max_iterations=3, kb_manager=kb)
    
    result = agent.run("什么是Python？")
    
    assert result['success'] == True, "执行失败"
    assert 'answer' in result, "没有答案"
    assert 'steps' in result, "没有步骤记录"
    
    print(f"执行了 {result['iterations']} 步")
    print(f"检索了 {result['retrieval_count']} 次")
    print(f"答案: {result['answer'][:100]}...")

@test_case("P2-3: Agentic RAG查询")
def test_agentic_rag():
    """测试Agentic RAG"""
    from react_agent import AgenticRAG
    from kb_manager import get_knowledge_base
    
    kb = get_knowledge_base()
    rag = AgenticRAG(kb_manager=kb)
    
    result = rag.query("什么是人工智能？")
    
    assert result['success'] == True, "查询失败"
    assert 'answer' in result, "没有答案"
    assert 'retrieval_count' in result, "没有检索计数"
    
    print(f"检索次数: {result['retrieval_count']}")
    print(f"迭代次数: {result['iterations']}")

# ========== Web API集成测试 ==========

@test_case("WebAPI-1: 模块导入")
def test_web_api_import():
    """测试Web API模块导入"""
    import web_api
    
    assert hasattr(web_api, 'app'), "FastAPI应用未创建"
    assert web_api.KB_MANAGER_AVAILABLE == True, "知识库管理器不可用"
    assert web_api.KB_ADVANCED_AVAILABLE == True, "高级知识库管理器不可用"
    assert web_api.REACT_AGENT_AVAILABLE == True, "ReAct Agent不可用"
    
    print("Web API模块导入成功")
    print(f"  - KB_MANAGER_AVAILABLE: {web_api.KB_MANAGER_AVAILABLE}")
    print(f"  - KB_ADVANCED_AVAILABLE: {web_api.KB_ADVANCED_AVAILABLE}")
    print(f"  - REACT_AGENT_AVAILABLE: {web_api.REACT_AGENT_AVAILABLE}")

# ========== 主测试流程 ==========

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("开始回归测试")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # P0测试
    test_kb_manager_init()
    test_advanced_kb_init()
    
    # P1测试
    test_recursive_splitter()
    test_bge_embedding()
    test_kb_search()
    test_advanced_kb_search()
    
    # P2测试
    test_react_agent_init()
    test_react_agent_run()
    test_agentic_rag()
    
    # WebAPI测试
    test_web_api_import()
    
    # 输出报告
    print("\n" + "="*70)
    print("回归测试报告")
    print("="*70)
    print(f"总测试数: {report['total']}")
    print(f"通过: {report['passed']} ✅")
    print(f"失败: {report['failed']} ❌")
    print(f"通过率: {report['passed']/report['total']*100:.1f}%")
    
    print("\n详细结果:")
    for test in report['tests']:
        status = test['status']
        print(f"  {status}: {test['name']}")
        if 'error' in test:
            print(f"    错误: {test['error']}")
    
    print("\n" + "="*70)
    
    if report['failed'] == 0:
        print("🎉 所有测试通过！")
        return 0
    else:
        print(f"⚠️ 有 {report['failed']} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
