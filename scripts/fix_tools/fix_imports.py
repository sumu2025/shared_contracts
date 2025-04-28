#!/usr/bin/env python3
"""
修复导入顺序和格式的工具

此脚本使用isort自动修复项目中的所有Python文件的导入问..."""

import os
import sys
from pathlib import Path


def main():
    """运行导入修复工具。...."""
    try:
        import isort
    except ImportError:
        print("未安装isort。请运行：pip install isort")
        sys.exit(1)

    # 获取项目根目录
    root_dir = Path(__file__).parents[2].absolute()
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        paths = [os.path.abspath(p) for p in sys.argv[1:]]
    else:
        # 默认处理整个项目
        paths = [str(root_dir)]
    
    # 设置isort配置文件路径
    config_file = root_dir / "pyproject.toml"
    
    # 打印开始信息
    print(f"正在修复导入问题，配置文件: {config_file}")
    
    # 对所有路径应用isort
    for path in paths:
        print(f"处理: {path}")
        try:
            # 使用isort API修复导入
            isort.api.sort_file(path, config=str(config_file), verbose=True)
        except Exception as e:
            print(f"处理文件 {path} 时出错: {e}")
    
    print("导入修复完成！")


if __name__ == "__main__":
    main()
