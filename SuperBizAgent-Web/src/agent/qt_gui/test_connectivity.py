#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 GUI 连通性测试
测试所有页面和组件是否正常加载
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from qt_gui.theme import Theme, get_stylesheet
from qt_gui.main_window import MainWindow
from qt_gui.video_page import VideoProcessingPage
from qt_gui.chat_page import ChatPage
from qt_gui.document_page import DocumentPage


def test_theme():
    """测试主题加载"""
    print("测试 1: 加载浅色主题...")
    Theme.use_light_theme()
    assert Theme.current["bg_main"] == "#f5f6f7"
    print("✓ 浅色主题加载成功")
    
    print("测试 2: 加载深色主题...")
    Theme.use_dark_theme()
    assert Theme.current["bg_main"] == "#1a1a1e"
    print("✓ 深色主题加载成功")
    
    print("测试 3: 生成样式表...")
    qss = get_stylesheet("light")
    assert len(qss) > 100
    print(f"✓ 样式表生成成功（{len(qss)} 字符）")
    
    return True


def test_pages():
    """测试页面加载"""
    print("\n测试 4: 创建 QApplication...")
    app = QApplication(sys.argv)
    print("✓ QApplication 创建成功")
    
    print("测试 5: 加载视频处理页面...")
    video_page = VideoProcessingPage()
    assert video_page.link_input is not None
    assert video_page.start_btn is not None
    print("✓ 视频处理页面加载成功")
    
    print("测试 6: 加载 AI 问答页面...")
    chat_page = ChatPage()
    assert chat_page.session_list is not None
    assert chat_page.input_box is not None
    print("✓ AI 问答页面加载成功")
    
    print("测试 7: 加载文档处理页面...")
    doc_page = DocumentPage()
    assert doc_page.file_list is not None
    assert doc_page.btn_start is not None
    print("✓ 文档处理页面加载成功")
    
    return True


def test_main_window():
    """测试主窗口"""
    print("\n测试 8: 创建主窗口...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = MainWindow()
    assert window.nav_bar is not None
    assert window.stack is not None
    assert window.stack.count() == 3
    print("✓ 主窗口创建成功")
    
    print("测试 9: 测试页面切换...")
    window.nav_bar.set_current_page(0)
    assert window.stack.currentIndex() == 0
    window.nav_bar.set_current_page(1)
    assert window.stack.currentIndex() == 1
    window.nav_bar.set_current_page(2)
    assert window.stack.currentIndex() == 2
    print("✓ 页面切换功能正常")
    
    return True


def test_backend_interfaces():
    """测试后端接口连通性"""
    print("\n测试 10: 测试后端模块导入...")
    
    try:
        from video_downloader import VideoDownloader
        print("✓ video_downloader 模块可导入")
    except ImportError as e:
        print(f"⚠ video_downloader 导入失败：{e}")
    
    try:
        from multimodal_tool import WhisperModel
        print("✓ multimodal_tool 模块可导入")
    except ImportError as e:
        print(f"⚠ multimodal_tool 导入失败：{e}")
    
    try:
        from link_analyzer import LinkAnalyzer
        print("✓ link_analyzer 模块可导入")
    except ImportError as e:
        print(f"⚠ link_analyzer 导入失败：{e}")
    
    try:
        from kb_manager import get_knowledge_base
        print("✓ kb_manager 模块可导入")
    except ImportError as e:
        print(f"⚠ kb_manager 导入失败：{e}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("PySide6 GUI 连通性测试")
    print("=" * 60)
    
    success = True
    
    try:
        success &= test_theme()
        success &= test_pages()
        success &= test_main_window()
        success &= test_backend_interfaces()
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
