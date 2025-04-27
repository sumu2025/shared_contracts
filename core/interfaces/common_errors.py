"""
Common error definitions for service interfaces.
"""

from typing import Any, Dict, Optional


class ServiceError(Exception):
    """Base class for all service errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "service_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(ServiceError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="not_found",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                **(details or {}),
            },
        )


class ValidationError(ServiceError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=400,
            details={
                "field": field,
                **(details or {}),
            },
        )


class AuthenticationError(ServiceError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="authentication_error",
            status_code=401,
            details=details or {},
        )
