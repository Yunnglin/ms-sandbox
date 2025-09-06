"""Response data models."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import Field

from .base import BaseModel, SandboxStatus, ExecutionStatus, ToolType


class ExecutionResult(BaseModel):
    """Result of code or command execution."""
    
    status: ExecutionStatus = Field(..., description="Execution status")
    output: Optional[str] = Field(None, description="Standard output")
    error: Optional[str] = Field(None, description="Error output")
    return_code: Optional[int] = Field(None, description="Process return code")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class FileOperationResult(BaseModel):
    """Result of file operations."""
    
    success: bool = Field(..., description="Operation success status")
    path: str = Field(..., description="File path")
    content: Optional[Union[str, bytes]] = Field(None, description="File content (for read operations)")
    size: Optional[int] = Field(None, description="File size in bytes")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")


class SandboxInfo(BaseModel):
    """Information about a sandbox instance."""
    
    id: str = Field(..., description="Sandbox identifier")
    status: SandboxStatus = Field(..., description="Current status")
    type: str = Field(..., description="Sandbox type (e.g., 'docker')")
    config: Dict[str, Any] = Field(default_factory=dict, description="Sandbox configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    available_tools: List[ToolType] = Field(default_factory=list, description="Available tools")


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""
    
    tool_type: ToolType = Field(..., description="Type of tool executed")
    status: ExecutionStatus = Field(..., description="Execution status")
    result: Any = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class HealthCheckResult(BaseModel):
    """Health check result."""
    
    healthy: bool = Field(..., description="Health status")
    version: str = Field(..., description="System version")
    uptime: float = Field(..., description="System uptime in seconds")
    active_sandboxes: int = Field(..., description="Number of active sandboxes")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="System information")
