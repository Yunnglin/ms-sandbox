"""Unit tests for the sandbox system functionality."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ms_sandbox.sandbox.boxes import SandboxFactory
from ms_sandbox.sandbox.model import DockerSandboxConfig, SandboxStatus, SandboxType
from ms_sandbox.sandbox.tools import ToolFactory


class TestSandboxBasicFunctionality(unittest.IsolatedAsyncioTestCase):
    """Test basic sandbox functionality."""

    async def test_direct_sandbox_creation_and_execution(self):
        """Test direct sandbox creation and Python code execution."""
        # Create Docker sandbox configuration
        config = DockerSandboxConfig(
            image='python-sandbox',
            timeout=30,
            memory_limit='512m',
            cpu_limit=1.0,
            tools_config={
                'python_executor': {}
            }
        )

        # Create and use sandbox with context manager
        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Verify sandbox creation
            self.assertIsNotNone(sandbox.id)
            self.assertIsNotNone(sandbox.status)

            # Execute simple Python code
            result = await sandbox.execute_tool('python_executor', {
                'code': "print('Hello from sandbox!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')",
                'timeout': 30
            })

            # Verify execution result
            self.assertIsNotNone(result.result)
            self.assertIn('Hello from sandbox!', result.result)
            self.assertIn('2 + 2 = 4', result.result)
            self.assertIsNone(result.error)

    async def test_sandbox_system_info_execution(self):
        """Test executing system information commands in sandbox."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}}
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Execute system info script
            result = await sandbox.execute_tool('python_executor', {
                'code': '''
import os
import sys
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Current user: {os.getenv('USER', 'unknown')}")

# Create some data
data = [i**2 for i in range(5)]
print(f"Squares: {data}")
'''
            })

            # Verify system info results
            self.assertIsNotNone(result.result)
            self.assertIn('Python version:', result.result)
            self.assertIn('Working directory:', result.result)
            self.assertIn('Squares: [0, 1, 4, 9, 16]', result.result)

    async def test_sandbox_available_tools(self):
        """Test getting available tools from sandbox."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}}
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Get available tools
            tools = sandbox.get_available_tools()
            self.assertIsInstance(tools, dict)
            self.assertIn('python_executor', tools)

            # Get sandbox info
            info = sandbox.get_info()
            self.assertEqual(info.type, SandboxType.DOCKER)
            self.assertIsNotNone(info.status)


class TestToolFactory(unittest.IsolatedAsyncioTestCase):
    """Test ToolFactory functionality."""

    def test_get_available_tools(self):
        """Test getting available tools from ToolFactory."""
        available_tools = ToolFactory.get_available_tools()
        self.assertIsInstance(available_tools, list)
        self.assertGreater(len(available_tools), 0)

    def test_create_python_executor_tool(self):
        """Test creating Python executor tool."""
        try:
            python_tool = ToolFactory.create_tool('python_executor')
            self.assertEqual(python_tool.name, 'python_executor')
            self.assertIsNotNone(python_tool.description)
            self.assertIsNotNone(python_tool.schema)
            self.assertIsNotNone(python_tool.required_sandbox_type)
        except Exception as e:
            self.fail(f'Failed to create Python executor tool: {e}')


class TestMultipleSandboxes(unittest.IsolatedAsyncioTestCase):
    """Test multiple sandbox scenarios."""

    async def test_multiple_sandboxes_execution(self):
        """Test running multiple sandboxes simultaneously."""
        config1 = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            working_dir='/workspace'
        )

        config2 = DockerSandboxConfig(
            image='python:3.9-slim',
            tools_config={'python_executor': {}},
            working_dir='/app'
        )

        # Create multiple sandboxes
        sandbox1 = SandboxFactory.create_sandbox(SandboxType.DOCKER, config1)
        sandbox2 = SandboxFactory.create_sandbox(SandboxType.DOCKER, config2)

        try:
            await sandbox1.start()
            await sandbox2.start()

            # Verify different sandbox IDs
            self.assertNotEqual(sandbox1.id, sandbox2.id)

            # Execute code in both sandboxes
            code = """
