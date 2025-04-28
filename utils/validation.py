"""Validation utilities for Pydantic models and other data types...."""

import re
import uuid
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class ValidationResult(Generic[T]):
    """Result of a model validation operation...."""

    def __init__(
        self,
        valid: bool,
        model: Optional[T] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        self.valid = valid
        self.model = model
        self.errors = errors or []

    def __bool__(self) -> bool:
        """Allow direct boolean checking of the validation result...."""
        return self.valid

    def __str__(self) -> str:
        """String representation of the validation result...."""
        if self.valid:
            return f"ValidationResult(valid=True, model={type(self.model).__name__})"
        return f"ValidationResult(valid=False, errors={self.errors})"


def validate_model(
    model_class: Type[T],
    data: Union[Dict[str, Any], BaseModel],
    strict: bool = False,
) -> ValidationResult[T]:
    """
    Validate data against a Pydantic model.

    Args:
        model_class: Pydantic model class to validate against
        data: Data to validate (dictionary or another model)
        strict: Whether to use strict validation

    Returns:
        ValidationResult indicating success or failure with error details
 ..."""
    try:
        # Handle case where data is already a Pydantic model
        if isinstance(data, BaseModel):
            data = data.model_dump()

        # Perform validation
        if strict:
            model = model_class.model_validate(data, strict=True)
        else:
            model = model_class.model_validate(data)

        return ValidationResult(valid=True, model=model)
    except ValidationError as e:
        try:
            # 处理Pydantic v2的ValidationError
            errors = []
            for err in e.errors():
                error_info = {
                    "type": err.get('type', 'unknown_error'),
                    "loc": err.get('loc', []),
                    "msg": err.get('msg', str(err))
                }
                errors.append(error_info)
            return ValidationResult(valid=False, errors=errors)
        except (AttributeError, TypeError):
            # 如果结构不匹配，回退到简单错误处理
            return ValidationResult(
                valid=False,
                errors=[{"type": "validation_error", "msg": str(e)}]
            )
    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[{"type": type(e).__name__, "msg": str(e)}],
        )


def validate_models(
    model_mapping: Dict[str, Dict[Type[BaseModel], Dict[str, Any]]],
    strict: bool = False,
) -> Dict[str, Dict[str, ValidationResult]]:
    """
    Validate multiple models at once.

    Args:
        model_mapping: A mapping from group names to model classes and data
                      e.g. {"group1": {ModelA: data1, ModelB: data2}}
        strict: Whether to use strict validation

    Returns:
        A nested dictionary of validation results by group and model
 ..."""
    results = {}

    for group_name, models in model_mapping.items():
        group_results = {}
        for model_class, data in models.items():
            model_name = model_class.__name__
            group_results[model_name] = validate_model(model_class, data, strict=strict)

        results[group_name] = group_results

    return results


def validate_uuid(value: Any) -> bool:
    """
    Validate that a value is a valid UUID.

    Args:
        value: Value to validate

    Returns:
        Whether the value is a valid UUID
 ..."""
    if isinstance(value, uuid.UUID):
        return True

    if not isinstance(value, str):
        return False

    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_model_type(
    value: Any,
    allowed_types: Set[str],
    case_sensitive: bool = False,
) -> bool:
    """
    Validate that a model type is in the set of allowed types.

    Args:
        value: Model type value to validate
        allowed_types: Set of allowed model types
        case_sensitive: Whether comparison is case-sensitive

    Returns:
        Whether the value is a valid model type
 ..."""
    if not isinstance(value, str):
        return False

    if case_sensitive:
        return value in allowed_types
    else:
        return value.lower() in {t.lower() for t in allowed_types}


def validate_service_name(
    value: Any,
    allowed_services: Optional[Set[str]] = None,
    pattern: str = r"^[a-z][a-z0-9-]{2,49}$",
) -> bool:
    """
    Validate a service name.

    Args:
        value: Service name to validate
        allowed_services: Optional set of allowed service names
        pattern: Regex pattern for valid service names

    Returns:
        Whether the value is a valid service name
 ..."""
    if not isinstance(value, str):
        return False

    # Check against pattern
    if not re.match(pattern, value):
        return False

    # Check against allowed services if provided
    if allowed_services is not None:
        return value in allowed_services

    return True


