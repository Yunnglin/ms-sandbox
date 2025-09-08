"""Response data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from .base import BaseModel, ExecutionStatus, SandboxStatus


class SandboxInfo(BaseModel):
    """Information about a sandbox instance."""

    id: str = Field(..., description='Sandbox identifier')
    status: SandboxStatus = Field(..., description='Current status')
    type: str = Field(..., description="Sandbox type (e.g., 'docker')")
    config: Dict[str, Any] = Field(default_factory=dict, description='Sandbox configuration')
    created_at: datetime = Field(default_factory=datetime.now, description='Creation timestamp')
    updated_at: datetime = Field(default_factory=datetime.now, description='Last update timestamp')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')
    available_tools: List[str] = Field(default_factory=list, description='Available tools')


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""

    tool_name: str = Field(..., description='Name of tool executed')
    status: ExecutionStatus = Field(..., description='Execution status')
    result: Any = Field(None, description='Tool execution result')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')
    error: Optional[str] = Field(None, description='Error message if failed')
    execution_time: Optional[float] = Field(None, description='Execution time in seconds')
    timestamp: datetime = Field(default_factory=datetime.now, description='Execution timestamp')


class HealthCheckResult(BaseModel):
    """Health check result."""

    healthy: bool = Field(..., description='Health status')
    version: str = Field(..., description='System version')
    uptime: float = Field(..., description='System uptime in seconds')
    active_sandboxes: int = Field(..., description='Number of active sandboxes')
    system_info: Dict[str, Any] = Field(default_factory=dict, description='System information')
