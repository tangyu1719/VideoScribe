#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 GUI 模块
模仿豆包/DeskClaw 现代风格
"""

from qt_gui.theme import Theme, get_stylesheet
from qt_gui.main_window import MainWindow
from qt_gui.video_page import VideoProcessingPage
from qt_gui.chat_page import ChatPage
from qt_gui.document_page import DocumentPage
from qt_gui.app import main

__all__ = [
    'Theme',
    'get_stylesheet',
    'MainWindow',
    'VideoProcessingPage',
    'ChatPage',
    'DocumentPage',
    'main'
]

__version__ = '2.0.0'
