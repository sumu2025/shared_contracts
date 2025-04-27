"""
Agent-related data models.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from .base_models import BaseModel


class AgentStatus(str, Enum):
    """Agent status enumeration."""

    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentCapability(str, Enum):
    """Agent capability enumeration."""

    CONVERSATION = "conversation"
    PLANNING = "planning"
    MEMORY = "memory"
    TOOL_USE = "tool_use"
    MULTI_AGENT = "multi_agent"
    CODE_EXECUTION = "code_execution"


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    agent_id: UUID = Field(default_factory=uuid4, description="Unique agent identifier")
    name: str = Field(..., description="Agent name", min_length=1, max_length=100)
    description: str = Field(
        ..., description="Agent description", min_length=1, max_length=500
    )
    capabilities: Set[AgentCapability] = Field(
        default_factory=set, description="Agent capabilities"
    )
    model_id: str = Field(..., description="ID of the model to use for this agent")
    max_tokens_per_response: int = Field(
        default=1024, description="Maximum tokens per response", ge=1, le=32000
    )
    temperature: float = Field(
        default=0.7, description="Temperature for sampling", ge=0.0, le=2.0
    )
    system_prompt: str = Field(
        ..., description="System prompt for the agent", min_length=1, max_length=10000
    )
    tools: List[str] = Field(
        default_factory=list, description="Tool IDs this agent can use"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate the agent name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or just whitespace")
        return v.strip()


class AgentState(BaseModel):
    """Agent state information."""

    agent_id: UUID = Field(..., description="Agent identifier")
    status: AgentStatus = Field(..., description="Current agent status")
    created_at: datetime = Field(..., description="When the agent was created")
    last_active: datetime = Field(..., description="When the agent was last active")
    conversation_count: int = Field(
        default=0, description="Number of conversations this agent has had", ge=0
    )
    error_message: Optional[str] = Field(
        None, description="Error message, only present when status is ERROR"
    )
    current_conversation_id: Optional[UUID] = Field(
        None, description="ID of the current conversation, if any"
    )
