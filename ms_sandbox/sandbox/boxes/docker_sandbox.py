"""Docker-based sandbox implementation."""

import asyncio
import io
import json
import os
import tarfile
import tempfile
import time
from typing import Any, Dict, List, Optional, Union

import docker
from docker.errors import APIError, ContainerError, ImageNotFound, NotFound

from ms_sandbox.utils import get_logger

from ..model import DockerSandboxConfig, ExecutionStatus, SandboxStatus, SandboxType
from ..tools import ToolFactory
from .base import BaseSandbox, register_sandbox

logger = get_logger()


@register_sandbox(SandboxType.DOCKER)
class DockerSandbox(BaseSandbox):
    """Docker-based sandbox implementation."""

    def __init__(self, config: DockerSandboxConfig, sandbox_id: Optional[str] = None):
        """Initialize Docker sandbox.

        Args:
            config: Docker sandbox configuration
            sandbox_id: Optional sandbox ID
        """
        super().__init__(config, sandbox_id)
        self.config: DockerSandboxConfig = config
        self.client: Optional[docker.DockerClient] = None
        self.container: Optional[docker.models.containers.Container] = None

    @property
    def sandbox_type(self) -> SandboxType:
        """Return sandbox type."""
        return SandboxType.DOCKER

    async def start(self) -> None:
        """Start the Docker container."""
        try:
            self.update_status(SandboxStatus.INITIALIZING)

            # Initialize Docker client
            self.client = docker.from_env()

            # Ensure image exists
            await self._ensure_image_exists()

            # Create and start container
            await self._create_container()
            await self._start_container()

            # Initialize tools
            await self.initialize_tools()

            self.update_status(SandboxStatus.READY)

        except Exception as e:
            self.update_status(SandboxStatus.ERROR)
            self.metadata['error'] = str(e)
            raise RuntimeError(f'Failed to start Docker sandbox: {e}')

    async def stop(self) -> None:
        """Stop the Docker container."""
        try:
            if self.container:
                self.update_status(SandboxStatus.STOPPED)
                self.container.stop(timeout=10)
        except Exception as e:
            logger.error(f'Error stopping container: {e}')

    async def cleanup(self) -> None:
        """Clean up Docker resources."""
        try:
            self.update_status(SandboxStatus.CLEANUP)

            if self.container:
                try:
                    # Remove container if configured to do so
                    if self.config.remove_on_exit:
                        self.container.remove(force=True)
                    else:
                        self.container.stop(timeout=5)
                except Exception as e:
                    logger.error(f'Error cleaning up container: {e}')
                finally:
                    self.container = None

            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
                finally:
                    self.client = None

        except Exception as e:
            logger.error(f'Error during cleanup: {e}')

    async def execute_code(self, code: str, language: str = 'python', **kwargs) -> Dict[str, Any]:
        """Execute code in the container.

        Args:
            code: Code to execute
            language: Programming language
            **kwargs: Additional parameters (timeout, working_dir, env)

        Returns:
            Execution result
        """
        if language == 'python':
            tool = self.get_tool('python_executor')
            if not tool:
                raise RuntimeError('Python executor tool not available')

            # For Docker sandbox, we need to execute in the container
            return await self._execute_python_in_container(code, **kwargs)
        else:
            raise ValueError(f'Unsupported language: {language}')

    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute shell command in the container.

        Args:
            command: Command to execute
            **kwargs: Additional parameters

        Returns:
            Execution result
        """
        if not self.container:
            raise RuntimeError('Container not started')

        try:
            timeout = kwargs.get('timeout', self.config.timeout)
            working_dir = kwargs.get('working_dir', self.config.working_dir)
            env = kwargs.get('env', {})

            # Prepare environment
            container_env = dict(self.config.env_vars)
            container_env.update(env)

            start_time = time.time()

            # Execute command
            exec_result = self.container.exec_run(
                command, workdir=working_dir, environment=container_env, demux=True, tty=False
            )

            execution_time = time.time() - start_time

            # Process output
            stdout, stderr = exec_result.output
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ''
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ''

            return {
                'status': 'success' if exec_result.exit_code == 0 else 'error',
                'output': stdout_str,
                'error': stderr_str,
                'return_code': exec_result.exit_code,
                'execution_time': execution_time
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Command execution failed: {str(e)}',
                'execution_time': time.time() - start_time if 'start_time' in locals() else 0
            }

    async def read_file(self, path: str, **kwargs) -> Dict[str, Any]:
        """Read file from container.

        Args:
            path: File path in container
            **kwargs: Additional parameters

        Returns:
            File content and metadata
        """
        if not self.container:
            raise RuntimeError('Container not started')

        try:
            encoding = kwargs.get('encoding', 'utf-8')
            binary = kwargs.get('binary', False)

            # Get file from container
            bits, stat = self.container.get_archive(path)

            # Extract file content
            tar_stream = io.BytesIO(b''.join(bits))
            with tarfile.open(fileobj=tar_stream, mode='r') as tar:
                member = tar.next()
                if member is None:
                    raise FileNotFoundError(f'File not found: {path}')

                file_obj = tar.extractfile(member)
                if file_obj is None:
                    raise ValueError(f'Could not extract file: {path}')

                content_bytes = file_obj.read()

                if binary:
                    content = content_bytes
                else:
                    content = content_bytes.decode(encoding, errors='replace')

                return {
                    'content': content,
                    'path': path,
                    'size': len(content_bytes),
                    'binary': binary,
                    'encoding': encoding if not binary else None
                }

        except Exception as e:
            return {'error': f'Failed to read file: {str(e)}'}

    async def write_file(self, path: str, content: Union[str, bytes], **kwargs) -> Dict[str, Any]:
        """Write file to container.

        Args:
            path: File path in container
            content: File content
            **kwargs: Additional parameters

        Returns:
            Operation result
        """
        if not self.container:
            raise RuntimeError('Container not started')

        try:
            encoding = kwargs.get('encoding', 'utf-8')
            binary = kwargs.get('binary', False)

            # Convert content to bytes if needed
            if isinstance(content, str):
                content_bytes = content.encode(encoding)
            else:
                content_bytes = content

            # Create tar archive with file
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name=os.path.basename(path))
                tarinfo.size = len(content_bytes)
                tarinfo.mode = 0o644
                tar.addfile(tarinfo, io.BytesIO(content_bytes))

            tar_stream.seek(0)

            # Put file in container
            self.container.put_archive(os.path.dirname(path) or '/', tar_stream.getvalue())

            return {
                'path': path,
                'size': len(content_bytes),
                'binary': binary,
                'encoding': encoding if not binary else None
            }

        except Exception as e:
            return {'error': f'Failed to write file: {str(e)}'}

    async def _ensure_image_exists(self) -> None:
        """Ensure Docker image exists."""
        try:
            self.client.images.get(self.config.image)
        except ImageNotFound:
            # Try to pull the image
            try:
                self.client.images.pull(self.config.image)
            except Exception as e:
                raise RuntimeError(f'Failed to pull image {self.config.image}: {e}')

    async def _create_container(self) -> None:
        """Create Docker container."""
        try:
            # Prepare container configuration
            container_config = {
                'image': self.config.image,
                'name': f'sandbox-{self.id}',
                'working_dir': self.config.working_dir,
                'environment': self.config.env_vars,
                'detach': True,
                'tty': True,
                'stdin_open': True,
            }

            # Add command if specified
            if self.config.command:
                container_config['command'] = self.config.command

            # Add resource limits
            if self.config.memory_limit:
                container_config['mem_limit'] = self.config.memory_limit

            if self.config.cpu_limit:
                container_config['cpu_quota'] = int(self.config.cpu_limit * 100000)
                container_config['cpu_period'] = 100000

            # Add volumes
            if self.config.volumes:
                container_config['volumes'] = self.config.volumes

            # Add ports
            if self.config.ports:
                container_config['ports'] = self.config.ports

            # Network configuration
            if not self.config.network_enabled:
                container_config['network_mode'] = 'none'
            elif self.config.network:
                container_config['network'] = self.config.network

            # Privileged mode
            container_config['privileged'] = self.config.privileged

            # Create container
            self.container = self.client.containers.create(**container_config)
            self.metadata['container_id'] = self.container.id

        except Exception as e:
            raise RuntimeError(f'Failed to create container: {e}')

    async def _start_container(self) -> None:
        """Start Docker container."""
        try:
            self.container.start()

            # Wait for container to be ready
            timeout = 30
            start_time = time.time()

            while time.time() - start_time < timeout:
                self.container.reload()
                if self.container.status == 'running':
                    break
                await asyncio.sleep(0.5)
            else:
                raise RuntimeError('Container failed to start within timeout')

        except Exception as e:
            raise RuntimeError(f'Failed to start container: {e}')

    async def _execute_python_in_container(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute Python code in container.

        Args:
            code: Python code to execute
            **kwargs: Additional parameters

        Returns:
            Execution result
        """
        if not self.container:
            raise RuntimeError('Container not started')

        try:
            # Create a temporary Python file
            temp_file = f'/tmp/exec_{int(time.time() * 1000000)}.py'

            # Write code to container
            await self.write_file(temp_file, code)

            # Execute Python file
            result = await self.execute_command(f'python3 {temp_file}', **kwargs)

            # Clean up temp file
            try:
                await self.execute_command(f'rm -f {temp_file}')
            except Exception:
                pass  # Ignore cleanup errors

            return result

        except Exception as e:
            return {'status': 'error', 'error': f'Python execution failed: {str(e)}'}