import sys
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Working directory: {__import__('os').getcwd()}")
"""

            result1 = await sandbox1.execute_tool('python_executor', {'code': code})
            result2 = await sandbox2.execute_tool('python_executor', {'code': code})

            # Verify both executions succeeded
            self.assertIsNotNone(result1.result)
            self.assertIsNotNone(result2.result)
            self.assertIn('Python version:', result1.result)
            self.assertIn('Python version:', result2.result)

        finally:
            await sandbox1.stop()
            await sandbox1.cleanup()
            await sandbox2.stop()
            await sandbox2.cleanup()


class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test error handling scenarios."""

    async def test_syntax_error_handling(self):
        """Test handling of Python syntax errors."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            timeout=5
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Test syntax error
            result = await sandbox.execute_tool('python_executor', {
                'code': 'print("Hello" # Missing closing parenthesis'
            })

            # Verify error is captured
            self.assertIsNotNone(result.error)
            self.assertIn('SyntaxError', result.error)

    async def test_runtime_error_handling(self):
        """Test handling of Python runtime errors."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            timeout=5
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Test runtime error (division by zero)
            result = await sandbox.execute_tool('python_executor', {
                'code': 'print(1/0)'
            })

            # Verify error is captured
            self.assertIsNotNone(result.error)
            self.assertIn('ZeroDivisionError', result.error)

    async def test_successful_execution_after_error(self):
        """Test that successful execution works after an error."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            timeout=5
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # First cause an error
            error_result = await sandbox.execute_tool('python_executor', {
                'code': 'print(1/0)'
            })
            self.assertIsNotNone(error_result.error)

            # Then execute successful code
            success_result = await sandbox.execute_tool('python_executor', {
                'code': 'print("This should work fine!")'
            })

            # Verify successful execution
            self.assertIsNone(success_result.error)
            self.assertIn('This should work fine!', success_result.result)


class TestAdvancedPythonExecution(unittest.IsolatedAsyncioTestCase):
    """Test advanced Python code execution scenarios."""

    async def test_data_processing_execution(self):
        """Test complex data processing code execution."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            memory_limit='1g',
            timeout=60
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            data_processing_code = '''
import json
import statistics

# Generate sample data
data = {
    "sales": [1000, 1200, 1100, 1300, 1150],
    "months": ["Jan", "Feb", "Mar", "Apr", "May"]
}

# Calculate statistics
sales_mean = statistics.mean(data["sales"])
sales_median = statistics.median(data["sales"])

print(f"Mean: {sales_mean}")
print(f"Median: {sales_median}")

# Find best month
best_month_idx = data["sales"].index(max(data["sales"]))
print(f"Best month: {data['months'][best_month_idx]}")
'''

            result = await sandbox.execute_tool('python_executor', {
                'code': data_processing_code,
                'timeout': 30
            })

            # Verify data processing results
            self.assertIsNone(result.error)
            self.assertIn('Mean:', result.result)
            self.assertIn('Median:', result.result)
            self.assertIn('Best month:', result.result)

    async def test_mathematical_computations(self):
        """Test mathematical computation execution."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            timeout=60
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            math_code = '''
import math

def fibonacci_sequence(n):
    """Generate Fibonacci sequence."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# Generate Fibonacci sequence
fib_seq = fibonacci_sequence(10)
print(f"Fibonacci: {fib_seq}")

# Calculate pi approximation
pi_approx = sum(((-1) ** i) / (2 * i + 1) for i in range(1000)) * 4
print(f"Pi approximation: {pi_approx:.5f}")
'''

            result = await sandbox.execute_tool('python_executor', {
                'code': math_code,
                'timeout': 30
            })

            # Verify mathematical results
            self.assertIsNone(result.error)
            self.assertIn('Fibonacci:', result.result)
            self.assertIn('Pi approximation:', result.result)


class TestPersistentState(unittest.IsolatedAsyncioTestCase):
    """Test persistent state across multiple executions."""

    async def test_variable_persistence_across_executions(self):
        """Test that variables persist across multiple tool executions."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # First execution - create variables
            result1 = await sandbox.execute_tool('python_executor', {
                'code': '''
counter = 0
data_store = {"initialized": True}
print(f"Initialized counter: {counter}")
print(f"Data store: {data_store}")
'''
            })

            self.assertIsNone(result1.error)
            self.assertIn('Initialized counter: 0', result1.result)
            self.assertIn("{'initialized': True}", result1.result)

            # Second execution - use existing variables
            result2 = await sandbox.execute_tool('python_executor', {
                'code': '''
