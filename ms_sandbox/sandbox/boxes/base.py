"""Base sandbox interface and factory."""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import shortuuid as uuid

from ms_sandbox.sandbox.model.base import SandboxType
from ms_sandbox.sandbox.utils import get_logger

from ..model import SandboxConfig, SandboxInfo, SandboxStatus, ToolType
from ..tools import BaseTool, ToolFactory

logger = get_logger()


class BaseSandbox(abc.ABC):
    """Abstract base class for all sandbox implementations."""

    def __init__(self, config: SandboxConfig, sandbox_id: Optional[str] = None):
        """Initialize sandbox.

        Args:
            config: Sandbox configuration
            sandbox_id: Optional sandbox ID (will be generated if not provided)
        """
        self.id = sandbox_id or str(uuid.uuid())
        self.config = config
        self.status = SandboxStatus.INITIALIZING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self._tools: Dict[ToolType, BaseTool] = {}

    @property
    @abc.abstractmethod
    def sandbox_type(self) -> SandboxType:
        """Return the sandbox type identifier."""
        pass

    @abc.abstractmethod
    async def start(self) -> None:
        """Start the sandbox environment."""
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        """Stop the sandbox environment."""
        pass

    @abc.abstractmethod
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        pass

    @abc.abstractmethod
    async def execute_code(self, code: str, language: str = 'python', **kwargs) -> Dict[str, Any]:
        """Execute code in the sandbox.

        Args:
            code: Code to execute
            language: Programming language
            **kwargs: Additional execution parameters

        Returns:
            Execution result
        """
        pass

    @abc.abstractmethod
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute shell command in the sandbox.

        Args:
            command: Command to execute
            **kwargs: Additional execution parameters

        Returns:
            Execution result
        """
        pass

    @abc.abstractmethod
    async def read_file(self, path: str, **kwargs) -> Dict[str, Any]:
        """Read file from sandbox.

        Args:
            path: File path
            **kwargs: Additional parameters

        Returns:
            File content and metadata
        """
        pass

    @abc.abstractmethod
    async def write_file(self, path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Write file to sandbox.

        Args:
            path: File path
            content: File content
            **kwargs: Additional parameters

        Returns:
            Operation result
        """
        pass

    async def initialize_tools(self, tool_configs: Dict[ToolType, Any] = None) -> None:
        """Initialize sandbox tools.

        Args:
            tool_configs: Tool configurations
        """
        tool_configs = tool_configs or {}

        # Initialize default tools
        available_tools = ToolFactory.get_available_tools()

        for tool_type in available_tools:
            try:
                config = tool_configs.get(tool_type)
                tool = ToolFactory.create_tool(tool_type, config)
                if tool.is_enabled():
                    self._tools[tool_type] = tool
            except Exception as e:
                # Log error but continue with other tools
                logger.error(f'Failed to initialize tool {tool_type}: {e}')

    def get_available_tools(self) -> List[ToolType]:
        """Get list of available tools."""
        return list(self._tools.keys())

    def get_tool(self, tool_type: ToolType) -> Optional[BaseTool]:
        """Get tool instance by type.

        Args:
            tool_type: Tool type

        Returns:
            Tool instance or None if not available
        """
        return self._tools.get(tool_type)

    def update_status(self, status: SandboxStatus) -> None:
        """Update sandbox status.

        Args:
            status: New status
        """
        self.status = status
        self.updated_at = datetime.now()

    def get_info(self) -> SandboxInfo:
        """Get sandbox information.

        Returns:
            Sandbox information
        """
        return SandboxInfo(
            id=self.id,
            status=self.status,
            type=self.sandbox_type,
            config=self.config.model_dump(exclude_none=True),
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata,
            available_tools=self.get_available_tools()
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
        await self.cleanup()


class SandboxFactory:
    """Factory for creating sandbox instances."""

    _sandboxes: Dict[SandboxType, Type[BaseSandbox]] = {}

    @classmethod
    def register_sandbox(cls, sandbox_type: SandboxType, sandbox_class: Type[BaseSandbox]):
        """Register a sandbox class.

        Args:
            sandbox_type: Sandbox type identifier
            sandbox_class: Sandbox class
        """
        cls._sandboxes[sandbox_type] = sandbox_class

    @classmethod
    def create_sandbox(
        cls, sandbox_type: SandboxType, config: SandboxConfig, sandbox_id: Optional[str] = None
    ) -> BaseSandbox:
        """Create a sandbox instance.

        Args:
            sandbox_type: Sandbox type
            config: Sandbox configuration
            sandbox_id: Optional sandbox ID

        Returns:
            Sandbox instance

        Raises:
            ValueError: If sandbox type is not registered
        """
        if sandbox_type not in cls._sandboxes:
            raise ValueError(f'Sandbox type {sandbox_type} is not registered')

        sandbox_class = cls._sandboxes[sandbox_type]
        return sandbox_class(config, sandbox_id)

    @classmethod
    def get_available_types(cls) -> List[SandboxType]:
        """Get list of available sandbox types.

        Returns:
            List of available sandbox types
        """
        return list(cls._sandboxes.keys())


def register_sandbox(sandbox_type: SandboxType):
    """Decorator for registering sandboxes.

    Args:
        sandbox_type: Sandbox type identifier
    """

    def decorator(sandbox_class: Type[BaseSandbox]):
        SandboxFactory.register_sandbox(sandbox_type, sandbox_class)
        return sandbox_class

    return decorator
