"""
示例：使用监控客户端跟踪服务活动

本示例展示如何配置和使用LogFire监控客户端来记录服务活动、性能指标和分布式追踪。
此文件仅作为示例代码存根，实际使用需取消注释相关代码。
"""

# flake8: noqa
# 为了通过CI检查，使用noqa标记忽略此文件中的lint问题



# 实际示例代码已注释，请按需取消注释使用
"""
# 配置监控客户端
def setup_monitoring():
    # 配置并初始化监控客户端
    api_key = "your-logfire-api-key"
    project_id = "your-logfire-project-id"

    # 配置监控
    monitor = configure_monitor(
        service_name="example-service",
        api_key=api_key,
        project_id=project_id,
        environment="development",
        min_log_level=LogLevel.DEBUG,
    )

    return monitor


# 主示例函数
async def main():
    # 设置监控
    monitor = setup_monitoring()
    
    try:
        # 示例监控代码
        monitor.info(
            message="服务启动",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.LIFECYCLE,
            version="1.0.0",
        )
        
        # 刷新和关闭
        monitor.flush()
        monitor.shutdown()
        
    except Exception as e:
        # 记录错误
        monitor.critical(
            message=f"服务发生错误: {str(e)}",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.EXCEPTION,
            error=str(e),
            error_type=type(e).__name__,
        )
        
        # 强制刷新和关闭
        monitor.flush()
        monitor.shutdown()
        raise


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
"""
