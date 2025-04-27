"""
LogFire监控设置模块

此模块提供从环境变量初始化LogFire监控的函数。
"""

import os
import logging
from typing import Optional

from .monitor_interface import MonitorInterface
from .monitor_types import LogLevel
from .implementations.logfire_client import LogFireClient
from .implementations.logfire_config import LogFireConfig

logger = logging.getLogger(__name__)

def setup_from_env(
    service_name: str,
    env_var: str = "LOGFIRE_WRITE_TOKEN",
    environment: str = None,
    min_log_level: LogLevel = LogLevel.INFO,
) -> Optional[MonitorInterface]:
    """
    从环境变量设置LogFire监控。
    
    Args:
        service_name: 服务名称
        env_var: 包含LogFire令牌的环境变量名
        environment: 部署环境，默认从ENVIRONMENT环境变量获取或使用"development"
        min_log_level: 最小日志级别
        
    Returns:
        配置好的监控接口，如果环境变量未设置则返回None
    """
    # 从环境变量获取令牌
    token = os.environ.get(env_var)
    if not token:
        logger.warning(f"未找到环境变量 {env_var}，跳过LogFire配置")
        return None
    
    # 确定环境
    if environment is None:
        environment = os.environ.get("ENVIRONMENT", "development")
    
    try:
        # 创建配置
        config = LogFireConfig(
            api_key=token,
            service_name=service_name,
            environment=environment,
            min_log_level=min_log_level,
        )
        
        # 创建客户端
        client = LogFireClient(config)
        logger.info(f"LogFire监控已初始化: 服务={service_name}, 环境={environment}")
        return client
    
    except Exception as e:
        logger.error(f"LogFire配置错误: {e}")
        return None
