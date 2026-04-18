#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flet GUI Web模式启动脚本 - 使用新版API
无需下载桌面环境，直接在浏览器中运行
"""

import flet as ft
from main_app import main

if __name__ == "__main__":
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        port=8550,
    )
