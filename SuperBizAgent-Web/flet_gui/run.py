#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flet GUI 启动脚本
"""

import flet as ft
from main_app import main

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets",
    )
