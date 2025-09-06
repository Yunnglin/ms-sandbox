"""Base client interface."""

import abc
from typing import Any, Dict, List, Optional, Union

from ..model import SandboxConfig, SandboxInfo, ToolType


class BaseSandboxClient(abc.ABC):
    """Abstract base class for sandbox clients."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize client.
        
        Args:
            base_url: Base URL for remote sandbox server (if applicable)
        """
        self.base_url = base_url
        self.current_sandbox_id: Optional[str] = None
    
    @abc.abstractmethod
    async def create_sandbox(self, sandbox_type: str, config: SandboxConfig) -> str:
        """Create a new sandbox.
        
        Args:
            sandbox_type: Type of sandbox to create
            config: Sandbox configuration
            
        Returns:
            Sandbox ID
        """
        pass
    
    @abc.abstractmethod
    async def get_sandbox_info(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """Get sandbox information.
        
        Args:
            sandbox_id: Sandbox ID
            
        Returns:
            Sandbox information or None if not found
        """
        pass
    
    @abc.abstractmethod
    async def list_sandboxes(self) -> List[SandboxInfo]:
        """List all sandboxes.
        
        Returns:
            List of sandbox information
        """
        pass
    
    @abc.abstractmethod
    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abc.abstractmethod
    async def execute_code(self, sandbox_id: str, code: str, language: str = "python", 
                          **kwargs) -> Dict[str, Any]:
        """Execute code in a sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            code: Code to execute
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        pass
    
    @abc.abstractmethod
    async def execute_command(self, sandbox_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command in a sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            command: Command to execute
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        pass
    
    @abc.abstractmethod
    async def read_file(self, sandbox_id: str, path: str, **kwargs) -> Dict[str, Any]:
        """Read file from sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            path: File path
            **kwargs: Additional parameters
            
        Returns:
            File content and metadata
        """
        pass
    
    @abc.abstractmethod
    async def write_file(self, sandbox_id: str, path: str, content: Union[str, bytes], 
                        **kwargs) -> Dict[str, Any]:
        """Write file to sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            path: File path
            content: File content
            **kwargs: Additional parameters
            
        Returns:
            Operation result
        """
        pass
    
    @abc.abstractmethod
    async def execute_tool(self, sandbox_id: str, tool_type: ToolType, 
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool in sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            tool_type: Tool type
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    @abc.abstractmethod
    async def get_sandbox_tools(self, sandbox_id: str) -> List[ToolType]:
        """Get available tools for a sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            
        Returns:
            List of available tool types
        """
        pass
    
    # Convenience methods for working with current sandbox
    
    async def set_current_sandbox(self, sandbox_id: str) -> None:
        """Set current sandbox ID.
        
        Args:
            sandbox_id: Sandbox ID to set as current
        """
        self.current_sandbox_id = sandbox_id
    
    async def execute_code_current(self, code: str, language: str = "python", 
                                  **kwargs) -> Dict[str, Any]:
        """Execute code in current sandbox.
        
        Args:
            code: Code to execute
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If no current sandbox is set
        """
        if not self.current_sandbox_id:
            raise ValueError("No current sandbox set")
        
        return await self.execute_code(self.current_sandbox_id, code, language, **kwargs)
    
    async def execute_command_current(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command in current sandbox.
        
        Args:
            command: Command to execute
            **kwargs: Additional parameters
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If no current sandbox is set
        """
        if not self.current_sandbox_id:
            raise ValueError("No current sandbox set")
        
        return await self.execute_command(self.current_sandbox_id, command, **kwargs)
    
    async def read_file_current(self, path: str, **kwargs) -> Dict[str, Any]:
        """Read file from current sandbox.
        
        Args:
            path: File path
            **kwargs: Additional parameters
            
        Returns:
            File content and metadata
            
        Raises:
            ValueError: If no current sandbox is set
        """
        if not self.current_sandbox_id:
            raise ValueError("No current sandbox set")
        
        return await self.read_file(self.current_sandbox_id, path, **kwargs)
    
    async def write_file_current(self, path: str, content: Union[str, bytes], 
                                **kwargs) -> Dict[str, Any]:
        """Write file to current sandbox.
        
        Args:
            path: File path
            content: File content
            **kwargs: Additional parameters
            
        Returns:
            Operation result
            
        Raises:
            ValueError: If no current sandbox set
        """
        if not self.current_sandbox_id:
            raise ValueError("No current sandbox set")
        
        return await self.write_file(self.current_sandbox_id, path, content, **kwargs)
    
    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Clean up current sandbox if set
        if self.current_sandbox_id:
            try:
                await self.delete_sandbox(self.current_sandbox_id)
            except Exception:
                pass  # Ignore errors during cleanup
