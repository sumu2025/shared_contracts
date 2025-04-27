"""
Error code constants used across the platform.
"""

# Dictionary of error codes with descriptions
ERROR_CODES = {
    # General errors (1xxx)
    "1000": "General service error",
    "1001": "Service unavailable",
    "1002": "Request timeout",
    "1003": "Rate limit exceeded",
    "1004": "Invalid request format",
    # Authentication and authorization errors (2xxx)
    "2000": "Authentication error",
    "2001": "Missing credentials",
    "2002": "Invalid credentials",
    "2003": "Insufficient permissions",
    "2004": "Authentication token expired",
    # Validation errors (3xxx)
    "3000": "Validation error",
    "3001": "Required field missing",
    "3002": "Invalid field value",
    "3003": "Invalid field type",
    "3004": "Field constraint violation",
    # Resource errors (4xxx)
    "4000": "Resource not found",
    "4001": "Resource already exists",
    "4002": "Resource locked",
    "4003": "Resource limit exceeded",
    # Agent-specific errors (5xxx)
    "5000": "Agent error",
    "5001": "Agent initialization failed",
    "5002": "Agent execution failed",
    "5003": "Agent communication error",
    "5004": "Agent timeout",
    # Model-specific errors (6xxx)
    "6000": "Model error",
    "6001": "Model not found",
    "6002": "Model initialization failed",
    "6003": "Model inference failed",
    "6004": "Model timeout",
    "6005": "Model content filtered",
    # Tool-specific errors (7xxx)
    "7000": "Tool error",
    "7001": "Tool not found",
    "7002": "Tool execution failed",
    "7003": "Tool parameter error",
    "7004": "Tool timeout",
    # External service errors (8xxx)
    "8000": "External service error",
    "8001": "External API error",
    "8002": "External resource not available",
    # Database errors (9xxx)
    "9000": "Database error",
    "9001": "Database connection error",
    "9002": "Database query error",
    "9003": "Database transaction error",
}
