"""
Service-related constants.
"""

# Service names
AGENT_SERVICE_NAME = "agent-service"
MODEL_SERVICE_NAME = "model-service"
TOOL_SERVICE_NAME = "tool-service"

# Default configuration
DEFAULT_SERVICE_PORT = 8000
DEFAULT_REQUEST_TIMEOUT = 30  # seconds

# HTTP status codes with descriptions
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    503: "Service Unavailable",
}
