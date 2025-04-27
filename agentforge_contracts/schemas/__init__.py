"""
API schema definitions for the AgentForge platform.

This module re-exports schema definitions from the shared_contracts package.
"""

from shared_contracts.schemas import (
    AGENT_API_SCHEMAS,
    COMMON_SCHEMAS,
    MODEL_API_SCHEMAS,
    TOOL_API_SCHEMAS,
)

__all__ = [
    "AGENT_API_SCHEMAS",
    "MODEL_API_SCHEMAS",
    "TOOL_API_SCHEMAS",
    "COMMON_SCHEMAS",
]
