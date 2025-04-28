#!/usr/bin/env python3
"""开发模式安装脚本。

此脚本用于在开发环境中以编辑模式安装当前包，使得可以直接从项目根目录导入。
..."""

import os
import subprocess
import sys

def main():
    """执行开发模式安装。..."""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 使用pip安装当前目录（编辑模式）
    print("以开发模式安装共享契约库...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", current_dir]
        )
        print("安装成功！现在可以使用 'from shared_contracts import ...' 导入模块")
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
