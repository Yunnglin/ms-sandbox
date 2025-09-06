# 快速开始指南

## 安装依赖

```bash
pip install docker fastapi uvicorn httpx pydantic
```

## 构建Docker镜像

```bash
./build_sandbox_image.sh
```

## 验证系统

```bash
python test_refactor.py
```

## 启动服务器

```bash
python -m ms_sandbox.sandbox.run_server
```

服务器将在 http://localhost:8000 启动
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 运行示例

```bash
python examples/usage_examples.py
```

## 基本使用

### 1. 管理器模式 (直接使用)

```python
import asyncio
from ms_sandbox.sandbox import SandboxManager, DockerSandboxConfig

async def main():
    async with SandboxManager() as manager:
        config = DockerSandboxConfig(image="python-sandbox:latest")
        sandbox_id = await manager.create_sandbox("docker", config)

        result = await manager.execute_code(
            sandbox_id,
            "print('Hello, Sandbox!')"
        )
        print(result)

asyncio.run(main())
```

### 2. 客户端模式 (HTTP API)

```python
import asyncio
from ms_sandbox.sandbox import HttpSandboxClient, DockerSandboxConfig

async def main():
    async with HttpSandboxClient() as client:
        config = DockerSandboxConfig(image="python-sandbox:latest")
        sandbox_id = await client.create_sandbox("docker", config)

        await client.set_current_sandbox(sandbox_id)
        result = await client.execute_code_current("print('Hello, HTTP!')")
        print(result)

asyncio.run(main())
```

## 故障排除

### Docker相关问题

1. 确保Docker已安装并运行
2. 确保用户有Docker权限: `sudo usermod -aG docker $USER`
3. 重启终端或重新登录

### 网络问题

1. 检查防火墙设置
2. 确保端口8000未被占用
3. 尝试使用127.0.0.1而不是localhost

### 权限问题

1. 确保Docker镜像可访问
2. 检查文件系统权限
3. 运行时使用适当的用户权限

## 下一步

1. 查看完整文档: [REFACTOR_README.md](REFACTOR_README.md)
2. 探索API文档: http://localhost:8000/docs
3. 查看使用示例: [examples/usage_examples.py](examples/usage_examples.py)
4. 开发自定义工具和沙箱类型
