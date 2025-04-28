#!/usr/bin/env python3
"""
设置和配置LogFire监控。

此脚本用于在开发环境或CI环境中设置LogFire监控。
"""

import os
import sys
import argparse
import logging
from typing import Optional

from shared_contracts.monitoring.implementations.logfire_config import LogFireConfig
from shared_contracts.monitoring.implementations.logfire_client import LogFireClient
from shared_contracts.monitoring.utils.logger_utils import configure_monitor


def setup_logfire(
    service_name: str,
    environment: str = "development",
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    log_level: str = "INFO",
) -> None:
    """
    设置LogFire监控。

    Args:
        service_name: 服务名称
        environment: 运行环境
        api_key: LogFire API密钥
        project_id: LogFire项目ID
        log_level: 日志级别
    """
    # 优先使用参数，其次从环境变量获取
    api_key = api_key or os.environ.get("LOGFIRE_WRITE_TOKEN")
    project_id = project_id or os.environ.get("LOGFIRE_PROJECT_ID", "")

    if not api_key:
        logging.warning("未提供LogFire API密钥，跳过监控设置")
        return

    # 确定日志级别
    from shared_contracts.monitoring.monitor_types import LogLevel

    log_level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
    }
    level = log_level_map.get(log_level.upper(), LogLevel.INFO)

    try:
        # 创建配置
        config = LogFireConfig(
            api_key=api_key,
            project_id=project_id,
            service_name=service_name,
            environment=environment,
            min_log_level=level,
            enable_metadata=True,
            additional_metadata={
                "setup_info": {
                    "script": os.path.basename(__file__),
                    "python_version": sys.version,
                },
            },
        )

        # 配置监控
        monitor = configure_monitor(
            service_name=service_name,
            api_key=api_key,
            project_id=project_id,
            environment=environment,
            min_log_level=level,
        )

        logging.info(
            f"LogFire监控已配置: 服务={service_name}, 环境={environment}, 日志级别={log_level}"
        )

        # 发送初始化事件
        from shared_contracts.monitoring.monitor_types import EventType, ServiceComponent

        monitor.info(
            message=f"LogFire监控已初始化: {service_name}",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            setup_info={
                "script": os.path.basename(__file__),
                "python_version": sys.version,
                "environment": environment,
                "log_level": log_level,
            },
        )

        return monitor

    except Exception as e:
        logging.error(f"LogFire监控配置失败: {e}")
        return None


def main():
    """命令行入口点。"""
    parser = argparse.ArgumentParser(description="设置LogFire监控")
    parser.add_argument(
        "--service-name",
        default="shared_contracts",
        help="服务名称",
    )
    parser.add_argument(
        "--environment",
        default=os.environ.get("ENVIRONMENT", "development"),
        help="运行环境",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="LogFire API密钥 (默认从LOGFIRE_WRITE_TOKEN环境变量获取)",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="LogFire项目ID (默认从LOGFIRE_PROJECT_ID环境变量获取)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志",
    )

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 设置监控
    monitor = setup_logfire(
        service_name=args.service_name,
        environment=args.environment,
        api_key=args.api_key,
        project_id=args.project_id,
        log_level=args.log_level,
    )

    if monitor:
        print(f"LogFire监控已成功配置: {args.service_name}/{args.environment}")
    else:
        print("LogFire监控配置失败，请检查参数和日志")


if __name__ == "__main__":
    main()
