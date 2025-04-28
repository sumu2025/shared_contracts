"""
示例：使用实用工具函数

本示例展示如何使用shared_contracts中的实用工具函数，包括模式操作、验证、序列化和计..."""

import json
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from agentforge_contracts.utils import (  # Schema工具; 验证工具; 序列化工具; 计时工具
    CustomJSONEncoder,
    deep_dict_update,
    dict_to_model,
    extract_json_schema,
    generate_openapi_schema,
    json_to_model,
    measure_execution_time,
    merge_schemas,
    model_to_dict,
    model_to_json,
    retry_with_backoff,
    timed,
    validate_enum_value,
    validate_model,
    validate_schema,
    validate_string_length,
    validate_uuid,
)


# ====== 定义示例模型 ======
class UserRole(str, Enum):
    """用户角色枚举...."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class Address(BaseModel):
    """地址模型...."""

    street: str
    city: str
    postal_code: str
    country: str = "China"


class User(BaseModel):
    """用户模型...."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    username: str
    email: str
    role: UserRole = UserRole.USER
    age: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    address: Optional[Address] = None
    tags: List[str] = Field(default_factory=list)


# ====== Schema工具示例 ======
def schema_tools_example():
    """Schema工具使用示例...."""
    print("\n=== Schema工具示例 ===")

    # 提取Schema
    user_schema = extract_json_schema(User)
    address_schema = extract_json_schema(Address)

    print("User模型Schema:")
    print(json.dumps(user_schema, indent=2, cls=CustomJSONEncoder)[:200] + "...\n")

    # 合并Schema
    merged_schema = merge_schemas([user_schema, address_schema], merge_properties=True)
    print(f"合并后的Schema包含 {len(merged_schema['properties'])} 个属性\n")

    # 验证数据
    test_data = {
        "username": "testuser",
        "email": "test@example.com",
        "role": "admin",
        "tags": ["tag1", "tag2"],
    }

    errors = validate_schema(test_data, user_schema)
    if errors:
        print(f"验证错误: {errors}")
    else:
        print("数据验证通过\n")

    # 生成OpenAPI Schema
    openapi_schema = generate_openapi_schema(
        title="用户API",
        version="1.0.0",
        description="用户管理API",
        schemas={"User": user_schema, "Address": address_schema},
    )

    print(f"生成的OpenAPI Schema包含 {len(openapi_schema['components']['schemas'])} 个模型定义")


# ====== 验证工具示例 ======
def validation_tools_example():
    """验证工具使用示例...."""
    print("\n=== 验证工具示例 ===")

    # 验证模型
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "role": "admin",
        "address": {
            "street": "Test Street",
            "city": "Test City",
            "postal_code": "123456",
        },
    }

    result = validate_model(User, user_data)
    if result.valid:
        print(f"用户模型验证成功: {result.model.username}")
    else:
        print(f"用户模型验证失败: {result.errors}")

    # UUID验证
    test_uuid = uuid.uuid4()
    print(f"UUID验证: {validate_uuid(test_uuid)}")
    print(f"字符串UUID验证: {validate_uuid(str(test_uuid))}")
    print(f"无效UUID验证: {validate_uuid('not-a-uuid')}")

    # 枚举验证
    print(f"有效枚举验证: {validate_enum_value(UserRole.ADMIN, UserRole)}")
    print(f"枚举字符串验证: {validate_enum_value('admin', UserRole)}")
    print(f"无效枚举验证: {validate_enum_value('supervisor', UserRole)}")

    # 字符串长度验证
    print(
        f"字符串长度验证 (3-10): {validate_string_length('test', min_length=3, max_length=10)}"
    )
    print(f"字符串长度验证 (太短): {validate_string_length('ab', min_length=3, max_length=10)}")
    print(
        f"字符串长度验证 (太长): {validate_string_length('very long string', min_length=3, max_length=10)}"  # noqa: E501
    )


# ====== 序列化工具示例 ======
def serialization_tools_example():
    """序列化工具使用示例...."""
    print("\n=== 序列化工具示例 ===")

    # 创建示例用户
    user = User(
        username="testuser",
        email="test@example.com",
        role=UserRole.ADMIN,
        age=30,
        address=Address(
            street="Test Street",
            city="Test City",
            postal_code="123456",
        ),
        tags=["tag1", "tag2"],
    )

    # 模型转字典
    user_dict = model_to_dict(user)
    print(f"模型转字典: {type(user_dict)}, 包含 {len(user_dict)} 个字段")

    # 字典转模型
    new_user = dict_to_model(user_dict, User)
    print(f"字典转模型: {type(new_user)}, username: {new_user.username}")

    # 模型转JSON
    user_json = model_to_json(user)
    print(f"模型转JSON: {type(user_json)}, 长度: {len(user_json)}")

    # JSON转模型
    json_user = json_to_model(user_json, User)
    print(f"JSON转模型: {type(json_user)}, username: {json_user.username}")

    # 深度字典更新
    base_dict = {
        "name": "Base",
        "config": {
            "setting1": 1,
            "setting2": 2,
        },
        "tags": ["tag1", "tag2"],
    }

    update_dict = {
        "name": "Updated",
        "config": {
            "setting2": 20,
            "setting3": 3,
        },
        "tags": ["tag3"],
    }

    # 默认更新（覆盖列表）
    updated1 = deep_dict_update(base_dict, update_dict)
    print(f"深度更新 (覆盖列表): {updated1}")

    # 扩展列表的更新
    updated2 = deep_dict_update(base_dict, update_dict, overwrite_lists=False)
    print(f"深度更新 (扩展列表): {updated2}")


# ====== 计时工具示例 ======
@timed
def slow_operation(delay):
    """模拟慢操作...."""
    time.sleep(delay)
    return delay


@retry_with_backoff(max_retries=3, initial_delay=0.1)
def unreliable_operation(succeed_after=None):
    """模拟不可靠操作...."""
    # 用于跟踪重试次数的局部变量
    if not hasattr(unreliable_operation, "_retry_count"):
        unreliable_operation._retry_count = 0

    unreliable_operation._retry_count += 1

    if succeed_after is not None and unreliable_operation._retry_count >= succeed_after:
        return f"成功（第 {unreliable_operation._retry_count} 次尝试）"
    else:
        raise ValueError(f"操作失败（第 {unreliable_operation._retry_count} 次尝试）")


def timing_tools_example():
    """计时工具使用示例...."""
    print("\n=== 计时工具示例 ===")

    # 使用装饰器计时
    result = slow_operation(0.5)
    print(f"慢操作结果: {result}")

    # 使用上下文管理器计时
    with measure_execution_time("手动计时操作"):
        time.sleep(0.3)
        print("操作完成")

    # 使用重试装饰器
    print("\n重试操作示例:")
    try:
        # 重置重试计数
        unreliable_operation._retry_count = 0

        # 在第2次尝试后成功
        result = unreliable_operation(succeed_after=2)
        print(f"重试操作结果: {result}")
    except Exception as e:
        print(f"重试操作异常: {e}")


# ====== 主函数 ======
def main():
    """主函数...."""
    print("==== AgentForge实用工具示例 ====\n")

    # 运行Schema工具示例
    schema_tools_example()

    # 运行验证工具示例
    validation_tools_example()

    # 运行序列化工具示例
    serialization_tools_example()

    # 运行计时工具示例
    timing_tools_example()


if __name__ == "__main__":
    main()
