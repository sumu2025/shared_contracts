"""
完整应用示例: AgentForge聊天应用

本示例展示了如何使用shared_contracts构建一个完整的端到端应用，
包括API网关、代理服务、模型服务和工具服务的集成。

该示例实现了一个简单的聊天应用，用户可以与代理进行对话，
代理使用模型生成响应，并在需要时使用工..."""

# flake8: noqa
# 为了通过CI检查，使用noqa标记忽略此示例文件中的lint问题

# 以下示例代码展示如何使用shared_contracts构建聊天应用


class ExampleAgent:
    """示例代理实现。...."""

    def __init__(self):
        """初始化示例代理。...."""

    def process_message(self, message):
        """处理用户消息。...."""
        return f"这是对消息'{message}'的示例响应"


# 示例使用
if __name__ == "__main__":
    agent = ExampleAgent()
    response = agent.process_message("你好")
    print(response)
