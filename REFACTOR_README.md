# Agent Sandbox System - 重构文档

## 项目概述

这是一个重构后的agent沙箱系统，提供安全的代码执行环境，具有模块化、可扩展的架构。系统支持Docker环境隔离，提供Python代码执行、文件读写、shell命令执行等工具，并基于FastAPI实现了客户端/服务器分离的使用模式。

## 架构设计

### 目录结构

```
sandbox/
├── model/              # 数据模型 (pydantic)
│   ├── __init__.py
│   ├── base.py         # 基础模型和枚举
│   ├── requests.py     # 请求模型
│   ├── responses.py    # 响应模型
│   └── config.py       # 配置模型
├── tools/              # 工具接口和实现
│   ├── __init__.py
│   ├── base.py         # 工具基类和工厂
│   ├── python_executor.py    # Python代码执行
│   ├── shell_executor.py     # Shell命令执行
│   └── file_operations.py    # 文件读写操作
├── boxes/              # 沙箱实现
│   ├── __init__.py
│   ├── base.py         # 沙箱基类和工厂
│   └── docker_sandbox.py     # Docker沙箱实现
├── manager/            # 沙箱环境管理器
│   ├── __init__.py
│   └── sandbox_manager.py    # 沙箱管理器
├── client/             # 客户端接口
│   ├── __init__.py
│   ├── base.py         # 客户端基类
│   └── http_client.py  # HTTP客户端实现
├── server.py           # FastAPI服务器
└── run_server.py       # 服务器启动脚本
```

### 核心组件

#### 1. 数据模型 (model/)

- **BaseModel**: 所有模型的基类，基于pydantic
- **SandboxConfig**: 沙箱配置基类
- **DockerSandboxConfig**: Docker特定配置
- **Request/Response Models**: 统一的API请求/响应格式

#### 2. 工具系统 (tools/)

- **BaseTool**: 工具抽象基类
- **ToolFactory**: 工具工厂，支持动态注册
- **PythonExecutor**: Python代码执行工具
- **ShellExecutor**: Shell命令执行工具
- **FileReader/FileWriter**: 文件操作工具

#### 3. 沙箱实现 (boxes/)

- **BaseSandbox**: 沙箱抽象基类
- **SandboxFactory**: 沙箱工厂
- **DockerSandbox**: Docker沙箱实现，提供完整的容器隔离

#### 4. 管理器 (manager/)

- **SandboxManager**: 核心管理器，负责沙箱生命周期管理
- 支持异步操作
- 自动清理过期沙箱
- 提供统计信息

#### 5. 客户端接口 (client/)

- **BaseSandboxClient**: 客户端抽象基类
- **HttpSandboxClient**: HTTP客户端实现
- 支持异步操作和上下文管理器

#### 6. 服务器 (server.py)

- 基于FastAPI的RESTful API
- 完整的OpenAPI文档
- 异步请求处理
- CORS支持

## 主要特性

### 1. 模块化设计

- 清晰的职责分离
- 易于扩展和维护
- 支持插件式工具注册

### 2. 类型安全

- 基于pydantic的数据验证
- 完整的类型注解
- 自动API文档生成

### 3. 异步支持

- 全异步架构
- 高并发处理能力
- 非阻塞I/O操作

### 4. 安全隔离

- Docker容器隔离
- 资源限制
- 网络隔离选项
- 文件系统访问控制

### 5. 工具扩展性

- 工具注册机制
- 可配置的安全策略
- 灵活的参数验证

## 使用方式

### 1. 直接使用管理器

```python
import asyncio
from ms_sandbox.sandbox import SandboxManager, DockerSandboxConfig

async def main():
    manager = SandboxManager()
    await manager.start()
    
    try:
        # 创建沙箱
        config = DockerSandboxConfig(image="python:3.11-slim")
        sandbox_id = await manager.create_sandbox("docker", config)
        
        # 执行代码
        result = await manager.execute_code(
            sandbox_id, 
            "print('Hello from sandbox!')"
        )
        print(result)
        
        # 清理
        await manager.delete_sandbox(sandbox_id)
    finally:
        await manager.stop()

asyncio.run(main())
```

### 2. 使用客户端/服务器模式

**启动服务器:**
```bash
python -m ms_sandbox.sandbox.run_server
```

**使用客户端:**
```python
import asyncio
from ms_sandbox.sandbox import HttpSandboxClient, DockerSandboxConfig

async def main():
    async with HttpSandboxClient("http://localhost:8000") as client:
        # 创建沙箱
        config = DockerSandboxConfig(image="python:3.11-slim")
        sandbox_id = await client.create_sandbox("docker", config)
        
        # 设置为当前沙箱
        await client.set_current_sandbox(sandbox_id)
        
        # 执行代码
        result = await client.execute_code_current(
            "print('Hello from HTTP client!')"
        )
        print(result)

asyncio.run(main())
```

