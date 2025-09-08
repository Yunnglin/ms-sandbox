"""Python code execution tool."""

import ast
import io
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from ..model import ExecutionStatus, PythonExecutorConfig, ToolExecutionResult
from .base import Tool, register_tool


@register_tool(ToolType.PYTHON_EXECUTOR)
class PythonExecutor(Tool):
    """Tool for executing Python code."""

    def __init__(self, config: PythonExecutorConfig = None):
        """Initialize Python executor.

        Args:
            config: Python executor configuration
        """
        super().__init__(config or PythonExecutorConfig())
        self.config: PythonExecutorConfig = self.config

    @property
    def tool_type(self) -> ToolType:
        """Return tool type."""
        return ToolType.PYTHON_EXECUTOR

    async def execute(self, parameters: Dict[str, Any], **kwargs) -> ToolExecutionResult:
        """Execute Python code.

        Args:
            parameters: Execution parameters containing 'code'
            **kwargs: Additional arguments

        Returns:
            Execution result
        """
        start_time = time.time()

        try:
            # Validate parameters
            self.validate_parameters(parameters)

            code = parameters['code']

            # Prepare execution environment
            exec_globals = self._prepare_execution_environment()

            # Capture output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            result = None
            error = None

            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Parse and execute code
                    parsed = ast.parse(code, mode='exec')

                    # Execute all but the last statement
                    if len(parsed.body) > 1:
                        exec(
                            compile(ast.Module(body=parsed.body[:-1], type_ignores=[]), '<sandbox>', 'exec'),
                            exec_globals
                        )

                    # Handle the last statement (might be an expression)
                    last_stmt = parsed.body[-1] if parsed.body else None
                    if last_stmt:
                        if isinstance(last_stmt, ast.Expr):
                            # It's an expression, evaluate and capture result
                            result = eval(
                                compile(ast.Expression(body=last_stmt.value), '<sandbox>', 'eval'), exec_globals
                            )
                        else:
                            # It's a statement, just execute
                            exec(
                                compile(ast.Module(body=[last_stmt], type_ignores=[]), '<sandbox>', 'exec'),
                                exec_globals
                            )

                status = ExecutionStatus.SUCCESS

            except Exception as e:
                error = f'{type(e).__name__}: {str(e)}\n{traceback.format_exc()}'
                status = ExecutionStatus.ERROR

            # Get captured output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()

            # Combine outputs
            output = stdout_output
            if stderr_output:
                if output:
                    output += '\n' + stderr_output
                else:
                    output = stderr_output

            # Limit output size
            if len(output) > self.config.max_output_size:
                output = output[:self.config.max_output_size] + '\n... (output truncated)'

            execution_time = time.time() - start_time

            return ToolExecutionResult(
                tool_type=self.tool_type,
                status=status,
                result={
                    'output': output,
                    'return_value': result,
                    'error': error
                },
                error=error,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f'Tool execution failed: {str(e)}'

            return ToolExecutionResult(
                tool_type=self.tool_type,
                status=ExecutionStatus.ERROR,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate execution parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            True if valid

        Raises:
            ValueError: If parameters are invalid
        """
        if 'code' not in parameters:
            raise ValueError("Parameter 'code' is required")

        code = parameters['code']
        if not isinstance(code, str):
            raise ValueError("Parameter 'code' must be a string")

        if not code.strip():
            raise ValueError("Parameter 'code' cannot be empty")

        # Check for blocked modules
        if self.config.blocked_modules:
            try:
                parsed = ast.parse(code)
                for node in ast.walk(parsed):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in self.config.blocked_modules:
                                raise ValueError(f"Module '{alias.name}' is blocked")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module in self.config.blocked_modules:
                            raise ValueError(f"Module '{node.module}' is blocked")
            except SyntaxError as e:
                raise ValueError(f'Invalid Python syntax: {str(e)}')

        return True

    def _prepare_execution_environment(self) -> Dict[str, Any]:
        """Prepare the execution environment.

        Returns:
            Global namespace for execution
        """
        # Start with minimal builtins
        exec_globals = {
            '__builtins__': {
                # Safe builtins
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'type': type,
                'isinstance': isinstance,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                # Math
                'pow': pow,
                'divmod': divmod,
                # I/O - limited
                'input': lambda prompt='': input(prompt),  # Can be dangerous in some contexts
            }
        }

        # Add allowed modules if specified
        if self.config.allowed_modules is not None:
            import importlib
            for module_name in self.config.allowed_modules:
                try:
                    module = importlib.import_module(module_name)
                    exec_globals[module_name] = module
                except ImportError:
                    pass  # Ignore missing modules

        return exec_globals
