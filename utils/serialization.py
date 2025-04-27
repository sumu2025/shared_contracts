"""
Serialization utilities for converting between different data formats.

This module provides functions for serializing and deserializing data between
different formats, with special handling for Pydantic models and common data types.
"""

import datetime
import json
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder with extended type support."""

    def default(self, obj: Any) -> Any:
        """Handle special types during JSON encoding."""
        # Handle datetime
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()

        # Handle UUID
        if isinstance(obj, uuid.UUID):
            return str(obj)

        # Handle enums
        if isinstance(obj, Enum):
            return obj.value

        # Handle sets
        if isinstance(obj, set):
            return list(obj)

        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            return obj.model_dump()

        # Handle bytes
        if isinstance(obj, bytes):
            return obj.decode("utf-8")

        # Let the base class handle it (or raise TypeError)
        return super().default(obj)


def model_to_dict(
    model: BaseModel,
    exclude: Optional[List[str]] = None,
    exclude_none: bool = False,
    by_alias: bool = False,
) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a dictionary.

    Args:
        model: Pydantic model to convert
        exclude: Optional list of fields to exclude
        exclude_none: Whether to exclude None values
        by_alias: Whether to use field aliases

    Returns:
        Dictionary representation of the model
    """
    return model.model_dump(
        exclude=set(exclude) if exclude else None,
        exclude_none=exclude_none,
        by_alias=by_alias,
    )


def dict_to_model(
    data: Dict[str, Any],
    model_class: Type[T],
    strict: bool = False,
) -> T:
    """
    Convert a dictionary to a Pydantic model.

    Args:
        data: Dictionary to convert
        model_class: Pydantic model class
        strict: Whether to use strict validation

    Returns:
        Pydantic model instance

    Raises:
        ValidationError: If the data does not match the model
    """
    return model_class.model_validate(data, strict=strict)


def model_to_json(
    model: BaseModel,
    exclude: Optional[List[str]] = None,
    exclude_none: bool = False,
    by_alias: bool = False,
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
) -> str:
    """
    Convert a Pydantic model to a JSON string.

    Args:
        model: Pydantic model to convert
        exclude: Optional list of fields to exclude
        exclude_none: Whether to exclude None values
        by_alias: Whether to use field aliases
        indent: Optional JSON indentation
        ensure_ascii: Whether to escape non-ASCII characters

    Returns:
        JSON string representation of the model
    """
    dict_data = model_to_dict(
        model=model,
        exclude=exclude,
        exclude_none=exclude_none,
        by_alias=by_alias,
    )

    return json.dumps(
        dict_data,
        cls=CustomJSONEncoder,
        indent=indent,
        ensure_ascii=ensure_ascii,
    )


def json_to_model(
    json_str: str,
    model_class: Type[T],
    strict: bool = False,
) -> T:
    """
    Convert a JSON string to a Pydantic model.

    Args:
        json_str: JSON string to convert
        model_class: Pydantic model class
        strict: Whether to use strict validation

    Returns:
        Pydantic model instance

    Raises:
        ValidationError: If the JSON data does not match the model
        json.JSONDecodeError: If the JSON is invalid
    """
    data = json.loads(json_str)
    return dict_to_model(data, model_class, strict=strict)


def deep_dict_update(
    base_dict: Dict[str, Any],
    update_dict: Dict[str, Any],
    overwrite_lists: bool = True,
) -> Dict[str, Any]:
    """
    Deep update a dictionary with another dictionary.

    Args:
        base_dict: Dictionary to update
        update_dict: Dictionary with updates
        overwrite_lists: Whether to overwrite lists or extend them

    Returns:
        Updated dictionary
    """
    result = base_dict.copy()

    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively update dictionaries
            result[key] = deep_dict_update(result[key], value, overwrite_lists)
        elif (
            key in result
            and isinstance(result[key], list)
            and isinstance(value, list)
            and not overwrite_lists
        ):
            # Extend lists
            result[key] = result[key] + value
        else:
            # Simple overwrite
            result[key] = value

    return result


def serialize_with_custom_handlers(
    data: Any,
    custom_handlers: Dict[Type, Callable[[Any], Any]] = None,
    default_handler: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """
    Serialize an object with custom type handlers.

    Args:
        data: Data to serialize
        custom_handlers: Dictionary mapping types to handler functions
        default_handler: Optional default handler for unhandled types

    Returns:
        Serialized data

    Raises:
        TypeError: If an object can't be serialized and no default_handler is provided
    """
    handlers = custom_handlers or {}

    def _serialize(obj: Any) -> Any:
        # Handle None
        if obj is None:
            return None

        # Handle simple types
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Try custom handlers
        for cls, handler in handlers.items():
            if isinstance(obj, cls):
                return handler(obj)

        # Handle common types
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()

        if isinstance(obj, uuid.UUID):
            return str(obj)

        if isinstance(obj, Enum):
            return obj.value

        if isinstance(obj, BaseModel):
            return {k: _serialize(v) for k, v in model_to_dict(obj).items()}

        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple, set)):
            return [_serialize(item) for item in obj]

        if isinstance(obj, bytes):
            return obj.decode("utf-8")

        # Use default handler if provided
        if default_handler:
            return default_handler(obj)

        # Raise error for unhandled types
        raise TypeError(f"Object of type {type(obj).__name__} is not serializable")

    return _serialize(data)


def data_to_bytes(
    data: Any,
    encoding: str = "utf-8",
) -> bytes:
    """
    Convert data to bytes.

    Args:
        data: Data to convert (str, dict, Pydantic model, etc.)
        encoding: String encoding to use

    Returns:
        Bytes representation of the data
    """
    if isinstance(data, bytes):
        return data

    if isinstance(data, str):
        return data.encode(encoding)

    if isinstance(data, BaseModel):
        json_str = model_to_json(data)
        return json_str.encode(encoding)

    # Convert to JSON for other types
    json_str = json.dumps(data, cls=CustomJSONEncoder)
    return json_str.encode(encoding)


def bytes_to_data(
    data_bytes: bytes,
    target_type: Optional[Type] = None,
    encoding: str = "utf-8",
) -> Any:
    """
    Convert bytes to data.

    Args:
        data_bytes: Bytes to convert
        target_type: Optional target type (e.g., dict, a Pydantic model class)
        encoding: String encoding to use

    Returns:
        Converted data

    Raises:
        ValueError: If conversion to the target type fails
    """
    # Decode to string
    str_data = data_bytes.decode(encoding)

    # If target is string, we're done
    if target_type is str:
        return str_data

    # Try to parse as JSON
    try:
        dict_data = json.loads(str_data)

        # If target is dict or not specified, return the parsed JSON
        if target_type is None or target_type is dict:
            return dict_data

        # If target is a Pydantic model, convert to it
        if issubclass(target_type, BaseModel):
            return dict_to_model(dict_data, target_type)

        # For other types, try direct conversion
        return target_type(dict_data)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        # If JSON parsing fails and no target type is specified, return the string
        if target_type is None:
            return str_data

        # Otherwise, try direct conversion of the string
        try:
            return target_type(str_data)
        except (TypeError, ValueError):
            raise ValueError(
                f"Could not convert bytes to {target_type.__name__}: {str(e)}"
            )
