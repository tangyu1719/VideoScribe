#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Tool GUI - PySide6版本
视频处理工具图形界面
"""

from video_tool_gui.main_app import MainApp
from video_tool_gui.video_page import VideoProcessingPage
from video_tool_gui.chat_page import ChatPage
from video_tool_gui.document_page import DocumentPage
from video_tool_gui.theme import Theme, StyleSheet, get_global_stylesheet

__all__ = [
    'MainApp',
    'VideoProcessingPage',
    'ChatPage',
    'DocumentPage',
    'Theme',
    'StyleSheet',
    'get_global_stylesheet'
]

__version__ = '2.0.0'
