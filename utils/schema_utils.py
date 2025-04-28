"""
Utilities for working with JSON schemas.

This module provides functions for extracting, merging, and validating JSON schemas,
which are used for API contracts and data validatio..."""

import copy
import json
from typing import Any, Dict, List, Optional, Set, Type, Union

import jsonschema
from pydantic import BaseModel


def extract_json_schema(
    model: Union[Type[BaseModel], BaseModel],
    by_alias: bool = True,
    ref_template: str = "#/components/schemas/{model}",
    exclude: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Extract a JSON schema from a Pydantic model.

    Args:
        model: Pydantic model class or instance
        by_alias: Whether to use field aliases
        ref_template: Template for references
        exclude: Fields to exclude

    Returns:
        JSON schema as a dictionary
 ..."""
    # Get model class if instance was provided
    model_class = model if isinstance(model, type) else model.__class__

    # Get schema from model
    schema = model_class.model_json_schema(
        by_alias=by_alias,
        ref_template=ref_template,
    )

    # Remove excluded fields
    if exclude and "properties" in schema:
        for field in exclude:
            if field in schema["properties"]:
                del schema["properties"][field]
                if "required" in schema and field in schema["required"]:
                    schema["required"].remove(field)

    return schema


def merge_schemas(
    schemas: List[Dict[str, Any]],
    merge_definitions: bool = True,
    merge_properties: bool = False,
) -> Dict[str, Any]:
    """
    Merge multiple JSON schemas.

    Args:
        schemas: List of schemas to merge
        merge_definitions: Whether to merge schema definitions
        merge_properties: Whether to merge schema properties (use with caution)

    Returns:
        Merged schema
 ..."""
    if not schemas:
        return {}

    if len(schemas) == 1:
        return copy.deepcopy(schemas[0])

    # Start with a copy of the first schema
    result = copy.deepcopy(schemas[0])

    # Merge remaining schemas
    for schema in schemas[1:]:
        # Merge definitions if present
        if merge_definitions and "definitions" in schema:
            if "definitions" not in result:
                result["definitions"] = {}

            for key, definition in schema["definitions"].items():
                if key not in result["definitions"]:
                    result["definitions"][key] = copy.deepcopy(definition)
                else:
                    # Recursively merge definitions of the same name
                    result["definitions"][key] = merge_schemas(
                        [result["definitions"][key], definition],
                        merge_definitions=merge_definitions,
                        merge_properties=merge_properties,
                    )

        # Merge properties if requested
        if merge_properties and "properties" in schema:
            if "properties" not in result:
                result["properties"] = {}

            for key, property_schema in schema["properties"].items():
                if key not in result["properties"]:
                    result["properties"][key] = copy.deepcopy(property_schema)
                else:
                    # Recursively merge properties of the same name
                    result["properties"][key] = merge_schemas(
                        [result["properties"][key], property_schema],
                        merge_definitions=merge_definitions,
                        merge_properties=merge_properties,
                    )

            # Merge required fields
            if "required" in schema:
                if "required" not in result:
                    result["required"] = []

                for field in schema["required"]:
                    if field not in result["required"]:
                        result["required"].append(field)

    return result


def validate_schema(
    instance: Any,
    schema: Dict[str, Any],
) -> List[str]:
    """
    Validate an instance against a JSON schema.

    Args:
        instance: Instance to validate
        schema: JSON schema

    Returns:
        List of validation errors, empty if valid
 ..."""
    errors = []

    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        # Collect all validation errors
        if e.path:
            path = ".".join(str(part) for part in e.path)
            errors.append(f"At {path}: {e.message}")
        else:
            errors.append(e.message)
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

    return errors


def generate_openapi_schema(
    title: str,
    version: str,
    description: str,
    schemas: Dict[str, Dict[str, Any]],
    paths: Optional[Dict[str, Any]] = None,
    servers: Optional[List[Dict[str, str]]] = None,
    tags: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Generate an OpenAPI schema from component schemas.

    Args:
        title: API title
        version: API version
        description: API description
        schemas: Component schemas
        paths: API paths
        servers: API servers
        tags: API tags

    Returns:
        OpenAPI schema
 ..."""
    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": version,
            "description": description,
        },
        "components": {
            "schemas": schemas,
        },
    }

    if paths:
        openapi["paths"] = paths
    else:
        openapi["paths"] = {}

    if servers:
        openapi["servers"] = servers

    if tags:
        openapi["tags"] = tags

    return openapi


def schema_to_json(schema: Dict[str, Any], indent: int = 2) -> str:
    """
    Convert a schema dictionary to a JSON string.

    Args:
        schema: Schema dictionary
        indent: JSON indentation level

    Returns:
        JSON string
 ..."""
    return json.dumps(schema, indent=indent)


def json_to_schema(json_str: str) -> Dict[str, Any]:
    """
    Convert a JSON string to a schema dictionary.

    Args:
        json_str: JSON string

    Returns:
        Schema dictionary

    Raises:
        json.JSONDecodeError: If the JSON is invalid
 ..."""
    return json.loads(json_str)


def get_referenced_schemas(
    schema: Dict[str, Any],
    schema_store: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Get all schemas referenced in a schema.

    Args:
        schema: Source schema
        schema_store: Dictionary of available schemas

    Returns:
        Dictionary of referenced schemas
 ..."""
    referenced = {}

    def _find_refs(obj: Any) -> None:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/components/schemas/"):
                    schema_name = ref.split("/")[-1]
                    if schema_name in schema_store and schema_name not in referenced:
                        referenced[schema_name] = schema_store[schema_name]
                        _find_refs(schema_store[schema_name])

            for value in obj.values():
                _find_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                _find_refs(item)

    _find_refs(schema)
    return referenced
