"""Simple test script to verify the refactored sandbox system."""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_imports():
    """Test that all imports work correctly."""
    print('Testing imports...')

    try:
        from ms_sandbox.sandbox import (
            Sandbox,
            DockerSandbox,
            DockerSandboxConfig,
            ExecutionStatus,
            FileReader,
            FileWriter,
            HttpSandboxClient,
            LocalSandboxManager,
            PythonExecutor,
            SandboxConfig,
            SandboxServer,
            SandboxStatus,
            ShellExecutor,
            Tool,
            ToolType,
            create_server,
        )
        print('✓ All imports successful')
        return True
    except ImportError as e:
        print(f'✗ Import failed: {e}')
        return False


async def test_models():
    """Test model creation."""
    print('\nTesting models...')

    try:
        from ms_sandbox.sandbox import DockerSandboxConfig, SandboxConfig

        # Test basic config
        config = SandboxConfig(timeout=60)
        print(f'✓ Basic config created: timeout={config.timeout}')

        # Test Docker config
        docker_config = DockerSandboxConfig(
            image='python:3.11-slim',
            timeout=30,
            memory_limit='512m',
            cpu_limit=1.0
        )
        print(f'✓ Docker config created: image={docker_config.image}')

        return True
    except Exception as e:
        print(f'✗ Model test failed: {e}')
        return False


async def test_tool_factory():
    """Test tool factory."""
    print('\nTesting tool factory...')

    try:
        from ms_sandbox.sandbox import PythonExecutor, ToolFactory

        # Check available tools
        available_tools = ToolFactory.get_available_tools()
        print(f'✓ Available tools: {available_tools}')

        # Create a tool
        if ToolType.PYTHON_EXECUTOR in available_tools:
            python_tool = ToolFactory.create_tool(ToolType.PYTHON_EXECUTOR)
            print(f'✓ Python executor created: {type(python_tool).__name__}')

        return True
    except Exception as e:
        print(f'✗ Tool factory test failed: {e}')
        return False


async def test_sandbox_factory():
    """Test sandbox factory."""
    print('\nTesting sandbox factory...')

    try:
        from ms_sandbox.sandbox import DockerSandboxConfig, SandboxFactory

        # Check available sandbox types
        available_types = SandboxFactory.get_available_types()
        print(f'✓ Available sandbox types: {available_types}')

        # Create a sandbox (without starting it)
        if 'docker' in available_types:
            config = DockerSandboxConfig(image='python:3.11-slim')
            sandbox = SandboxFactory.create_sandbox('docker', config)
            print(f'✓ Docker sandbox created: {sandbox.id}')

        return True
    except Exception as e:
        print(f'✗ Sandbox factory test failed: {e}')
        return False


async def test_manager_creation():
    """Test manager creation."""
    print('\nTesting manager creation...')

    try:
        from ms_sandbox.sandbox import LocalSandboxManager

        manager = LocalSandboxManager(cleanup_interval=600)
        print(f'✓ Sandbox manager created')

        # Test stats (should be empty initially)
        stats = manager.get_stats()
        print(f'✓ Manager stats: {stats}')

        return True
    except Exception as e:
        print(f'✗ Manager creation test failed: {e}')
        return False


async def test_server_creation():
    """Test server creation."""
    print('\nTesting server creation...')

    try:
        from ms_sandbox.sandbox import create_server

        server = create_server(cleanup_interval=600)
        print(f'✓ Sandbox server created')
        print(f'✓ FastAPI app available: {server.app is not None}')

        return True
    except Exception as e:
        print(f'✗ Server creation test failed: {e}')
        return False


async def test_client_creation():
    """Test client creation."""
    print('\nTesting client creation...')

    try:
        from ms_sandbox.sandbox import HttpSandboxClient

        client = HttpSandboxClient('http://localhost:8000')
        print(f'✓ HTTP client created with base_url: {client.base_url}')

        return True
    except Exception as e:
        print(f'✗ Client creation test failed: {e}')
        return False


async def main():
    """Run all tests."""
    print('Sandbox System Verification')
    print('===========================')

    tests = [
        test_imports,
        test_models,
        test_tool_factory,
        test_sandbox_factory,
        test_manager_creation,
        test_server_creation,
        test_client_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f'✗ Test {test.__name__} failed with exception: {e}')

    print(f"\n{'='*50}")
    print(f'Test Results: {passed}/{total} passed')

    if passed == total:
        print('🎉 All tests passed! The refactored system is working correctly.')
        print('\nNext steps:')
        print('1. Install required dependencies: pip install docker fastapi uvicorn httpx')
        print('2. Build a Docker image for sandboxes')
        print('3. Run the server: python -m ms_sandbox.sandbox.run_server')
        print('4. Try the examples: python examples/usage_examples.py')
    else:
        print('❌ Some tests failed. Please check the errors above.')

    return passed == total


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
