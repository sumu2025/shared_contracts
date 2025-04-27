"""
示例：模型服务实现

本示例展示如何实现和使用ModelServiceInterface接口，包括多种模型提供商的集成。
"""

import os
import uuid
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterable
from enum import Enum
from datetime import datetime

# 导入shared_contracts组件
from agentforge_contracts.core.interfaces.model_interface import ModelServiceInterface
from agentforge_contracts.core.models.base_models import BaseResponse
from agentforge_contracts.core.models.model_models import (
    ModelConfig, 
    ModelResponse, 
    ModelProvider, 
    ModelType, 
    ModelCapability
)
from agentforge_contracts.monitoring import (
    configure_monitor, 
    ServiceComponent, 
    EventType, 
    with_monitoring,
    track_performance
)
from agentforge_contracts.utils.timing import retry_with_backoff

# 模拟HTTP客户端
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("model_service_example")

# 配置监控
monitor = configure_monitor(
    service_name="model-service-example",
    api_key=os.environ.get("LOGFIRE_API_KEY", "dummy-key"),
    project_id=os.environ.get("LOGFIRE_PROJECT_ID", "dummy-project"),
    environment="development"
)


# ====== 通用模型服务实现 ======

class ModelService(ModelServiceInterface):
    """模型服务基类实现。"""
    
    def __init__(self):
        self.models = {}  # 存储模型配置
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册模型。"""
        # 存储模型配置
        self.models[config.model_id] = config
        
        # 记录模型注册
        monitor.info(
            message=f"Model registered: {config.model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.SYSTEM,
            provider=config.provider,
            model_type=config.model_type
        )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=config
        )
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def get_model(self, model_id: str) -> BaseResponse[ModelConfig]:
        """获取模型配置。"""
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model not found: {model_id}"
            )
        
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=self.models[model_id]
        )
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def list_models(self) -> BaseResponse[List[ModelConfig]]:
        """列出所有模型。"""
        return BaseResponse(
            request_id=uuid.uuid4(),
            success=True,
            data=list(self.models.values())
        )
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """生成文本完成。"""
        # 这个方法由子类实现
        raise NotImplementedError("Subclasses must implement generate_completion")


# ====== OpenAI模型服务实现 ======

class OpenAIModelService(ModelService):
    """OpenAI模型服务实现。"""
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册OpenAI模型。"""
        # 检查API密钥环境变量
        env_var = config.api_key_env_var
        api_key = os.environ.get(env_var)
        if not api_key:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Missing API key: Environment variable {env_var} not set"
            )
        
        # 验证模型提供商
        if config.provider != ModelProvider.OPENAI:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Unsupported provider: {config.provider} (expected OpenAI)"
            )
        
        # 调用父类方法存储模型配置
        return await super().register_model(config)
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5, max_delay=5.0)
    async def _call_openai_api(self, endpoint: str, payload: Dict[str, Any], api_key: str, timeout: float) -> Dict[str, Any]:
        """调用OpenAI API。"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """生成文本完成。"""
        # 检查模型是否存在
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model not found: {model_id}"
            )
        
        config = self.models[model_id]
        api_key = os.environ.get(config.api_key_env_var)
        request_id = uuid.uuid4()
        
        # 记录请求
        monitor.info(
            message=f"Generating completion with {model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.REQUEST,
            model_id=model_id,
            prompt_length=len(prompt),
            request_id=str(request_id)
        )
        
        try:
            # 准备API调用
            if config.model_type == ModelType.CHAT:
                endpoint = "https://api.openai.com/v1/chat/completions"
                payload = {
                    "model": config.provider_model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature or config.capabilities.get("temperature", 0.7),
                    "max_tokens": max_tokens or config.capabilities.get("max_tokens", 1000)
                }
            else:
                endpoint = "https://api.openai.com/v1/completions"
                payload = {
                    "model": config.provider_model_id,
                    "prompt": prompt,
                    "temperature": temperature or config.capabilities.get("temperature", 0.7),
                    "max_tokens": max_tokens or config.capabilities.get("max_tokens", 1000)
                }
            
            # 添加其他选项
            for key, value in options.items():
                payload[key] = value
            
            # 调用API并测量性能
            with track_performance("openai_api_call", ServiceComponent.MODEL_SERVICE) as span:
                response_data = await self._call_openai_api(
                    endpoint=endpoint,
                    payload=payload,
                    api_key=api_key,
                    timeout=config.timeout
                )
                
                span.add_data({
                    "model_id": model_id,
                    "prompt_length": len(prompt),
                    "response_size": len(json.dumps(response_data))
                })
            
            # 解析响应
            if config.model_type == ModelType.CHAT:
                content = response_data["choices"][0]["message"]["content"]
                finish_reason = response_data["choices"][0]["finish_reason"]
            else:
                content = response_data["choices"][0]["text"]
                finish_reason = response_data["choices"][0]["finish_reason"]
            
            usage = response_data.get("usage", {})
            
            # 创建响应对象
            model_response = ModelResponse(
                model_id=model_id,
                request_id=request_id,
                content=content,
                usage=usage,
                finish_reason=finish_reason,
                raw_response=response_data
            )
            
            # 记录成功响应
            monitor.info(
                message=f"Successfully generated completion",
                component=ServiceComponent.MODEL_SERVICE,
                event_type=EventType.RESPONSE,
                model_id=model_id,
                content_length=len(content),
                usage=usage,
                request_id=str(request_id)
            )
            
            return BaseResponse(
                request_id=request_id,
                success=True,
                data=model_response
            )
            
        except Exception as e:
            error_message = f"Error generating completion: {str(e)}"
            
            # 记录错误
            monitor.error(
                message=error_message,
                component=ServiceComponent.MODEL_SERVICE,
                event_type=EventType.EXCEPTION,
                model_id=model_id,
                error=str(e),
                request_id=str(request_id)
            )
            
            return BaseResponse(
                request_id=request_id,
                success=False,
                error=error_message
            )


# ====== Claude模型服务实现 ======

class ClaudeModelService(ModelService):
    """Anthropic Claude模型服务实现。"""
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册Claude模型。"""
        # 检查API密钥环境变量
        env_var = config.api_key_env_var
        api_key = os.environ.get(env_var)
        if not api_key:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Missing API key: Environment variable {env_var} not set"
            )
        
        # 验证模型提供商
        if config.provider != ModelProvider.ANTHROPIC:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Unsupported provider: {config.provider} (expected Anthropic)"
            )
        
        # 调用父类方法存储模型配置
        return await super().register_model(config)
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5, max_delay=5.0)
    async def _call_claude_api(self, payload: Dict[str, Any], api_key: str, timeout: float) -> Dict[str, Any]:
        """调用Claude API。"""
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """生成文本完成。"""
        # 检查模型是否存在
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model not found: {model_id}"
            )
        
        config = self.models[model_id]
        api_key = os.environ.get(config.api_key_env_var)
        request_id = uuid.uuid4()
        
        # 记录请求
        monitor.info(
            message=f"Generating completion with {model_id}",
            component=ServiceComponent.MODEL_SERVICE,
            event_type=EventType.REQUEST,
            model_id=model_id,
            prompt_length=len(prompt),
            request_id=str(request_id)
        )
        
        try:
            # 准备API调用
            payload = {
                "model": config.provider_model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature or config.capabilities.get("temperature", 0.7),
                "max_tokens": max_tokens or config.capabilities.get("max_tokens", 1000)
            }
            
            # 添加系统提示
            if "system_prompt" in options:
                payload["system"] = options["system_prompt"]
            
            # 调用API并测量性能
            with track_performance("claude_api_call", ServiceComponent.MODEL_SERVICE) as span:
                response_data = await self._call_claude_api(
                    payload=payload,
                    api_key=api_key,
                    timeout=config.timeout
                )
                
                span.add_data({
                    "model_id": model_id,
                    "prompt_length": len(prompt),
                    "response_size": len(json.dumps(response_data))
                })
            
            # 解析响应
            content = response_data["content"][0]["text"]
            usage = {
                "prompt_tokens": response_data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response_data.get("usage", {}).get("output_tokens", 0),
                "total_tokens": response_data.get("usage", {}).get("input_tokens", 0) + response_data.get("usage", {}).get("output_tokens", 0)
            }
            
            # 创建响应对象
            model_response = ModelResponse(
                model_id=model_id,
                request_id=request_id,
                content=content,
                usage=usage,
                finish_reason="stop",
                raw_response=response_data
            )
            
            # 记录成功响应
            monitor.info(
                message=f"Successfully generated completion",
                component=ServiceComponent.MODEL_SERVICE,
                event_type=EventType.RESPONSE,
                model_id=model_id,
                content_length=len(content),
                usage=usage,
                request_id=str(request_id)
            )
            
            return BaseResponse(
                request_id=request_id,
                success=True,
                data=model_response
            )
            
        except Exception as e:
            error_message = f"Error generating completion: {str(e)}"
            
            # 记录错误
            monitor.error(
                message=error_message,
                component=ServiceComponent.MODEL_SERVICE,
                event_type=EventType.EXCEPTION,
                model_id=model_id,
                error=str(e),
                request_id=str(request_id)
            )
            
            return BaseResponse(
                request_id=request_id,
                success=False,
                error=error_message
            )


