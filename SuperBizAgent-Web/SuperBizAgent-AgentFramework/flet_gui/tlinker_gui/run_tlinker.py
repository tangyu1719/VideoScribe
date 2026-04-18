#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLink GUI 启动脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'agent'))

def main():
    """主函数"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont
        from tlinker_app import MainWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("TLink")
        app.setApplicationVersion("2.0.0")
        
        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"错误: 缺少必要的依赖 - {e}")
        print("请安装 PySide6: pip install PySide6")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
