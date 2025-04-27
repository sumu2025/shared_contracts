"""
Utility functions for the AgentForge platform.

This module re-exports utility functions from the shared_contracts package.
"""

# Schema工具
from shared_contracts.utils.schema_utils import (
    extract_json_schema,
    merge_schemas,
    validate_schema,
    generate_openapi_schema,
    schema_to_json,
    json_to_schema,
    get_referenced_schemas,
)

# 验证工具
from shared_contracts.utils.validation import (
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

# 序列化工具
from shared_contracts.utils.serialization import (
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

# 计时工具
from shared_contracts.utils.timing import (
    timed,
    measure_execution_time,
    async_timed,
    retry_with_backoff,
    rate_limit,
)

# 版本工具
from shared_contracts.utils.version import (
    get_version,
    compare_versions,
    is_compatible_version,
)

__all__ = [
    # Schema工具
    "extract_json_schema",
    "merge_schemas",
    "validate_schema",
    "generate_openapi_schema",
    "schema_to_json",
    "json_to_schema",
    "get_referenced_schemas",
    
    # 验证工具
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
    
    # 序列化工具
    "model_to_dict",
    "dict_to_model",
    "model_to_json",
    "json_to_model",
    "deep_dict_update",
    "serialize_with_custom_handlers",
    "data_to_bytes",
    "bytes_to_data",
    "CustomJSONEncoder",
    
    # 计时工具
    "timed",
    "measure_execution_time",
    "async_timed",
    "retry_with_backoff",
    "rate_limit",
    
    # 版本工具
    "get_version",
    "compare_versions",
    "is_compatible_version",
]
