"""
通用错误定义

这个模块定义了所有服务共享的错误类型。
"""

from typing import Any, Dict, Optional
from uuid import UUID

from ..models.base_models import BaseError


class ServiceError(Exception):
    """服务错误基类"""

    def __init__(
        self,
        message: str,
        error_code: str = "service_error",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[UUID] = None,
    ):
        """
        初始化服务错误。

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
            request_id: 相关请求ID
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id

        if request_id:
            self.details["request_id"] = str(request_id)

        super().__init__(message)

    def to_error_model(self) -> BaseError:
        """转换为错误模型对象"""
        return BaseError(
            error_code=self.error_code, message=self.message, details=self.details
        )


class ValidationError(ServiceError):
    """输入验证错误"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[UUID] = None,
    ):
        super().__init__(
            message=message,
            error_code="validation_error",
            details=details,
            request_id=request_id,
        )


class NotFoundError(ServiceError):
    """资源未找到错误"""

    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        request_id: Optional[UUID] = None,
    ):
        details = {"resource_type": resource_type, "resource_id": resource_id}

        super().__init__(
            message=message,
            error_code="not_found",
            details=details,
            request_id=request_id,
        )


class AuthorizationError(ServiceError):
    """授权错误"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[UUID] = None,
    ):
        super().__init__(
            message=message,
            error_code="authorization_error",
            details=details,
            request_id=request_id,
        )


class RateLimitError(ServiceError):
    """速率限制错误"""

    def __init__(
        self,
        message: str,
        limit: int,
        window_seconds: int,
        request_id: Optional[UUID] = None,
    ):
        details = {"limit": limit, "window_seconds": window_seconds}

        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            details=details,
            request_id=request_id,
        )


class DependencyError(ServiceError):
    """依赖服务错误"""

    def __init__(
        self,
        message: str,
        dependency_name: str,
        dependency_error: Optional[str] = None,
        request_id: Optional[UUID] = None,
    ):
        details = {"dependency_name": dependency_name}

        if dependency_error:
            details["dependency_error"] = dependency_error

        super().__init__(
            message=message,
            error_code="dependency_error",
            details=details,
            request_id=request_id,
        )
