"""Sandbox environment manager."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ms_sandbox.sandbox.utils import get_logger

from ..boxes import BaseSandbox, SandboxFactory
from ..model import SandboxConfig, SandboxInfo, SandboxStatus, ToolType, SandboxType

logger = get_logger()


class SandboxManager:
    """Manager for sandbox environments."""

    def __init__(self, cleanup_interval: int = 300):  # 5 minutes
        """Initialize sandbox manager.

        Args:
            cleanup_interval: Interval between cleanup runs in seconds
        """
        self._sandboxes: Dict[str, BaseSandbox] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the sandbox manager."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the sandbox manager."""
        if not self._running:
            return

        self._running = False

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop and cleanup all sandboxes
        await self.cleanup_all_sandboxes()

    async def create_sandbox(self, sandbox_type: SandboxType, config: SandboxConfig, sandbox_id: Optional[str] = None) -> str:
        """Create a new sandbox.

        Args:
            sandbox_type: Type of sandbox to create
            config: Sandbox configuration
            sandbox_id: Optional sandbox ID

        Returns:
            Sandbox ID

        Raises:
            ValueError: If sandbox type is not supported
            RuntimeError: If sandbox creation fails
        """
        try:
            # Create sandbox instance
            sandbox = SandboxFactory.create_sandbox(sandbox_type, config, sandbox_id)

            # Start the sandbox
            await sandbox.start()

            # Store sandbox
            self._sandboxes[sandbox.id] = sandbox

            return sandbox.id

        except Exception as e:
            raise RuntimeError(f'Failed to create sandbox: {e}')

    async def get_sandbox(self, sandbox_id: str) -> Optional[BaseSandbox]:
        """Get sandbox by ID.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            Sandbox instance or None if not found
        """
        return self._sandboxes.get(sandbox_id)

    async def get_sandbox_info(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """Get sandbox information.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            Sandbox information or None if not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if sandbox:
            return sandbox.get_info()
        return None

    async def list_sandboxes(self, status_filter: Optional[SandboxStatus] = None) -> List[SandboxInfo]:
        """List all sandboxes.

        Args:
            status_filter: Optional status filter

        Returns:
            List of sandbox information
        """
        result = []
        for sandbox in self._sandboxes.values():
            info = sandbox.get_info()
            if status_filter is None or info.status == status_filter:
                result.append(info)
        return result

    async def stop_sandbox(self, sandbox_id: str) -> bool:
        """Stop a sandbox.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            True if stopped successfully, False if not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return False

        try:
            await sandbox.stop()
            return True
        except Exception as e:
            logger.error(f'Error stopping sandbox {sandbox_id}: {e}')
            return False

    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            True if deleted successfully, False if not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return False

        try:
            await sandbox.stop()
            await sandbox.cleanup()
            del self._sandboxes[sandbox_id]
            return True
        except Exception as e:
            logger.error(f'Error deleting sandbox {sandbox_id}: {e}')
            return False

    async def execute_code(self, sandbox_id: str, code: str, language: str = 'python', **kwargs) -> Dict[str, Any]:
        """Execute code in a sandbox.

        Args:
            sandbox_id: Sandbox ID
            code: Code to execute
            language: Programming language
            **kwargs: Additional parameters

        Returns:
            Execution result

        Raises:
            ValueError: If sandbox not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f'Sandbox {sandbox_id} not found')

        return await sandbox.execute_code(code, language, **kwargs)

    async def execute_command(self, sandbox_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command in a sandbox.

        Args:
            sandbox_id: Sandbox ID
            command: Command to execute
            **kwargs: Additional parameters

        Returns:
            Execution result

        Raises:
            ValueError: If sandbox not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f'Sandbox {sandbox_id} not found')

        return await sandbox.execute_command(command, **kwargs)

    async def read_file(self, sandbox_id: str, path: str, **kwargs) -> Dict[str, Any]:
        """Read file from sandbox.

        Args:
            sandbox_id: Sandbox ID
            path: File path
            **kwargs: Additional parameters

        Returns:
            File content and metadata

        Raises:
            ValueError: If sandbox not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f'Sandbox {sandbox_id} not found')

        return await sandbox.read_file(path, **kwargs)

    async def write_file(self, sandbox_id: str, path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Write file to sandbox.

        Args:
            sandbox_id: Sandbox ID
            path: File path
            content: File content
            **kwargs: Additional parameters

        Returns:
            Operation result

        Raises:
            ValueError: If sandbox not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f'Sandbox {sandbox_id} not found')

        return await sandbox.write_file(path, content, **kwargs)

    async def execute_tool(self, sandbox_id: str, tool_type: ToolType, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool in sandbox.

        Args:
            sandbox_id: Sandbox ID
            tool_type: Tool type to execute
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If sandbox or tool not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f'Sandbox {sandbox_id} not found')

        tool = sandbox.get_tool(tool_type)
        if not tool:
            raise ValueError(f'Tool {tool_type} not available in sandbox {sandbox_id}')

        result = await tool.execute(parameters)
        return result.model_dump()

    async def get_sandbox_tools(self, sandbox_id: str) -> List[ToolType]:
        """Get available tools for a sandbox.

        Args:
            sandbox_id: Sandbox ID

        Returns:
            List of available tool types

        Raises:
            ValueError: If sandbox not found
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f'Sandbox {sandbox_id} not found')

        return sandbox.get_available_tools()

    async def cleanup_all_sandboxes(self) -> None:
        """Clean up all sandboxes."""
        sandbox_ids = list(self._sandboxes.keys())

        for sandbox_id in sandbox_ids:
            try:
                await self.delete_sandbox(sandbox_id)
            except Exception as e:
                logger.error(f'Error cleaning up sandbox {sandbox_id}: {e}')

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self._running:
            try:
                await self._cleanup_expired_sandboxes()
                await asyncio.sleep(self._cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f'Error in cleanup loop: {e}')
                await asyncio.sleep(self._cleanup_interval)

    async def _cleanup_expired_sandboxes(self) -> None:
        """Clean up expired sandboxes."""
        current_time = datetime.now()
        expired_sandboxes = []

        for sandbox_id, sandbox in self._sandboxes.items():
            # Check if sandbox is in error state or stopped for too long
            if sandbox.status in [SandboxStatus.ERROR, SandboxStatus.STOPPED]:
                # Clean up after 1 hour
                if current_time - sandbox.updated_at > timedelta(hours=1):
                    expired_sandboxes.append(sandbox_id)
            # Check for very old sandboxes (24 hours)
            elif current_time - sandbox.created_at > timedelta(hours=24):
                expired_sandboxes.append(sandbox_id)

        # Clean up expired sandboxes
        for sandbox_id in expired_sandboxes:
            try:
                logger.info(f'Cleaning up expired sandbox: {sandbox_id}')
                await self.delete_sandbox(sandbox_id)
            except Exception as e:
                logger.error(f'Error cleaning up expired sandbox {sandbox_id}: {e}')

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            'total_sandboxes': len(self._sandboxes),
            'status_counts': {},
            'sandbox_types': {},
        }

        for sandbox in self._sandboxes.values():
            # Count by status
            status = sandbox.status.value
            stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1

            # Count by type
            sandbox_type = sandbox.sandbox_type
            stats['sandbox_types'][sandbox_type] = stats['sandbox_types'].get(sandbox_type, 0) + 1

        return stats
