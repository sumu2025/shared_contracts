"""
Tests for utility functions in agentforge-contracts.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

import pytest
from pydantic import BaseModel, Field

from shared_contracts.utils.schema_utils import (
    extract_json_schema,
    json_to_schema,
    merge_schemas,
    schema_to_json,
    validate_schema,
)
from shared_contracts.utils.serialization import (
    deep_dict_update,
    dict_to_model,
    json_to_model,
    model_to_dict,
    model_to_json,
)
from shared_contracts.utils.timing import async_timed, measure_execution_time, timed
from shared_contracts.utils.validation import (
    validate_enum_value,
    validate_model,
    validate_model_type,
    validate_service_name,
    validate_uuid,
)
from shared_contracts.utils.version import (
    compare_versions,
    get_version,
    is_compatible_version,
)


# Test models for validation and serialization
class TestEnum(str, Enum):
    """Test enumeration."""

    VALUE1 = "value1"
    VALUE2 = "value2"
    VALUE3 = "value3"


class NestedModel(BaseModel):
    """Nested model for testing."""

    field1: str
    field2: Optional[int] = None


class TestModel(BaseModel):
    """Test model for validation and serialization."""

    id: uuid.UUID
    name: str
    value: float
    enum_field: TestEnum
    created_at: datetime
    nested: Optional[NestedModel] = None
    tags: List[str] = Field(default_factory=list)


class TestSchemaUtils:
    """Tests for schema_utils module."""

    def test_extract_json_schema(self):
        """Test extracting JSON schema from a Pydantic model."""
        schema = extract_json_schema(TestModel)

        assert schema["type"] == "object"
        assert "id" in schema["properties"]
        assert "name" in schema["properties"]
        assert "value" in schema["properties"]
        assert "enum_field" in schema["properties"]
        assert "created_at" in schema["properties"]
        assert "nested" in schema["properties"]
        assert "tags" in schema["properties"]

        # Test with exclude
        schema_excluded = extract_json_schema(TestModel, exclude={"tags", "nested"})
        assert "tags" not in schema_excluded["properties"]
        assert "nested" not in schema_excluded["properties"]

    def test_merge_schemas(self):
        """Test merging schemas."""
        schema1 = {
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "integer"},
            },
            "required": ["field1"],
        }

        schema2 = {
            "type": "object",
            "properties": {
                "field2": {"type": "number"},  # Different type
                "field3": {"type": "boolean"},
            },
            "required": ["field2"],
        }

        # Test merge without properties
        merged = merge_schemas([schema1, schema2], merge_properties=False)
        assert merged["type"] == "object"
        assert "field1" in merged["properties"]
        assert "field2" in merged["properties"]
        assert "field3" not in merged["properties"]  # Not merged

        # Test merge with properties
        merged = merge_schemas([schema1, schema2], merge_properties=True)
        assert merged["type"] == "object"
        assert "field1" in merged["properties"]
        assert "field2" in merged["properties"]
        assert "field3" in merged["properties"]  # Merged

        # Check required fields
        assert "required" in merged
        assert "field1" in merged["required"]
        assert "field2" in merged["required"]

    def test_validate_schema(self):
        """Test schema validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["name"],
        }

        # Valid data
        valid_data = {"name": "John", "age": 30}
        errors = validate_schema(valid_data, schema)
        assert len(errors) == 0

        # Invalid data - missing required field
        invalid_data1 = {"age": 30}
        errors = validate_schema(invalid_data1, schema)
        assert len(errors) > 0

        # Invalid data - wrong type
        invalid_data2 = {"name": "John", "age": "thirty"}
        errors = validate_schema(invalid_data2, schema)
        assert len(errors) > 0

        # Invalid data - value out of range
        invalid_data3 = {"name": "John", "age": -5}
        errors = validate_schema(invalid_data3, schema)
        assert len(errors) > 0

    def test_schema_to_json(self):
        """Test schema_to_json function."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }

        json_str = schema_to_json(schema)
        assert isinstance(json_str, str)

        # Verify the JSON can be parsed back
        parsed = json.loads(json_str)
        assert parsed["type"] == "object"
        assert "name" in parsed["properties"]
        assert "age" in parsed["properties"]

    def test_json_to_schema(self):
        """Test json_to_schema function."""
        json_str = json.dumps(
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            }
        )

        schema = json_to_schema(json_str)
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]


class TestValidationUtils:
    """Tests for validation_utils module."""

    def test_validate_model(self):
        """Test validate_model function."""
        # Create a valid model
        test_data = {
            "id": str(uuid.uuid4()),
            "name": "Test",
            "value": 42.0,
            "enum_field": "value1",
            "created_at": datetime.utcnow().isoformat(),
            "nested": {
                "field1": "nested value",
                "field2": 123,
            },
            "tags": ["tag1", "tag2"],
        }

        # Test validation success
        result = validate_model(TestModel, test_data)
        assert result.valid is True
        assert result.model is not None
        assert result.model.name == "Test"
        assert result.model.value == 42.0
        assert result.model.enum_field == TestEnum.VALUE1
        assert len(result.model.tags) == 2

        # Test validation failure - missing field
        invalid_data = test_data.copy()
        del invalid_data["name"]
        result = validate_model(TestModel, invalid_data)
        assert result.valid is False
        assert result.model is None
        assert len(result.errors) > 0

        # Test validation failure - wrong type
        invalid_data = test_data.copy()
        invalid_data["value"] = "not a float"
        result = validate_model(TestModel, invalid_data)
        assert result.valid is False
        assert result.model is None
        assert len(result.errors) > 0

    def test_validate_uuid(self):
        """Test validate_uuid function."""
        # Valid UUIDs
        valid_uuid1 = uuid.uuid4()
        valid_uuid2 = str(uuid.uuid4())

        assert validate_uuid(valid_uuid1) is True
        assert validate_uuid(valid_uuid2) is True

        # Invalid UUIDs
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid(123) is False
        assert (
            validate_uuid("123e4567-e89b-12d3-a456-426655440-0") is False
        )  # Wrong format

    def test_validate_model_type(self):
        """Test validate_model_type function."""
        allowed_types = {"type1", "type2", "Type3"}

        # Test case-sensitive
        assert validate_model_type("type1", allowed_types, case_sensitive=True) is True
        assert validate_model_type("Type1", allowed_types, case_sensitive=True) is False
        assert validate_model_type("type3", allowed_types, case_sensitive=True) is False

        # Test case-insensitive
        assert validate_model_type("type1", allowed_types) is True
        assert validate_model_type("Type1", allowed_types) is True
        assert validate_model_type("TYPE1", allowed_types) is True
        assert validate_model_type("type4", allowed_types) is False

    def test_validate_service_name(self):
        """Test validate_service_name function."""
        # Valid service names
        assert validate_service_name("service-name") is True
        assert validate_service_name("s123") is True
        assert validate_service_name("service-name-123") is True

        # Invalid service names
        assert validate_service_name("Service") is False  # Uppercase not allowed
        assert validate_service_name("1service") is False  # Must start with a letter
        assert validate_service_name("s") is False  # Too short
        assert validate_service_name("service_name") is False  # Underscore not allowed

        # Test with allowed services
        allowed = {"service-1", "service-2"}
        assert validate_service_name("service-1", allowed_services=allowed) is True
        assert validate_service_name("service-3", allowed_services=allowed) is False

    def test_validate_enum_value(self):
        """Test validate_enum_value function."""
        # Test with string enum
        assert validate_enum_value(TestEnum.VALUE1, TestEnum) is True
        assert validate_enum_value("value1", TestEnum) is True
        assert validate_enum_value("VALUE1", TestEnum) is False  # Case-sensitive
        assert validate_enum_value("invalid", TestEnum) is False


class TestSerializationUtils:
    """Tests for serialization_utils module."""

    def test_model_to_dict(self):
        """Test model_to_dict function."""
        # Create a test model
        model = TestModel(
            id=uuid.uuid4(),
            name="Test",
            value=42.0,
            enum_field=TestEnum.VALUE1,
            created_at=datetime.utcnow(),
            nested=NestedModel(field1="nested value", field2=123),
            tags=["tag1", "tag2"],
        )

        # Convert to dict
        result = model_to_dict(model)

        # Verify the result
        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["value"] == 42.0
        assert result["enum_field"] == "value1"
        assert len(result["tags"]) == 2
        assert result["nested"]["field1"] == "nested value"

        # Test with exclude
        result_excluded = model_to_dict(model, exclude=["tags", "nested"])
        assert "tags" not in result_excluded
        assert "nested" not in result_excluded

        # Test with exclude_none
        model.nested.field2 = None
        result_exclude_none = model_to_dict(model, exclude_none=True)
        assert "field2" not in result_exclude_none["nested"]

    def test_dict_to_model(self):
        """Test dict_to_model function."""
        # Create a test dict
        data = {
            "id": str(uuid.uuid4()),
            "name": "Test",
            "value": 42.0,
            "enum_field": "value1",
            "created_at": datetime.utcnow().isoformat(),
            "nested": {
                "field1": "nested value",
                "field2": 123,
            },
            "tags": ["tag1", "tag2"],
        }

        # Convert to model
        model = dict_to_model(data, TestModel)

        # Verify the result
        assert isinstance(model, TestModel)
        assert model.name == "Test"
        assert model.value == 42.0
        assert model.enum_field == TestEnum.VALUE1
        assert len(model.tags) == 2
        assert model.nested.field1 == "nested value"
        assert model.nested.field2 == 123

    def test_model_to_json(self):
        """Test model_to_json function."""
        # Create a test model
        model = TestModel(
            id=uuid.uuid4(),
            name="Test",
            value=42.0,
            enum_field=TestEnum.VALUE1,
            created_at=datetime.utcnow(),
            nested=NestedModel(field1="nested value", field2=123),
            tags=["tag1", "tag2"],
        )

        # Convert to JSON
        json_str = model_to_json(model)

        # Verify the result
        assert isinstance(json_str, str)

        # Parse the JSON and verify
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test"
        assert parsed["value"] == 42.0
        assert parsed["enum_field"] == "value1"
        assert len(parsed["tags"]) == 2
        assert parsed["nested"]["field1"] == "nested value"

    def test_json_to_model(self):
        """Test json_to_model function."""
        # Create a test model and convert to JSON
        id_value = uuid.uuid4()
        now = datetime.utcnow()

        # Create a JSON string
        json_str = json.dumps(
            {
                "id": str(id_value),
                "name": "Test",
                "value": 42.0,
                "enum_field": "value1",
                "created_at": now.isoformat(),
                "nested": {
                    "field1": "nested value",
                    "field2": 123,
                },
                "tags": ["tag1", "tag2"],
            }
        )

        # Convert to model
        model = json_to_model(json_str, TestModel)

        # Verify the result
        assert isinstance(model, TestModel)
        assert model.id == id_value
        assert model.name == "Test"
        assert model.value == 42.0
        assert model.enum_field == TestEnum.VALUE1
        assert len(model.tags) == 2
        assert model.nested.field1 == "nested value"
        assert model.nested.field2 == 123

    def test_deep_dict_update(self):
        """Test deep_dict_update function."""
        # Create test dictionaries
        base = {
            "a": 1,
            "b": {
                "c": 2,
                "d": [1, 2, 3],
            },
            "e": [4, 5, 6],
        }

        update = {
            "a": 10,
            "b": {
                "c": 20,
                "f": 30,
            },
            "e": [7, 8],
        }

        # Test with overwrite_lists=True
        result1 = deep_dict_update(base, update, overwrite_lists=True)
        assert result1["a"] == 10
        assert result1["b"]["c"] == 20
        assert result1["b"]["d"] == [1, 2, 3]
        assert result1["b"]["f"] == 30
        assert result1["e"] == [7, 8]

        # Test with overwrite_lists=False
        result2 = deep_dict_update(base, update, overwrite_lists=False)
        assert result2["a"] == 10
        assert result2["b"]["c"] == 20
        assert result2["b"]["d"] == [1, 2, 3]
        assert result2["b"]["f"] == 30
        assert result2["e"] == [4, 5, 6, 7, 8]


class TestVersionUtils:
    """Tests for version_utils module."""

    def test_get_version(self):
        """Test get_version function."""
        # Test simple version
        info = get_version("1.2.3")
        assert info["major"] == 1
        assert info["minor"] == 2
        assert info["patch"] == 3

        # Test with prerelease and build
        info = get_version("1.2.3-alpha.1+build.123")
        assert info["major"] == 1
        assert info["minor"] == 2
        assert info["patch"] == 3
        assert info["prerelease"] == "alpha.1"
        assert info["build"] == "build.123"

        # Test invalid version
        with pytest.raises(ValueError):
            get_version("invalid")

        with pytest.raises(ValueError):
            get_version("1.2")

    def test_compare_versions(self):
        """Test compare_versions function."""
        # Equal versions
        assert compare_versions("1.2.3", "1.2.3") == 0

        # Different versions
        assert compare_versions("1.2.3", "1.2.4") < 0
        assert compare_versions("1.2.4", "1.2.3") > 0
        assert compare_versions("1.3.0", "1.2.9") > 0
        assert compare_versions("2.0.0", "1.9.9") > 0

        # With prerelease
        assert compare_versions("1.2.3-alpha", "1.2.3") < 0
        assert compare_versions("1.2.3-alpha", "1.2.3-beta") < 0
        assert compare_versions("1.2.3-beta.2", "1.2.3-beta.1") > 0

    def test_is_compatible_version(self):
        """Test is_compatible_version function."""
        # Test with min_version only
        assert is_compatible_version("1.2.3", min_version="1.2.0") is True
        assert is_compatible_version("1.2.3", min_version="1.2.3") is True
        assert is_compatible_version("1.2.3", min_version="1.2.4") is False

        # Test with max_version only
        assert is_compatible_version("1.2.3", max_version="1.3.0") is True
        assert is_compatible_version("1.2.3", max_version="1.2.3") is False
        assert is_compatible_version("1.2.3", max_version="1.2.2") is False

        # Test with both min and max
        assert (
            is_compatible_version("1.2.3", min_version="1.2.0", max_version="1.3.0")
            is True
        )
        assert (
            is_compatible_version("1.2.3", min_version="1.2.3", max_version="1.3.0")
            is True
        )
        assert (
            is_compatible_version("1.2.3", min_version="1.2.4", max_version="1.3.0")
            is False
        )
        assert (
            is_compatible_version("1.2.3", min_version="1.2.0", max_version="1.2.3")
            is False
        )


class TestTimingUtils:
    """Tests for timing_utils module."""

    def test_timed_decorator(self):
        """Test timed decorator."""

        # Define a test function
        @timed
        def test_function(delay: float):
            time.sleep(delay)
            return delay

        # Call the function
        result = test_function(0.1)
        assert result == 0.1

    @pytest.mark.asyncio
    async def test_async_timed_decorator(self):
        """Test async_timed decorator."""

        # Define a test async function
        @async_timed
        async def test_async_function(delay: float):
            await asyncio.sleep(delay)
            return delay

        # Call the function
        result = await test_async_function(0.1)
        assert result == 0.1

    def test_measure_execution_time(self):
        """Test measure_execution_time context manager."""
        # Use as a context manager
        with measure_execution_time("test operation"):
            time.sleep(0.1)

        # Use as a decorator
        @measure_execution_time
        def test_function(delay: float):
            time.sleep(delay)
            return delay

        result = test_function(0.1)
        assert result == 0.1
