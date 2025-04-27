"""
API schema definitions for the Agent Service.

These schemas define the API contracts for the Agent Service,
including endpoints for agent management and interaction.
"""

from typing import Dict, Any

# Schema for creating an agent
CREATE_AGENT_SCHEMA = {
    "type": "object",
    "required": ["name", "description", "model_id", "system_prompt"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "Agent name",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Agent description",
        },
        "capabilities": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "conversation",
                    "planning",
                    "memory",
                    "tool_use",
                    "multi_agent",
                    "code_execution",
                ],
            },
            "description": "Agent capabilities",
        },
        "model_id": {
            "type": "string",
            "description": "ID of the model to use for this agent",
        },
        "max_tokens_per_response": {
            "type": "integer",
            "minimum": 1,
            "maximum": 32000,
            "default": 1024,
            "description": "Maximum tokens per response",
        },
        "temperature": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 2.0,
            "default": 0.7,
            "description": "Temperature for sampling",
        },
        "system_prompt": {
            "type": "string",
            "minLength": 1,
            "maxLength": 10000,
            "description": "System prompt for the agent",
        },
        "tools": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "description": "Tool IDs this agent can use",
        },
        "metadata": {
            "$ref": "#/components/schemas/Metadata",
        },
    },
    "additionalProperties": False,
}

# Schema for updating an agent
UPDATE_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "Agent name",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Agent description",
        },
        "capabilities": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "conversation",
                    "planning",
                    "memory",
                    "tool_use",
                    "multi_agent",
                    "code_execution",
                ],
            },
            "description": "Agent capabilities",
        },
        "model_id": {
            "type": "string",
            "description": "ID of the model to use for this agent",
        },
        "max_tokens_per_response": {
            "type": "integer",
            "minimum": 1,
            "maximum": 32000,
            "description": "Maximum tokens per response",
        },
        "temperature": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 2.0,
            "description": "Temperature for sampling",
        },
        "system_prompt": {
            "type": "string",
            "minLength": 1,
            "maxLength": 10000,
            "description": "System prompt for the agent",
        },
        "tools": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "description": "Tool IDs this agent can use",
        },
        "metadata": {
            "$ref": "#/components/schemas/Metadata",
        },
    },
    "additionalProperties": False,
}

# Schema for sending a message to an agent
SEND_MESSAGE_SCHEMA = {
    "type": "object",
    "required": ["message"],
    "properties": {
        "message": {
            "type": "string",
            "minLength": 1,
            "description": "Message content",
        },
        "conversation_id": {
            "type": "string",
            "format": "uuid",
            "description": "Optional conversation ID, if continuing an existing conversation",
        },
        "stream": {
            "type": "boolean",
            "default": False,
            "description": "Whether to stream the response",
        },
        "options": {
            "type": "object",
            "description": "Additional options for the message",
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}

# Collection of all agent API schemas
AGENT_API_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "CreateAgent": CREATE_AGENT_SCHEMA,
    "UpdateAgent": UPDATE_AGENT_SCHEMA,
    "SendMessage": SEND_MESSAGE_SCHEMA,
}
