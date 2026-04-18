# 多模态文档化助手（Multimodal Doc Assistant）

## 标准Agent工程框架版本

基于业界标准的Python Agent工程框架构建，保持原始功能完整。

## 项目结构（标准Agent框架）

```
SuperBizAgent-AgentFramework/
├── main.py                      # 项目入口
├── start.bat                    # Windows启动脚本
├── README.md                    # 项目说明
├── .env                         # 环境变量（需创建）
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── agent/                  # Agent核心模块
│   │   ├── __init__.py
│   │   ├── video_gui.py        # 视频GUI（原始代码完整）
│   │   ├── ai_chat_system.py   # AI聊天系统
│   │   ├── tools/              # Agent工具定义
│   │   └── prompts/            # 提示词模板
│   ├── services/               # 服务层
│   │   ├── __init__.py
│   │   └── video_downloader.py # 视频下载服务
│   ├── models/                 # 模型层
│   │   └── __init__.py
│   ├── utils/                  # 工具函数
│   │   └── __init__.py
│   └── graph/                  # 工作流/图定义
│       └── __init__.py
├── config/                      # 配置文件
├── data/                        # 数据目录
│   ├── videos/                 # 视频下载目录
│   ├── output/                 # 输出文件目录
│   └── knowledge/              # 知识库数据
├── logs/                        # 日志目录
├── tests/                       # 测试目录
└── examples/                    # 示例代码
```

## 标准Agent框架说明

### 分层架构
1. **入口层** (`main.py`) - 接收用户请求，返回响应
2. **Agent层** (`src/agent/`) - Agent核心逻辑、决策、工具调用
3. **服务层** (`src/services/`) - 业务逻辑封装
4. **模型层** (`src/models/`) - 模型创建与管理
5. **工具层** (`src/utils/`) - 通用工具函数

### 核心功能

#### 1. 视频下载
- 支持抖音、小红书等平台
- 自动去水印
- 多线程下载

#### 2. 语音转文字
- Whisper模型
- 多语言识别
- 自动分段

#### 3. AI分析
- 火山引擎API
- 自动总结
- 结构化文档生成

#### 4. AI聊天
- 豆包AI风格界面
- 图片上传支持
- 知识库集成

#### 5. 文档处理
- 飞书文档上传
- Markdown导出
- 历史记录管理

## 启动方式

### Windows
```bash
start.bat
```

### 或直接运行
```bash
python main.py
```

## 配置说明

配置文件保存在项目根目录：
- `config.json` - 应用配置
- `history.json` - 历史记录
- `ai_chat_config.json` - AI聊天配置

创建 `.env` 文件配置环境变量：
```
VOLCENGINE_API_KEY=your_api_key
BAIDU_OCR_API_KEY=your_key
BAIDU_OCR_SECRET_KEY=your_secret
```

## 依赖要求

- Python 3.8+
- tkinter
- requests
- whisper
- yt-dlp

## 代码完整性保证

- ✅ `video_gui.py` 代码完整保留，未做任何修改
- ✅ 仅调整文件位置，符合标准Agent框架
- ✅ 所有功能保持原样

## 框架参考

- [LangChain Agent Framework](https://docs.langchain.com)
- [OpenAI Agents Python](https://github.com/openai/openai-agents-python)
- [CSDN Agent项目架构设计](https://blog.csdn.net/weixin_53236070/article/details/159155889)
