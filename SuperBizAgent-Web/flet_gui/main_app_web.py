#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperBizAgent Flet GUI - Web模式启动
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from main_app import SuperBizAgentApp


def main(page: ft.Page):
    """应用入口"""
    SuperBizAgentApp(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
