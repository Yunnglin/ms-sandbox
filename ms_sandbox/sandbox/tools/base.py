"""Base tool interface and factory."""

import abc
from typing import Any, Dict, Optional, Type, Union

from ..model import BaseModel, ToolConfig, ToolExecutionResult, ToolType


class BaseTool(abc.ABC):
    """Abstract base class for all tools."""

    def __init__(self, config: Optional[ToolConfig] = None):
        """Initialize the tool with configuration.

        Args:
            config: Tool configuration
        """
        self.config = config or ToolConfig()

    @property
    @abc.abstractmethod
    def tool_type(self) -> ToolType:
        """Return the tool type."""
        pass

    @abc.abstractmethod
    async def execute(self, parameters: Dict[str, Any], **kwargs) -> ToolExecutionResult:
        """Execute the tool with given parameters.

        Args:
            parameters: Tool execution parameters
            **kwargs: Additional keyword arguments

        Returns:
            Tool execution result
        """
        pass

    @abc.abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            True if parameters are valid

        Raises:
            ValueError: If parameters are invalid
        """
        pass

    def is_enabled(self) -> bool:
        """Check if the tool is enabled."""
        return self.config.enabled


class ToolFactory:
    """Factory for creating tool instances."""

    _tools: Dict[ToolType, Type[BaseTool]] = {}

    @classmethod
    def register_tool(cls, tool_type: ToolType, tool_class: Type[BaseTool]):
        """Register a tool class for a specific tool type.

        Args:
            tool_type: The tool type
            tool_class: The tool class
        """
        cls._tools[tool_type] = tool_class

    @classmethod
    def create_tool(cls, tool_type: ToolType, config: Optional[ToolConfig] = None) -> BaseTool:
        """Create a tool instance.

        Args:
            tool_type: The tool type to create
            config: Tool configuration

        Returns:
            Tool instance

        Raises:
            ValueError: If tool type is not registered
        """
        if tool_type not in cls._tools:
            raise ValueError(f'Tool type {tool_type} is not registered')

        tool_class = cls._tools[tool_type]
        return tool_class(config)

    @classmethod
    def get_available_tools(cls) -> list[ToolType]:
        """Get list of available tool types.

        Returns:
            List of available tool types
        """
        return list(cls._tools.keys())


def register_tool(tool_type: ToolType):
    """Decorator for registering tools.

    Args:
        tool_type: The tool type to register
    """

    def decorator(tool_class: Type[BaseTool]):
        ToolFactory.register_tool(tool_type, tool_class)
        return tool_class

    return decorator
