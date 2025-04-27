"""
Utility functions and classes for the AgentForge platform.
"""

# Validation utilities
from .validation import (
    validate_model,
    validate_models,
    ValidationResult,
    validate_uuid,
    validate_model_type,
    validate_service_name,
    validate_enum_value,
    validate_string_length,
    validate_numeric_range,
    validate_with_validators,
    validate_dict_schema,
)

# Serialization utilities
from .serialization import (
    model_to_dict,
    dict_to_model,
    model_to_json,
    json_to_model,
    deep_dict_update,
    serialize_with_custom_handlers,
    data_to_bytes,
    bytes_to_data,
    CustomJSONEncoder,
)

# Schema utilities
from .schema_utils import (
    extract_json_schema,
    merge_schemas,
    validate_schema,
    generate_openapi_schema,
    schema_to_json,
    json_to_schema,
    get_referenced_schemas,
)

# Version utilities
from .version import (
    get_version,
    compare_versions,
    is_compatible_version,
)

# Timing utilities
from .timing import (
    timed,
    measure_execution_time,
    async_timed,
)

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
