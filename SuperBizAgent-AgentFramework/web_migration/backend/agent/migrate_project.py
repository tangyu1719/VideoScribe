#!/usr/bin/env python3
"""
项目代码迁移脚本
将旧项目的代码按功能模块迁移到新的规范化目录结构
"""
import os
import shutil
from pathlib import Path

# 源目录和目标目录
OLD_PROJECT = r"f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua"
NEW_PROJECT = r"f:\java\AIOPS\SuperBizAgent_v2"

# 文件映射关系：源文件 -> 目标目录
FILE_MAPPING = {
    # === 核心业务逻辑 -> src/core ===
    'react_agent.py': 'src/core',
    'kb_manager.py': 'src/core',
    'kb_manager_advanced.py': 'src/core',
    'document_processor.py': 'src/core',
    'mineru_processor.py': 'src/core',
    'chat_memory_system.py': 'src/core',
    'logging_system.py': 'src/core',
    
    # === Web API -> src/api ===
    'web_api.py': 'src/api',
    'web_api_stream.py': 'src/api',
    
    # === 业务服务 -> src/services ===
    'link_analyzer.py': 'src/services',
    'unified_link_document_processor.py': 'src/services',
    'wechat_article_processor.py': 'src/services',
    'video_downloader.py': 'src/services',
    'multimodal_tool.py': 'src/services',
    
    # === GUI 界面 -> src/gui ===
    'doubao_chat_page.py': 'src/gui',
    'rag_manager_gui.py': 'src/gui',
    'video_gui.py': 'src/gui',
    'multimodal_gui.py': 'src/gui',
    'unified_link_document_gui.py': 'src/gui',
    'ai_chat_system.py': 'src/gui',
    
    # === 数据模型 -> src/models ===
    'db.py': 'src/models',
    'data_store.py': 'src/models',
    
    # === 工具函数 -> src/utils ===
    'config_api.py': 'src/utils',
    'init_database.py': 'src/utils',
    
    # === 配置文件 -> 根目录 configs ===
    'requirements.txt': 'configs',
    '.gitignore': '',
}

# 需要复制的目录
DIR_MAPPING = {
    'web': 'web',  # 前端项目整体迁移
}

def create_init_files():
    """为所有 Python 包目录创建__init__.py"""
    src_dir = Path(NEW_PROJECT) / 'src'
    for subdir in src_dir.iterdir():
        if subdir.is_dir():
            init_file = subdir / '__init__.py'
            if not init_file.exists():
                init_file.write_text('"""\n{} 模块\n"""\n'.format(subdir.name))
                print(f"✓ 创建 {init_file}")

def copy_files():
    """复制文件到新位置"""
    for src_file, dest_dir in FILE_MAPPING.items():
        src_path = Path(OLD_PROJECT) / src_file
        if not src_path.exists():
            print(f"✗ 文件不存在：{src_file}")
            continue
        
        dest_path = Path(NEW_PROJECT) / dest_dir / src_file if dest_dir else Path(NEW_PROJECT) / src_file
        
        try:
            shutil.copy2(src_path, dest_path)
            print(f"✓ 复制 {src_file} -> {dest_dir or '/'}")
        except Exception as e:
            print(f"✗ 复制失败 {src_file}: {e}")

def copy_directories():
    """复制整个目录"""
    for src_dir, dest_dir in DIR_MAPPING.items():
        src_path = Path(OLD_PROJECT) / src_dir
        dest_path = Path(NEW_PROJECT) / dest_dir
        
        if not src_path.exists():
            print(f"✗ 目录不存在：{src_dir}")
            continue
        
        if dest_path.exists():
            shutil.rmtree(dest_path)
        
        shutil.copytree(src_path, dest_path)
        print(f"✓ 复制目录 {src_dir} -> {dest_dir}")

