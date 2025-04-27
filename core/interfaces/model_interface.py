"""
Model service interface definition.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, AsyncIterable
from uuid import UUID

from ..models.model_models import ModelConfig, ModelResponse
from ..models.base_models import BaseResponse


@runtime_checkable
class ModelServiceInterface(Protocol):
    """Interface for the model service."""
    
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """
        Register a new model with the given configuration.
        
        Args:
            config: Model configuration
            
        Returns:
            Response containing the registered model configuration
        
        Raises:
            ValidationError: If the configuration is invalid
            ServiceError: For other service errors
        """
        ...
    
    async def get_model(self, model_id: str) -> BaseResponse[ModelConfig]:
        """
        Get a model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Response containing the model configuration
        
        Raises:
            NotFoundError: If the model is not found
            ServiceError: For other service errors
        """
        ...
    
    async def update_model(
        self, model_id: str, config_updates: Dict[str, Any]
    ) -> BaseResponse[ModelConfig]:
        """
        Update a model's configuration.
        
        Args:
            model_id: Model ID
            config_updates: Updates to apply to the configuration
            
        Returns:
            Response containing the updated model configuration
        
        Raises:
            NotFoundError: If the model is not found
            ValidationError: If the updates are invalid
            ServiceError: For other service errors
        """
        ...
    
    async def delete_model(self, model_id: str) -> BaseResponse[bool]:
        """
        Delete a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Response indicating success
        
        Raises:
            NotFoundError: If the model is not found
            ServiceError: For other service errors
        """
        ...
    
    async def list_models(
        self, offset: int = 0, limit: int = 100, filter_by: Optional[Dict[str, Any]] = None
    ) -> BaseResponse[List[ModelConfig]]:
        """
        List models, with optional filtering.
        
        Args:
            offset: Pagination offset
            limit: Pagination limit
            filter_by: Filter criteria
            
        Returns:
            Response containing a list of model configurations
        
        Raises:
            ValidationError: If the pagination or filter parameters are invalid
            ServiceError: For other service errors
        """
        ...
    
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """
        Generate a completion from a model.
        
        Args:
            model_id: Model ID
            prompt: Prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            **options: Additional model-specific options
            
        Returns:
            Response containing the model's response
        
        Raises:
            NotFoundError: If the model is not found
            ValidationError: If the request is invalid
            ServiceError: For other service errors
        """
        ...
    
    async def generate_streaming_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **options: Any,
    ) -> AsyncIterable[ModelResponse]:
        """
        Generate a streaming completion from a model.
        
        Args:
            model_id: Model ID
            prompt: Prompt to complete
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **options: Additional model-specific options
            
        Returns:
            Asynchronous iterable of model responses
        
        Raises:
            NotFoundError: If the model is not found
            ValidationError: If the request is invalid
            ServiceError: For other service errors
        """
        ...
