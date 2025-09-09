"""Unit tests for the tool system functionality."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ms_sandbox.sandbox.model import SandboxType
from ms_sandbox.sandbox.tools import ToolFactory


class TestToolFactory(unittest.TestCase):
    """Test ToolFactory functionality."""

    def test_get_available_tools(self):
        """Test getting list of available tools."""
        available_tools = ToolFactory.get_available_tools()
        self.assertIsInstance(available_tools, list)
        self.assertGreater(len(available_tools), 0)

    def test_create_python_executor_tool(self):
        """Test creating Python executor tool."""
        tool = ToolFactory.create_tool('python_executor')

        self.assertEqual(tool.name, 'python_executor')
        self.assertIsNotNone(tool.description)
        self.assertIsNotNone(tool.schema)
        self.assertEqual(tool.required_sandbox_type, SandboxType.DOCKER)

    def test_create_unknown_tool_raises_error(self):
        """Test that creating unknown tool raises appropriate error."""
        with self.assertRaises(ValueError):
            ToolFactory.create_tool('unknown_tool')

    def test_tool_registry_not_empty(self):
        """Test that tool registry contains expected tools."""
        available_tools = ToolFactory.get_available_tools()
        self.assertIn('python_executor', available_tools)


class TestPythonExecutorTool(unittest.IsolatedAsyncioTestCase):
    """Test Python executor tool functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = ToolFactory.create_tool('python_executor')

    def test_tool_properties(self):
        """Test tool basic properties."""
        self.assertEqual(self.tool.name, 'python_executor')
        self.assertIn('Python', self.tool.description)
        self.assertIsInstance(self.tool.schema, dict)
        self.assertIn('properties', self.tool.schema)

    def test_tool_schema_validation(self):
        """Test tool schema contains required fields."""
        schema = self.tool.schema
        self.assertIn('code', schema['properties'])
        self.assertIn('timeout', schema['properties'])
        self.assertIn('code', schema['required'])

    async def test_tool_execution_with_mock_sandbox(self):
        """Test tool execution with mocked sandbox."""
        # Create mock sandbox
        mock_sandbox = AsyncMock()
        mock_sandbox.execute_code = AsyncMock(return_value={
            'result': 'Hello World',
            'error': None
        })

        # Execute tool
        params = {'code': 'print("Hello World")', 'timeout': 30}
        result = await self.tool.execute(mock_sandbox, params)

        # Verify execution
        mock_sandbox.execute_code.assert_called_once_with(
            'print("Hello World")', timeout=30
        )
        self.assertEqual(result['result'], 'Hello World')
        self.assertIsNone(result['error'])

    async def test_tool_execution_with_error(self):
        """Test tool execution handling errors."""
        # Create mock sandbox that returns error
        mock_sandbox = AsyncMock()
        mock_sandbox.execute_code = AsyncMock(return_value={
            'result': None,
            'error': 'SyntaxError: invalid syntax'
        })

        # Execute tool with invalid code
        params = {'code': 'print("invalid syntax', 'timeout': 30}
        result = await self.tool.execute(mock_sandbox, params)

        # Verify error handling
        self.assertIsNone(result['result'])
        self.assertIn('SyntaxError', result['error'])

    def test_tool_validate_params_valid(self):
        """Test parameter validation with valid parameters."""
        valid_params = {'code': 'print("test")', 'timeout': 30}
        # Should not raise exception
        self.tool.validate_params(valid_params)

    def test_tool_validate_params_missing_required(self):
        """Test parameter validation with missing required parameter."""
        invalid_params = {'timeout': 30}  # Missing 'code'
        with self.assertRaises(ValueError):
            self.tool.validate_params(invalid_params)

    def test_tool_validate_params_invalid_type(self):
        """Test parameter validation with invalid parameter types."""
        invalid_params = {'code': 123, 'timeout': 30}  # code should be string
        with self.assertRaises(ValueError):
            self.tool.validate_params(invalid_params)


class TestToolExecution(unittest.IsolatedAsyncioTestCase):
    """Test tool execution scenarios."""

    async def test_multiple_tools_execution(self):
        """Test executing multiple different tools."""
        available_tools = ToolFactory.get_available_tools()

        for tool_name in available_tools[:2]:  # Test first 2 tools
            tool = ToolFactory.create_tool(tool_name)
            self.assertIsNotNone(tool)
            self.assertEqual(tool.name, tool_name)

    async def test_tool_execution_timeout_handling(self):
        """Test tool execution with timeout parameters."""
        tool = ToolFactory.create_tool('python_executor')

        # Mock sandbox with slow execution
        mock_sandbox = AsyncMock()
        mock_sandbox.execute_code = AsyncMock(side_effect=asyncio.TimeoutError())

        params = {'code': 'import time; time.sleep(10)', 'timeout': 1}

        with self.assertRaises(asyncio.TimeoutError):
            await tool.execute(mock_sandbox, params)

    async def test_tool_concurrent_execution(self):
        """Test concurrent tool execution."""
        tool = ToolFactory.create_tool('python_executor')

        # Create multiple mock sandboxes
        mock_sandbox1 = AsyncMock()
        mock_sandbox1.execute_code = AsyncMock(return_value={
            'result': 'Result 1', 'error': None
        })

        mock_sandbox2 = AsyncMock()
        mock_sandbox2.execute_code = AsyncMock(return_value={
            'result': 'Result 2', 'error': None
        })

        # Execute concurrently
        tasks = [
            tool.execute(mock_sandbox1, {'code': 'print("test1")', 'timeout': 30}),
            tool.execute(mock_sandbox2, {'code': 'print("test2")', 'timeout': 30})
        ]

        results = await asyncio.gather(*tasks)

        # Verify both executions
        self.assertEqual(results[0]['result'], 'Result 1')
        self.assertEqual(results[1]['result'], 'Result 2')


if __name__ == '__main__':
    import asyncio
    unittest.main()
