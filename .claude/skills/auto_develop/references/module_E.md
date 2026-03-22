# 模块 E：Agent 模块

## 1. 模块概述

Agent 模块是 SmartClaw 的核心协调器，负责整合记忆、工具、检索等子系统，提供统一的 AI 交互体验。

**技术栈**：
- **Agent 框架**：使用 LangChain v1.0 的 `create_agent` API 创建 Agent
- **复杂状态管理**：使用 LangGraph 管理预压缩冲刷等复杂流程
- **会话存储**：使用 LangGraph 的 InMemorySaver 管理每轮 Session 的历史会话

**设计原则**：
1. **LangChain v1.0 作为 Agent 框架**：利用 LangChain 的成熟实现，减少自研复杂度
2. **LangGraph 管理复杂状态**：将预压缩冲刷等复杂流程从 LangChain Agent 中解耦
3. **混合状态管理策略**：根据状态特性选择最优管理方式，平衡性能和持久性
4. **LangChain 与 LangGraph 协作**：清晰的职责分离

## 2. 核心组件

### 2.1 SmartClawAgent

```python
from langchain.agents import create_agent, AgentExecutor
from langchain.graph import Graph
from langchain.memory import ConversationBufferMemory
from langgraph.graph import GraphState

class SmartClawAgent:
    def __init__(self, config):
        # LangChain Agent 配置
        self.llm = config.llm.default
        self.tools = self._load_tools()
        self.memory = InMemorySaver()

        # LangGraph 状态管理
        self.graph = self._create_graph()

        # 工具调用管理
        self.agent = self._create_agent()
```

### 2.2 SystemPromptBuilder

System Prompt 拼接器，负责按顺序加载记忆文件。

**加载顺序**（严格遵循）：
1. AGENTS.md — Agent 基础定义
2. SKILLS_SNAPSHOT.md — 可用技能列表
3. SOUL.md — 人格与边界
4. IDENTITY.md — 名称与风格
5. USER.md — 用户画像
6. MEMORY.md — 用户偏好与重要决策
7. 近端记忆 — 最近 N 天的对话摘要

```python
class SystemPromptBuilder:
    """System Prompt 拼接器"""

    def build_prompt(self, session_id: str) -> str:
        """拼接完整的 System Prompt

        Args:
            session_id: 会话标识

        Returns:
            拼接后的 System Prompt 字符串
        """
        prompt_parts = []

        # 1. 加载核心记忆（按顺序）
        core_memory = self._load_core_memory()
        if core_memory:
            prompt_parts.append(f"## 核心记忆\n{core_memory}")

        # 2. 加载近端记忆（最近 2 天）
        near_memory = self._load_near_memory(days=2)
        if near_memory:
            prompt_parts.append(f"## 近期对话摘要\n{near_memory}")

        # 3. 加载会话上下文（可选）
        context = self._get_session_context(session_id)
        if context:
            prompt_parts.append(f"## 当前会话\n{context}")

        return "\n\n".join(prompt_parts)
```

**完整构建流程**：

```python
def build_system_prompt(self, session_key: str) -> str:
    """
    构建 System Prompt
    加载顺序：AGENTS.md → SKILLS_SNAPSHOT.md → SOUL.md → IDENTITY.md → USER.md → MEMORY.md → 近端记忆
    """
    session_info = self.session_manager.get_session(session_key)
    session_id = session_info.session_id if session_info else None
    prompt_parts = []

    # 1. 加载核心记忆文件
    core_files = [
        "AGENTS.md",      # Agent 自身信息
        "SKILLS_SNAPSHOT.md",  # 可用技能列表
        "SOUL.md",        # 人格、语气、边界
        "IDENTITY.md",    # 名称、风格、表情
        "USER.md",        # 用户画像、称呼方式
        "MEMORY.md"       # 用户偏好、重要决策
    ]

    for file_path in core_files:
        try:
            content = self.read_file(file_path)
            if content:
                prompt_parts.append(content)
        except Exception as e:
            self.logger.warning(f"Failed to load {file_path}: {e}")

    # 2. 加载近端记忆（最近2天）
    near_memory = self.memory.load_near_memory(days=2)
    if near_memory:
        prompt_parts.append(f"\n## 近期对话摘要\n{near_memory}")

    # 3. 添加会话上下文（可选）
    context = self.get_session_context(session_id)
    if context:
        prompt_parts.append(f"\n## 当前会话\n{context}")

    return "\n\n".join(prompt_parts)
```

