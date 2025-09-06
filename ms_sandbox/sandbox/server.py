"""FastAPI server for sandbox system."""

import asyncio
import base64
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .manager import SandboxManager
from .model import (
    DockerSandboxConfig,
    ExecuteCodeRequest,
    ExecuteCommandRequest,
    HealthCheckResult,
    ReadFileRequest,
    SandboxConfig,
    SandboxInfo,
    SandboxStatus,
    SandboxType,
    ToolExecutionRequest,
    ToolType,
    WriteFileRequest,
)


class SandboxServer:
    """FastAPI-based sandbox server."""

    def __init__(self, cleanup_interval: int = 300):
        """Initialize sandbox server.

        Args:
            cleanup_interval: Cleanup interval in seconds
        """
        self.manager = SandboxManager(cleanup_interval)
        self.app = FastAPI(
            title='Sandbox API',
            description='Agent sandbox execution environment',
            version='1.0.0',
            lifespan=self.lifespan
        )
        self._setup_middleware()
        self._setup_routes()
        self.start_time = time.time()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Application lifespan management."""
        # Startup
        await self.manager.start()
        yield
        # Shutdown
        await self.manager.stop()

    def _setup_middleware(self):
        """Setup middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    def _setup_routes(self):
        """Setup API routes."""

        # Health check
        @self.app.get('/health', response_model=HealthCheckResult)
        async def health_check():
            """Health check endpoint."""
            stats = self.manager.get_stats()
            return HealthCheckResult(
                healthy=True,
                version='1.0.0',
                uptime=time.time() - self.start_time,
                active_sandboxes=stats['total_sandboxes'],
                system_info=stats
            )

        # Sandbox management
        @self.app.post('/sandbox/create')
        async def create_sandbox(sandbox_type: str, config: Dict[str, Any], background_tasks: BackgroundTasks):
            """Create a new sandbox."""
            try:
                # Parse config based on sandbox type
                if sandbox_type == SandboxType.DOCKER:
                    sandbox_config = DockerSandboxConfig(**config)
                else:
                    sandbox_config = SandboxConfig(**config)

                sandbox_id = await self.manager.create_sandbox(sandbox_type, sandbox_config)

                return {'sandbox_id': sandbox_id}

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get('/sandbox/{sandbox_id}', response_model=SandboxInfo)
        async def get_sandbox_info(sandbox_id: str):
            """Get sandbox information."""
            info = await self.manager.get_sandbox_info(sandbox_id)
            if not info:
                raise HTTPException(status_code=404, detail='Sandbox not found')
            return info

        @self.app.get('/sandbox/list')
        async def list_sandboxes(status: Optional[SandboxStatus] = None):
            """List all sandboxes."""
            sandboxes = await self.manager.list_sandboxes(status)
            return {'sandboxes': sandboxes}

        @self.app.delete('/sandbox/{sandbox_id}')
        async def delete_sandbox(sandbox_id: str):
            """Delete a sandbox."""
            success = await self.manager.delete_sandbox(sandbox_id)
            if not success:
                raise HTTPException(status_code=404, detail='Sandbox not found')
            return {'message': 'Sandbox deleted successfully'}

        # Code execution
        @self.app.post('/sandbox/execute/code')
        async def execute_code(request: ExecuteCodeRequest):
            """Execute code in a sandbox."""
            try:
                result = await self.manager.execute_code(
                    request.sandbox_id,
                    request.code,
                    request.language,
                    timeout=request.timeout,
                    working_dir=request.working_dir,
                    env=request.env
                )
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post('/sandbox/execute/command')
        async def execute_command(request: ExecuteCommandRequest):
            """Execute command in a sandbox."""
            try:
                result = await self.manager.execute_command(
                    request.sandbox_id,
                    request.command,
                    timeout=request.timeout,
                    working_dir=request.working_dir,
                    env=request.env
                )
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # File operations
        @self.app.post('/sandbox/file/read')
        async def read_file(request: ReadFileRequest):
            """Read file from sandbox."""
            try:
                result = await self.manager.read_file(
                    request.sandbox_id, request.path, encoding=request.encoding, binary=request.binary
                )
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post('/sandbox/file/write')
        async def write_file(request: WriteFileRequest):
            """Write file to sandbox."""
            try:
                content = request.content

                # Handle base64 encoded binary content
                if request.binary and isinstance(content, str):
                    try:
                        content = base64.b64decode(content)
                    except Exception:
                        raise HTTPException(status_code=400, detail='Invalid base64 content')

                result = await self.manager.write_file(
                    request.sandbox_id,
                    request.path,
                    content,
                    encoding=request.encoding,
                    binary=request.binary,
                    create_dirs=request.create_dirs
                )
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Tool execution
        @self.app.post('/sandbox/tool/execute')
        async def execute_tool(request: ToolExecutionRequest):
            """Execute tool in sandbox."""
            try:
                result = await self.manager.execute_tool(request.sandbox_id, request.tool_type, request.parameters)
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get('/sandbox/{sandbox_id}/tools')
        async def get_sandbox_tools(sandbox_id: str):
            """Get available tools for a sandbox."""
            try:
                tools = await self.manager.get_sandbox_tools(sandbox_id)
                return {'tools': [tool.value for tool in tools]}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        # System info
        @self.app.get('/stats')
        async def get_stats():
            """Get system statistics."""
            return self.manager.get_stats()

    def run(self, host: str = '0.0.0.0', port: int = 8000, **kwargs):
        """Run the server.

        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn arguments
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, **kwargs)


# Create a default server instance
def create_server(cleanup_interval: int = 300) -> SandboxServer:
    """Create a sandbox server instance.

    Args:
        cleanup_interval: Cleanup interval in seconds

    Returns:
        Sandbox server instance
    """
    return SandboxServer(cleanup_interval)
