# Copyright (c) Alibaba, Inc. and its affiliates.
"""Modern agent sandbox system.

A modular, extensible sandbox system for safe code execution with Docker isolation,
FastAPI-based client/server architecture, and comprehensive tool support.
"""

# Import main components
from .model import (
    SandboxConfig, DockerSandboxConfig, SandboxInfo, SandboxStatus, ToolType, ExecutionStatus,
    ExecuteCodeRequest, ExecuteCommandRequest, ReadFileRequest, WriteFileRequest, ToolExecutionRequest,
    ExecutionResult, FileOperationResult, ToolExecutionResult, HealthCheckResult
)
from .tools import BaseTool, PythonExecutor, ShellExecutor, FileReader, FileWriter, ToolFactory
from .boxes import BaseSandbox, DockerSandbox, SandboxFactory
from .manager import SandboxManager
from .client import BaseSandboxClient, HttpSandboxClient
from .server import SandboxServer, create_server


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
