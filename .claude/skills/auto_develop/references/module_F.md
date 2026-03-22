# 模块 F：FastAPI 接口

## 1. 设计概述

SmartClaw 采用前后端分离架构，后端通过 FastAPI 提供 RESTful API 和 SSE 流式响应接口。

**设计决策**：

| 决策项 | 选择 | 说明 |
|-------|------|------|
| 流式响应方案 | **SSE** | Server-Sent Events，单向流，实现简单，适合 AI 响应场景 |
| 认证机制 | **不需要** | 个人电脑场景，无需认证 |
| 请求限流 | **不需要** | 单用户场景，无需限流 |

## 2. API 端点

### 2.1 会话管理 API (`/api/sessions`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| POST | `/api/sessions` | 创建或获取会话 | `{session_key}` | `SessionInfo` |
| GET | `/api/sessions/{session_key}` | 获取会话信息 | - | `SessionInfo` |
| GET | `/api/sessions` | 列出所有会话 | - | `List[SessionInfo]` |
| POST | `/api/sessions/{session_key}/archive` | 归档会话 | - | `SuccessResponse` |
| DELETE | `/api/sessions/{session_key}` | 关闭并删除会话 | - | `SuccessResponse` |

### 2.2 消息处理 API (`/api/messages`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| POST | `/api/messages` | 发送消息（同步响应） | `SendMessageRequest` | `MessageResponse` |
| POST | `/api/messages/stream` | 发送消息（SSE 流式） | `SendMessageRequest` | SSE 流 |
| GET | `/api/messages/{session_key}/history` | 获取消息历史 | - | `List[Message]` |

### 2.3 记忆管理 API (`/api/memory`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| GET | `/api/memory/core` | 获取所有核心记忆 | - | `Dict[str, str]` |
| GET | `/api/memory/core/{file_key}` | 获取指定核心记忆 | - | `{content}` |
| PUT | `/api/memory/core/{file_key}` | 写入核心记忆 | `WriteCoreRequest` | `SuccessResponse` |
| GET | `/api/memory/near` | 获取近端记忆 | `?days=N` | `List[NearMemoryEntry]` |
| POST | `/api/memory/near` | 写入近端记忆 | `WriteNearRequest` | `SuccessResponse` |

### 2.4 RAG 检索 API (`/api/search`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| POST | `/api/search` | 搜索长期记忆 | `SearchRequest` | `SearchResponse` |
| POST | `/api/search/index/rebuild` | 重建索引 | - | `SuccessResponse` |

### 2.5 技能管理 API (`/api/skills`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| GET | `/api/skills` | 获取技能列表 | - | `List[SkillInfo]` |
| GET | `/api/skills/{skill_name}` | 获取技能详情 | - | `SkillInfo` |

### 2.6 健康检查 API (`/api/health`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| GET | `/api/health` | 健康检查 | - | `HealthStatus` |

## 3. 数据模型

### 3.1 请求模型

```python
# api/models/requests.py
from pydantic import BaseModel, Field
from typing import Optional, Tuple
from datetime import date

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    session_key: str = Field(..., description="前端生成的客户端 ID")

class SendMessageRequest(BaseModel):
    """发送消息请求"""
    session_key: str = Field(..., description="会话标识")
    message: str = Field(..., description="用户消息内容")

class WriteCoreRequest(BaseModel):
    """写入核心记忆请求"""
    content: str = Field(..., description="记忆内容")
    mode: str = Field(default="append", description="写入模式：append/replace")

class WriteNearRequest(BaseModel):
    """写入近端记忆请求"""
    content: str = Field(..., description="记忆内容")
    category: Optional[str] = Field(default=None, description="内容类别")
    date: Optional[str] = Field(default=None, description="日期 YYYY-MM-DD")

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(default=5, description="返回结果数量")
    date_range: Optional[Tuple[str, str]] = Field(default=None, description="日期范围")
```

### 3.2 响应模型

```python
# api/models/responses.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    session_key: str
    created_at: datetime
    last_active: datetime
    status: str = "active"

class Message(BaseModel):
    """消息"""
    role: str  # user/assistant/tool
    content: str
    timestamp: datetime

class MessageResponse(BaseModel):
    """消息响应"""
    response: str
    session_id: str
    message_count: int

class SearchResult(BaseModel):
    """搜索结果"""
    content: str
    source: str
    file_type: str
    timestamp: Optional[str]
    score: float

class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[SearchResult]
    total_count: int

class SkillInfo(BaseModel):
    """技能信息"""
    name: str
    description: str
    location: str

class HealthStatus(BaseModel):
    """健康状态"""
    status: str  # healthy/unhealthy
    version: str
    uptime: float
    components: Dict[str, str]

class ErrorResponse(BaseModel):
    """错误响应"""
    error_code: str
    message: str
    detail: Optional[str] = None
    suggestion: Optional[str] = None

class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool
    message: str
    data: Optional[dict] = None
```

