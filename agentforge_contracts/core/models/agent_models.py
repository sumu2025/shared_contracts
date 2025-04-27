"""
代理相关数据模型

定义与AI代理相关的模型，包括配置、状态等。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from .base_models import BaseModel


class AgentType(str, Enum):
    """代理类型枚举"""
    
    ASSISTANT = "assistant"
    AUTONOMOUS = "autonomous"
    SPECIALIZED = "specialized"
    CUSTOM = "custom"


class AgentConfig(BaseModel):
    """代理配置模型"""
    
    agent_id: UUID = Field(
        default_factory=uuid4,
        description="代理唯一标识符"
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="代理名称"
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="代理描述"
    )
    
    agent_type: AgentType = Field(
        ...,
        description="代理类型"
    )
    
    base_model_id: str = Field(
        ..., 
        min_length=1,
        description="代理使用的基础模型ID"
    )
    
    system_prompt: str = Field(
        ...,
        min_length=1,
        description="系统提示词"
    )
    
    tools: List[str] = Field(
        default_factory=list,
        description="代理可用工具列表"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="自定义元数据"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )
    
    updated_at: Optional[datetime] = Field(
        default=None,
        description="最后更新时间"
    )
    
    creator_id: Optional[str] = Field(
        default=None,
        description="创建者ID"
    )
    
    capabilities: Set[str] = Field(
        default_factory=set,
        description="代理能力标签"
    )
    
    @model_validator(mode='after')
    def update_timestamps(self) -> 'AgentConfig':
        """确保更新时间总是最新的"""
        self.updated_at = datetime.utcnow()
        return self
    
    @field_validator('capabilities')
    @classmethod
    def validate_capabilities(cls, value: Set[str]) -> Set[str]:
        """验证能力集合中的值"""
        valid_capabilities = {
            "text-generation", 
            "code-generation",
            "web-search",
            "data-analysis",
            "planning",
            "reasoning",
            "chain-of-thought",
            "memory"
        }
        
        invalid_capabilities = value - valid_capabilities
        if invalid_capabilities:
            raise ValueError(
                f"不支持的能力: {', '.join(invalid_capabilities)}. "
                f"有效的能力包括: {', '.join(valid_capabilities)}"
            )
        
        return value


class AgentState(BaseModel):
    """代理状态模型"""
    
    agent_id: UUID = Field(
        ...,
        description="代理ID"
    )
    
    status: str = Field(
        ...,
        description="代理当前状态"
    )
    
    current_task: Optional[str] = Field(
        default=None,
        description="当前正在执行的任务"
    )
    
    last_active: datetime = Field(
        default_factory=datetime.utcnow,
        description="上次活动时间"
    )
    
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="当前对话ID"
    )
    
    memory_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="代理记忆快照"
    )
    
    execution_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="执行指标"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, value: str) -> str:
        """验证状态值是否有效"""
        valid_statuses = [
            'idle', 'busy', 'paused', 'error', 
            'initializing', 'terminated'
        ]
        
        if value not in valid_statuses:
            raise ValueError(
                f"无效的状态: {value}. "
                f"有效的状态包括: {', '.join(valid_statuses)}"
            )
        
        return value