### 2.3 AgentGraph（LangGraph 状态管理）

```python
from typing import TypedDict
from langgraph.checkpoint import MemorySaver

class AgentState(TypedDict):
    """Agent 状态定义"""
    messages: list
    flush_triggered: bool
    flush_messages: list
    session_id: str

class AgentGraph:
    """Agent 图构建"""

    def __init__(self, config):
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建 Agent 状态图"""
        from langgraph.graph import StateGraph

        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("check_flush", self._check_flush_node)
        workflow.add_node("compress", self._compress_node)

        # 添加边
        workflow.add_conditional_edges(
            "agent",
            self._should_flush,
            {
                "flush": "check_flush",
                "end": "__end__"
            }
        )
        workflow.add_edge("check_flush", "agent")
        workflow.add_edge("compress", "__end__")

        return workflow.compile(checkpointer=self.checkpointer)
```

### 2.4 ToolRegistry

工具注册器，负责所有工具的注册和管理。

```python
class ToolRegistry:
    """工具注册器"""

    def __init__(self, config):
        self.tools = []
        self.config = config

    def register_all(self):
        """注册所有工具"""
        # 1. 注册内置工具
        self._register_builtin_tools()

        # 2. 注册记忆工具
        self._register_memory_tools()

        # 3. 注册 RAG 工具
        self._register_rag_tools()

        return self.tools

    def _register_builtin_tools(self):
        """注册内置工具"""
        from core_tools import (
            terminal_tool,
            python_repl_tool,
            fetch_url_tool,
            read_file_tool,
            write_file_tool
        )
        self.tools.extend([
            terminal_tool,
            python_repl_tool,
            fetch_url_tool,
            read_file_tool,
            write_file_tool
        ])

    def _register_memory_tools(self):
        """注册记忆写入工具（由 Memory 模块提供）"""
        from memory.tools import (
            write_near_memory_tool,
            write_core_memory_tool
        )
        self.tools.extend([
            write_near_memory_tool,
            write_core_memory_tool
        ])

    def _register_rag_tools(self):
        """注册记忆检索工具（由 RAG 模块提供）"""
        from rag.tools import search_memory_tool
        self.tools.append(search_memory_tool)
```

### 2.5 预压缩冲刷机制

**设计原则**：
- 函数式实现而非状态机
- 信息优先级保护
- Agent 驱动的信息提取
- 透明可恢复

**函数式实现**：

```python
def check_and_trigger_flush(self, session_id):
    """检查并触发预压缩冲刷"""
    messages = self.get_session_messages(session_id)
    total_tokens = self.count_tokens(messages)

    if total_tokens > self.config.session.token_threshold:
        self.logger.info(f"Token threshold reached: {total_tokens}")

        # 1. 触发预压缩流程
        flush_messages = self.get_oldest_messages(
            messages,
            ratio=self.config.memory.near_memory.flush_ratio
        )

        # 2. 构建冲刷提示
        flush_prompt = self.build_flush_prompt(flush_messages)

        # 3. 插入冲刷消息到会话
        self.insert_flush_message(session_id, flush_prompt)

        # 4. 等待 Agent 处理
        # Agent 会调用 write_near_memory，然后回复 NO_REPLY

        return True
    return False

def on_flush_completed(self, session_id):
    """冲刷完成后的处理"""
    messages = self.get_session_messages(session_id)
    flush_messages = self.get_flush_messages(messages)

    # 1. 压缩会话
    compressed = self.compress_conversation(flush_messages)

    # 2. 更新会话历史
    self.update_conversation_history(session_id, compressed)

    # 3. 清理冲刷标记
    self.clear_flush_markers(session_id)
```

**防抖机制**：

