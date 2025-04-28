"""
测试辅助工具。

提供常用的测试工具函数，用于简化和标准化测试过..."""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

# 泛型类型变量
ModelT = TypeVar("ModelT", bound=BaseModel)


def assert_model_validation(
    model_cls: Type[ModelT], valid_data: Dict[str, Any], expect_success: bool = True
) -> Optional[ModelT]:
    """
    断言模型验证结果。

    Args:
        model_cls: Pydantic模型类
        valid_data: 要验证的数据
        expect_success: 是否期望验证成功

    Returns:
        如果验证成功，返回模型实例；否则返回None
 ..."""
    try:
        model = model_cls.model_validate(valid_data)
        if not expect_success:
            assert False, f"预期验证失败，但验证成功: {model}"
        return model
    except ValidationError as e:
        if expect_success:
            assert False, f"预期验证成功，但验证失败: {e}"
        return None


def assert_models_equal(
    model1: BaseModel, model2: BaseModel, exclude: Optional[List[str]] = None
) -> None:
    """
    断言两个Pydantic模型实例相等。

    Args:
        model1: 第一个模型实例
        model2: 第二个模型实例
        exclude: 要排除比较的字段列表
 ..."""
    exclude_set = set(exclude or [])
    dict1 = model1.model_dump(exclude=exclude_set)
    dict2 = model2.model_dump(exclude=exclude_set)
    assert dict1 == dict2, f"模型不相等:\n{dict1}\n!=\n{dict2}"


def run_async(async_func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    运行异步函数并返回结果。

    Args:
        async_func: 要运行的异步函数
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        异步函数的返回值
 ..."""
    return asyncio.run(async_func(*args, **kwargs))


def serialize_deserialize(model: BaseModel) -> BaseModel:
    """
    序列化和反序列化模型，用于测试序列化逻辑。

    Args:
        model: 要序列化的模型实例

    Returns:
        反序列化后的模型实例
 ..."""
    json_data = model.model_dump_json()
    return type(model).model_validate_json(json_data)


def get_test_file_path(file_name: str) -> str:
    """
    获取测试文件的完整路径。

    Args:
        file_name: 文件名

    Returns:
        完整的文件路径
 ..."""
    test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(test_dir, "test_data", file_name)


def load_test_json(file_name: str) -> Dict[str, Any]:
    """
    加载测试JSON文件。

    Args:
        file_name: JSON文件名

    Returns:
        解析后的JSON数据
 ..."""
    file_path = get_test_file_path(file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_test_uuid(index: int = 1) -> uuid.UUID:
    """
    创建确定性的测试UUID。

    Args:
        index: UUID索引，用于创建不同但可预测的UUID

    Returns:
        UUID实例
 ..."""
    # 创建确定性UUID，适用于测试
    uuid_str = f"12345678-1234-5678-1234-{index:012d}"
    return uuid.UUID(uuid_str)


def create_test_datetime(days_offset: int = 0) -> datetime:
    """
    创建确定性的测试datetime。

    Args:
        days_offset: 相对于基准时间的天数偏移

    Returns:
        datetime实例
 ..."""
    # 创建确定性datetime，适用于测试
    base = datetime(2023, 1, 1, 12, 0, 0)
    if days_offset:
        from datetime import timedelta
        base += timedelta(days=days_offset)
    return base
