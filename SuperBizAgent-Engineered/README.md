# SuperBizAgent - AI 文档处理与知识库系统

## 工程化版本 v2.0

SuperBizAgent 是一个功能强大的AI文档处理与知识库系统，支持多模态文档处理、RAG知识库问答、链接内容分析等功能。

## 项目结构

```
SuperBizAgent-Engineered/
├── main.py                      # 主入口文件
├── requirements.txt             # 依赖包列表
├── README.md                    # 项目说明
├── config/                      # 配置文件目录
├── data/                        # 数据目录
│   ├── knowledge_base/         # 知识库数据
│   ├── uploads/                # 上传文件
│   └── output/                 # 输出文件
├── docs/                        # 文档目录
├── src/                         # 源代码目录
│   ├── core/                   # 核心工具模块
│   ├── knowledge_base/         # 知识库模块
│   ├── document_processing/    # 文档处理模块
│   ├── link_analysis/          # 链接分析模块
│   ├── ai_chat/                # AI对话模块
│   └── gui/                    # GUI界面模块
└── tests/                       # 测试目录
```

## 功能特性

### 1. 知识库管理
- 📚 RAG知识库问答
- 🔍 混合召回（语义相似度 + BM25 + RRF）
- 📄 动态语义分割
- 🎯 BGE-Large向量嵌入

### 2. 多模态文档处理
- 📁 支持PDF、Word、图片、音频、视频
- 🖼️ OCR文字识别
- 📝 文档结构化提取
- 🎬 视频转文字

### 3. 链接内容分析
- 🔗 链接内容提取
- 📱 支持抖音、小红书等平台
- 🤖 AI智能分析
- 📄 生成结构化文档

### 4. AI对话系统
- 💬 支持知识库问答
- 🧠 主模型：Doubao-Seed-2.0-Code
- 🔄 备用模型：Doubao-Seed-2.0-mini
- 🎭 角色扮演模式

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python main.py
```

### 3. 使用功能

- 点击"📚 知识库管理"管理文档和生成索引
- 点击"📁 多模态文档处理"处理各类文档
- 点击"🔗 链接+文档统一处理"分析链接内容
- 点击"🎬 视频下载"下载平台视频

## 模型配置

### 主模型
- **名称**: Doubao-Seed-2.0-Code
- **用途**: 默认对话模型

### 备用模型
- **名称**: Doubao-Seed-2.0-mini (ep-20260320202115-9jqfp)
- **用途**: 轻量级对话

### 嵌入模型
- **名称**: BGE-Large
- **用途**: 文档向量嵌入

## 开发说明

### 添加新模块

1. 在 `src/` 下创建新模块目录
2. 在目录中添加模块文件
3. 在 `main.py` 中导入并集成

### 运行测试

```bash
pytest tests/
```

## 技术栈

- **Python**: 3.8+
- **GUI**: Tkinter
- **向量数据库**: 本地存储（可选Milvus）
- **嵌入模型**: BGE-Large
- **LLM**: 火山引擎 Doubao系列

## 许可证

MIT License

## 作者

AI Assistant

## 更新日志

### v2.0 (2026-04-08)
- ✅ 工程化项目结构
- ✅ 模块化代码组织
- ✅ 支持主/备模型切换
- ✅ 优化知识库检索
