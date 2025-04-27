"""
Utility functions and classes for the AgentForge platform.
"""

# Schema utilities
from .schema_utils import (
    extract_json_schema,
    generate_openapi_schema,
    get_referenced_schemas,
    json_to_schema,
    merge_schemas,
    schema_to_json,
    validate_schema,
)

# Serialization utilities
from .serialization import (
    CustomJSONEncoder,
    bytes_to_data,
    data_to_bytes,
    deep_dict_update,
    dict_to_model,
    json_to_model,
    model_to_dict,
    model_to_json,
    serialize_with_custom_handlers,
)

# Timing utilities
from .timing import async_timed, measure_execution_time, timed

# Validation utilities
from .validation import (
    ValidationResult,
    validate_dict_schema,
    validate_enum_value,
    validate_model,
    validate_model_type,
    validate_models,
    validate_numeric_range,
    validate_service_name,
    validate_string_length,
    validate_uuid,
    validate_with_validators,
)

# Version utilities
from .version import compare_versions, get_version, is_compatible_version

__all__ = [
    # Validation
    "validate_model",
    "validate_models",
    "ValidationResult",
    "validate_uuid",
    "validate_model_type",
    "validate_service_name",
    "validate_enum_value",
    "validate_string_length",
    "validate_numeric_range",
    "validate_with_validators",
    "validate_dict_schema",
    # Serialization
    "model_to_dict",
    "dict_to_model",
    "model_to_json",
    "json_to_model",
    "deep_dict_update",
    "serialize_with_custom_handlers",
    "data_to_bytes",
    "bytes_to_data",
    "CustomJSONEncoder",
    # Schema
    "extract_json_schema",
    "merge_schemas",
    "validate_schema",
    "generate_openapi_schema",
    "schema_to_json",
    "json_to_schema",
    "get_referenced_schemas",
    # Version
    "get_version",
    "compare_versions",
    "is_compatible_version",
    # Timing
    "timed",
    "measure_execution_time",
    "async_timed",
]
