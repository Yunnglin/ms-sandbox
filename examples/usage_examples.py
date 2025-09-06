"""Example usage of the sandbox system."""

import asyncio

from ms_sandbox.sandbox import DockerSandboxConfig, HttpSandboxClient, SandboxManager, create_server


async def manager_example():
    """Example using SandboxManager directly."""
    print('=== SandboxManager Example ===')

    # Create manager
    manager = SandboxManager()
    await manager.start()

    try:
        # Create Docker sandbox
        config = DockerSandboxConfig(
            image='python:3.11-slim',
            timeout=30,
            memory_limit='512m',
            cpu_limit=1.0
        )

        sandbox_id = await manager.create_sandbox('docker', config)
        print(f'Created sandbox: {sandbox_id}')

        # Execute Python code
        result = await manager.execute_code(
            sandbox_id,
            "print('Hello from sandbox!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')"
        )
        print(f'Code execution result: {result}')

        # Execute shell command
        result = await manager.execute_command(sandbox_id, 'ls -la /')
        print(f'Command execution result: {result}')

        # Write and read file
        write_result = await manager.write_file(
            sandbox_id,
            '/tmp/test.txt',
            'Hello, sandbox file system!'
        )
        print(f'Write file result: {write_result}')

        read_result = await manager.read_file(sandbox_id, '/tmp/test.txt')
        print(f'Read file result: {read_result}')

        # List sandboxes
        sandboxes = await manager.list_sandboxes()
        print(f'Active sandboxes: {len(sandboxes)}')

        # Cleanup
        await manager.delete_sandbox(sandbox_id)
        print('Sandbox deleted')

    finally:
        await manager.stop()


async def client_server_example():
    """Example using HTTP client/server architecture."""
    print('\n=== Client/Server Example ===')

    # Note: This assumes the server is running separately
    # Run: python -m ms_sandbox.sandbox.server

    async with HttpSandboxClient('http://localhost:8000') as client:
        try:
            # Health check
            health = await client.health_check()
            print(f'Server health: {health}')

            # Create sandbox
            config = DockerSandboxConfig(
                image='python:3.11-slim',
                timeout=30
            )

            sandbox_id = await client.create_sandbox('docker', config)
            print(f'Created sandbox via HTTP: {sandbox_id}')

            # Set as current sandbox
            await client.set_current_sandbox(sandbox_id)

            # Execute code using convenience method
            result = await client.execute_code_current(
                """
import os
import sys

print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment variables: {len(os.environ)}")

# Create some data
data = [i**2 for i in range(10)]
print(f"Squares: {data}")
                """
            )
            print(f'Code execution via HTTP: {result}')

            # File operations
            await client.write_file_current(
                '/tmp/data.json',
                '{"message": "Hello from HTTP client!", "numbers": [1, 2, 3, 4, 5]}'
            )

            read_result = await client.read_file_current('/tmp/data.json')
            print(f'File read via HTTP: {read_result}')

            # Get available tools
            tools = await client.get_sandbox_tools(sandbox_id)
            print(f'Available tools: {tools}')

            # List all sandboxes
            sandboxes = await client.list_sandboxes()
            print(f'Total sandboxes: {len(sandboxes)}')

        except Exception as e:
            print(f'Client error: {e}')
            print('Make sure the server is running: python -m ms_sandbox.sandbox.server')


async def context_manager_example():
    """Example using context managers."""
    print('\n=== Context Manager Example ===')

    # Manager with auto-cleanup
    async with SandboxManager() as manager:
        config = DockerSandboxConfig(image='python:3.11-slim')
        sandbox_id = await manager.create_sandbox('docker', config)

        result = await manager.execute_code(
            sandbox_id,
            """
# Fibonacci sequence
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 Fibonacci numbers
fib_numbers = [fibonacci(i) for i in range(10)]
print(f"Fibonacci sequence: {fib_numbers}")
            """
        )
        print(f'Fibonacci result: {result}')

    print('Manager automatically cleaned up')


def server_example():
    """Example of running the server."""
    print('\n=== Server Example ===')
    print('Starting sandbox server...')

    # Create and run server
    server = create_server(cleanup_interval=600)  # 10 minutes

    print('Server will run on http://localhost:8000')
    print('API documentation available at http://localhost:8000/docs')
    print('Press Ctrl+C to stop')

    try:
        server.run(host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print('\nServer stopped')


async def main():
    """Run all examples."""
    print('Sandbox System Examples')
    print('======================')

    # Run direct manager example
    await manager_example()

    # Run context manager example
    await context_manager_example()

    # Try client/server example (may fail if server not running)
    try:
        await client_server_example()
    except Exception as e:
        print(f'\nClient/server example failed: {e}')
        print('To run the server, execute: python examples/usage_examples.py --server')

    print('\n=== Examples completed ===')


if __name__ == '__main__':
    import sys

    if '--server' in sys.argv:
        server_example()
    else:
        asyncio.run(main())
