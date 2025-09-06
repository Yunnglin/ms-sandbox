"""HTTP client for sandbox API."""

import json
from typing import Any, Dict, List, Optional, Union

import httpx

from ..model import SandboxConfig, SandboxInfo, ToolType
from .base import BaseSandboxClient


class HttpSandboxClient(BaseSandboxClient):
    """HTTP client for interacting with sandbox API."""

    def __init__(self, base_url: str = 'http://localhost:8000', timeout: float = 30.0):
        """Initialize HTTP client.

        Args:
            base_url: Base URL of sandbox server
            timeout: Request timeout in seconds
        """
        super().__init__(base_url)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._client

    async def _close_client(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_sandbox(self, sandbox_type: str, config: SandboxConfig) -> str:
        """Create a new sandbox."""
        client = await self._get_client()

        response = await client.post(
            '/sandbox/create', json={
                'sandbox_type': sandbox_type,
                'config': config.model_dump(exclude_none=True)
            }
        )
        response.raise_for_status()

        data = response.json()
        return data['sandbox_id']

    async def get_sandbox_info(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """Get sandbox information."""
        client = await self._get_client()

        try:
            response = await client.get(f'/sandbox/{sandbox_id}')
            response.raise_for_status()

            data = response.json()
            return SandboxInfo(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def list_sandboxes(self) -> List[SandboxInfo]:
        """List all sandboxes."""
        client = await self._get_client()

        response = await client.get('/sandbox/list')
        response.raise_for_status()

        data = response.json()
        return [SandboxInfo(**item) for item in data['sandboxes']]

    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox."""
        client = await self._get_client()

        try:
            response = await client.delete(f'/sandbox/{sandbox_id}')
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    async def execute_code(self, sandbox_id: str, code: str, language: str = 'python', **kwargs) -> Dict[str, Any]:
        """Execute code in a sandbox."""
        client = await self._get_client()

        payload = {
            'sandbox_id': sandbox_id,
            'code': code,
            'language': language,
        }
        payload.update(kwargs)

        response = await client.post('/sandbox/execute/code', json=payload)
        response.raise_for_status()

        return response.json()

    async def execute_command(self, sandbox_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command in a sandbox."""
        client = await self._get_client()

        payload = {
            'sandbox_id': sandbox_id,
            'command': command,
        }
        payload.update(kwargs)

        response = await client.post('/sandbox/execute/command', json=payload)
        response.raise_for_status()

        return response.json()

    async def read_file(self, sandbox_id: str, path: str, **kwargs) -> Dict[str, Any]:
        """Read file from sandbox."""
        client = await self._get_client()

        payload = {
            'sandbox_id': sandbox_id,
            'path': path,
        }
        payload.update(kwargs)

        response = await client.post('/sandbox/file/read', json=payload)
        response.raise_for_status()

        return response.json()

    async def write_file(self, sandbox_id: str, path: str, content: Union[str, bytes], **kwargs) -> Dict[str, Any]:
        """Write file to sandbox."""
        client = await self._get_client()

        # Handle binary content
        if isinstance(content, bytes):
            import base64
            content_data = base64.b64encode(content).decode('utf-8')
            kwargs['binary'] = True
        else:
            content_data = content

        payload = {
            'sandbox_id': sandbox_id,
            'path': path,
            'content': content_data,
        }
        payload.update(kwargs)

        response = await client.post('/sandbox/file/write', json=payload)
        response.raise_for_status()

        return response.json()

    async def execute_tool(self, sandbox_id: str, tool_type: ToolType, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool in sandbox."""
        client = await self._get_client()

        payload = {
            'sandbox_id': sandbox_id,
            'tool_type': tool_type.value,
            'parameters': parameters,
        }

        response = await client.post('/sandbox/tool/execute', json=payload)
        response.raise_for_status()

        return response.json()

    async def get_sandbox_tools(self, sandbox_id: str) -> List[ToolType]:
        """Get available tools for a sandbox."""
        client = await self._get_client()

        response = await client.get(f'/sandbox/{sandbox_id}/tools')
        response.raise_for_status()

        data = response.json()
        return [ToolType(tool) for tool in data['tools']]

    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        client = await self._get_client()

        response = await client.get('/health')
        response.raise_for_status()

        return response.json()

    # Context manager support

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self._close_client()
