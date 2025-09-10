import asyncio

from ms_sandbox.sandbox.manager import HttpSandboxManager
from ms_sandbox.sandbox.model import DockerSandboxConfig, SandboxType


async def main():

    async with HttpSandboxManager(base_url='http://127.0.0.1:8000') as manager:
        # Create sandbox
        config = DockerSandboxConfig(image='python:3.11-slim', tools_config={'python_executor': {}})
        sandbox_id = await manager.create_sandbox(SandboxType.DOCKER, config)

        # Execute code
        result = await manager.execute_tool(
            sandbox_id, 'python_executor', {'code': 'print("Hello from remote sandbox!")'}
        )
        print(result.model_dump())


asyncio.run(main())
