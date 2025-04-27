"""
Message type enumeration for the platform.
"""

from enum import Enum, auto


class MessageType(str, Enum):
    """
    Enumeration of message types for communication within the system.

    This enum is used to categorize messages exchanged between services,
    agents, and users, enabling proper routing and handling.
    """

    # User-related messages
    USER_MESSAGE = "user_message"  # Message from a user to an agent
    USER_FEEDBACK = "user_feedback"  # Feedback from a user about an agent response

    # Agent-related messages
    AGENT_MESSAGE = "agent_message"  # Message from an agent to a user
    AGENT_THINKING = "agent_thinking"  # Agent's internal reasoning process
    AGENT_TOOL_REQUEST = "agent_tool_request"  # Agent's request to use a tool
    AGENT_TOOL_RESPONSE = "agent_tool_response"  # Response from a tool to an agent

    # System-related messages
    SYSTEM_PROMPT = "system_prompt"  # System prompt for an agent
    SYSTEM_NOTIFICATION = (
        "system_notification"  # System notification to a user or agent
    )
    SYSTEM_ERROR = "system_error"  # System error message

    # Function calling related messages
    FUNCTION_CALL = "function_call"  # Function call request
    FUNCTION_RESULT = "function_result"  # Function call result

    # Chat-related messages
    CHAT_START = "chat_start"  # Start of a chat session
    CHAT_END = "chat_end"  # End of a chat session

    # Monitoring-related messages
    MONITORING_EVENT = "monitoring_event"  # Event for monitoring purposes
    MONITORING_METRIC = "monitoring_metric"  # Metric for monitoring purposes
    MONITORING_LOG = "monitoring_log"  # Log for monitoring purposes

    # Other types
    CUSTOM = "custom"  # Custom message type
    UNKNOWN = "unknown"  # Unknown message type