def validate_enum_value(value: Any, enum_class: Type[Enum], case_sensitive: bool = False) -> bool:
    """
    Validate that a value is a valid enum value.

    Args:
        value: Value to validate
        enum_class: Enum class to validate against
        case_sensitive: Whether name matching is case-sensitive

    Returns:
        Whether the value is a valid enum value
 ..."""
    # 处理None值
    if value is None:
        return False
        
    # 处理Enum实例
    if isinstance(value, enum_class):
        return True
    
    # 准备枚举值列表（用于值匹配）
    enum_values = [member.value for member in enum_class]
        
    try:
        # 首先尝试直接值匹配（这不受case_sensitive影响）
        if value in enum_values:
            return True
        
        # 处理枚举名称匹配（受case_sensitive影响）
        if isinstance(value, str):
            # 区分大小写的名称匹配
            try:
                enum_class[value]  # 尝试通过名称查找
                return True
            except KeyError:
                pass
                
            # 不区分大小写的名称匹配（仅当case_sensitive=False时）
            if not case_sensitive:
                value_lower = value.lower()
                for member in enum_class:
                    if member.name.lower() == value_lower:
                        return True

        # 最后尝试通过构造函数匹配
        enum_class(value)
        return True
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def validate_string_length(
    value: Any,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> bool:
    """
    Validate that a string has a valid length.

    Args:
        value: String to validate
        min_length: Optional minimum length
        max_length: Optional maximum length

    Returns:
        Whether the string has a valid length
 ..."""
    if not isinstance(value, str):
        return False

    if min_length is not None and len(value) < min_length:
        return False

    if max_length is not None and len(value) > max_length:
        return False

    return True


def validate_numeric_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> bool:
    """
    Validate that a number is within a valid range.

    Args:
        value: Number to validate
        min_value: Optional minimum value
        max_value: Optional maximum value
        exclusive_min: Whether the minimum is exclusive
        exclusive_max: Whether the maximum is exclusive

    Returns:
        Whether the number is within the valid range
 ..."""
    if not isinstance(value, (int, float)):
        return False

    if min_value is not None:
        if exclusive_min and value <= min_value:
            return False
        elif not exclusive_min and value < min_value:
            return False

    if max_value is not None:
        if exclusive_max and value >= max_value:
            return False
        elif not exclusive_max and value > max_value:
            return False

    return True


def validate_with_validators(
    value: Any,
    validators: List[Callable[[Any], bool]],
    all_must_pass: bool = True,
) -> bool:
    """
    Validate a value using multiple validators.

    Args:
        value: Value to validate
        validators: List of validator functions
        all_must_pass: Whether all validators must pass (AND) or just one (OR)

    Returns:
        Whether the value is valid according to the validators
 ..."""
    if not validators:
        return True

    results = [validator(value) for validator in validators]

    if all_must_pass:
        return all(results)
    else:
        return any(results)


def validate_dict_schema(
    value: Any,
    required_keys: Optional[Set[str]] = None,
    optional_keys: Optional[Set[str]] = None,
    allow_extra_keys: bool = False,
    key_validators: Optional[Dict[str, Callable[[Any], bool]]] = None,
) -> Union[bool, List[str]]:
    """
    Validate a dictionary against a schema.

    Args:
        value: Dictionary to validate
        required_keys: Set of required keys
        optional_keys: Set of optional keys
        allow_extra_keys: Whether to allow extra keys not in required or optional
        key_validators: Dictionary of validators for specific keys

    Returns:
        True if valid, or a list of error messages
 ..."""
    if not isinstance(value, dict):
        return ["Value must be a dictionary"]

    errors = []

    # Check required keys
    if required_keys:
        for key in required_keys:
            if key not in value:
                errors.append(f"Missing required key: {key}")

    # Check for extra keys
    if not allow_extra_keys and (required_keys or optional_keys):
        allowed_keys = set()
        if required_keys:
            allowed_keys.update(required_keys)
        if optional_keys:
            allowed_keys.update(optional_keys)

        extra_keys = set(value.keys()) - allowed_keys
        if extra_keys:
            errors.append(f"Extra keys not allowed: {', '.join(extra_keys)}")

    # Validate values
    if key_validators:
        for key, validator in key_validators.items():
            if key in value:
                if not validator(value[key]):
                    errors.append(f"Invalid value for key: {key}")

    if errors:
        return errors

    return True