```python
def _should_trigger_flush(self, session_id):
    """检查是否应该触发冲刷（带防抖）"""
    now = time.time()
    last_flush = self.get_last_flush_time(session_id)

    # 避免连续触发，最小间隔10秒
    if last_flush and (now - last_flush) < 10:
        return False

    # 检查token数量
    if self.check_and_trigger_flush(session_id):
        self.update_last_flush_time(session_id, now)
        return True

    return False
```

### 2.6 混合状态管理

**状态管理策略**：

| 状态类型 | 管理方式 | 持久化 | 作用范围 |
|---------|---------|--------|---------|
| Agent 会话状态 | LangChain Agent | 内存 | 单次会话 |
| 工具调用状态 | LangGraph | 内存 | 复杂流程 |
| 记忆状态 | Memory 模块 | 文件 | 跨会话 |
| 容器状态 | ContainerManager | 内存 | 会话绑定 |

**会话标识使用规范**：

| 场景 | 使用标识 | 说明 |
|-----|---------|------|
| 外部 API 接口 | `session_key` | 前端传入的客户端 ID |
| 内部状态管理 | `session_id` | 后端生成的会话唯一标识 |
| 容器绑定 | `session_id` | 容器与会话实例绑定 |
| 日志追踪 | 两者都记录 | 便于关联和排查 |

**状态传递机制**：

```python
def process_message(self, message, session_key):
    # 0. 获取 session_id（通过 session_key 查询 sessions.json）
    session_info = self.session_manager.get_session(session_key)
    if not session_info:
        session_info = self.session_manager.create_session(session_key)
    session_id = session_info.session_id

    # 1. LangChain 处理基础会话
    response = self.agent.run(
        input=message,
        state={"session_id": session_id}
    )

    # 2. 检查是否需要触发预压缩
    if self._should_trigger_flush(session_id):
        # 3. 交由 LangGraph 处理复杂状态
        self.graph.invoke({
            "messages": self.get_session_messages(session_id),
            "session_id": session_id
        })

    return response
```

## 3. 接口规范

### 3.1 AgentManager 接口

AgentManager 是 Agent 模块的核心入口，负责 Agent 实例的创建、管理和调度。

**职责范围**：
- 根据 session_key 创建或获取 Agent 实例
- 管理 Agent 的生命周期
- 协调 Memory、RAG、Tools 等子模块
- 处理消息的接收和响应

**会话标识说明**：
- **外部接口**：使用 `session_key`（前端传入的客户端 ID）
- **内部状态**：使用 `session_id`（后端生成的会话唯一标识）
- AgentManager 内部负责 `session_key` → `session_id` 的转换

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `get_or_create_session(session_key: str) -> SessionInfo` | 获取或创建会话，返回会话信息 |
| `get_agent(session_key: str) -> Agent` | 根据 session_key 获取 Agent 实例 |
| `send_message(session_key: str, message: str) -> AsyncIterator[str]` | 发送消息并流式返回响应 |
| `close_session(session_key: str) -> None` | 关闭会话并清理资源 |
| `archive_session(session_key: str) -> str` | 归档会话到长期记忆，返回归档路径 |

**依赖注入**：
- 接收 ConfigManager 实例获取配置
- 接收 SessionManager 实例管理会话映射
- 接收 MemoryManager 实例管理记忆
- 接收 RAGManager 实例进行检索
- 接收 ToolRegistry 实例注册工具

### 3.2 Session 接口

Session 代表单个对话会话，维护会话状态和历史消息。

**职责范围**：
- 存储会话的消息历史
- 追踪 token 使用量
- 触发预压缩冲刷
- 生成会话摘要

**主要属性**：

| 属性名 | 类型 | 说明 |
|-------|------|------|
| `session_key` | str | 前端生成的匿名客户端 ID（外部标识） |
| `session_id` | str | 后端生成的会话唯一标识（内部标识，格式：`{YYYY-MM-DD}-{random}`） |
| `messages` | List[Message] | 消息历史列表 |
| `token_count` | int | 当前 token 总数 |
| `created_at` | datetime | 会话创建时间 |
| `status` | SessionStatus | 会话状态（active/archived/closed） |

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `add_message(role: str, content: str) -> None` | 添加消息到历史 |
| `get_messages() -> List[Message]` | 获取所有消息 |
| `check_flush_needed() -> bool` | 检查是否需要预压缩冲刷 |
| `compress_history() -> str` | 压缩历史消息，返回摘要 |
| `to_markdown() -> str` | 将会话导出为 Markdown 格式 |

