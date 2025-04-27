"""
AgentForge Contracts - 共享契约库

这个包包含AgentForge平台所有服务共享的契约定义，
包括数据模型、接口规范和通用工具。
"""

from . import core
from . import monitoring
from . import schemas
from . import utils
from shared_contracts.utils.version import get_version

__version__ = "0.1.0"

__all__ = [
    "core",
    "monitoring",
    "schemas",
    "utils",
    "__version__",
]
