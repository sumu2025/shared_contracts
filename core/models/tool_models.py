"""Tool-related data models...."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from .base_models import BaseModel


class ToolParameterType(str, Enum):
    """Tool parameter type enumeration...."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"


class ToolParameter(BaseModel):
    """Definition of a tool parameter...."""

    name: str = Field(..., description="Parameter name", min_length=1)
    description: str = Field(..., description="Parameter description", min_length=1)
    type: ToolParameterType = Field(..., description="Parameter type")
    required: bool = Field(
        default=True, description="Whether this parameter is required"
    )
    default: Optional[Any] = Field(None, description="Default value for this parameter")
    enum: Optional[List[Any]] = Field(None, description="Enumeration of allowed values")
    min_value: Optional[Union[int, float]] = Field(
        None, description="Minimum value (for INTEGER and NUMBER types)"
    )
    max_value: Optional[Union[int, float]] = Field(
        None, description="Maximum value (for INTEGER and NUMBER types)"
    )
    min_length: Optional[int] = Field(
        None, description="Minimum length (for STRING and ARRAY types)"
    )
    max_length: Optional[int] = Field(
        None, description="Maximum length (for STRING and ARRAY types)"
    )
    pattern: Optional[str] = Field(None, description="Regex pattern (for STRING type)")

    @model_validator(mode="after")
    def validate_parameter(self) -> "ToolParameter":
        """Validate parameter constraints based on type...."""
        if self.type in (ToolParameterType.INTEGER, ToolParameterType.NUMBER):
            if self.min_value is not None and self.max_value is not None:
                if self.min_value > self.max_value:
                    raise ValueError("min_value cannot be greater than max_value")

        if self.type in (ToolParameterType.STRING, ToolParameterType.ARRAY):
            if self.min_length is not None and self.max_length is not None:
                if self.min_length > self.max_length:
                    raise ValueError("min_length cannot be greater than max_length")

        # Validate that enum values match the parameter type
        if self.enum is not None:
            for value in self.enum:
                if self.type == ToolParameterType.STRING and not isinstance(value, str):
                    raise ValueError(f"Enum value {value} is not a string")
                elif self.type == ToolParameterType.INTEGER and not isinstance(
                    value, int
                ):
                    raise ValueError(f"Enum value {value} is not an integer")
                elif self.type == ToolParameterType.NUMBER and not isinstance(
                    value, (int, float)
                ):
                    raise ValueError(f"Enum value {value} is not a number")
                elif self.type == ToolParameterType.BOOLEAN and not isinstance(
                    value, bool
                ):
                    raise ValueError(f"Enum value {value} is not a boolean")

        return self


class ToolParameters(BaseModel):
    """Container for tool parameters with JSON schema generation...."""

    parameters: Dict[str, ToolParameter] = Field(
        default_factory=dict, description="Map of parameter names to definitions"
    )

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format...."""
        properties = {}
        required = []

        for param_name, param in self.parameters.items():
            prop = {
                "type": param.type.value,
                "description": param.description,
            }

            if param.enum is not None:
                prop["enum"] = param.enum

            if param.type in (ToolParameterType.INTEGER, ToolParameterType.NUMBER):
                if param.min_value is not None:
                    prop["minimum"] = param.min_value
                if param.max_value is not None:
                    prop["maximum"] = param.max_value

            if param.type == ToolParameterType.STRING:
                if param.min_length is not None:
                    prop["minLength"] = param.min_length
                if param.max_length is not None:
                    prop["maxLength"] = param.max_length
                if param.pattern is not None:
                    prop["pattern"] = param.pattern

            if param.type == ToolParameterType.ARRAY:
                if param.min_length is not None:
                    prop["minItems"] = param.min_length
                if param.max_length is not None:
                    prop["maxItems"] = param.max_length

            properties[param_name] = prop

            if param.required:
                required.append(param_name)

        schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        return schema


class ToolDefinition(BaseModel):
    """Definition of a tool...."""

    tool_id: str = Field(..., description="Unique tool identifier", min_length=1)
    name: str = Field(..., description="Tool name", min_length=1)
    description: str = Field(..., description="Tool description", min_length=1)
    parameters: ToolParameters = Field(
        default_factory=ToolParameters, description="Parameters for this tool"
    )
    version: str = Field(default="1.0.0", description="Tool version", min_length=1)
    is_streaming: bool = Field(
        default=False, description="Whether this tool supports streaming"
    )
    requires_auth: bool = Field(
        default=False, description="Whether this tool requires authentication"
    )
    is_stateful: bool = Field(
        default=False,
        description="Whether this tool maintains state between invocations",
    )


class ToolResultStatus(str, Enum):
    """Tool result status enumeration...."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # For streaming results


class ToolResult(BaseModel):
    """Result of a tool execution...."""

    tool_id: str = Field(..., description="Tool identifier")
    request_id: UUID = Field(..., description="Request identifier")
    status: ToolResultStatus = Field(..., description="Status of the execution")
    data: Optional[Any] = Field(
        None, description="Result data (for SUCCESS and PARTIAL)"
    )
    error: Optional[str] = Field(None, description="Error message (for ERROR)")
    is_final: bool = Field(
        default=True, description="Whether this is the final result (for streaming)"
    )

    @model_validator(mode="after")
    def validate_result(self) -> "ToolResult":
        """Validate result fields based on status...."""
        if self.status == ToolResultStatus.SUCCESS and self.data is None:
            raise ValueError("Data must be present when status is SUCCESS")
        if self.status == ToolResultStatus.ERROR and self.error is None:
            raise ValueError("Error must be present when status is ERROR")
        return self

    model_config = ConfigDict(json_schema_mode="validation")