### 3.3 SystemPromptBuilder 接口

SystemPromptBuilder 负责 System Prompt 的拼接和管理。

**职责范围**：
- 按顺序加载核心记忆文件
- 加载近端记忆内容
- 加载 Skills Snapshot
- 处理 token 限制和截断

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `build(session_id: str) -> str` | 构建完整的 System Prompt |
| `load_core_memory() -> str` | 加载核心记忆内容 |
| `load_near_memory(days: int) -> str` | 加载近端记忆内容 |
| `estimate_tokens(content: str) -> int` | 估算内容的 token 数 |
| `truncate_to_limit(content: str, max_tokens: int) -> str` | 截断内容到指定 token 限制 |

### 3.4 SessionInfo 数据模型

```python
from pydantic import BaseModel
from datetime import datetime

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str              # 格式: {YYYY-MM-DD}-{random}
    session_key: str             # 前端生成的匿名客户端 ID
    created_at: datetime
    last_active: datetime
    status: str = "active"       # active / archived
```

### 3.5 Message 数据模型

Message 表示对话中的单条消息。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `role` | str | 角色（user/assistant/system/tool） |
| `content` | str | 消息内容 |
| `timestamp` | datetime | 消息时间戳 |
| `token_count` | int | 消息的 token 数量 |
| `tool_calls` | Optional[List] | 工具调用记录（如有） |
| `tool_results` | Optional[List] | 工具返回结果（如有） |

### 3.6 Agent 工具接口规范

所有供 Agent 调用的工具必须遵循 LangChain 的 `@tool` 装饰器规范。

**命名规范**：
- 工具名称使用 snake_case 格式
- 名称应简洁且能准确描述功能
- 避免使用缩写或模糊名称

**文档字符串规范**：
- 第一行简述功能（不超过 80 字符）
- 空行后详细描述功能和使用方法
- 使用 Args/Returns/Example 等标准段落
- 提供清晰的使用示例

**参数规范**：
- 使用 Python 类型注解
- 必需参数在前，可选参数在后
- 可选参数必须提供默认值
- 复杂参数类型使用 Pydantic 模型

**返回值规范**：
- 返回类型为 str
- 返回内容应易于 Agent 理解和处理
- 错误情况返回清晰的错误描述
- 大量数据应进行截断或分页

**工具列表**：

| 工具名称 | 参数 | 返回值说明 |
|---------|------|----------|
| `terminal` | command: str | 命令执行输出或错误信息 |
| `python_repl` | code: str | 代码执行结果或错误信息 |
| `fetch_url` | url: str | 清洗后的网页内容 |
| `read_file` | file_path: str | 文件内容 |
| `write_file` | file_path: str, content: str | 操作结果消息 |
| `search_memory` | query: str, top_k: int, date_range: tuple | 格式化的检索结果 |
| `write_near_memory` | content: str, category: str, date: str | 操作结果消息 |
| `write_core_memory` | file_key: str, content: str, mode: str | 操作结果消息 |

### 3.7 ToolRegistry 接口

ToolRegistry 负责所有工具的注册和管理。

**职责范围**：
- 注册所有内置工具
- 管理工具实例的生命周期
- 提供工具查找接口
- 协调容器管理器

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `register_tools() -> None` | 注册所有工具 |
| `get_tool(name: str) -> Tool` | 获取工具实例 |
| `get_all_tools() -> List[Tool]` | 获取所有工具列表 |
| `cleanup_session(session_id: str) -> None` | 清理会话相关资源 |

**工具分类**：
- **基础工具（5个）**：terminal, python_repl, fetch_url, read_file, write_file
- **记忆工具（3个）**：search_memory（RAG 提供）, write_near_memory（Memory 提供）, write_core_memory（Memory 提供）
