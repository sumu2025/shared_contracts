"""
LogFire集成测试脚本

此脚本测试LogFire集成是否正常工作，使用环境变量中的写入令牌。
"""

import os
import time
import sys
from shared_contracts.monitoring import (
    configure_monitor,
    ServiceComponent,
    EventType,
    LogLevel,
)

def test_logfire():
    """测试LogFire集成"""
    # 检查环境变量
    token = os.environ.get("LOGFIRE_WRITE_TOKEN")
    if not token:
        print("错误: 未设置LOGFIRE_WRITE_TOKEN环境变量")
        print("请使用以下命令设置:")
        print("export LOGFIRE_WRITE_TOKEN='您的LogFire写入令牌'")
        return False
    
    print(f"找到LOGFIRE_WRITE_TOKEN环境变量")
    
    try:
        # 设置监控客户端
        print("正在初始化LogFire客户端...")
        monitor = configure_monitor(
            service_name="agentforge-test",
            api_key=token,
            project_id="agentforge-test",  # 添加必要的project_id参数
            environment="development",
            min_log_level=LogLevel.DEBUG,
        )
        
        # 发送测试日志
        print("发送测试日志...")
        test_id = str(int(time.time()))
        monitor.info(
            message=f"LogFire测试消息 (ID: {test_id})",
            component=ServiceComponent.SYSTEM,
            event_type=EventType.SYSTEM,
            test_id=test_id,
        )
        
        # 发送测试指标
        print("发送测试指标...")
        monitor.record_metric(
            metric_name="test_connection",
            value=1.0,
            tags={"test_id": test_id},
        )
        
        # 刷新确保发送
        print("刷新日志缓冲区...")
        monitor.flush()
        
        print("=== 测试完成 ===")
        print("成功: 测试日志和指标已发送到LogFire")
        print(f"测试ID: {test_id}")
        print("请登录LogFire控制台确认日志是否正确接收")
        return True
    
    except Exception as e:
        print(f"错误: LogFire测试失败: {e}")
        return False
    finally:
        if 'monitor' in locals():
            print("关闭LogFire客户端...")
            monitor.shutdown()

if __name__ == "__main__":
    print("=== LogFire集成测试 ===")
    success = test_logfire()
    sys.exit(0 if success else 1)