# ====== 多提供商模型服务代理 ======

class MultiProviderModelService(ModelService):
    """多提供商模型服务代理，根据配置自动路由到对应服务。"""
    
    def __init__(self):
        super().__init__()
        self.provider_services = {
            ModelProvider.OPENAI: OpenAIModelService(),
            ModelProvider.ANTHROPIC: ClaudeModelService()
        }
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def register_model(self, config: ModelConfig) -> BaseResponse[ModelConfig]:
        """注册模型，路由到对应的服务。"""
        # 检查是否支持该提供商
        if config.provider not in self.provider_services:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Unsupported provider: {config.provider}"
            )
        
        # 存储模型配置
        self.models[config.model_id] = config
        
        # 路由到对应服务注册
        service = self.provider_services[config.provider]
        return await service.register_model(config)
    
    @with_monitoring(component=ServiceComponent.MODEL_SERVICE)
    async def generate_completion(
        self,
        model_id: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **options: Any,
    ) -> BaseResponse[ModelResponse]:
        """生成文本完成，路由到对应的服务。"""
        # 检查模型是否存在
        if model_id not in self.models:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Model not found: {model_id}"
            )
        
        # 获取模型配置
        config = self.models[model_id]
        
        # 路由到对应的服务
        if config.provider not in self.provider_services:
            return BaseResponse(
                request_id=uuid.uuid4(),
                success=False,
                error=f"Unsupported provider: {config.provider}"
            )
        
        service = self.provider_services[config.provider]
        return await service.generate_completion(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            **options
        )


