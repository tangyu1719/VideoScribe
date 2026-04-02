# SuperBizAgent Web端

SuperBizAgent的Web前端实现，使用React + TypeScript + Tailwind CSS构建。

## 功能特性

- 📹 **视频下载** - 支持抖音、B站、小红书等平台视频下载和转文字
- 🤖 **AI对话** - 豆包AI风格聊天界面，支持流式响应和图片上传
- 📚 **知识库管理** - RAG知识库文档管理和语义搜索
- 🔗 **链接分析** - 小红书图文/视频内容提取和分析
- 📱 **多端适配** - 响应式设计，支持桌面和移动端
- 🌙 **深色模式** - 支持浅色/深色主题切换

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **路由**: React Router
- **UI组件**: Radix UI
- **图标**: Lucide React
- **HTTP客户端**: Axios

## 项目结构

```
web/
├── src/
│   ├── components/
│   │   ├── ui/           # 基础UI组件
│   │   └── Layout.tsx    # 布局组件
│   ├── pages/            # 页面组件
│   │   ├── VideoDownload.tsx
│   │   ├── AIChat.tsx
│   │   ├── KnowledgeBase.tsx
│   │   ├── LinkAnalyzer.tsx
│   │   └── Settings.tsx
│   ├── services/         # API服务
│   │   ├── api.ts
│   │   ├── video.ts
│   │   ├── chat.ts
│   │   ├── knowledgeBase.ts
│   │   └── linkAnalyzer.ts
│   ├── store/            # 状态管理
│   │   ├── useAppStore.ts
│   │   ├── useVideoStore.ts
│   │   └── useChatStore.ts
│   ├── types/            # TypeScript类型
│   │   └── index.ts
│   ├── lib/              # 工具函数
│   │   └── utils.ts
│   ├── hooks/            # 自定义Hooks
│   │   └── useToast.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── index.html
```

## 安装依赖

```bash
cd web
npm install
```

## 开发运行

```bash
# 启动前端开发服务器
npm run dev

# 启动后端API服务（在另一个终端）
python web_api.py
```

前端默认运行在 http://localhost:3000
后端API默认运行在 http://localhost:8000

## 构建部署

```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## API接口

后端API提供以下接口：

### 视频任务
- `GET /api/video/tasks` - 获取任务列表
- `POST /api/video/tasks` - 创建任务
- `GET /api/video/tasks/{id}` - 获取任务详情
- `DELETE /api/video/tasks/{id}` - 删除任务
- `POST /api/video/tasks/{id}/retry` - 重试任务

### AI对话
- `GET /api/chat/sessions` - 获取会话列表
- `POST /api/chat/sessions` - 创建会话
- `POST /api/chat/sessions/{id}/messages` - 发送消息
- `GET /api/chat/sessions/{id}/messages/stream` - 流式发送消息

### 知识库
- `GET /api/kb/stats` - 获取统计信息
- `GET /api/kb/files` - 获取文件列表
- `POST /api/kb/files` - 上传文件
- `GET /api/kb/search` - 搜索知识库

### 链接分析
- `POST /api/link/analyze` - 分析链接
- `GET /api/link/history` - 获取历史记录

## 与现有代码集成

Web端通过`web_api.py`与现有的Python代码集成：

1. **视频处理** - 复用现有的视频下载和转文字逻辑
2. **AI对话** - 复用现有的火山引擎API调用
3. **知识库** - 复用现有的RAG知识库实现
4. **链接分析** - 复用现有的链接分析模块

## 注意事项

1. 确保后端API服务已启动
2. 配置正确的API密钥
3. 生产环境需要配置CORS和安全性设置