## 4. SSE 流式响应

### 4.1 请求格式

```http
POST /api/messages/stream
Content-Type: application/json

{
  "session_key": "client_abc123",
  "message": "帮我写一个 Python 脚本"
}
```

### 4.2 响应格式

```
data: {"content": "好的"}
data: {"content": "，"}
data: {"content": "我来"}
data: {"content": "帮你"}
data: {"content": "写一个"}
data: {"content": "Python"}
data: {"content": "脚本"}
data: {"content": "..."}

data: [DONE]
```

### 4.3 实现代码

```python
# api/routers/messages.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

from ..models.requests import SendMessageRequest
from ..dependencies import get_agent_manager

router = APIRouter()

@router.post("/stream")
async def send_message_stream(
    request: SendMessageRequest,
    agent_manager = Depends(get_agent_manager)
):
    """发送消息并流式返回响应（SSE）"""

    async def event_generator():
        try:
            async for chunk in agent_manager.send_message(
                session_key=request.session_key,
                message=request.message
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

## 5. FastAPI 应用入口

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import sessions, messages, memory, search, skills, health
from .exceptions import setup_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    from backend.config import ConfigManager
    from backend.memory import MemoryManager
    from backend.rag import RAGManager
    from backend.agent import AgentManager

    config = ConfigManager.load()
    app.state.config = config
    app.state.memory_manager = MemoryManager(config)
    app.state.rag_manager = RAGManager(config)
    app.state.agent_manager = AgentManager(config)

    yield

    # 关闭时清理
    app.state.rag_manager.stop_watcher()

app = FastAPI(
    title="SmartClaw API",
    description="SmartClaw Agent RESTful API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(health.router, prefix="/api", tags=["Health"])

# 异常处理
setup_exception_handlers(app)
```

## 6. 依赖注入

```python
# api/dependencies.py
from fastapi import Request
from functools import lru_cache

from backend.agent import AgentManager
from backend.memory import MemoryManager
from backend.rag import RAGManager
from backend.config import ConfigManager

def get_agent_manager(request: Request) -> AgentManager:
    """获取 AgentManager 实例"""
    return request.app.state.agent_manager

def get_memory_manager(request: Request) -> MemoryManager:
    """获取 MemoryManager 实例"""
    return request.app.state.memory_manager

def get_rag_manager(request: Request) -> RAGManager:
    """获取 RAGManager 实例"""
    return request.app.state.rag_manager

def get_config(request: Request) -> ConfigManager:
    """获取配置实例"""
    return request.app.state.config
```

## 7. 错误处理

### 7.1 异常处理器

```python
# api/exceptions.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.errors import (
    SmartClawError, ConfigError, SessionError,
    MemoryError, RAGError, ToolError, SecurityError
)

def setup_exception_handlers(app):
    """注册异常处理器"""

    @app.exception_handler(SmartClawError)
    async def smartclaw_exception_handler(request: Request, exc: SmartClawError):
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "detail": exc.detail,
                "suggestion": exc.suggestion
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VAL_001",
                "message": "请求参数验证失败",
                "detail": str(exc.errors()),
                "suggestion": "请检查请求参数格式"
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "detail": None,
                "suggestion": None
            }
        )
```

### 7.2 错误处理路径

| 错误场景 | HTTP 状态码 | 处理方式 |
|---------|------------|---------|
| session_key 无效 | 200 | 自动创建新会话 |
| LLM API 超时 | 500 | 重试 3 次，返回错误信息 |
| 工具执行失败 | 200 | 返回错误信息给 Agent，让 Agent 决定如何处理 |
| 文件写入失败 | 500 | 重试 3 次，记录日志 |
| 请求参数验证失败 | 422 | 返回详细验证错误 |
| 配置错误 | 500 | 返回配置错误信息 |

## 8. 启动与测试

**启动命令**：
```bash
# 开发模式
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**API 文档访问**：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**测试接口**：
```bash
# 创建会话
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_key": "test_client_123"}'

# 发送消息（流式）
curl -X POST http://localhost:8000/api/messages/stream \
  -H "Content-Type: application/json" \
  -d '{"session_key": "test_client_123", "message": "你好"}'

# 搜索记忆
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "用户偏好", "top_k": 5}'
```

## 9. 项目路由结构

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sessions.py         # 会话管理 API
│   │   ├── messages.py         # 消息处理 API（含 SSE）
│   │   ├── memory.py           # 记忆管理 API
│   │   ├── search.py           # RAG 检索 API
│   │   ├── skills.py           # 技能管理 API
│   │   └── health.py           # 健康检查 API
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py         # 请求模型定义
│   │   └── responses.py        # 响应模型定义
│   ├── dependencies.py         # 依赖注入
│   └── exceptions.py           # API 异常处理
```