# ====== 示例应用 ======

async def run_example():
    """运行模型服务示例。"""
    print("\n==== AgentForge模型服务示例 ====\n")
    
    # 创建多提供商模型服务
    model_service = MultiProviderModelService()
    
    # 注册OpenAI模型
    print("注册OpenAI模型...")
    openai_config = ModelConfig(
        model_id="gpt-4",
        display_name="GPT-4",
        provider=ModelProvider.OPENAI,
        provider_model_id="gpt-4-1106-preview",
        model_type=ModelType.CHAT,
        api_key_env_var="OPENAI_API_KEY",
        capabilities={
            "temperature": 0.7,
            "max_tokens": 4000,
            "supports_streaming": True,
            "supports_function_calling": True
        },
        timeout=30.0
    )
    
    gpt4_result = await model_service.register_model(openai_config)
    
    if gpt4_result.success:
        print(f"✅ GPT-4注册成功: {gpt4_result.data.model_id}")
    else:
        print(f"❌ GPT-4注册失败: {gpt4_result.error}")
    
    # 注册Claude模型
    print("\n注册Claude模型...")
    claude_config = ModelConfig(
        model_id="claude-3",
        display_name="Claude 3 Opus",
        provider=ModelProvider.ANTHROPIC,
        provider_model_id="claude-3-opus-20240229",
        model_type=ModelType.CHAT,
        api_key_env_var="ANTHROPIC_API_KEY",
        capabilities={
            "temperature": 0.7,
            "max_tokens": 4000,
            "supports_streaming": True,
            "supports_vision": True
        },
        timeout=30.0
    )
    
    claude_result = await model_service.register_model(claude_config)
    
    if claude_result.success:
        print(f"✅ Claude注册成功: {claude_result.data.model_id}")
    else:
        print(f"❌ Claude注册失败: {claude_result.error}")
    
    # 列出所有模型
    print("\n列出所有模型...")
    models_result = await model_service.list_models()
    
    if models_result.success:
        for model in models_result.data:
            print(f"- {model.model_id}: {model.display_name} ({model.provider})")
    
    # 执行OpenAI完成请求（如果注册成功）
    if gpt4_result.success and "OPENAI_API_KEY" in os.environ:
        print("\n使用GPT-4生成完成...")
        
        openai_response = await model_service.generate_completion(
            model_id="gpt-4",
            prompt="What is the capital of France? Answer in one word.",
            max_tokens=50,
            temperature=0.2
        )
        
        if openai_response.success:
            print(f"GPT-4响应: {openai_response.data.content}")
            print(f"使用的tokens: {openai_response.data.usage}")
        else:
            print(f"GPT-4请求失败: {openai_response.error}")
    
    # 执行Claude完成请求（如果注册成功）
    if claude_result.success and "ANTHROPIC_API_KEY" in os.environ:
        print("\n使用Claude生成完成...")
        
        claude_response = await model_service.generate_completion(
            model_id="claude-3",
            prompt="What is the capital of Italy? Answer in one word.",
            max_tokens=50,
            temperature=0.2,
            system_prompt="You are a helpful AI assistant that gives concise answers."
        )
        
        if claude_response.success:
            print(f"Claude响应: {claude_response.data.content}")
            print(f"使用的tokens: {claude_response.data.usage}")
        else:
            print(f"Claude请求失败: {claude_response.error}")


# ====== 主函数 ======

if __name__ == "__main__":
    # 运行示例
    asyncio.run(run_example())
