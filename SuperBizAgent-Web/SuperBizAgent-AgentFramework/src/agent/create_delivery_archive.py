#!/usr/bin/env python3
"""
创建项目功能交付压缩包 - 仅包含核心功能代码
排除: 测试文件、数据文件、临时文件
"""
import os
import zipfile
from datetime import datetime

def create_delivery_archive():
    """创建精简的项目交付压缩包"""
    base_dir = r"f:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua"
    
    # 生成压缩包名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"SuperBizAgent_功能交付_v2.0_{timestamp}.zip"
    archive_path = os.path.join(os.path.dirname(base_dir), archive_name)
    
    print(f"开始创建交付压缩包: {archive_name}")
    print(f"源目录: {base_dir}")
    
    # ========== 核心功能文件列表 ==========
    core_files = [
        # === 知识库核心模块 ===
        'kb_manager.py',                    # 知识库管理器（服务启动初始化）
        'kb_manager_advanced.py',           # 高级知识库（Hybrid RAG + ChromaDB）
        'rag_manager_gui.py',               # 知识库GUI
        'react_agent.py',                   # ReAct Agent框架
        'mineru_processor.py',              # MinerU文档解析
        'document_processor.py',            # 文档处理器
        
        # === 聊天系统核心 ===
        'doubao_chat_page.py',              # 豆包聊天页面（含设置按钮、复制/导出/重试功能）
        'ai_chat_system.py',                # AI聊天系统
        'chat_memory_system.py',            # 聊天记忆系统
        
        # === 链接分析核心 ===
        'link_analyzer.py',                 # 链接分析器
        'unified_link_document_processor.py',  # 统一链接文档处理器
        'unified_link_document_gui.py',     # 统一链接文档GUI
        'wechat_article_processor.py',      # 微信文章处理器
        
        # === 视频下载核心 ===
        'video_gui.py',                     # 视频下载GUI
        'video_downloader.py',              # 视频下载器
        
        # === 多模态处理核心 ===
        'multimodal_gui.py',                # 多模态GUI
        'multimodal_tool.py',               # 多模态工具
        
        # === API和Web服务 ===
        'web_api.py',                       # Web API服务
        'web_api_stream.py',                # 流式Web API
        'config_api.py',                    # 配置API
        
        # === 数据库和存储 ===
        'db.py',                            # 数据库模块
        'data_store.py',                    # 数据存储
        'init_database.py',                 # 数据库初始化
        'graded_logging_schema.sql',        # 分级日志数据库Schema
        
        # === 日志和监控 ===
        'logging_system.py',                # 日志系统
        
        # === 配置文件 ===
        'requirements.txt',                 # 依赖配置
        'README.md',                        # 项目说明
        '.gitignore',                       # Git忽略配置
        
        # === 启动脚本 ===
        'start_web.bat',                    # 启动Web服务
        'run_video_gui.bat',                # 启动视频GUI
    ]
    
    # ========== Web前端核心文件 ==========
    web_files = [
        'web/package.json',
        'web/tsconfig.json',
        'web/vite.config.ts',
        'web/tailwind.config.js',
        'web/postcss.config.js',
        'web/index.html',
        'web/README.md',
        'web/src/main.tsx',
        'web/src/App.tsx',
        'web/src/index.css',
        'web/src/vite-env.d.ts',
        'web/src/lib/utils.ts',
        'web/src/types/index.ts',
        'web/src/hooks/useToast.ts',
        'web/src/store/useAppStore.ts',
        'web/src/store/useChatStore.ts',
        'web/src/store/useVideoStore.ts',
        'web/src/services/api.ts',
        'web/src/services/chat.ts',
        'web/src/services/config.ts',
        'web/src/services/knowledgeBase.ts',
        'web/src/services/linkAnalyzer.ts',
        'web/src/services/video.ts',
        'web/src/pages/AIChat.tsx',
        'web/src/pages/KnowledgeBase.tsx',
        'web/src/pages/LinkAnalyzer.tsx',
        'web/src/pages/Logs.tsx',
        'web/src/pages/Settings.tsx',
        'web/src/pages/VideoDownload.tsx',
        'web/src/components/Layout.tsx',
        'web/src/components/ui/Button.tsx',
        'web/src/components/ui/Card.tsx',
        'web/src/components/ui/Dialog.tsx',
        'web/src/components/ui/Input.tsx',
        'web/src/components/ui/Badge.tsx',
        'web/src/components/ui/Progress.tsx',
        'web/src/components/ui/ScrollArea.tsx',
        'web/src/components/ui/Select.tsx',
        'web/src/components/ui/Slider.tsx',
        'web/src/components/ui/Tabs.tsx',
    ]
    
    # 合并所有需要包含的文件
    all_files = core_files + web_files
    
    # 排除的模式（文件或目录）
    exclude_patterns = [
        'test_',            # 测试文件
        '_test.',
        'test.',
        'check_',
        'fix_',
        'verify_',
        'launch_',
        'build_kb_',        # 构建脚本
        'simple_',
        'extract_',         # 提取脚本（已整合到统一处理器）
        'agentic_rag',      # 旧版本Agentic RAG（已整合到react_agent）
        'rag_knowledge_base',  # 旧版本RAG（已整合到kb_manager）
        'chat_gui',         # 旧版本GUI
        'ai_chat_page',     # 旧版本
        'ai_api_config_gui', # 旧版本
        'link_analyzer_debug',
        'link_analyzer_tracer',
        'link_analyzer.py.backup',
        'video_gui_with_nav',
        'install_dependencies',
        'init_graded_logging_db',
        'redis_node_state_cache',
        'create_archive',
        '.json',            # 数据文件（保留配置类json）
        'knowledge_base/',  # 知识库数据目录
        'uploads/',         # 上传文件目录
        'wechat_images/',   # 图片目录
        'Pictures/',        # 图片目录
        '__pycache__',
        '.git',
        'node_modules',
        '.pyc',
        '.pyo',
    ]
    
    def should_include_file(filepath):
        """检查是否应该包含该文件"""
        # 获取相对路径
        rel_path = os.path.relpath(filepath, base_dir)
        
        # 检查是否在核心文件列表中
        if rel_path.replace('\\', '/') in all_files:
            return True
            
        # 检查排除模式
        for pattern in exclude_patterns:
            if pattern in filepath or pattern in rel_path:
                return False
        
        return False
    
    # 创建压缩包
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        total_size = 0
        included_files = []
        
        for root, dirs, files in os.walk(base_dir):
            # 过滤目录
            dirs[:] = [d for d in dirs if not any(p in d for p in ['__pycache__', '.git', 'node_modules', 'knowledge_base', 'uploads', 'wechat_images', 'Pictures'])]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # 检查是否应该包含
                if not should_include_file(file_path):
                    continue
                
                # 计算相对路径
                arcname = os.path.relpath(file_path, os.path.dirname(base_dir))
                
                try:
                    file_size = os.path.getsize(file_path)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    total_size += file_size
                    included_files.append(arcname)
                    
                    if file_count % 20 == 0:
                        print(f"  已添加 {file_count} 个文件...")
                        
                except Exception as e:
                    print(f"  跳过文件 {file_path}: {e}")
    
    # 获取压缩包大小
    archive_size = os.path.getsize(archive_path)
    archive_size_mb = archive_size / (1024 * 1024)
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n{'='*60}")
    print(f"✅ 交付压缩包创建成功!")
    print(f"{'='*60}")
    print(f"📦 文件名: {archive_name}")
    print(f"📍 路径: {archive_path}")
    print(f"📊 文件数量: {file_count}")
    print(f"📈 原始大小: {total_size_mb:.2f} MB")
    print(f"📉 压缩后大小: {archive_size_mb:.2f} MB")
    if total_size > 0:
        print(f"🎯 压缩率: {(1 - archive_size/total_size)*100:.1f}%")
    
    print(f"\n📋 包含的核心模块:")
    print(f"  • 知识库系统 (kb_manager, kb_manager_advanced, rag_manager_gui)")
    print(f"  • ReAct Agent框架 (react_agent)")
    print(f"  • 文档解析 (mineru_processor, document_processor)")
    print(f"  • 聊天系统 (doubao_chat_page, ai_chat_system)")
    print(f"  • 链接分析 (link_analyzer, unified_link_document_processor)")
    print(f"  • 视频下载 (video_gui, video_downloader)")
    print(f"  • 多模态处理 (multimodal_gui, multimodal_tool)")
    print(f"  • Web API服务 (web_api, web_api_stream)")
    print(f"  • 数据库模块 (db, data_store, init_database)")
    print(f"  • 前端Web应用 (React + TypeScript)")
    
    return archive_path, included_files

if __name__ == "__main__":
    archive_path, files = create_delivery_archive()
    print(f"\n✨ 压缩包已保存到: {archive_path}")
