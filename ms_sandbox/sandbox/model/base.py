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
    DUMMY = 'dummy'


class ToolType(str, Enum):
    """Tool type enumeration."""
    SANDBOX = 'sandbox'
    FUNCTION = 'function'
    EXTERNAL = 'external'


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""

    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'
