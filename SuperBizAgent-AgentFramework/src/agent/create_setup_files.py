#!/usr/bin/env python3
"""
创建项目初始化脚本
"""
from pathlib import Path

PROJECT_ROOT = Path(r"f:\java\AIOPS\SuperBizAgent_v2")

# 创建 init_all.py
init_all_py = """#!/usr/bin/env python3
\"\"\"
项目初始化脚本
- 创建必要目录
- 初始化数据库
- 检查依赖
\"\"\"
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def create_directories():
    \"\"\"创建必要的目录\"\"\"
    dirs = [
        'data/knowledge_base',
        'data/sessions',
        'data/uploads',
        'logs',
        'tests',
        'scripts',
        'docs'
    ]
    
    print("1. 创建必要目录...")
    for dir_path in dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {dir_path}")

def check_dependencies():
    \"\"\"检查 Python 依赖\"\"\"
    print("\\n2. 检查 Python 依赖...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'chromadb',
        'sqlalchemy',
        'pymysql',
        'requests'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ✗ {package} (未安装)")
    
    if missing:
        print(f"\\n请运行：pip install -r requirements.txt")
        return False
    return True

def init_database():
    \"\"\"初始化数据库\"\"\"
    print("\\n3. 初始化数据库...")
    try:
        from utils.init_database import init_all_tables
        init_all_tables()
        print("   ✓ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"   ✗ 数据库初始化失败：{e}")
        print(f"   请确保 MariaDB 服务已启动并正确配置")
        return False

def main():
    print("="*60)
    print("SuperBizAgent v2.0 - 项目初始化")
    print("="*60)
    
    # 1. 创建目录
    create_directories()
    
    # 2. 检查依赖
    if not check_dependencies():
        print("\\n⚠ 依赖检查失败，请先安装依赖")
        return
    
    # 3. 初始化数据库
    if not init_database():
        print("\\n⚠ 数据库初始化失败，但可稍后手动执行")
    
    print("\\n" + "="*60)
    print("✅ 项目初始化完成！")
    print("="*60)
    print("\\n下一步:")
    print("1. 编辑 configs/config.py 配置数据库和 API 密钥")
    print("2. 运行：python main.py 启动服务")
    print("3. 或运行：start.bat 同时启动前后端")

if __name__ == "__main__":
    main()
"""

(PROJECT_ROOT / 'init_all.py').write_text(init_all_py, encoding='utf-8')
print("✓ 创建 init_all.py")

# 创建 setup.py
setup_py = """#!/usr/bin/env python3
\"\"\"
SuperBizAgent - 安装脚本
\"\"\"
from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

# 读取依赖
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = [
    line.strip()
    for line in requirements_path.read_text().splitlines()
    if line.strip() and not line.startswith('#')
]

setup(
    name="superbizagent",
    version="2.0.0",
    author="SuperBizAgent Team",
    description="AI 驱动的智能业务助手 - 基于 Agentic RAG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tangyu1719/VideoScribe",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "superbizagent=main:main",
        ],
    },
)
"""

(PROJECT_ROOT / 'setup.py').write_text(setup_py, encoding='utf-8')
print("✓ 创建 setup.py")

# 创建 pyproject.toml
pyproject_toml = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "superbizagent"
version = "2.0.0"
description = "AI 驱动的智能业务助手 - 基于 Agentic RAG"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "SuperBizAgent Team"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "chromadb>=0.4.0",
    "sqlalchemy>=2.0.0",
    "pymysql>=1.1.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
superbizagent = "main:main"

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
"""

(PROJECT_ROOT / 'pyproject.toml').write_text(pyproject_toml, encoding='utf-8')
print("✓ 创建 pyproject.toml")

print("\\n✅ 所有安装配置文件创建完成！")
