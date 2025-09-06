# Copyright (c) Alibaba, Inc. and its affiliates.
"""Modern agent sandbox system.

A modular, extensible sandbox system for safe code execution with Docker isolation,
FastAPI-based client/server architecture, and comprehensive tool support.
"""

from .boxes import BaseSandbox, DockerSandbox, SandboxFactory
from .client import BaseSandboxClient, HttpSandboxClient
from .manager import SandboxManager

# Import main components
from .model import (
    DockerSandboxConfig,
    ExecuteCodeRequest,
    ExecuteCommandRequest,
    ExecutionResult,
    ExecutionStatus,
    FileOperationResult,
    HealthCheckResult,
    ReadFileRequest,
    SandboxConfig,
    SandboxInfo,
    SandboxStatus,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolType,
    WriteFileRequest,
)
from .server import SandboxServer, create_server
from .tools import BaseTool, FileReader, FileWriter, PythonExecutor, ShellExecutor, ToolFactory

__all__ = [
    # Core components
    'SandboxManager',
    'SandboxServer',
    'BaseSandboxClient',
    'HttpSandboxClient',

    # Sandbox implementations
    'BaseSandbox',
    'DockerSandbox',
    'SandboxFactory',

    # Tools
    'BaseTool',
    'PythonExecutor',
    'ShellExecutor',
    'FileReader',
    'FileWriter',
    'ToolFactory',

    # Models
    'SandboxConfig',
    'DockerSandboxConfig',
    'SandboxInfo',
    'SandboxStatus',
    'ToolType',
    'ExecutionStatus',
    'ExecuteCodeRequest',
    'ExecuteCommandRequest',
    'ReadFileRequest',
    'WriteFileRequest',
    'ToolExecutionRequest',
    'ExecutionResult',
    'FileOperationResult',
    'ToolExecutionResult',
    'HealthCheckResult',

    # Server utilities
    'create_server',
]
