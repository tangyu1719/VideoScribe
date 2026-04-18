#!/usr/bin/env python3
"""
Agentic RAG 集成测试 - 使用更大的文档验证完整功能
"""

from agentic_rag_final import AgenticRAG
import os

def create_large_test_document():
    """创建大型测试文档"""
    content = """
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。
AI的研究领域包括机器学习、自然语言处理、计算机视觉、知识图谱等多个方向。

机器学习是AI的核心技术之一。它使计算机能够从数据中学习，而无需明确编程。
机器学习算法可以分为监督学习、无监督学习和强化学习三大类。
监督学习使用标记数据训练模型，无监督学习发现数据中的隐藏模式，强化学习通过与环境交互来学习最优策略。

深度学习是机器学习的一个子集，使用神经网络来处理复杂的数据模式。
深度神经网络包含多个隐藏层，能够学习数据的层次化表示。
卷积神经网络（CNN）在图像处理领域表现出色，循环神经网络（RNN）适合处理序列数据，Transformer架构则在自然语言处理任务中取得了突破性进展。

自然语言处理（NLP）是AI的另一个重要领域。它使计算机能够理解、解释和生成人类语言。
NLP的应用包括机器翻译、情感分析、问答系统和聊天机器人。
近年来，基于Transformer的预训练语言模型如BERT、GPT系列在各项NLP任务上都取得了显著成果。

计算机视觉让机器能够"看"和理解图像及视频。应用包括人脸识别、自动驾驶和医学影像分析。
目标检测、图像分割和图像生成是计算机视觉的主要研究方向。
生成对抗网络（GAN）和扩散模型在图像生成领域表现出色。

AI的伦理问题也日益受到关注，包括隐私保护、算法偏见和就业影响等方面。
确保AI系统的公平性、透明性和可解释性是当前研究的重要课题。
AI治理框架和伦理准则的制定对于AI技术的健康发展至关重要。

强化学习是一种通过与环境交互来学习的方法。它在游戏、机器人控制和资源管理等领域有广泛应用。
AlphaGo和AlphaZero是强化学习的著名成功案例。
深度强化学习结合了深度学习和强化学习的优势，能够处理高维状态空间的问题。

迁移学习允许模型将在一个任务上学到的知识应用到另一个相关任务上，大大提高了学习效率。
预训练-微调范式已经成为深度学习领域的标准做法。
在NLP领域，大规模预训练模型通过迁移学习在各种下游任务上取得了优异性能。

联邦学习是一种分布式机器学习方法，允许多个参与方在不共享原始数据的情况下协作训练模型。
联邦学习在保护数据隐私的同时，能够利用分布式数据资源。
它在医疗健康、金融等对数据隐私要求较高的领域具有重要应用价值。

知识图谱是一种结构化的知识表示方法，用于存储实体及其之间的关系。
知识图谱在智能搜索、推荐系统和问答系统中发挥重要作用。
构建大规模、高质量的知识图谱是AI领域的重要研究方向。
"""
    return content

def test_with_large_document():
    """使用大文档测试"""
    print("\n" + "=" * 70)
    print("Agentic RAG 集成测试 - 大文档")
    print("=" * 70)
    
    # 初始化RAG
    rag = AgenticRAG()
    
    # 创建测试文档
    test_doc_path = "test_large_doc_page_1.txt"
    content = create_large_test_document()
    
    with open(test_doc_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n创建测试文档: {test_doc_path}")
    print(f"文档大小: {len(content)} 字符")
    
    # 添加文档
    success = rag.add_document(test_doc_path)
    
    if success:
        print("\n" + "-" * 70)
        print("执行搜索测试...")
        print("-" * 70)
        
        # 测试查询
        queries = [
            "什么是机器学习",
            "深度学习",
            "自然语言处理的应用",
            "联邦学习是什么",
            "计算机视觉",
            "强化学习的应用"
        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"查询: {query}")
            print('='*70)
            result = rag.search(query, threshold=0.3)
            
            print(f"返回 {result['top_k']} 个结果 (总块数: {result['total_chunks']}):")
            for i, item in enumerate(result['results'], 1):
                print(f"\n[{i}] 内容:")
                print(f"    {item['content'][:120]}...")
                print(f"    来源: {item['source']['file_name']} (页{item['source']['page_number']}, 块{item['source']['chunk_index']})")
                print(f"    位置: 字符{item['source']['position']}")
                print(f"    分数: 语义={item['scores']['semantic']}, BM25={item['scores']['bm25']}, RRF={item['scores']['rrf']}")
    
    # 清理
    if os.path.exists(test_doc_path):
        os.remove(test_doc_path)
        print(f"\n清理测试文件: {test_doc_path}")
    
    print("\n" + "=" * 70)
    print("集成测试完成")
    print("=" * 70)

def test_multiple_documents():
    """测试多文档场景"""
    print("\n" + "=" * 70)
    print("Agentic RAG 集成测试 - 多文档")
    print("=" * 70)
    
    # 初始化RAG
    rag = AgenticRAG()
    
    # 创建多个测试文档
    docs = [
        ("doc_page_1.txt", """
Python是一种高级编程语言，由Guido van Rossum于1991年创建。
Python的设计哲学强调代码的可读性和简洁性。
Python支持多种编程范式，包括面向对象、函数式和过程式编程。
Python拥有丰富的标准库和第三方库，广泛应用于Web开发、数据分析、人工智能等领域。
"""),
        ("doc_page_2.txt", """
Java是另一种流行的编程语言，由Sun Microsystems于1995年发布。
Java的特点是"一次编写，到处运行"，具有良好的跨平台性。
Java广泛应用于企业级应用开发、Android应用开发和大数据处理。
Java的强类型系统和自动内存管理使其成为大型项目的首选语言之一。
"""),
        ("doc_page_3.txt", """
JavaScript是Web开发的核心语言，最初由Netscape公司于1995年开发。
JavaScript可以在浏览器中运行，也可以用于服务器端开发（Node.js）。
JavaScript支持事件驱动、函数式和面向对象编程范式。
现代JavaScript框架如React、Vue和Angular极大地简化了前端开发。
""")
    ]
    
    # 写入文档
    for filename, content in docs:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"创建文档: {filename}")
    
    # 添加所有文档
    for filename, _ in docs:
        rag.add_document(filename)
    
    print("\n" + "-" * 70)
    print("执行多文档搜索测试...")
    print("-" * 70)
    
    # 测试查询
    queries = [
        "Python编程",
        "Java应用",
        "JavaScript框架"
    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"查询: {query}")
        print('='*70)
        result = rag.search(query)
        
        print(f"返回 {result['top_k']} 个结果:")
        for i, item in enumerate(result['results'], 1):
            print(f"\n[{i}] 内容: {item['content'][:80]}...")
            print(f"    来源: {item['source']['file_name']} (页{item['source']['page_number']})")
            print(f"    分数: RRF={item['scores']['rrf']}")
    
    # 清理
    for filename, _ in docs:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"\n清理: {filename}")
    
    print("\n" + "=" * 70)
    print("多文档测试完成")
    print("=" * 70)

if __name__ == "__main__":
    test_with_large_document()
    test_multiple_documents()