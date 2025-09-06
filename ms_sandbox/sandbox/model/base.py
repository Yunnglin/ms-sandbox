"""Base data models."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""

    class Config:
        extra = 'forbid'
        validate_assignment = True


class SandboxBase(BaseModel):
    """Base model for sandbox-related objects."""

    id: Optional[str] = Field(None, description='Unique identifier')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')


class SandboxStatus(str, Enum):
    """Sandbox status enumeration."""

    INITIALIZING = 'initializing'
    READY = 'ready'
    RUNNING = 'running'
    STOPPED = 'stopped'
    ERROR = 'error'
    CLEANUP = 'cleanup'


class SandboxType(str, Enum):
    """Sandbox type enumeration."""
    DOCKER = 'docker'


class ToolType(str, Enum):
    """Tool type enumeration."""

    PYTHON_EXECUTOR = 'python_executor'
    SHELL_EXECUTOR = 'shell_executor'
    FILE_READER = 'file_reader'
    FILE_WRITER = 'file_writer'
    PACKAGE_INSTALLER = 'package_installer'


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""

    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'
