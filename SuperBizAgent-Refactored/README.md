# SuperBizAgent - 视频转文字处理工具 (GUI)

## 工程化版本

基于 `video_gui.py` 重构的工程项目，保持原有功能不变，优化代码组织结构。

## 原始功能

### 1. 视频下载
- 支持抖音、小红书等平台视频下载
- 自动去水印
- 多线程下载

### 2. 语音转文字
- 使用Whisper模型
- 支持多语言识别
- 自动分段处理

### 3. AI分析
- 火山引擎API集成
- 自动总结视频内容
- 生成结构化文档

### 4. AI聊天
- 豆包AI风格界面
- 支持图片上传
- 知识库集成

### 5. 文档处理
- 飞书文档上传
- Markdown导出
- 历史记录管理

## 项目结构

```
SuperBizAgent-Refactored/
├── main.py                      # 主入口文件
├── start.bat                    # Windows启动脚本
├── README.md                    # 项目说明
├── src/                         # 源代码目录
│   ├── gui/                    # GUI界面模块
│   │   └── video_gui.py        # 主GUI文件（原始）
│   ├── video/                  # 视频处理模块
│   │   └── video_downloader.py # 视频下载器
│   ├── chat/                   # AI聊天模块
│   │   └── ai_chat_system.py   # AI聊天系统
│   ├── core/                   # 核心工具模块
│   └── utils/                  # 工具函数模块
├── config/                      # 配置文件目录
└── data/                        # 数据目录
    ├── videos/                 # 视频下载目录
    ├── output/                 # 输出文件目录
    └── chat_sessions/          # 聊天会话目录
```

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

## 依赖要求

- Python 3.8+
- tkinter
- requests
- whisper
- yt-dlp

## 注意事项

1. 保持 `video_gui.py` 原始功能不变
2. 仅调整代码组织结构
3. 所有配置和数据路径保持不变
