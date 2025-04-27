"""
Base models for the AgentForge platform.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, field_validator, model_validator

T = TypeVar("T")


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""
    
    model_config = ConfigDict(
        extra="forbid",  # Forbid extra attributes
        validate_assignment=True,  # Validate when attributes are assigned
        arbitrary_types_allowed=True,  # Allow arbitrary types (needed for some edge cases)
        populate_by_name=True,  # Allow populating by field name
    )


class BaseRequest(BaseModel):
    """Base class for all request models."""
    
    request_id: UUID = Field(default_factory=uuid4, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp in UTC")


class BaseResponse(BaseModel, Generic[T]):
    """Base class for all response models."""
    
    request_id: UUID = Field(..., description="Request identifier this response is for")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp in UTC")
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data, only present on success")
    error: Optional[str] = Field(None, description="Error message, only present on failure")
    
    @model_validator(mode="after")
    def validate_success_data_error(self) -> "BaseResponse":
        """Validate that data is present on success and error on failure."""
        if self.success and self.data is None:
            raise ValueError("Data must be present when success is True")
        if not self.success and self.error is None:
            raise ValueError("Error must be present when success is False")
        return self