def create_readme():
    """创建项目 README"""
    readme_content = """# SuperBizAgent v2.0

AI 驱动的智能业务助手 - 基于 Agentic RAG 的企业级 AI 助手系统

## 项目结构

```
SuperBizAgent_v2/
├── src/                    # 源代码目录
│   ├── core/              # 核心业务逻辑
│   │   ├── react_agent.py           # ReAct Agent 框架
│   │   ├── kb_manager.py            # 知识库管理器
│   │   ├── kb_manager_advanced.py   # 高级知识库（Hybrid RAG）
│   │   ├── document_processor.py    # 文档处理器
│   │   ├── mineru_processor.py      # MinerU 文档解析
│   │   ├── chat_memory_system.py    # 聊天记忆系统
│   │   └── logging_system.py        # 日志系统
│   ├── api/               # Web API 接口
│   │   ├── web_api.py               # FastAPI 主服务
│   │   └── web_api_stream.py        # 流式 API
│   ├── services/          # 业务服务层
│   │   ├── link_analyzer.py         # 链接分析器
│   │   ├── unified_link_document_processor.py  # 统一链接文档处理器
│   │   ├── wechat_article_processor.py  # 微信文章处理器
│   │   ├── video_downloader.py      # 视频下载器
│   │   └── multimodal_tool.py       # 多模态工具
│   ├── gui/               # 图形用户界面
│   │   ├── doubao_chat_page.py      # 豆包聊天页面
│   │   ├── rag_manager_gui.py       # 知识库管理 GUI
│   │   ├── video_gui.py             # 视频下载 GUI
│   │   ├── multimodal_gui.py        # 多模态 GUI
│   │   └── ai_chat_system.py        # AI 聊天系统
│   ├── models/            # 数据模型
│   │   ├── db.py                    # 数据库模块
│   │   └── data_store.py            # 数据存储
│   ├── utils/             # 工具函数
│   │   ├── config_api.py            # 配置 API
│   │   └── init_database.py         # 数据库初始化
│   └── config/            # 配置管理
├── configs/               # 配置文件目录
│   ├── database/          # 数据库配置
│   └── api/               # API 配置
├── data/                  # 数据文件目录
│   ├── knowledge_base/    # 知识库数据
│   ├── sessions/          # 会话数据
│   └── uploads/           # 上传文件
├── logs/                  # 日志文件目录
├── tests/                 # 测试代码
├── scripts/               # 工具脚本
├── web/                   # 前端项目（React + TypeScript）
├── docs/                  # 文档
├── requirements.txt       # Python 依赖
└── README.md              # 项目说明
```

## 核心功能

### 1. Agentic RAG 知识库系统
- **ReAct 执行框架**: Thought-Action-Observation 循环
- **Hybrid RAG**: 向量相似度 + BM25 + RRF 融合检索
- **ChromaDB**: 向量数据库存储
- **BGE-Large 中文嵌入**: 1024 维语义表示
- **MinerU 文档解析**: PDF/Word 等文档智能解析

### 2. 多模态处理
- 微信文章提取与分析
- 小红书图文内容解析
- 抖音视频无水印下载
- 链接内容智能提取

### 3. Web API 服务
- FastAPI 后端服务
- RESTful API 接口
- SSE 流式响应
- 前后端分离架构

### 4. 前端界面
- React + TypeScript
- TailwindCSS 样式
- 实时聊天界面
- 知识库可视化管理

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+
- MariaDB 10.6+

### 安装步骤

1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

2. 安装前端依赖
```bash
cd web
npm install
```

3. 配置数据库
```bash
# 编辑 configs/database/config.py
# 设置 MariaDB 连接信息
```

4. 初始化数据库
```bash
python -m src.utils.init_database
```

5. 启动后端服务
```bash
python -m src.api.web_api
```

6. 启动前端开发服务器
```bash
cd web
npm run dev
```

## 技术栈

**后端**
- Python 3.9+
- FastAPI
- ChromaDB
- SQLAlchemy
- BGE-Embeddings

**前端**
- React 18
- TypeScript
- Vite
- TailwindCSS
- Zustand

**数据库**
- MariaDB (关系型数据)
- ChromaDB (向量数据)

## 项目规范

### 代码风格
- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 类型注解（Type Hints）

### 提交规范
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

## License

MIT License
"""
    
    readme_path = Path(NEW_PROJECT) / 'README.md'
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"✓ 创建 README.md")

def main():
    print("="*60)
    print("开始迁移项目代码...")
    print("="*60)
    
    # 1. 创建__init__.py
    print("\n1. 创建包初始化文件...")
    create_init_files()
    
    # 2. 复制文件
    print("\n2. 复制源代码文件...")
    copy_files()
    
    # 3. 复制目录
    print("\n3. 复制前端项目...")
    copy_directories()
    
    # 4. 创建 README
    print("\n4. 创建项目文档...")
    create_readme()
    
    print("\n" + "="*60)
    print("✅ 项目迁移完成！")
    print("="*60)
    print(f"\n新项目位置：{NEW_PROJECT}")

if __name__ == '__main__':
    main()
