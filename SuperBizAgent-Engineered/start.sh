#!/bin/bash

echo "========================================"
echo " SuperBizAgent - AI 文档处理与知识库系统"
echo " 工程化版本 v2.0"
echo "========================================"
echo

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请确保Python已安装"
    exit 1
fi

echo "[1/3] Python环境检查通过"

# 检查依赖
echo "[2/3] 检查依赖..."
python3 -c "import tkinter" 2>/dev/null || echo "[警告] 未找到tkinter，GUI功能可能无法使用"

echo "[3/3] 启动应用程序..."
echo

# 启动应用
python3 main.py

if [ $? -ne 0 ]; then
    echo
    echo "[错误] 应用程序异常退出"
    read -p "按回车键退出..."
fi