### 3. 上下文管理器

```python
async with SandboxManager() as manager:
    config = DockerSandboxConfig(image="python:3.11-slim")
    sandbox_id = await manager.create_sandbox("docker", config)
    
    # 使用沙箱
    result = await manager.execute_code(sandbox_id, "print('Hello!')")
    
# 自动清理
```

## API接口

### RESTful API端点

- `POST /sandbox/create` - 创建沙箱
- `GET /sandbox/{id}` - 获取沙箱信息
- `GET /sandbox/list` - 列出所有沙箱
- `DELETE /sandbox/{id}` - 删除沙箱
- `POST /sandbox/execute/code` - 执行代码
- `POST /sandbox/execute/command` - 执行命令
- `POST /sandbox/file/read` - 读取文件
- `POST /sandbox/file/write` - 写入文件
- `POST /sandbox/tool/execute` - 执行工具
- `GET /sandbox/{id}/tools` - 获取可用工具
- `GET /health` - 健康检查
- `GET /stats` - 系统统计

API文档可通过 `http://localhost:8000/docs` 访问

## 配置选项

### Docker沙箱配置

```python
DockerSandboxConfig(
    image="python:3.11-slim",       # Docker镜像
    timeout=30,                     # 超时时间
    memory_limit="512m",            # 内存限制
    cpu_limit=1.0,                  # CPU限制
    network_enabled=False,          # 网络访问
    working_dir="/sandbox",         # 工作目录
    env_vars={"VAR": "value"},      # 环境变量
    volumes={},                     # 卷挂载
    ports={},                       # 端口映射
)
```

### 工具配置

```python
PythonExecutorConfig(
    timeout=30,                     # 执行超时
    allowed_modules=["math", "json"], # 允许的模块
    blocked_modules=["os", "sys"],  # 禁止的模块
    max_output_size=1024*1024,      # 最大输出大小
)
```

## 安全特性

1. **容器隔离**: 使用Docker提供进程和文件系统隔离
2. **资源限制**: 可配置内存和CPU限制
3. **网络隔离**: 可选择禁用网络访问
4. **模块控制**: Python执行器支持模块白名单/黑名单
5. **命令控制**: Shell执行器支持命令过滤
6. **文件访问控制**: 文件操作支持路径限制
7. **超时保护**: 所有操作都有超时限制

## 扩展开发

### 添加新工具

```python
from ms_sandbox.sandbox.tools import BaseTool, register_tool
from ms_sandbox.sandbox.model import ToolType

@register_tool(ToolType.MY_TOOL)
class MyTool(BaseTool):
    @property
    def tool_type(self):
        return ToolType.MY_TOOL
    
    async def execute(self, parameters, **kwargs):
        # 实现工具逻辑
        pass
    
    def validate_parameters(self, parameters):
        # 验证参数
        pass
```

### 添加新沙箱类型

```python
from ms_sandbox.sandbox.boxes import BaseSandbox, register_sandbox

@register_sandbox("my_sandbox")
class MySandbox(BaseSandbox):
    @property
    def sandbox_type(self):
        return "my_sandbox"
    
    async def start(self):
        # 启动逻辑
        pass
    
    # 实现其他抽象方法...
```

## 性能优化

1. **异步架构**: 全异步设计，支持高并发
2. **连接池**: HTTP客户端使用连接池
3. **资源复用**: 沙箱可重复使用
4. **懒加载**: 按需创建和加载组件
5. **自动清理**: 定期清理过期资源

## 监控和日志

- 支持结构化日志
- 提供健康检查端点
- 系统统计信息
- 执行时间追踪
- 错误追踪和报告

## 部署建议

1. **容器化部署**: 推荐使用Docker部署服务器
2. **反向代理**: 使用Nginx或Traefik作为反向代理
3. **负载均衡**: 支持多实例水平扩展
4. **监控**: 集成Prometheus和Grafana
5. **日志**: 集中化日志收集和分析

## 示例和测试

- `examples/usage_examples.py`: 完整的使用示例
- `test_refactor.py`: 重构验证测试
- API文档: `http://localhost:8000/docs`

## 兼容性

- 保留了原有API的向后兼容性
- 支持渐进式迁移
- 提供Legacy导入别名

---

这个重构版本提供了更好的架构设计、更强的类型安全、更灵活的扩展性，同时保持了系统的易用性和安全性。
