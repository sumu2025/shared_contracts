"""
Common schema definitions used across all services.

These schemas define common structures like pagination, error responses,
and other shared patterns used in API contracts.
"""

from typing import Any, Dict

# Schema for pagination parameters
PAGINATION_SCHEMA = {
    "type": "object",
    "properties": {
        "offset": {
            "type": "integer",
            "minimum": 0,
            "default": 0,
            "description": "Number of items to skip",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 1000,
            "default": 100,
            "description": "Maximum number of items to return",
        },
    },
    "additionalProperties": False,
}

# Schema for standard error response
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["request_id", "timestamp", "success", "error"],
    "properties": {
        "request_id": {
            "type": "string",
            "format": "uuid",
            "description": "Request identifier",
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "Response timestamp in UTC",
        },
        "success": {
            "type": "boolean",
            "enum": [False],
            "description": "Whether the request was successful",
        },
        "error": {
            "type": "string",
            "description": "Error message",
        },
        "error_code": {
            "type": "string",
            "description": "Error code for programmatic handling",
        },
        "error_details": {
            "type": "object",
            "description": "Additional error details",
        },
    },
    "additionalProperties": False,
}

# Schema for standard success response with a data field
SUCCESS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["request_id", "timestamp", "success", "data"],
    "properties": {
        "request_id": {
            "type": "string",
            "format": "uuid",
            "description": "Request identifier",
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "Response timestamp in UTC",
        },
        "success": {
            "type": "boolean",
            "enum": [True],
            "description": "Whether the request was successful",
        },
        "data": {
            "description": "Response data",
        },
    },
    "additionalProperties": False,
}

# Schema for metadata object that can be attached to various resources
METADATA_SCHEMA = {
    "type": "object",
    "description": "Additional metadata as key-value pairs",
    "additionalProperties": {
        "type": "string",
    },
}

# Collection of all common schemas
COMMON_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "Pagination": PAGINATION_SCHEMA,
    "ErrorResponse": ERROR_RESPONSE_SCHEMA,
    "SuccessResponse": SUCCESS_RESPONSE_SCHEMA,
    "Metadata": METADATA_SCHEMA,
}
