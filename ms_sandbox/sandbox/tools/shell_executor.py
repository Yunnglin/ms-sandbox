"""Shell command execution tool."""

import asyncio
import shlex
import time
from typing import Any, Dict, List, Union

from ..model import ExecutionStatus, ShellExecutorConfig, ToolExecutionResult
from .base import Tool, register_tool


@register_tool('shell_executor')
class ShellExecutor(Tool):
    """Tool for executing shell commands."""

    def __init__(self, config: ShellExecutorConfig = None):
        """Initialize shell executor.

        Args:
            config: Shell executor configuration
        """
        super().__init__(config or ShellExecutorConfig())
        self.config: ShellExecutorConfig = self.config

    async def execute(self, parameters: Dict[str, Any], **kwargs) -> ToolExecutionResult:
        """Execute shell command.

        Args:
            parameters: Execution parameters containing 'command'
            **kwargs: Additional arguments including 'working_dir', 'env'

        Returns:
            Execution result
        """
        start_time = time.time()

        try:
            # Validate parameters
            self.validate_parameters(parameters)

            command = parameters['command']
            working_dir = kwargs.get('working_dir')
            env = kwargs.get('env', {})

            # Prepare command
            if isinstance(command, str):
                cmd_args = shlex.split(command)
            else:
                cmd_args = command

            # Security check for blocked commands
            if self._is_command_blocked(cmd_args[0]):
                raise ValueError(f"Command '{cmd_args[0]}' is blocked")

            # Execute command
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir,
                    env=env if env else None
                )

                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.config.timeout)

                return_code = process.returncode

                # Decode output
                stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ''
                stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ''

                # Combine outputs
                output = stdout_str
                if stderr_str:
                    if output:
                        output += '\n' + stderr_str
                    else:
                        output = stderr_str

                # Limit output size
                if len(output) > self.config.max_output_size:
                    output = output[:self.config.max_output_size] + '\n... (output truncated)'

                status = ExecutionStatus.SUCCESS if return_code == 0 else ExecutionStatus.ERROR
                error = stderr_str if return_code != 0 else None

                execution_time = time.time() - start_time

                return ToolExecutionResult(
                    tool_type=self.tool_type,
                    status=status,
                    result={
                        'output': output,
                        'stdout': stdout_str,
                        'stderr': stderr_str,
                        'return_code': return_code
                    },
                    error=error,
                    execution_time=execution_time
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                return ToolExecutionResult(
                    tool_type=self.tool_type,
                    status=ExecutionStatus.TIMEOUT,
                    result=None,
                    error=f'Command timed out after {self.config.timeout} seconds',
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f'Shell execution failed: {str(e)}'

            return ToolExecutionResult(
                tool_type=self.tool_type,
                status=ExecutionStatus.ERROR,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )
