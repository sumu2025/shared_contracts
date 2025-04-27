"""
AI Model-related data models.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from .base_models import BaseModel


class ModelProvider(str, Enum):
    """AI model provider enumeration."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    MISTRAL = "mistral"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelType(str, Enum):
    """AI model type enumeration."""

    COMPLETION = "completion"
    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class ModelCapability(BaseModel):
    """Capabilities of an AI model."""

    supports_streaming: bool = Field(
        default=False, description="Whether the model supports streaming"
    )
    supports_function_calling: bool = Field(
        default=False, description="Whether the model supports function calling"
    )
    supports_json_mode: bool = Field(
        default=False, description="Whether the model supports JSON mode"
    )
    supports_vision: bool = Field(
        default=False, description="Whether the model supports vision"
    )
    max_tokens: int = Field(
        ..., description="Maximum tokens supported by the model", ge=1
    )
    input_cost_per_token: float = Field(
        default=0.0, description="Cost per input token in USD", ge=0.0
    )
    output_cost_per_token: float = Field(
        default=0.0, description="Cost per output token in USD", ge=0.0
    )


class ModelConfig(BaseModel):
    """Configuration for an AI model."""

    model_id: str = Field(..., description="Unique model identifier", min_length=1)
    provider: ModelProvider = Field(..., description="Model provider")
    model_type: ModelType = Field(..., description="Model type")
    display_name: str = Field(
        ..., description="Human-readable model name", min_length=1
    )
    capabilities: ModelCapability = Field(..., description="Model capabilities")
    provider_model_id: str = Field(
        ..., description="Model identifier used by the provider", min_length=1
    )
    api_key_env_var: str = Field(
        ..., description="Environment variable name for the API key", min_length=1
    )
    api_endpoint: Optional[str] = Field(
        None, description="Custom API endpoint (for non-standard deployments)"
    )
    timeout: int = Field(
        default=30, description="Request timeout in seconds", ge=1, le=300
    )
    retry_count: int = Field(
        default=3, description="Number of retries on failure", ge=0, le=10
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """Validate model ID format."""
        v = v.strip()
        if not v:
            raise ValueError("Model ID cannot be empty")
        if " " in v:
            raise ValueError("Model ID cannot contain spaces")
        return v


class ModelResponse(BaseModel):
    """Response from an AI model."""

    model_id: str = Field(..., description="Model identifier")
    request_id: UUID = Field(..., description="Request identifier")
    content: str = Field(..., description="Response content")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    finish_reason: Optional[str] = Field(
        None, description="Reason why the model finished generating"
    )
    raw_response: Optional[Dict[str, Any]] = Field(
        None, description="Raw response from the provider"
    )
