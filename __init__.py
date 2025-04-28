"""
AgentForge共享契约库

此包包含AgentForge平台的服务间接口定义和共享工具。

这个库可以通过两种方式导入：
1. 作为已安装的包：`from shared_contracts import ...`
2. 从项目中直接导入：`from core import ...`, `from monitoring import ...` 等

导入策略在各个模块中都有实现，通过尝试绝对导入并在失败时回退到相对导入。
..."""

__version__ = "0.1.0"

# Ensure shared_contracts package is importable as a top-level module
try:
    # Make the shared_contracts package available for import
    import sys
    import os
    
    # Add the current directory to Python path if not already there
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
except Exception:
    # Silently ignore errors in path setup
    pass
