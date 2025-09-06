"""File operation tools."""

import os
import time
from pathlib import Path
from typing import Any, Dict, Union

from ..model import ExecutionStatus, FileOperationConfig, ToolExecutionResult, ToolType
from .base import BaseTool, register_tool


@register_tool(ToolType.FILE_READER)
class FileReader(BaseTool):
    """Tool for reading files."""

    def __init__(self, config: FileOperationConfig = None):
        """Initialize file reader.

        Args:
            config: File operation configuration
        """
        super().__init__(config or FileOperationConfig())
        self.config: FileOperationConfig = self.config

    @property
    def tool_type(self) -> ToolType:
        """Return tool type."""
        return ToolType.FILE_READER

    async def execute(self, parameters: Dict[str, Any], **kwargs) -> ToolExecutionResult:
        """Read a file.

        Args:
            parameters: Parameters containing 'path', 'encoding', 'binary'
            **kwargs: Additional arguments

        Returns:
            Execution result
        """
        start_time = time.time()

        try:
            # Validate parameters
            self.validate_parameters(parameters)

            path = parameters['path']
            encoding = parameters.get('encoding', 'utf-8')
            binary = parameters.get('binary', False)

            # Security check
            if not self._is_path_allowed(path):
                raise ValueError(f"Access to path '{path}' is not allowed")

            # Check if file exists
            if not os.path.exists(path):
                raise FileNotFoundError(f"File '{path}' does not exist")

            # Check file size
            file_size = os.path.getsize(path)
            if file_size > self.config.max_file_size:
                raise ValueError(f'File size ({file_size} bytes) exceeds limit ({self.config.max_file_size} bytes)')

            # Read file
            try:
                if binary:
                    with open(path, 'rb') as f:
                        content = f.read()
                else:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read()

                execution_time = time.time() - start_time

                return ToolExecutionResult(
                    tool_type=self.tool_type,
                    status=ExecutionStatus.SUCCESS,
                    result={
                        'content': content,
                        'path': path,
                        'size': file_size,
                        'binary': binary,
                        'encoding': encoding if not binary else None
                    },
                    error=None,
                    execution_time=execution_time
                )

            except UnicodeDecodeError as e:
                raise ValueError(f"Failed to decode file with encoding '{encoding}': {str(e)}")

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f'File read failed: {str(e)}'

            return ToolExecutionResult(
                tool_type=self.tool_type,
                status=ExecutionStatus.ERROR,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters."""
        if 'path' not in parameters:
            raise ValueError("Parameter 'path' is required")

        path = parameters['path']
        if not isinstance(path, str):
            raise ValueError("Parameter 'path' must be a string")

        if not path.strip():
            raise ValueError("Parameter 'path' cannot be empty")

        return True

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path access is allowed."""
        path = os.path.abspath(path)

        # Check blocked paths
        for blocked_path in self.config.blocked_paths:
            if path.startswith(os.path.abspath(blocked_path)):
                return False

        # Check allowed paths (if specified)
        if self.config.allowed_paths is not None:
            for allowed_path in self.config.allowed_paths:
                if path.startswith(os.path.abspath(allowed_path)):
                    return True
            return False

        return True


@register_tool(ToolType.FILE_WRITER)
class FileWriter(BaseTool):
    """Tool for writing files."""

    def __init__(self, config: FileOperationConfig = None):
        """Initialize file writer.

        Args:
            config: File operation configuration
        """
        super().__init__(config or FileOperationConfig())
        self.config: FileOperationConfig = self.config

    @property
    def tool_type(self) -> ToolType:
        """Return tool type."""
        return ToolType.FILE_WRITER

    async def execute(self, parameters: Dict[str, Any], **kwargs) -> ToolExecutionResult:
        """Write a file.

        Args:
            parameters: Parameters containing 'path', 'content', 'encoding', 'binary', 'create_dirs'
            **kwargs: Additional arguments

        Returns:
            Execution result
        """
        start_time = time.time()

        try:
            # Validate parameters
            self.validate_parameters(parameters)

            path = parameters['path']
            content = parameters['content']
            encoding = parameters.get('encoding', 'utf-8')
            binary = parameters.get('binary', False)
            create_dirs = parameters.get('create_dirs', True)

            # Security check
            if not self._is_path_allowed(path):
                raise ValueError(f"Access to path '{path}' is not allowed")

            # Check file extension
            if self.config.allowed_extensions is not None:
                file_ext = Path(path).suffix.lower()
                if file_ext not in self.config.allowed_extensions:
                    raise ValueError(f"File extension '{file_ext}' is not allowed")

            # Create parent directories if needed
            if create_dirs:
                os.makedirs(os.path.dirname(path), exist_ok=True)

            # Write file
            try:
                if binary:
                    if not isinstance(content, bytes):
                        raise ValueError('Content must be bytes for binary write')
                    with open(path, 'wb') as f:
                        f.write(content)
                else:
                    if not isinstance(content, str):
                        raise ValueError('Content must be string for text write')
                    with open(path, 'w', encoding=encoding) as f:
                        f.write(content)

                # Get file size
                file_size = os.path.getsize(path)

                execution_time = time.time() - start_time

                return ToolExecutionResult(
                    tool_type=self.tool_type,
                    status=ExecutionStatus.SUCCESS,
                    result={
                        'path': path,
                        'size': file_size,
                        'binary': binary,
                        'encoding': encoding if not binary else None
                    },
                    error=None,
                    execution_time=execution_time
                )

            except UnicodeEncodeError as e:
                raise ValueError(f"Failed to encode content with encoding '{encoding}': {str(e)}")

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f'File write failed: {str(e)}'

            return ToolExecutionResult(
                tool_type=self.tool_type,
                status=ExecutionStatus.ERROR,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters."""
        if 'path' not in parameters:
            raise ValueError("Parameter 'path' is required")

        if 'content' not in parameters:
            raise ValueError("Parameter 'content' is required")

        path = parameters['path']
        content = parameters['content']

        if not isinstance(path, str):
            raise ValueError("Parameter 'path' must be a string")

        if not path.strip():
            raise ValueError("Parameter 'path' cannot be empty")

        if not isinstance(content, (str, bytes)):
            raise ValueError("Parameter 'content' must be string or bytes")

        # Check content size
        content_size = len(content)
        if content_size > self.config.max_file_size:
            raise ValueError(f'Content size ({content_size} bytes) exceeds limit ({self.config.max_file_size} bytes)')

        return True

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path access is allowed."""
        path = os.path.abspath(path)

        # Check blocked paths
        for blocked_path in self.config.blocked_paths:
            if path.startswith(os.path.abspath(blocked_path)):
                return False

        # Check allowed paths (if specified)
        if self.config.allowed_paths is not None:
            for allowed_path in self.config.allowed_paths:
                if path.startswith(os.path.abspath(allowed_path)):
                    return True
            return False

        return True
