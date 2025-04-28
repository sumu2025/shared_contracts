"""
API schema definitions for the Tool Service.

These schemas define the API contracts for the Tool Service,
including endpoints for tool management and executio..."""

from typing import Any, Dict

# Schema for registering a tool
REGISTER_TOOL_SCHEMA = {
    "type": "object",
    "required": ["tool_id", "name", "description"],
    "properties": {
        "tool_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$",
            "description": "Unique tool identifier",
        },
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Tool name",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Tool description",
        },
        "parameters": {
            "type": "object",
            "properties": {
                "parameters": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["name", "description", "type"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Parameter name",
                            },
                            "description": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Parameter description",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "string",
                                    "integer",
                                    "number",
                                    "boolean",
                                    "object",
                                    "array",
                                    "null",
                                ],
                                "description": "Parameter type",
                            },
                            "required": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether this parameter is required",
                            },
                            "default": {
                                "description": "Default value for this parameter",
                            },
                            "enum": {
                                "type": "array",
                                "description": "Enumeration of allowed values",
                            },
                            "min_value": {
                                "type": ["integer", "number", "null"],
                                "description": "Minimum value (for INTEGER and NUMBER types)",  # noqa: E501
                            },
                            "max_value": {
                                "type": ["integer", "number", "null"],
                                "description": "Maximum value (for INTEGER and NUMBER types)",  # noqa: E501
                            },
                            "min_length": {
                                "type": ["integer", "null"],
                                "minimum": 0,
                                "description": "Minimum length (for STRING and ARRAY types)",  # noqa: E501
                            },
                            "max_length": {
                                "type": ["integer", "null"],
                                "minimum": 0,
                                "description": "Maximum length (for STRING and ARRAY types)",  # noqa: E501
                            },
                            "pattern": {
                                "type": ["string", "null"],
                                "description": "Regex pattern (for STRING type)",
                            },
                        },
                        "additionalProperties": False,
                    },
                },
            },
            "description": "Parameters for this tool",
        },
        "version": {
            "type": "string",
            "minLength": 1,
            "default": "1.0.0",
            "description": "Tool version",
        },
        "is_streaming": {
            "type": "boolean",
            "default": False,
            "description": "Whether this tool supports streaming",
        },
        "requires_auth": {
            "type": "boolean",
            "default": False,
            "description": "Whether this tool requires authentication",
        },
        "is_stateful": {
            "type": "boolean",
            "default": False,
            "description": "Whether this tool maintains state between invocations",
        },
    },
    "additionalProperties": False,
}

# Schema for updating a tool
UPDATE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Tool name",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Tool description",
        },
        "parameters": {
            "type": "object",
            "properties": {
                "parameters": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["name", "description", "type"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Parameter name",
                            },
                            "description": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Parameter description",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "string",
                                    "integer",
                                    "number",
                                    "boolean",
                                    "object",
                                    "array",
                                    "null",
                                ],
                                "description": "Parameter type",
                            },
                            "required": {
                                "type": "boolean",
                                "description": "Whether this parameter is required",
                            },
                            "default": {
                                "description": "Default value for this parameter",
                            },
                            "enum": {
                                "type": "array",
                                "description": "Enumeration of allowed values",
                            },
                            "min_value": {
                                "type": ["integer", "number", "null"],
                                "description": "Minimum value (for INTEGER and NUMBER types)",  # noqa: E501
                            },
                            "max_value": {
                                "type": ["integer", "number", "null"],
                                "description": "Maximum value (for INTEGER and NUMBER types)",  # noqa: E501
                            },
                            "min_length": {
                                "type": ["integer", "null"],
                                "minimum": 0,
                                "description": "Minimum length (for STRING and ARRAY types)",  # noqa: E501
                            },
                            "max_length": {
                                "type": ["integer", "null"],
                                "minimum": 0,
                                "description": "Maximum length (for STRING and ARRAY types)",  # noqa: E501
                            },
                            "pattern": {
                                "type": ["string", "null"],
                                "description": "Regex pattern (for STRING type)",
                            },
                        },
                        "additionalProperties": False,
                    },
                },
            },
            "description": "Parameters for this tool",
        },
        "version": {
            "type": "string",
            "minLength": 1,
            "description": "Tool version",
        },
        "is_streaming": {
            "type": "boolean",
            "description": "Whether this tool supports streaming",
        },
        "requires_auth": {
            "type": "boolean",
            "description": "Whether this tool requires authentication",
        },
        "is_stateful": {
            "type": "boolean",
            "description": "Whether this tool maintains state between invocations",
        },
    },
    "additionalProperties": False,
}

# Schema for executing a tool
EXECUTE_TOOL_SCHEMA = {
    "type": "object",
    "required": ["parameters"],
    "properties": {
        "parameters": {
            "type": "object",
            "description": "Tool parameters",
            "additionalProperties": True,
        },
        "stream": {
            "type": "boolean",
            "default": False,
            "description": "Whether to stream the result",
        },
        "context": {
            "type": "object",
            "description": "Additional execution context",
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}

# Collection of all tool API schemas
TOOL_API_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "RegisterTool": REGISTER_TOOL_SCHEMA,
    "UpdateTool": UPDATE_TOOL_SCHEMA,
    "ExecuteTool": EXECUTE_TOOL_SCHEMA,
}
