"""
API schema definitions for the Model Service.

These schemas define the API contracts for the Model Service,
including endpoints for model management and inferenc..."""

from typing import Any, Dict

# Schema for registering a model
REGISTER_MODEL_SCHEMA = {
    "type": "object",
    "required": [
        "model_id",
        "provider",
        "model_type",
        "display_name",
        "capabilities",
        "provider_model_id",
        "api_key_env_var",
    ],
    "properties": {
        "model_id": {
            "type": "string",
            "description": "Unique model identifier",
            "pattern": "^[a-zA-Z0-9_-]+$",
        },
        "provider": {
            "type": "string",
            "enum": ["openai", "anthropic", "cohere", "mistral", "local", "custom"],
            "description": "Model provider",
        },
        "model_type": {
            "type": "string",
            "enum": ["completion", "chat", "embedding", "image", "multimodal"],
            "description": "Model type",
        },
        "display_name": {
            "type": "string",
            "description": "Human-readable model name",
        },
        "capabilities": {
            "type": "object",
            "required": ["max_tokens"],
            "properties": {
                "supports_streaming": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether the model supports streaming",
                },
                "supports_function_calling": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether the model supports function calling",
                },
                "supports_json_mode": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether the model supports JSON mode",
                },
                "supports_vision": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether the model supports vision",
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum tokens supported by the model",
                },
                "input_cost_per_token": {
                    "type": "number",
                    "minimum": 0.0,
                    "default": 0.0,
                    "description": "Cost per input token in USD",
                },
                "output_cost_per_token": {
                    "type": "number",
                    "minimum": 0.0,
                    "default": 0.0,
                    "description": "Cost per output token in USD",
                },
            },
            "additionalProperties": False,
        },
        "provider_model_id": {
            "type": "string",
            "description": "Model identifier used by the provider",
        },
        "api_key_env_var": {
            "type": "string",
            "description": "Environment variable name for the API key",
        },
        "api_endpoint": {
            "type": "string",
            "format": "uri",
            "description": "Custom API endpoint (for non-standard deployments)",
        },
        "timeout": {
            "type": "integer",
            "minimum": 1,
            "maximum": 300,
            "default": 30,
            "description": "Request timeout in seconds",
        },
        "retry_count": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
            "default": 3,
            "description": "Number of retries on failure",
        },
        "metadata": {
            "$ref": "#/components/schemas/Metadata",
        },
    },
    "additionalProperties": False,
}

# Schema for updating a model
UPDATE_MODEL_SCHEMA = {
    "type": "object",
    "properties": {
        "display_name": {
            "type": "string",
            "description": "Human-readable model name",
        },
        "capabilities": {
            "type": "object",
            "properties": {
                "supports_streaming": {
                    "type": "boolean",
                    "description": "Whether the model supports streaming",
                },
                "supports_function_calling": {
                    "type": "boolean",
                    "description": "Whether the model supports function calling",
                },
                "supports_json_mode": {
                    "type": "boolean",
                    "description": "Whether the model supports JSON mode",
                },
                "supports_vision": {
                    "type": "boolean",
                    "description": "Whether the model supports vision",
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum tokens supported by the model",
                },
                "input_cost_per_token": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Cost per input token in USD",
                },
                "output_cost_per_token": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Cost per output token in USD",
                },
            },
            "additionalProperties": False,
        },
        "provider_model_id": {
            "type": "string",
            "description": "Model identifier used by the provider",
        },
        "api_key_env_var": {
            "type": "string",
            "description": "Environment variable name for the API key",
        },
        "api_endpoint": {
            "type": "string",
            "format": "uri",
            "description": "Custom API endpoint (for non-standard deployments)",
        },
        "timeout": {
            "type": "integer",
            "minimum": 1,
            "maximum": 300,
            "description": "Request timeout in seconds",
        },
        "retry_count": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
            "description": "Number of retries on failure",
        },
        "metadata": {
            "$ref": "#/components/schemas/Metadata",
        },
    },
    "additionalProperties": False,
}

# Schema for generating a completion
GENERATE_COMPLETION_SCHEMA = {
    "type": "object",
    "required": ["prompt"],
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Prompt to complete",
        },
        "max_tokens": {
            "type": "integer",
            "minimum": 1,
            "description": "Maximum tokens to generate",
        },
        "temperature": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 2.0,
            "description": "Sampling temperature",
        },
        "stream": {
            "type": "boolean",
            "default": False,
            "description": "Whether to stream the response",
        },
        "options": {
            "type": "object",
            "description": "Additional model-specific options",
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}

# Collection of all model API schemas
MODEL_API_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "RegisterModel": REGISTER_MODEL_SCHEMA,
    "UpdateModel": UPDATE_MODEL_SCHEMA,
    "GenerateCompletion": GENERATE_COMPLETION_SCHEMA,
}