# Use variables from previous execution
counter += 5
data_store["updated"] = True
print(f"Updated counter: {counter}")
print(f"Updated data store: {data_store}")
'''
            })

            self.assertIsNone(result2.error)
            self.assertIn('Updated counter: 5', result2.result)
            self.assertIn("'updated': True", result2.result)

            # Third execution - verify persistence
            result3 = await sandbox.execute_tool('python_executor', {
                'code': '''
# Verify state is still available
print(f"Final counter: {counter}")
print(f"Final data store keys: {list(data_store.keys())}")
'''
            })

            self.assertIsNone(result3.error)
            self.assertIn('Final counter: 5', result3.result)
            self.assertIn('initialized', result3.result)
            self.assertIn('updated', result3.result)

    async def test_function_persistence_across_executions(self):
        """Test that functions persist across multiple tool executions."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # First execution - define function
            result1 = await sandbox.execute_tool('python_executor', {
                'code': '''
def calculate_square(x):
    return x * x

result = calculate_square(5)
print(f"Square of 5: {result}")
'''
            })

            self.assertIsNone(result1.error)
            self.assertIn('Square of 5: 25', result1.result)

            # Second execution - use existing function
            result2 = await sandbox.execute_tool('python_executor', {
                'code': '''
# Use function from previous execution
result = calculate_square(10)
print(f"Square of 10: {result}")
'''
            })

            self.assertIsNone(result2.error)
            self.assertIn('Square of 10: 100', result2.result)


class TestSandboxConfiguration(unittest.IsolatedAsyncioTestCase):
    """Test sandbox configuration options."""

    async def test_memory_limit_configuration(self):
        """Test sandbox memory limit configuration."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            memory_limit='256m',
            timeout=30
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Simple execution to verify configuration works
            result = await sandbox.execute_tool('python_executor', {
                'code': 'print("Memory limit test passed")'
            })

            self.assertIsNone(result.error)
            self.assertIn('Memory limit test passed', result.result)

    async def test_timeout_configuration(self):
        """Test sandbox timeout configuration."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            timeout=5  # Short timeout
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Quick execution should work
            result = await sandbox.execute_tool('python_executor', {
                'code': 'print("Quick execution")',
                'timeout': 2
            })

            self.assertIsNone(result.error)
            self.assertIn('Quick execution', result.result)

    async def test_working_directory_configuration(self):
        """Test sandbox working directory configuration."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            working_dir='/tmp'
        )

        async with SandboxFactory.create_sandbox(SandboxType.DOCKER, config) as sandbox:
            # Check working directory
            result = await sandbox.execute_tool('python_executor', {
                'code': '''
import os
print(f"Current directory: {os.getcwd()}")
'''
            })

            self.assertIsNone(result.error)
            self.assertIn('Current directory:', result.result)


class TestSandboxFactory(unittest.TestCase):
    """Test SandboxFactory functionality."""

    def test_get_available_sandbox_types(self):
        """Test getting available sandbox types."""
        # This assumes SandboxFactory has a method to get available types
        self.assertIn(SandboxType.DOCKER, [SandboxType.DOCKER])

    def test_create_docker_sandbox_config(self):
        """Test creating Docker sandbox configuration."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}},
            memory_limit='512m',
            timeout=60
        )

        self.assertEqual(config.image, 'python:3.11-slim')
        self.assertEqual(config.memory_limit, '512m')
        self.assertEqual(config.timeout, 60)
        self.assertIn('python_executor', config.tools_config)

    def test_invalid_sandbox_type_creation(self):
        """Test creating sandbox with invalid type."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={'python_executor': {}}
        )

        with self.assertRaises(ValueError):
            SandboxFactory.create_sandbox('invalid_type', config)


class TestSandboxModel(unittest.TestCase):
    """Test sandbox model classes."""

    def test_sandbox_type_enum(self):
        """Test SandboxType enum values."""
        self.assertEqual(SandboxType.DOCKER.value, 'docker')

    def test_sandbox_status_enum(self):
        """Test SandboxStatus enum values."""
        expected_statuses = ['starting', 'running', 'stopping', 'stopped', 'error']
        for status in expected_statuses:
            # Check that all expected statuses exist
            self.assertTrue(any(s.value == status for s in SandboxStatus))

    def test_docker_sandbox_config_defaults(self):
        """Test DockerSandboxConfig default values."""
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            tools_config={}
        )

        self.assertEqual(config.image, 'python:3.11-slim')
        self.assertIsNotNone(config.timeout)
        self.assertIsNotNone(config.memory_limit)


if __name__ == '__main__':
    unittest.main()
