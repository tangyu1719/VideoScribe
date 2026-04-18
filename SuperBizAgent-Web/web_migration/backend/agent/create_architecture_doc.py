#!/usr/bin/env python3
"""
创建项目架构文档
"""
from pathlib import Path

PROJECT_ROOT = Path(r"f:\java\AIOPS\SuperBizAgent_v2")

# 创建 ARCHITECTURE.md
architecture_md = """# SuperBizAgent v2.0 - 系统架构文档

## 1. 项目概述

SuperBizAgent 是一个基于 Agentic RAG 的企业级 AI 助手系统，集成了知识库管理、多模态处理、智能对话等功能。

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
├─────────────────────────────────────────────────────────────┤
│  GUI 应用 (Tkinter)  │  Web 前端 (React)  │  API 接口        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                      业务逻辑层                              │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  核心模块    │  服务模块    │  API 模块    │  GUI 模块      │
│  (core)      │  (services)  │  (api)       │  (gui)        │
└──────────────┴──────────────┴──────────────┴───────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                      数据访问层                              │
├─────────────────────────────────────────────────────────────┤
│  数据模型 (models)  │  工具函数 (utils)  │  配置管理 (config)│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                      基础设施层                              │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  MariaDB     │  ChromaDB    │  文件系统    │  外部 API      │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

## 3. 目录结构详解

### 3.1 源代码目录 (src/)

#### core/ - 核心业务逻辑
- **react_agent.py**: ReAct Agent 框架实现
  - Thought-Action-Observation 循环
  - 自适应多轮检索
  - 工具调用机制

- **kb_manager.py**: 知识库管理器
  - 服务启动初始化
  - 向量索引管理
  - 文件记录管理

- **kb_manager_advanced.py**: 高级知识库
  - Hybrid RAG 实现
  - BM25 + 向量相似度融合
  - RRF 排序融合

- **document_processor.py**: 文档处理器
  - 文档加载
  - 文本分块
  - 语义分割

- **mineru_processor.py**: MinerU 文档解析
  - PDF 转 Markdown
  - 公式识别
  - 表格提取

- **chat_memory_system.py**: 聊天记忆系统
  - 会话管理
  - 消息历史
  - 上下文维护

- **logging_system.py**: 日志系统
  - 分级日志
  - 日志轮转
  - 异常追踪

#### api/ - Web API 接口
- **web_api.py**: FastAPI 主服务
  - RESTful API
  - CORS 配置
  - 路由管理

- **web_api_stream.py**: 流式 API
  - SSE 流式响应
  - 实时推送
  - 连接管理

#### services/ - 业务服务层
- **link_analyzer.py**: 链接分析器
  - 链接内容提取
  - SEO 分析
  - 元数据解析

- **unified_link_document_processor.py**: 统一链接文档处理器
  - 多平台支持
  - 内容提取
  - 格式转换

- **wechat_article_processor.py**: 微信文章处理器
  - 文章提取
  - 图片下载
  - 格式整理

- **video_downloader.py**: 视频下载器
  - 多平台支持
  - 无水印下载
  - 批量处理

- **multimodal_tool.py**: 多模态工具
  - 图像处理
  - OCR 识别
  - 内容分析

#### gui/ - 图形用户界面
- **doubao_chat_page.py**: 豆包聊天页面
  - 聊天界面
  - 消息管理
  - 设置面板

- **rag_manager_gui.py**: 知识库管理 GUI
  - 文件上传
  - 统计展示
  - 进度监控

- **video_gui.py**: 视频下载 GUI
  - URL 输入
  - 下载管理
  - 进度显示

- **multimodal_gui.py**: 多模态 GUI
  - 文件选择
  - 处理选项
  - 结果展示

- **ai_chat_system.py**: AI 聊天系统
  - 对话管理
  - 上下文处理
  - 响应生成

#### models/ - 数据模型
- **db.py**: 数据库模块
  - 连接管理
  - ORM 映射
  - 查询构建

- **data_store.py**: 数据存储
  - 数据序列化
  - 缓存管理
  - 持久化

#### utils/ - 工具函数
- **config_api.py**: 配置 API
  - 配置读取
  - 配置更新
  - 环境变量

- **init_database.py**: 数据库初始化
  - 表创建
  - 索引创建
  - 数据迁移

#### config/ - 配置管理
- 系统配置文件
- 环境变量管理
- 密钥管理

### 3.2 配置文件目录 (configs/)

- **config.py**: 主配置文件
  - 数据库配置
  - API 配置
  - 路径配置

- **database/**: 数据库配置
- **api/**: API 密钥配置

### 3.3 数据目录 (data/)

- **knowledge_base/**: 知识库数据
  - 向量索引
  - 文件记录
  - 元数据

- **sessions/**: 会话数据
  - 聊天记录
  - 上下文

- **uploads/**: 上传文件
  - 临时文件
  - 用户文件

### 3.4 日志目录 (logs/)

- 应用日志
- 错误日志
- 访问日志

### 3.5 测试目录 (tests/)

- 单元测试
- 集成测试
- 端到端测试

### 3.6 前端目录 (web/)

```
web/
├── src/
│   ├── components/     # React 组件
│   ├── pages/         # 页面组件
│   ├── services/      # API 服务
│   ├── store/         # 状态管理
│   ├── hooks/         # 自定义 Hooks
│   ├── types/         # TypeScript 类型
│   └── lib/           # 工具库
├── public/            # 静态资源
└── package.json       # 依赖配置
```

## 4. 核心模块交互流程

### 4.1 Agentic RAG 流程

```
用户提问
   │
   ▼
ReAct Agent
   │
   ├─→ Thought: 分析问题
   │      │
   │      ▼
   │   是否需要检索？
   │      │
   │      ├─ 是 → Action: 调用 RAG
   │      │         │
   │      │         ▼
   │      │      Hybrid RAG 检索
   │      │         │
   │      │         ├─→ 向量检索 (ChromaDB)
   │      │         ├─→ BM25 检索
   │      │         └─→ RRF 融合排序
   │      │
   │      └─ 否 → 直接回答
   │
   ▼
Observation: 整合信息
   │
   ▼
生成回答
```

### 4.2 知识库构建流程

```
上传文档
   │
   ▼
文档解析 (MinerU)
   │
   ▼
文本分块 (RecursiveCharacterTextSplitter)
   │
   ▼
向量化 (BGE-Large-Chinese)
   │
   ▼
存储到 ChromaDB
   │
   ▼
更新文件记录
```

### 4.3 Web API 请求流程

```
HTTP 请求
   │
   ▼
FastAPI Router
   │
   ▼
中间件处理
   │
   ├─→ CORS
   ├─→ 认证
   └─→ 日志
   │
   ▼
业务逻辑层 (src/services)
   │
   ▼
数据访问层 (src/models)
   │
   ├─→ MariaDB
   └─→ ChromaDB
   │
   ▼
返回响应 (JSON/SSE)
```

## 5. 技术栈

### 后端
- **Python 3.9+**: 主要编程语言
- **FastAPI**: Web 框架
- **SQLAlchemy**: ORM
- **ChromaDB**: 向量数据库
- **MariaDB**: 关系数据库
- **BGE-Embeddings**: 文本嵌入模型

### 前端
- **React 18**: UI 框架
- **TypeScript**: 类型系统
- **Vite**: 构建工具
- **TailwindCSS**: 样式框架
- **Zustand**: 状态管理

### AI/ML
- **ReAct Framework**: Agent 框架
- **Hybrid RAG**: 检索增强生成
- **MinerU**: 文档解析
- **BGE-Large-Chinese**: 中文嵌入模型

## 6. 部署架构

### 开发环境
```
本地开发服务器
├── FastAPI (localhost:8000)
└── Vite Dev Server (localhost:5173)
```

### 生产环境
```
Nginx 反向代理
├── Frontend (静态文件)
└── Backend (Gunicorn + Uvicorn)
    ├── MariaDB
    └── ChromaDB
```

## 7. 安全考虑

- API 密钥管理（环境变量）
- CORS 配置
- SQL 注入防护（ORM 参数化）
- XSS 防护（前端输入验证）
- 请求频率限制

## 8. 性能优化

- 向量检索索引
- 数据库连接池
- 前端代码分割
- 静态资源缓存
- SSE 流式响应

## 9. 扩展性

### 水平扩展
- 无状态 API 设计
- Redis 会话存储
- 负载均衡

### 功能扩展
- 插件化 Agent 工具
- 可配置 RAG 策略
- 多租户支持

## 10. 监控与日志

- 结构化日志
- 异常追踪
- 性能指标
- 健康检查端点
"""

(PROJECT_ROOT / 'docs' / 'ARCHITECTURE.md').write_text(architecture_md, encoding='utf-8')
print("✓ 创建 docs/ARCHITECTURE.md")

print("\n✅ 架构文档创建完成！")
