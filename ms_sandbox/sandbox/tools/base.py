"""Base tool interface and factory."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

from ..model import ToolExecutionResult
from .tool_info import ToolParams


class Tool(ABC):
    """Abstract base class for all tools.

    This abstract class defines the common interface that all tool
    implementations must follow, including both SandboxTool and FunctionTool.

    Key responsibilities:
    - Define the standard tool interface
    - Ensure consistent behavior across different tool types
    - Provide common functionality where applicable
    """

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[ToolParams] = None,
        tool_type: Optional[str] = None,
        enabled: bool = True,
        timeout: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the tool with basic parameters.

        Args:
            name: Tool name
            tool_type: Tool type identifier
            **kwargs: Additional tool-specific parameters
        """
        self._name = name
        self._description = description
        self._parameters = parameters
        self._tool_type = tool_type
        self.enabled = enabled
        self.timeout = timeout

    @property
    def name(self) -> str:
        """Get the tool name."""
        self._name = self._name or self.__class__.__name__

    @property
    def description(self) -> Optional[str]:
        """Get the tool description."""
        return self._description

    @property
    def parameters(self) -> Optional[ToolParams]:
        """Get the tool parameters."""
        return self._parameters

    @property
    def tool_type(self) -> Optional[str]:
        """Get the tool type."""
        return self._tool_type

    @property
    def schema(self) -> Dict:
        """Get the tool schema in OpenAI function calling format."""
        return {
            'name': self.name,
            'description': self._description,
            'parameters': self._parameters.model_dump() if self._parameters else {},
        }

    def __call__(self, *args, **kwargs):
        """Call the tool with optional sandbox override.

        This is a convenience method that delegates to the call() method.

        Args:
            sandbox: Optional sandbox to use for this call
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        return self.call(*args, **kwargs)

    @abstractmethod
    def call(self, *args, **kwargs) -> ToolExecutionResult:
        """Execute the tool call.

        This is the core method that each tool implementation must provide.

        Returns:
            Tool execution result in standardized format.
        """
        pass

    @abstractmethod
    def bind(self, *args, **kwargs) -> 'Tool':
        """Bind parameters or context to create a new tool instance.

        Returns:
            New tool instance with bound parameters/context
        """

    def __str__(self) -> str:
        """String representation of the tool."""
        return (f"{self.__class__.__name__}(name='{self.name}', type="
                f"'{self.tool_type}')")

    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return (
            f'{self.__class__.__name__}('
            f"name='{self.name}', "
            f"tool_type='{self.tool_type}', "
            f"schema='{self.schema}'"
            f')'
        )


class ToolFactory:
    """Factory for creating tool instances."""

    _tools: Dict[str, Type[Tool]] = {}

    @classmethod
    def register_tool(cls, tool_name: str, tool_class: Type[Tool]):
        """Register a tool class for a specific tool type.

        Args:
            tool_name: The tool name
            tool_class: The tool class
        """
        cls._tools[tool_name] = tool_class

    @classmethod
    def create_tool(cls, tool_name: str, **kwargs) -> Tool:
        """Create a tool instance.

        Args:
            tool_name: The tool name to create

        Returns:
            Tool instance

        Raises:
            ValueError: If tool name is not registered
        """
        if tool_name not in cls._tools:
            raise ValueError(f'Tool name {tool_name} is not registered')

        tool_class = cls._tools[tool_name]
        return tool_class(**kwargs)

    @classmethod
    def get_available_tools(cls) -> list[str]:
        """Get list of available tool names.

        Returns:
            List of available tool names
        """
        return list(cls._tools.keys())


def register_tool(tool_name: str):
    """Decorator for registering tools.

    Args:
        tool_name: The tool name to register
    """

    def decorator(tool_class: Type[Tool]):
        ToolFactory.register_tool(tool_name, tool_class)
        return tool_class

    return decorator
