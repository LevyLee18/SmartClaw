# SmartClaw Agent 模块开发规范 (DEV_SPEC)

## 1. 项目概述

### 1.1 项目背景与目标

SmartClaw 是一个基于 Python 重构的、轻量级且高度透明的 AI Agent 系统，旨在复刻并优化 OpenClaw（原名 Moltbot/Clawdbot）的核心体验。

本项目不追求构建庞大的 SaaS 平台，而是致力于打造一个运行在本地、拥有”真实记忆”的数字副手。其核心目标是：

- 提供可解释、可控制的 AI Agent 交互体验
- 实现真正的长期记忆机制，保留所有对话历史
- 支持灵活的技能扩展系统
- 确保系统稳定性和安全性

### 1.2 核心差异化定位

SmartClaw 的核心差异化定位在于：

- **文件即记忆 (File-first Memory)**：摒弃不透明的向量数据库，回归最原始、最通用的Markdown/JSON文件系统。用户的每一次对话、Agent的每一次反思，都以人类可读的文件形式存在。

- **技能即插件 (Skills as Plugins)**：遵循Anthropic的Agent Skills范式，通过文件夹结构管理能力，实现”拖入即用”的技能扩展。

- **透明可控**：所有的System Prompt拼接逻辑、工具调用过程、记忆读写操作对开发者完全透明，拒绝”黑盒”Agent。

### 1.3 技术架构总览

**技术栈**：
- **Agent 框架**：使用 LangChain v1.0 的 `create_agent` API 创建 Agent
- **复杂状态管理**：使用 LangGraph 管理预压缩冲刷等复杂流程
- **会话存储**：使用 LangGraph 的 InMemorySaver 管理每轮 Session 的历史会话

**核心模块**：
- Agent 模块：负责工具调用决策和会话管理
- Memory 模块：三层记忆架构和生命周期管理
- RAG 模块：混合检索和增量索引更新
- Built-in Tools 模块：9个核心工具的容器化实现
- Configuration 模块：统一的 YAML 配置管理
- Logging 模块：全生命周期日志记录

**数据流向**：
用户输入 → Agent 处理 → 工具调用 → 记忆更新 → 响应生成

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SmartClaw 系统架构                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                                 用户                                    │
│                                                                         │
│  ┌─────────────┐                                                  │
│  │   Web UI    │                                                  │
│  └─────────────┘                                                  │
│           │                                                        │
│           └─────────────────────────────────────────────────────────┘
│                           │                                          │
└───────────────────────────┼─────────────────────────────────────────┘
                           ▼
                    ┌─────────────────────────────────────────────┐
                    │                Agent 层                     │
                    │  ┌─────────────┐  ┌─────────────┐          │
                    │  │ LangChain   │  │  LangGraph  │          │
                    │  │  Agent      │  │  State      │          │
                    │  └─────────────┘  └─────────────┘          │
                    │           │               │                 │
                    │           ▼               ▼                 │
                    │    ┌─────────────────────────────┐        │
                    │    │      工具调用决策            │        │
                    │    └─────────────────────────────┘        │
                    └─────────────────────────────────────────────┘
                                                     │
                             ┌───────────────────────┼───────────────────────┐
                             │                       │                       │
                    ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
                    │   Memory 模块 │      │   RAG 模块    │      │ 内置工具模块  │
                    │               │      │               │      │               │
                    │ • 三层记忆架构 │      │ • 混合检索    │      │ • terminal   │
                    │ • 记忆加载管理 │      │ • 增量索引    │      │ • python_repl│
                    │ • 会话生命周期 │      │ • 文件监听    │      │ • fetch_url  │
                    │               │      │               │      │ • read_file   │
                    │               │      │               │      │ • write_file  │
                    │               │      │               │      │ • search_memory│
                    │               │      │               │      │ • write_near_memory│
                    │               │      │               │      │ • write_core_memory│
                    └───────────────┘      └───────────────┘      └───────────────┘
                             │                       │                       │
                             └───────────────────────┼───────────────────────┘
                                                     │
                                   ┌─────────────────┼─────────────────┐
                                   │                 │                 │
                          ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                          │   配置管理     │  │   日志系统     │  │   监控告警     │
                          │                │  │                │  │                │
                          │ • YAML 配置   │  │ • 全生命周期   │  │ • 性能监控     │
                          │ • 环境变量    │  │ • 关键操作记录 │  │ • 错误告警     │
                          │ • 动态更新    │  │ • 日志轮转     │  │ • 资源监控     │
                          └─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 模块关联关系

#### 2.2.1 Agent 与其他模块的依赖
- **Agent → Memory**：依赖 Memory 模块提供的三层记忆架构
- **Agent → RAG**：依赖 RAG 模块的记忆检索功能
- **Agent → Built-in Tools**：依赖 9 个核心工具的执行能力
- **Agent → Configuration**：依赖配置模块的参数管理
- **Agent → Logging**：依赖日志系统的全生命周期记录

#### 2.2.2 模块间数据流
```
配置加载 → Agent 初始化 → 会话创建 →
↓
用户输入 → System Prompt 拼接 → 工具调用决策 →
↓
工具执行 → 结果返回 → 记忆更新 → 响应生成
↓
Token 检查 → 预压缩冲刷（如需要）→ 会话状态更新
```

### 2.3 数据流向

#### 2.3.1 请求处理流
1. **输入阶段**：用户输入通过 Web UI 接收
2. **System Prompt 构建**：按照预定顺序加载记忆文件
3. **推理阶段**：Agent 做出工具调用决策
4. **执行阶段**：调用相应工具执行任务
5. **响应阶段**：生成最终响应返回给用户
6. **记忆更新**：将重要信息写入记忆系统
7. **状态维护**：更新会话历史和状态

#### 2.3.2 记忆流
```
核心记忆 (MD) → 长期记忆 (RAG) → 近端记忆 (文件) → 会话历史 (内存)
     ↑                                          ↓
     └────────── 检索整合 ───────────────────────┘
```

### 2.4 部署架构

#### 2.4.1 单机部署架构
```
┌─────────────────────────────────────────────────────────────┐
│                    SmartClaw 单机部署                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        客户端层                            │
│  ┌─────────────┐                                            │
│  │   Web UI    │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        应用层                               │
│  ┌─────────────────────────────────────────────┐           │
│  │               Agent Core                     │           │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────┐          │
│  │  │ LangChain   │ │ LangGraph   │ │ Tools   │          │
│  │  │ Agent       │ │ State       │ │ Manager │          │
│  │  └─────────────┘ └─────────────┘ └─────────┘          │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        存储层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Memory    │  │    RAG      │  │   Logs     │        │
│  │   Files     │  │  Indexes    │  │  Files     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

#### 2.4.2 容器化部署（可选）
```yaml
# docker-compose.yml
version: '3.8'
services:
  smartclaw:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ~/.smartclaw:/app/data
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  redis:  # 用于缓存（可选）
    image: redis:alpine
    ports:
      - "6379:6379"
```

## 3. 核心模块设计

### 3.1 Agent 模块

#### 3.1.1 技术选型（LangChain v1.0 + LangGraph）

**设计意图与架构哲学**：

Agent 模块是 SmartClaw 的核心协调器，负责整合记忆、工具、检索等子系统，提供统一的 AI 交互体验。该模块的设计遵循以下原则：

1. **LangChain v1.0 作为 Agent 框架**：成熟稳定的功能丰富的 Agent 框架
   - **create_agent API**：提供简洁的 Agent 创建方式，自动处理工具绑定和 System Prompt 管理
   - **工具调用决策**：LangChain 内置的推理引擎，根据任务和工具描述自动选择最佳工具
   - **结果格式化**：自动格式化工具调用结果，便于 Agent 理解和处理
   - **设计目的**：利用 LangChain 的成熟实现，减少自研复杂度，专注于业务逻辑

2. **LangGraph 管理复杂状态**：处理需要多步骤的复杂流程
   - **状态机管理**：使用 LangGraph 的图状态机管理预压缩冲刷等多步骤流程
   - **条件分支和循环**：支持复杂的条件判断和循环控制
   - **内存状态持久化**：使用 InMemorySaver 保存中间状态，支持流程恢复
   - **设计目的**：将预压缩冲刷等复杂流程从 LangChain Agent 中解耦，简化 Agent 逻辑

3. **混合状态管理策略**：不同类型的状态使用不同管理方式
   - **Agent 会话状态**：LangChain Agent 管理，存储在内存中，单次会话有效
   - **工具调用状态**：LangGraph 管理，用于复杂工作流，状态可持久化
   - **记忆状态**：Memory 模块管理，存储在文件中，跨会话有效
   - **容器状态**：ContainerManager 管理，存储在内存中，会话绑定
   - **设计目的**：根据状态特性选择最优管理方式，平衡性能和持久性

4. **LangChain 与 LangGraph 协作**：清晰的职责分离
   - **LangChain Agent 负责**：基础会话管理、工具调用决策、消息格式化
   - **LangGraph 负责**：预压缩冲刷等复杂多步骤流程
   - **状态传递机制**：通过 session_id 进行状态隔离，支持并发会话
   - **设计目的**：避免状态机过载，保持 Agent 核心逻辑简洁

**技术架构**：
```python
# Agent 模块技术栈
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

**LangChain v1.0 特性**：
- 使用 `create_agent` API 创建 Agent 实例
- 支持自定义工具绑定
- 内置 System Prompt 管理
- 工具调用结果的自动格式化

**LangGraph 集成**：
- 管理复杂的工作流状态
- 处理预压缩冲刷的多步骤流程
- 支持条件分支和循环控制

#### 3.1.2 混合状态管理

**状态管理策略**：

| 状态类型 | 管理方式 | 持久化 | 作用范围 |
|---------|---------|--------|---------|
| Agent 会话状态 | LangChain Agent | 内存 | 单次会话 |
| 工具调用状态 | LangGraph | 内存 | 复杂流程 |
| 记忆状态 | Memory 模块 | 文件 | 跨会话 |
| 容器状态 | ContainerManager | 内存 | 会话绑定 |

**状态传递机制**：
```python
# LangChain Agent 与 LangGraph 的协作
# 注意：外部接口使用 session_key，内部状态使用 session_id
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

**会话标识使用规范**：

| 场景 | 使用标识 | 说明 |
|-----|---------|------|
| 外部 API 接口 | `session_key` | 前端传入的客户端 ID |
| 内部状态管理 | `session_id` | 后端生成的会话唯一标识 |
| 容器绑定 | `session_id` | 容器与会话实例绑定 |
| 日志追踪 | 两者都记录 | 便于关联和排查 |

#### 3.1.3 System Prompt 拼接策略

**拼接算法实现**：
```python
def build_system_prompt(self, session_key: str) -> str:
    """
    构建 System Prompt
    加载顺序：AGENTS.md → SKILLS_SNAPSHOT.md → SOUL.md → IDENTITY.md → USER.md → MEMORY.md → 近端记忆

    Args:
        session_key: 前端传入的会话标识，用于获取 session_id 和会话上下文

    Note:
        内部通过 session_key 获取 session_id，用于加载会话相关上下文
    """
    # 获取 session_id
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

**容错机制**：
- 文件不存在时跳过，继续加载下一个
- 文件读取失败时记录警告
- 保证至少有基本的 Agent 信息

#### 3.1.4 预压缩冲刷机制（函数式）

**设计意图与架构哲学**：

预压缩冲刷机制是 SmartClaw 记忆管理的关键组件，用于在会话 token 数接近上下文窗口上限时，自动将重要信息保存到近端记忆，防止因会话压缩导致的信息丢失。该机制遵循以下设计原则：

1. **函数式实现而非状态机**：采用简单的函数调用链而非复杂的状态机
   - **设计理由**：预压缩冲刷是一个线性的、确定性的流程，不需要状态机的复杂性
   - **优势**：代码简洁、易于理解和维护、状态信息通过函数参数传递
   - **防抖机制**：避免连续触发，最小间隔 10 秒

2. **信息优先级保护**：在压缩前先将重要信息写入近端记忆
   - **触发时机**：会话 token 数超过阈值（默认 3000）时触发
   - **冲刷范围**：最旧的 50% 会话（可配置）
   - **信息提取**：由 Agent 自主判断哪些信息重要，调用 write_near_memory 写入
   - **设计目的**：确保重要信息不会因会话压缩而丢失

3. **Agent 驱动的信息提取**：由 Agent 决定保留哪些信息
   - **冲刷提示**：插入特殊的冲刷消息，引导 Agent 提取重要信息
   - **NO_REPLY 机制**：Agent 完成写入后回复 NO_REPLY，系统继续压缩流程
   - **设计目的**：利用 Agent 的理解能力进行智能筛选，而非简单的规则过滤

4. **透明可恢复**：冲刷过程对用户透明，信息可追溯
   - **近端记忆文件**：所有冲刷的信息都保存在人类可读的 Markdown 文件中
   - **时间窗口**：近端记忆保留 2 天，足够覆盖短期上下文需求
   - **设计目的**：用户可以查看和编辑冲刷的信息，完全掌控记忆内容

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

#### 3.1.5 Agent 模块接口设计

**核心接口**：
- **LangChain Agent 接口**：工具调用决策，使用 `create_agent` API
- **LangGraph State 接口**：预压缩冲刷状态管理，使用 `InMemorySaver`
- **SystemPromptBuilder 接口**：System Prompt 拼接

**SystemPromptBuilder 接口设计**：
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

    def _load_core_memory(self) -> str:
        """加载核心记忆文件"""
        # 严格按照顺序加载：AGENTS.md → SKILLS_SNAPSHOT.md → SOUL.md → IDENTITY.md → USER.md → MEMORY.md
        pass

    def _load_near_memory(self, days: int = 2) -> str:
        """加载近端记忆"""
        pass
```

**LangGraph 状态管理接口**：
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

**工具注册接口**：
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

### 3.2 Memory 模块

#### 3.2.1 三层记忆架构

**记忆层级结构**：
```
┌─────────────────────────────────────────────────────────────┐
│                        记忆架构                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     核心记忆 (Core)                         │
│  • AGENTS.md    - Agent 自身信息                           │
│  • SKILLS_SNAPSHOT.md - 可用技能列表                      │
│  • SOUL.md      - 人格、语气、边界                         │
│  • IDENTITY.md  - 名称、风格、表情                         │
│  • USER.md      - 用户画像、称呼方式                       │
│  • MEMORY.md    - 用户偏好、重要决策                       │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                     长期记忆 (Long-term)                     │
│  • RAG 索引化的历史会话                                    │
│  • 归档的对话内容 (sessions/archive/)                      │
│  • 支持混合检索 (BM25 + Vector)                           │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                     近端记忆 (Near-term)                    │
│  • memory/YYYY-MM-DD.md                                  │
│  • 临时性偏好、对话摘要                                   │
│  • 2天内有效，自动管理                                     │
└─────────────────────────────────────────────────────────────┘
```

**设计意图与架构哲学**：

Memory 模块的设计核心是"文件即记忆 (File-first Memory)"理念。这一理念摒弃了不透明的向量数据库或黑盒记忆系统，将所有记忆以人类可读的 Markdown 文件形式存储。这种设计带来以下优势：

1. **透明性**：用户可以随时查看和编辑任何记忆文件，完全掌控自己的数据
2. **可审计性**：所有记忆变更都有明确的文件版本记录，便于追溯
3. **可迁移性**：基于标准文件格式，可以轻松迁移或备份
4. **可编辑性**：用户可以直接编辑记忆文件来修正或补充信息，无需通过 API

**三层记忆架构的设计逻辑**：

- **核心记忆 (Core Memory)**：定义 Agent 的基础属性和长期配置
  - 设计目的：确保每次会话都有一致的 Agent 身份、人格、用户画像
  - 加载策略：会话初始化时完整加载，不进行任何截断或压缩
  - 安全考虑：AGENTS.md 和 SKILLS_SNAPSHOT.md 设为只读，防止 Agent 误修改

- **长期记忆 (Long-term Memory)**：存储历史对话的归档内容
  - 设计目的：支持跨会话的长期记忆检索，让 Agent 能够引用过去的对话内容
  - 索引策略：使用 RAG 模块的混合检索（BM25 + Vector），平衡精确匹配和语义相似性
  - 生命周期：会话归档时自动触发索引更新，无需手动操作

- **近端记忆 (Near-term Memory)**：存储临时性、近期的上下文信息
  - 设计目的：在不占用长期记忆存储空间的情况下，保持近期对话的上下文连贯性
  - 时间窗口：仅加载最近 2 天的内容，自动过期
  - 写入策略：仅追加（append-only），保证写入的安全性和一致性

**记忆加载优先级**：
1. **核心记忆**：初始化时加载，定义 Agent 基础属性
2. **长期记忆**：需要时通过 RAG 检索
3. **近端记忆**：System Prompt 拼接时加载最近2天内容
4. **会话记忆**：实时维护，存储在内存中

**记忆冲突解决**：
```python
def resolve_memory_conflicts(self, memories):
    """解决记忆冲突"""
    # 1. 按时间排序
    sorted_memories = sorted(memories, key=lambda x: x['timestamp'])

    # 2. 新的记忆优先级更高
    resolved = {}
    for mem in sorted_memories:
        key = mem['key']
        # 除非明确标记为覆盖，否则不覆盖旧记忆
        if key not in resolved or mem.get('override', False):
            resolved[key] = mem

    return list(resolved.values())
```

#### 3.2.3 会话生命周期

**会话标识说明**：

| 标识 | 来源 | 用途 |
|-----|------|------|
| `session_key` | 前端 localStorage 生成 | 浏览器匿名客户端 ID，长期有效，外部接口使用 |
| `session_id` | 后端生成 | 单次会话唯一标识，格式 `{YYYY-MM-DD}-{random}`，内部状态使用 |

**SessionInfo 数据模型**：
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

**会话状态管理**：
```python
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import uuid
from filelock import FileLock, Timeout

class SessionManager:
    """会话管理器（持久化版本）"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.sessions_dir = base_path / "sessions"
        self.sessions_json_path = self.sessions_dir / "sessions.json"
        self._lock = FileLock(str(self.sessions_json_path) + ".lock", timeout=10)

    def get_session(self, session_key: str) -> Optional[SessionInfo]:
        """获取指定 session_key 对应的会话

        Args:
            session_key: 前端生成的匿名客户端 ID

        Returns:
            会话信息，如果不存在返回 None
        """
        data = self._read_sessions_json()
        if session_key in data["sessions"]:
            return SessionInfo(**data["sessions"][session_key])
        return None

    def create_session(self, session_key: str) -> SessionInfo:
        """创建新会话

        Args:
            session_key: 前端生成的匿名客户端 ID

        Returns:
            创建的会话信息
        """
        # 检查是否已存在
        existing = self.get_session(session_key)
        if existing:
            return existing

        # 生成 session_id
        timestamp = datetime.now().strftime("%Y-%m-%d")
        random_suffix = uuid.uuid4().hex[:6]
        session_id = f"{timestamp}-{random_suffix}"

        # 创建 SessionInfo
        session_info = SessionInfo(
            session_id=session_id,
            session_key=session_key,
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active"
        )

        # 创建会话文件
        self._create_session_file(session_info)

        # 更新 sessions.json
        self._update_sessions_json(
            lambda data: data["sessions"].__setitem__(
                session_key, session_info.model_dump()
            )
        )

        return session_info

    def update_last_active(self, session_key: str) -> None:
        """更新会话最后活跃时间

        Args:
            session_key: 前端生成的匿名客户端 ID
        """
        def update(data):
            if session_key in data["sessions"]:
                data["sessions"][session_key]["lastActive"] = datetime.now().isoformat()

        self._update_sessions_json(update)

    def archive_session(self, session_key: str) -> None:
        """归档会话

        Args:
            session_key: 前端生成的匿名客户端 ID

        Raises:
            SessionNotFoundError: 会话不存在
        """
        session_info = self.get_session(session_key)
        if not session_info:
            raise SessionNotFoundError(f"Session not found: {session_key}")

        if session_info.status == "archived":
            return  # 已归档，无需重复操作

        # 移动文件
        current_path = self.sessions_dir / "current" / f"{session_info.session_id}.md"
        archive_path = self.sessions_dir / "archive" / f"{session_info.session_id}.md"

        if current_path.exists():
            # 更新元数据
            self._update_session_file_metadata(current_path)
            # 移动文件
            current_path.rename(archive_path)

        # 更新 sessions.json
        self._update_sessions_json(
            lambda data: data["sessions"][session_key].__setitem__("status", "archived")
        )

    def _read_sessions_json(self) -> dict:
        """读取 sessions.json"""
        if not self.sessions_json_path.exists():
            return {"version": "1.0", "sessions": {}}
        return json.loads(self.sessions_json_path.read_text())

    def _update_sessions_json(self, update_func) -> None:
        """更新 sessions.json（带文件锁）"""
        try:
            with self._lock:
                data = self._read_sessions_json()
                update_func(data)
                self.sessions_json_path.write_text(json.dumps(data, indent=2))
        except Timeout:
            raise TimeoutError("Failed to acquire lock for sessions.json")

    def _create_session_file(self, session_info: SessionInfo) -> None:
        """创建会话文件"""
        file_path = self.sessions_dir / "current" / f"{session_info.session_id}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# 会话信息
- sessionId: {session_info.session_id}
- createdAt: {session_info.created_at.strftime("%Y-%m-%d %H:%M:%S")}
- updatedAt: {session_info.last_active.strftime("%Y-%m-%d %H:%M:%S")}
- messageCount: 0
- tokenCount: 0

## 对话历史
"""
        file_path.write_text(content)

    def _update_session_file_metadata(self, file_path: Path) -> None:
        """更新会话文件元数据"""
        # 读取文件，更新 updatedAt、messageCount、tokenCount
        pass
```

#### 3.2.4 sessions.json 文件格式

**文件路径**：`~/.smartclaw/sessions/sessions.json`

**格式**：
```json
{
  "version": "1.0",
  "sessions": {
    "{sessionKey}": {
      "sessionId": "2026-03-16-abc123",
      "sessionKey": "client_xyz789",
      "createdAt": "2026-03-16T14:35:22Z",
      "lastActive": "2026-03-16T14:45:38Z",
      "status": "active"
    }
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| `version` | string | 映射表版本号 |
| `sessionKey` | string | 键：前端生成的匿名客户端 ID（localStorage） |
| `sessionId` | string | 值：后端生成的会话唯一标识 |
| `createdAt` | string | 创建时间（ISO 格式） |
| `lastActive` | string | 最后活跃时间（ISO 格式） |
| `status` | string | 会话状态：`active` 或 `archived` |

#### 3.2.5 会话创建算法

```
Algorithm: CreateSession(session_key)
Input:
  - session_key: string (浏览器生成的匿名客户端 ID)

Output: SessionInfo

Preconditions:
  - sessions.json 文件存在（初始化时创建）
  - session_key 不为空

Steps:
1. 检查会话是否已存在:
   - 读取 sessions.json
   - if session_key in sessions_json["sessions"]:
     - 返回现有 SessionInfo（不重复创建）

2. 生成 session_id:
   - timestamp = datetime.now().strftime("%Y-%m-%d")
   - random_suffix = uuid.uuid4().hex[:6]
   - session_id = f"{timestamp}-{random_suffix}"
   - 示例: "2026-03-16-a1b2c3"

3. 创建 SessionInfo 对象:
   - session_info = SessionInfo(
       session_id=session_id,
       session_key=session_key,
       created_at=datetime.now(),
       last_active=datetime.now(),
       status="active"
     )

4. 创建会话文件:
   - file_path = sessions/current/{session_id}.md
   - 写入文件模板（见 10.1.2）

5. 更新 sessions.json (加文件锁):
   - with FileLock(sessions_json_path, timeout=10):
     - data = json.loads(sessions_json_path.read_text())
     - data["sessions"][session_key] = session_info.model_dump()
     - sessions_json_path.write_text(json.dumps(data, indent=2))

6. 返回 session_info
```

#### 3.2.6 会话续期算法

```
Algorithm: RenewSession(session_key)
Input:
  - session_key: string

Output: None

Steps:
1. 读取 sessions.json (加文件锁):
   - with FileLock(sessions_json_path, timeout=10):
     - data = json.loads(sessions_json_path.read_text())

2. 检查会话是否存在:
   - if session_key not in data["sessions"]:
     - 抛出 SessionNotFoundError

3. 更新 lastActive:
   - data["sessions"][session_key]["lastActive"] = datetime.now().isoformat()

4. 写回 sessions.json:
   - sessions_json_path.write_text(json.dumps(data, indent=2))

5. 同时更新会话文件中的 updatedAt:
   - session_id = data["sessions"][session_key]["sessionId"]
   - file_path = sessions/current/{session_id}.md
   - 更新文件头部的 updatedAt 字段
```

**触发场景**：
- 每次用户发送消息时
- 前端心跳请求（可选）

#### 3.2.7 会话归档算法

```
Algorithm: ArchiveSession(session_key)
Input:
  - session_key: string

Output: None

Steps:
1. 读取 sessions.json (加文件锁):
   - with FileLock(sessions_json_path, timeout=10):
     - data = json.loads(sessions_json_path.read_text())

2. 检查会话是否存在且为活跃状态:
   - if session_key not in data["sessions"]:
     - 抛出 SessionNotFoundError
   - if data["sessions"][session_key]["status"] == "archived":
     - 返回 (已归档，无需重复操作)

3. 获取会话信息:
   - session_info = data["sessions"][session_key]
   - session_id = session_info["sessionId"]

4. 更新会话文件元数据:
   - current_path = sessions/current/{session_id}.md
   - 读取文件，更新 messageCount 和 tokenCount
   - 更新 updatedAt = datetime.now()

5. 移动文件到归档目录:
   - archive_path = sessions/archive/{session_id}.md
   - shutil.move(current_path, archive_path)

6. 更新 sessions.json:
   - data["sessions"][session_key]["status"] = "archived"
   - sessions_json_path.write_text(json.dumps(data, indent=2))

7. 触发 RAG 模块索引更新:
   - 无需主动调用（RAG 模块通过 watchdog 监听 archive/ 目录）
   - 文件移动完成后，watchdog 自动检测到新文件
   - RAG 模块异步执行索引更新
```

**触发场景**：
- 用户主动关闭会话
- 会话超时（可配置，如 24 小时无活动）
- 用户请求创建新会话（替换旧会话）

#### 3.2.8 并发控制

为保证 `sessions.json` 的并发写入一致性，使用 `filelock` 库实现文件锁。

**选型依据**：
- 功能完整：内置重试机制、超时处理
- 跨平台：支持 Windows、macOS、Linux
- 简单易用：上下文管理器 API

**配置**：
- 锁超时时间：10 秒
- 锁文件路径：`sessions.json.lock`

**错误处理**：

| 错误场景 | 处理方式 |
|---------|---------|
| 文件锁超时 | 抛出 `TimeoutError("Failed to acquire lock for sessions.json")` |
| 会话不存在 | 抛出 `SessionNotFoundError` |
| 文件写入失败 | 重试 3 次，间隔 1 秒 |

#### 3.2.9 RAG 模块事件驱动集成

**设计原则**：Memory 模块与 RAG 模块完全解耦，通过文件系统事件驱动。

**归档流程**：
```
Memory 模块                              RAG 模块
    │                                       │
    │ 会话归档                              │
    │ (文件移动到 archive/)                 │
    │                                       │
    └───────────────────────────────────────┤
                    文件系统
                    │
                    ▼
              ┌─────────────────┐
              │   watchdog      │
              │   检测新文件     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ IngestionPipeline│
              │ 增量索引更新      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Chroma + BM25   │
              │ 索引已更新        │
              └─────────────────┘
```

**设计优势**：
- **解耦**：Memory 模块不依赖 RAG 模块的任何接口
- **异步**：索引更新不阻塞会话归档操作
- **可靠**：即使 RAG 模块暂时不可用，归档操作仍能完成

**RAG 模块监听配置**：
```yaml
rag:
  indexes:
    memory:
      watch_dir: "~/.smartclaw/sessions/archive"
      debounce_seconds: 2  # 防抖时间
```

#### 3.2.10 Memory 模块接口设计

**记忆管理器基类接口**：
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List

class MemoryManager(ABC):
    """记忆管理器基类"""

    def __init__(self, base_path: Path):
        """初始化记忆管理器

        Args:
            base_path: 记忆存储根路径
        """
        self.base_path = base_path

    @abstractmethod
    def load(self) -> str:
        """加载记忆内容

        Returns:
            拼接后的记忆内容
        """
        pass

    def write(self, **kwargs) -> None:
        """写入记忆内容

        子类应实现各自的参数定义和验证逻辑

        Raises:
            IOError: 文件写入失败
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """检查记忆是否存在

        Returns:
            如果记忆文件存在返回 True，否则返回 False
        """
        pass
```

**近端记忆管理器接口**：
```python
from enum import Enum

class NearMemoryCategory(str, Enum):
    """近端记忆类别"""
    CONVERSATION_SUMMARY = "对话摘要"
    IMPORTANT_FACT = "重要事实"
    DECISION_RECORD = "决策记录"

class NearMemoryManager(MemoryManager):
    """近端记忆管理器"""

    def __init__(self, base_path: Path):
        """初始化近端记忆管理器"""
        super().__init__(base_path)
        self.memory_dir = base_path / "memory"

    def load(self, days: int = 2) -> str:
        """加载最近 N 天的近端记忆

        Args:
            days: 加载最近几天的记忆，默认 2 天

        Returns:
            拼接后的近端记忆内容，按日期降序排列
        """
        # 实现加载逻辑
        pass

    def write(self, date: str, content: str, category: Optional[str] = None) -> None:
        """写入近端记忆

        Args:
            date: 日期（YYYY-MM-DD 格式）
            content: 要写入的内容（Markdown 格式）
            category: 内容类别（对话摘要/重要事实/决策记录）

        Raises:
            ValueError: 日期格式错误
            IOError: 文件写入失败
        """
        # 实现写入逻辑
        pass

    def get_file_path(self, date: str) -> Path:
        """获取指定日期的近端记忆文件路径"""
        return self.memory_dir / f"{date}.md"
```

**核心记忆管理器接口**：
```python
from enum import Enum

class CoreMemoryFile(str, Enum):
    """核心记忆文件类型"""
    SOUL = "soul"
    IDENTITY = "identity"
    USER = "user"
    MEMORY = "memory"

class CoreMemoryManager(MemoryManager):
    """核心记忆管理器"""

    def __init__(self, base_path: Path):
        """初始化核心记忆管理器"""
        super().__init__(base_path)
        self.core_dir = base_path / "core_memory"

    def load(self) -> str:
        """加载所有核心记忆文件

        Returns:
            拼接后的核心记忆内容
        """
        content_parts = []

        # 按顺序加载核心记忆文件
        files = ["AGENTS.md", "SKILLS_SNAPSHOT.md", "SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md"]

        for file_name in files:
            file_path = self.core_dir / file_name
            if file_path.exists():
                content_parts.append(f"## {file_name}\n{file_path.read_text()}")

        return "\n\n".join(content_parts)

    def write(self, file_key: CoreMemoryFile, content: str, mode: str = "append") -> None:
        """写入核心记忆

        Args:
            file_key: 文件标识
            content: 要写入的内容（Markdown 格式）
            mode: 写入模式（append/replace）

        Raises:
            SecurityError: 尝试修改只读文件
            IOError: 文件操作失败
        """
        # 禁止修改的文件
        if file_key.value in ["agents", "skills_snapshot"]:
            raise SecurityError("Cannot modify core memory files: agents, skills_snapshot")

        file_path = self.core_dir / f"{file_key.value}.md"

        if mode == "append":
            # 追加模式，添加时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            existing_content = file_path.read_text() if file_path.exists() else ""
            new_content = f"{existing_content}\n\n[{timestamp}]\n{content}"
            file_path.write_text(new_content)
        elif mode == "replace":
            # 替换模式
            file_path.write_text(content)
```

**Agent 工具接口**：
```python
from langchain.tools import tool

@tool
def write_near_memory(
    date: Optional[str] = None,
    content: str = "",
    category: Optional[str] = None
) -> str:
    """写入近端记忆

    Args:
        date: 日期（YYYY-MM-DD 格式），默认为当天
        content: 要写入的内容（Markdown 格式）
        category: 内容类别（对话摘要/重要事实/决策记录）

    Returns:
        操作结果消息
    """
    # 实现调用逻辑
    return f"Successfully wrote to near memory: {content[:50]}..."

@tool
def write_core_memory(
    file_key: str,
    content: str,
    mode: str = "append"
) -> str:
    """写入核心记忆

    Args:
        file_key: 文件标识（soul/identity/user/memory）
        content: 要写入的内容（Markdown 格式）
        mode: 写入模式（append/replace）

    Returns:
        操作结果消息
    """
    # 实现调用逻辑
    return f"Successfully wrote to {file_key} core memory: {content[:50]}..."

@tool
def search_memory(
    query: str,
    top_k: int = 5,
    date_range: Optional[tuple[str, str]] = None
) -> str:
    """检索长期记忆

    **注意**：此工具由 RAG 模块提供实现，详见 3.3.6 RAG 模块接口设计。

    Args:
        query: 查询文本
        top_k: 返回结果数量，默认 5
        date_range: 日期范围 (start_date, end_date)，格式 YYYY-MM-DD

    Returns:
        检索结果（格式化字符串）
    """
    # 实际实现由 RAG 模块提供
    pass
```

### 3.3 RAG 模块

**技术选型**：
| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 索引框架 | LlamaIndex | 提供文档解析、分块、索引构建 |
| 向量存储 | Chroma | 轻量级，支持持久化 |
| BM25 | LlamaIndex BM25Retriever | LlamaIndex 内建实现 |
| 文件监听 | watchdog | 跨平台文件系统监控 |
| LLM | OpenAI/Qwen/Ollama/vLLM/... | 从配置文件读取，使用 LLM Factory 进行实例化 |
| Embedding | OpenAI/Qwen/Ollama/vLLM/... | 从配置文件读取，使用 Embedding Factory 进行实例化 |

**设计意图与架构哲学**：

RAG 模块的设计核心是为 SmartClaw 提供高效、可靠的长期记忆检索能力。该模块遵循以下设计原则：

1. **本地优先与轻量级**：所有索引数据存储在本地，使用轻量级技术栈
   - Chroma 作为向量存储：无需额外服务部署，支持持久化
   - SQLite 作为缓存：符合项目轻量级定位，避免引入 Redis 等重量级依赖
   - BM25 索引：LlamaIndex 内置实现，无需额外依赖

2. **混合检索策略**：结合语义相似性和关键词精确匹配
   - **向量检索**：捕捉语义相关性，适合模糊查询和概念性搜索
   - **BM25 检索**：基于关键词精确匹配，适合低频词和专有名词查询
   - **RRF 融合**：互惠秩融合算法无需额外模型训练，鲁棒性强，易于实现
   - **设计目的**：兼顾不同查询场景，提高检索准确率和召回率

3. **增量索引更新**：高效的文件变更处理机制
   - **DocStore 哈希对比**：通过文档哈希值识别新增或修改的文档
   - **SQLite Cache 缓存**：缓存节点与转换（分块、嵌入）的组合结果，避免重复计算
   - **文件监听事件驱动**：watchdog 监听 sessions/archive/ 目录变化，自动触发索引更新
   - **性能优势**：未变更文档直接使用缓存，缓存命中率达 80-99%

4. **透明性与可审计性**：索引仅作为检索加速层
   - **源文件完整保留**：原始 Markdown 文件始终完整可读
   - **索引可重建**：删除索引不影响源文件，可随时重建
   - **设计目的**：符合"文件即记忆"哲学，确保用户始终掌控原始数据

5. **可扩展性与抽象设计**：IndexManager 抽象基类支持未来扩展
   - **接口抽象**：定义统一的检索和索引管理接口
   - **未来扩展**：可轻松接入外部知识库（数据库、API 等）
   - **向后兼容**：新增索引类型不影响现有 Agent 工具接口
   - **设计目的**：为未来外部知识库需求预留架构空间

6. **异步非阻塞**：索引构建不影响用户交互
   - **后台处理**：所有索引操作在后台异步执行
   - **实时可用**：用户可立即开始对话，后台持续增量更新
   - **设计目的**：确保用户体验流畅，索引构建不阻塞主流程

#### 3.3.1 核心组件设计

**LlamaIndex 核心组件架构**：
```python
from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext
)
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.extractors import QuestionsAnsweredExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.vector_stores import ChromaVectorStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
import chromadb
```

**核心组件职责**：

| 组件 | 职责 |
|------|------|
| `SimpleDirectoryReader` | 从本地目录递归读取 `.md` 文件，生成 `Document` 对象 |
| `MarkdownNodeParser` | 按标题层级将文档分割为节点，自动提取标题编号和名称 |
| `QuestionsAnsweredExtractor` | 调用 LLM 为每个节点生成可回答问题列表 |
| `IngestionPipeline` | 文档处理管道，集成 DocStore 和缓存，支持增量更新 |
| `SimpleDocumentStore` | 文档存储，记录文档哈希值和节点 ID 列表 |
| `ChromaVectorStore` | Chroma 向量存储，保存节点的嵌入向量及元数据 |
| `VectorStoreIndex` | 基于向量存储构建的索引，生成向量检索器 |
| `BM25Retriever` | 基于 BM25 算法的关键词检索器 |
| `QueryFusionRetriever` | 融合多个检索器的结果，使用 `mode="reciprocal_rank"` 进行 RRF 融合 |

**整体架构图**：
```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 模块架构                          │
└─────────────────────────────────────────────────────────────┘

文件系统 (sessions/archive/*.md)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│           SimpleDirectoryReader                            │
│    递归读取 .md 文件 → Document 对象                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              IngestionPipeline                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  MarkdownNodeParser                               │  │
│  │    • 按标题层级分块                               │  │
│  │    • 自动提取 section_hierarchy, heading            │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  QuestionsAnsweredExtractor                      │  │
│  │    • 调用 LLM 生成可回答问题                     │  │
│  │    • 结果存入 questions_this_excerpt_can_answer   │  │
│  └─────────────────────────────────────────────────────┘  │
│  • 与 DocStore 集成，跳过未变更文档                      │
│  • 与 SQLite Cache 集成，缓存节点+转换结果               │
└─────────────────────────────────────────────────────────────┘
    │
    ├──→ SimpleDocumentStore (docstore.json)
    │    • 记录文档哈希值
    │    • 记录节点 ID 列表
    │
    ├──→ ChromaVectorStore (chroma/)
    │    • 节点嵌入向量
    │    • 节点元数据
    │
    └──→ BM25 索引 (bm25/)
         • BM25 统计信息

    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│           QueryFusionRetriever (RRF)                      │
│  ┌─────────────┐         ┌─────────────┐               │
│  │  Vector     │         │  BM25      │               │
│  │  Retriever  │         │  Retriever  │               │
│  └─────────────┘         └─────────────┘               │
│         │                       │                         │
│         └───────────┬───────────┘                         │
│                     ▼                                   │
│         Reciprocal Rank Fusion (k=60)                     │
│                     │                                   │
│                     ▼                                   │
│              融合后的 NodeWithScore 列表                  │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.2 数据模型设计

**Document 对象（LlamaIndex 自动生成）**：
```python
@dataclass
class Document:
    """LlamaIndex Document 对象"""
    id_: str
    text: str
    metadata: Dict[str, Any]

    # 自动提取的元数据：
    # - file_path: 文件完整路径
    # - file_name: 文件名（含扩展名）
    # - file_size: 文件大小（字节）
    # - last_modified: 文件最后修改时间
    # - file_type: 记忆类型（通过 file_metadata 钩子添加）
```

**Node 对象（LlamaIndex 自动生成）**：
```python
@dataclass
class Node:
    """LlamaIndex Node 对象"""
    id_: str
    text: str
    metadata: Dict[str, Any]

    # 继承自 Document 的元数据：
    # - file_path, file_name, last_modified, file_type

    # MarkdownNodeParser 自动添加：
    # - source_line: 节点在源文件中的起始行号
    # - section_hierarchy: Markdown 标题层级列表
    # - heading: 节点所属的最近一级标题

    # QuestionsAnsweredExtractor 添加：
    # - questions_this_excerpt_can_answer: 该节点能回答的问题列表
```

**Segment 对象（Agent 工具接口使用）**：
```python
@dataclass
class Segment:
    """检索结果数据载体"""
    content: str                          # 节点文本内容
    source: str                           # 来源文件路径
    file_type: str                        # 记忆类型（"long_term"）
    timestamp: Optional[str]              # 时间戳（ISO 格式）
    score: float                          # RRF 融合后的相关性得分
```

**分块策略**：
- 使用 `MarkdownNodeParser` 按标题层级进行分块
- 默认参数（可配置）：
  - `chunk_size`: 1024 字符
  - `chunk_overlap`: 128 字符

#### 3.3.3 IndexManager 抽象基类

为支持未来可能的外部知识库 RAG 需求，SmartClaw 将索引管理器设计为**接口基类**模式。`IndexManager` 定义所有具体索引管理器必须实现的核心接口，确保系统可扩展性。

**核心接口方法**：
- `search(query: str, top_k: int = TOP_K) -> List[Segment]`：执行检索，返回相关片段列表
- `update_document(doc_id: str, content: str, metadata: Optional[Dict] = None) -> bool`：添加或更新单个文档
- `delete_document(doc_id: str) -> bool`：从索引中删除指定文档
- `build_index(force: bool = False) -> bool`：全量重建索引
- `check_consistency() -> Dict[str, List[str]]`：检查索引与数据源的一致性，返回异常文档 ID 列表
- `repair_consistency() -> Dict[str, int]`：修复一致性异常，返回修复统计

**设计理念**：
- `MemoryIndexManager` 继承自 `IndexManager`，实现上述所有方法
- 未来如需接入外部知识库（如数据库、API 等），可创建 `KnowledgeIndexManager` 继承 `IndexManager`
- 上层 Agent 工具无需修改，即可支持不同的索引管理器实现

**IndexManager 抽象基类定义**：
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class Segment:
    """检索结果数据载体"""
    content: str                          # 节点文本内容
    source: str                           # 来源文件路径
    file_type: str                        # 记忆类型（"long_term"、"near"、"core"）
    timestamp: Optional[str]              # 时间戳（ISO 格式）
    score: float                          # RRF 融合后的相关性得分

class IndexManager(ABC):
    """索引管理器抽象基类

    为支持未来扩展（如外部知识库），所有具体索引管理器都必须继承此类。
    """

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Segment]:
        """执行检索，返回相关片段列表

        Args:
            query: 搜索查询内容
            top_k: 返回结果数量

        Returns:
            相关片段列表
        """
        pass

    @abstractmethod
    def update_document(self, doc_id: str, content: str,
                       metadata: Optional[Dict] = None) -> bool:
        """添加或更新单个文档

        Args:
            doc_id: 文档唯一标识（如文件路径）
            content: 文档内容
            metadata: 附加元数据（如文件类型、修改时间）

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """从索引中删除指定文档

        Args:
            doc_id: 文档唯一标识

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def build_index(self, force: bool = False) -> bool:
        """全量重建索引

        Args:
            force: 是否强制重建（若为 False，利用 DocStore 哈希对比实现增量式重建）

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def check_consistency(self) -> Dict[str, List[str]]:
        """检查索引与数据源的一致性

        Returns:
            字典，包含以下键值：
            - missing_in_index: 磁盘上存在但索引中无记录的文件列表
            - missing_on_disk: 索引中有记录但磁盘上已删除的文件列表
            - outdated_in_index: 磁盘文件已修改但索引未更新的文件列表
        """
        pass

    @abstractmethod
    def repair_consistency(self) -> Dict[str, int]:
        """修复一致性异常

        Returns:
            字典，包含以下键值：
            - added: 新增的文件数量
            - updated: 更新的文件数量
            - deleted: 删除的文件数量
        """
        pass
```

#### 3.3.4 MemoryIndexManager 核心实现

**MemoryIndexManager 类**：
```python
from llama_index.core import VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.extractors import QuestionsAnsweredExtractor

class MemoryIndexManager(IndexManager):
    """长期记忆索引管理器（LlamaIndex 实现）

    继承自 IndexManager 抽象基类，实现所有核心接口方法。
    """

    def __init__(self, config):
        """初始化索引管理器

        Args:
            config: 配置对象，包含 RAG 相关配置
        """
        self.config = config
        self._dir = config['rag']['index_path']  # 索引目录
        self.storage_context = self._init_storage_context()
        self.pipeline = self._init_pipeline()
        self.fusion_retriever = None
        self._init_retriever()

#### 3.3.4.1 SQLite Cache 自定义实现

为符合项目轻量级定位，SmartClaw 使用自定义的 SQLite Cache 而非 Redis 等重量级方案。该 Cache 与 LlamaIndex 的 IngestionPipeline 无缝集成，提供高效的节点转换结果缓存。

**SQLiteCache 类定义**：
```python
import sqlite3
import hashlib
import pickle
from typing import Any, Optional
from llama_index.core.cache.base import BaseCache

class SQLiteCache(BaseCache):
    """SQLite 缓存实现

    缓存内容：
    1. 节点分块结果（MarkdownNodeParser 输出）
    2. 节点嵌入向量（Embedding 模型输出）
    3. 避免重复计算昂贵的转换操作

    存储结构：
    - cache_key: 缓存键（基于节点内容哈希生成）
    - cache_value: 缓存值（pickle 序列化）
    - created_at: 创建时间
    - accessed_at: 最后访问时间
    """

    def __init__(self, cache_path: str):
        """初始化 SQLite 缓存

        Args:
            cache_path: 缓存文件路径（如 ~/.smartclaw/store/memory/cache.db）
        """
        self.cache_path = cache_path
        self.conn = self._init_database()
        self._create_tables()

    def _init_database(self) -> sqlite3.Connection:
        """初始化数据库连接"""
        conn = sqlite3.connect(self.cache_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """创建缓存表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                cache_value BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 创建索引以加速查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_accessed_at
            ON cache(accessed_at)
        ''')
        self.conn.commit()

    def _generate_cache_key(self, key: str, content: str) -> str:
        """生成缓存键

        Args:
            key: 基础键（如节点 ID）
            content: 节点内容

        Returns:
            缓存键（哈希值）
        """
        # 使用 SHA256 生成哈希
        key_str = f"{key}:{content[:1000]}"  # 只取前 1000 字符以提高性能
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存的值，如果不存在则返回 None
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT cache_value, accessed_at
            FROM cache
            WHERE cache_key = ?
        ''', (key,))

        row = cursor.fetchone()
        if row:
            # 更新访问时间
            cursor.execute('''
                UPDATE cache
                SET accessed_at = CURRENT_TIMESTAMP
                WHERE cache_key = ?
            ''', (key,))
            self.conn.commit()
            return pickle.loads(row[0])
        return None

    def put(self, key: str, value: Any, content: str = "") -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 要缓存的值
            content: 用于生成哈希的内容（如节点文本）

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()

        # 序列化值
        serialized_value = pickle.dumps(value)

        # 生成缓存键
        cache_key = self._generate_cache_key(key, content)

        # 插入或更新缓存
        cursor.execute('''
            INSERT OR REPLACE INTO cache (cache_key, cache_value)
            VALUES (?, ?)
        ''', (cache_key, serialized_value))

        self.conn.commit()
        return True

    def delete(self, key: str) -> bool:
        """删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM cache WHERE cache_key = ?
        ''', (key,))

        affected = cursor.rowcount
        self.conn.commit()
        return affected > 0

    def clear(self) -> bool:
        """清空所有缓存

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM cache')
        self.conn.commit()
        return True

    def cleanup_old_entries(self, days: int = 30) -> int:
        """清理过期缓存条目

        Args:
            days: 保留天数，删除超过此天数的条目

        Returns:
            删除的条目数量
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM cache
            WHERE accessed_at < datetime('now', '-{} days'.format(days))
        ''')
        affected = cursor.rowcount
        self.conn.commit()
        return affected

    def get_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                COUNT(*) as total_entries,
                SUM(LENGTH(cache_value)) as total_size,
                MAX(accessed_at) as last_accessed
            FROM cache
        ''')

        row = cursor.fetchone()
        return {
            'total_entries': row[0],
            'total_size': row[1],
            'last_accessed': row[2]
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()
```

**与 LlamaIndex 集成说明**：

SQLiteCache 实现 LlamaIndex 的 `BaseCache` 接口，可以直接作为 `IngestionPipeline` 的 `cache` 参数使用。

**集成方式**：
```python
# 在 StorageContext 中初始化
storage_context = StorageContext.from_defaults(
    vector_store=vector_store,
    docstore=SimpleDocumentStore.from_persist_dir(index_dir),
    # 使用自定义的 SQLite Cache
    cache=SQLiteCache(cache_path=f"{index_dir}/cache.db")
)
```

**缓存策略**：

1. **缓存键生成**：基于节点内容和节点ID生成SHA256哈希
2. **缓存内容**：
   - MarkdownNodeParser 的输出（节点列表）
   - Embedding 模型的输出（嵌入向量）
3. **缓存更新**：
   - 节点未变更：直接使用缓存
   - 节点已变更：重新计算并更新缓存
4. **缓存清理**：定期清理超过30天的旧条目

**性能优势**：

- **轻量级**：使用 SQLite 而非 Redis，无需额外依赖
- **高效**：支持索引加速查询
- **可靠**：SQLite 支持事务，保证数据一致性
- **本地优先**：所有数据存储在本地，无网络依赖


    继承自 IndexManager 抽象基类，实现所有核心接口方法。
    """

    def __init__(self, config):
        """初始化索引管理器

        Args:
            config: 配置对象，包含 RAG 相关配置
        """
        self.config = config
        self._dir = config['rag']['index_path']  # 索引目录
        self.storage_context = self._init_storage_context()
        self.pipeline = self._init_pipeline()
        self.fusion_retriever = None
        self._init_retriever()

    def _init_storage_context(self) -> StorageContext:
        """初始化存储上下文

        StorageContext 包含三个核心组件：

        1. VectorStore (ChromaVectorStore)：
           - 存储节点的嵌入向量及元数据
           - 用于稠密向量检索

        2. DocStore (SimpleDocumentStore)：
           - 存储文档元数据：doc_id、文档哈希值、节点列表等
           - **实现增量更新的核心**：通过哈希对比识别新增或修改的文档
           - 持久化为 JSON 文件（docstore.json）

        3. Cache (SQLite Cache)：
           - 缓存每个节点与转换的组合结果
           - 避免重复计算：分块、嵌入等昂贵操作
           - 持久化为 SQLite 文件（cache.db）
        """
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore

        # 初始化 Chroma 客户端
        chroma_client = chromadb.PersistentClient(path=f"{self._dir}/chroma")

        # 创建 Chroma 向量存储
        chroma_collection = chroma_client.get_or_create_collection("memory")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # 创建存储上下文

        # 创建分块器
        node_parser = MarkdownNodeParser.from_defaults(
            chunk_size=self.config['rag']['chunk_size'],
            chunk_overlap=self.config['rag']['chunk_overlap']
        )

        # 创建问题提取器（需要 LLM）
        llm = LLMFactory.get_instance(self.config['llm'])
        extractor = QuestionsAnsweredExtractor(
            llm=llm,
            questions=self.config['rag']['generate_queries']
        )

        # 创建管道
        # 关键：通过 storage_context 参数传入 DocStore 和 Cache
        # IngestionPipeline 会自动利用它们实现增量更新
        pipeline = IngestionPipeline(
            transformations=[node_parser, extractor],
            storage_context=self.storage_context
        )

        return pipeline

**增量更新机制说明**：

SmartClaw 的 RAG 模块使用 LlamaIndex 的 IngestionPipeline、DocStore 和 Cache 实现高效的增量更新。以下是详细机制：

```
┌─────────────────────────────────────────────────────────────────┐
│                    增量更新机制                              │
└─────────────────────────────────────────────────────────────────┘

文件变更（新增/修改）
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│          SimpleDirectoryReader                           │
│    加载 .md 文件 → Document 对象                          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│          IngestionPipeline                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  DocStore 检查                             │  │
│  │  • 计算文档哈希值                            │  │
│  │  • 对比存储的哈希值                            │  │
│  │  • 判断文档状态：                              │  │
│  │    - 新增：哈希值不存在                         │  │
│  │    - 未变更：哈希值相同                          │  │
│  │    - 已变更：哈希值不同                          │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  增量处理决策                               │  │
│  │  • 未变更：跳过处理，使用 Cache 中的节点和      │  │
│  │           转换结果（分块、嵌入）                 │  │
│  │  • 已变更：执行 transformations                  │  │
│  │           - MarkdownNodeParser（分块）          │  │
│  │           - QuestionsAnsweredExtractor（问题生成）│  │
│  │  • 更新 DocStore 和 Cache                    │  │
│  └─────────────────────────────────────────────────────┘  │
│         │                                            │
│         ├──→ Cache（SQLite）                            │
│         │    • 缓存每个节点的分块结果                │  │
│         │    • 缓存每个节点的嵌入向量                │  │
│         │    • 避免重复计算                            │  │
│         │                                            │
│         ├──→ DocStore（JSON）                            │
│         │    • 记录文档哈希值                          │  │
│         │    • 记录节点 ID 列表                        │  │
│         │    • 支持增量更新                          │  │
│         │                                            │
│         └──→ VectorStore & BM25 Index                   │
│              • 更新索引数据                              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
重建 QueryFusionRetriever
```

**核心优势**：

1. **性能提升**：未变更的文档直接使用缓存结果，跳过昂贵的分块和嵌入操作
2. **资源节约**：避免重复计算分块、嵌入等资源密集型操作
3. **实时同步**：文件变更自动触发增量更新，保持索引与源文件同步
4. **可靠性**：DocStore 记录文档哈希，确保增量更新的准确性

**缓存命中率**：
- 全量重建（首次）：0%（所有文档都需要处理）
- 小幅修改：~80-90%（大部分文档未变更）
- 仅单文件修改：~95-99%（仅变更的文件需要处理）

    def _init_retriever(self):
        """初始化融合检索器"""
        # 创建向量检索器
        vector_index = VectorStoreIndex.from_documents([], storage_context=self.storage_context)
        vector_retriever = vector_index.as_retriever(
            similarity_top_k=self.config['rag']['top_k'] * 2
        )

        # 创建 BM25 检索器
        bm25_retriever = BM25Retriever.from_defaults(
            index=vector_index,
            similarity_top_k=self.config['rag']['top_k'] * 2
        )

        # 创建融合检索器（RRF 模式）
        self.fusion_retriever = QueryFusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            mode="reciprocal_rank",
            query_gen_kwargs={
                "n_queries": self.config['rag']['generate_queries'],
                "use_async": True
            }
        )

    def build_index(self, force: bool = False) -> bool:
        """构建或重建索引

        Args:
            force: 是否强制重建所有文档
                     - 若为 False：利用 DocStore 的哈希对比跳过未变更文件，
                       实现增量式全量重建，仅处理变更的文档
                     - 若为 True：强制重新处理所有文档，不使用缓存

        Returns:
            是否成功

        增量更新机制：
            1. 使用 SimpleDirectoryReader 加载所有记忆文件
            2. 调用 pipeline.run(documents=all_documents)
            3. IngestionPipeline 通过 DocStore 对比文件哈希：
               - 哈希未变：跳过该文档，直接使用缓存结果
               - 哈希已变：重新处理该文档的节点
            4. SQLite Cache 缓存每个节点与转换（分块、嵌入）的组合结果：
               - 未变更的节点：从缓存直接读取，避免重复计算
               - 变更的节点：重新计算并更新缓存
            5. 更新向量索引（Chroma）和 BM25 索引
            6. 重建 QueryFusionRetriever 确保使用最新索引
        """
        try:
            # 使用 SimpleDirectoryReader 加载所有记忆文件
            reader = SimpleDirectoryReader(
                input_dir="sessions/archive",
                required_exts=[".md"],
                filename_as_id=True
            )

            all_documents = reader.load_data()

            # 添加 file_type 元数据
            for doc in all_documents:
                doc.metadata['file_type'] = 'long_term'

            # 执行管道处理
            # 关键：IngestionPipeline 会自动通过 DocStore 和 Cache 实现增量更新
            # - DocStore 记录每个文档的哈希值，用于检测变更
            # - Cache 缓存每个节点的转换结果，避免重复计算
            self.pipeline.run(documents=all_documents)

            # 重建检索器
            self._init_retriever()

            return True

        except Exception as e:
            logging.error(f"Failed to build index: {e}")
            return False

    def update_document(self, doc_id: str, content: str, metadata: dict = None) -> bool:
        """添加或更新单个文档

        Args:
            doc_id: 文档标识（文件路径）
            content: 文档内容
            metadata: 附加元数据

        Returns:
            是否成功

        增量更新机制：
            1. 创建 Document 对象
            2. 调用 pipeline.run(documents=[document])
            3. IngestionPipeline 通过 DocStore 对比文件哈希：
               - 文档不存在：作为新增文档处理，执行完整流程
               - 文档已存在且哈希未变：跳过处理，使用缓存结果
               - 文档已存在但哈希已变：重新处理该文档的节点
            4. SQLite Cache 缓存每个节点的转换结果：
               - 未变更的节点：从缓存直接读取
               - 变更的节点：重新计算并更新缓存
            5. 更新向量索引（Chroma）和 BM25 索引
            6. 重建 QueryFusionRetriever 确保使用最新索引
        """
        try:
            from llama_index.core import Document

            # 创建 Document 对象
            document = Document(text=content, id_=doc_id)
            if metadata:
                document.metadata.update(metadata)
            document.metadata['file_type'] = 'long_term'

            # 执行管道处理（利用 DocStore 和缓存实现增量更新）
            # 关键：IngestionPipeline 会自动处理增量更新
            self.pipeline.run(documents=[document])

            # 重建检索器
            self._init_retriever()

            return True

        except Exception as e:
            logging.error(f"Failed to update document {doc_id}: {e}")
            return False

    def delete_document(self, doc_id: str) -> bool:
        """从索引中删除指定文档

        Args:
            doc_id: 文档标识（文件路径）

        Returns:
            是否成功
        """
        try:
            # 从 DocStore 中删除文档
            self.storage_context.docstore.delete_document(doc_id)

            # 重建检索器
            self._init_retriever()

            return True

        except Exception as e:
            logging.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> List[Segment]:
        """执行混合检索

        Args:
            query: 查询字符串
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if not self.fusion_retriever:
            raise RuntimeError("Fusion retriever not initialized")

        # 执行检索
        nodes_with_score = self.fusion_retriever.retrieve(query)

        # 转换为 Segment 对象
        segments = []
        for node_with_score in nodes_with_score[:top_k]:
            segment = Segment(
                content=node_with_score.node.text,
                source=node_with_score.node.metadata.get('file_path', 'unknown'),
                file_type=node_with_score.node.metadata.get('file_type', 'long_term'),
                timestamp=node_with_score.node.metadata.get('last_modified'),
                score=node_with_score.score
            )
            segments.append(segment)

        return segments

    def _search_with_filters(self, query: str, top_k: int,
                            date_range: Optional[tuple] = None) -> List[Segment]:
        """带过滤条件的搜索

        Args:
            query: 查询字符串
            top_k: 返回结果数量
            date_range: 日期范围 (start_date, end_date)

        Returns:
            过滤后的检索结果列表
        """
        # 先执行基础检索
        results = self.search(query, top_k * 2)

        # 应用过滤条件
        if date_range:
            results = self._filter_by_date_range(results, date_range)

        return results[:top_k]

    def _filter_by_date_range(self, segments: List[Segment],
                             date_range: tuple) -> List[Segment]:
        """按日期范围过滤

        Args:
            segments: 原始检索结果
            date_range: 日期范围 (start_date, end_date)

        Returns:
            过滤后的结果
        """
        from datetime import datetime

        start_date, end_date = date_range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        filtered = []
        for segment in segments:
            if not segment.timestamp:
                continue

            # 从文件路径提取日期
            date_str = self._extract_date_from_path(segment.source)
            if not date_str:
                continue

            seg_date = datetime.strptime(date_str, "%Y-%m-%d")
            if start <= seg_date <= end:
                filtered.append(segment)

        return filtered

    def _extract_date_from_path(self, file_path: str) -> Optional[str]:
        """从文件路径提取日期

        支持格式：sessions/archive/YYYY-MM-DD-*.md

        Args:
            file_path: 文件路径

        Returns:
            提取到的日期字符串（YYYY-MM-DD），无法提取则返回 None
        """
        import re

        # 匹配 sessions/archive/2026-03-16-*.md 格式
        match = re.search(r'sessions/archive/(\d{4}-\d{2}-\d{2})-', file_path)
        if match:
            return match.group(1)

        return None

    def check_consistency(self) -> Dict[str, List[str]]:
        """检查索引与数据源的一致性

        Returns:
            字典，包含以下键值：
            - missing_in_index: 磁盘上存在但索引中无记录的文件列表
            - missing_on_disk: 索引中有记录但磁盘上已删除的文件列表
            - outdated_in_index: 磁盘文件已修改但索引未更新的文件列表
        """
        import os
        from pathlib import Path

        result = {
            'missing_in_index': [],
            'missing_on_disk': [],
            'outdated_in_index': []
        }

        archive_dir = Path('sessions/archive')

        # 检查磁盘上存在但索引中缺少的文件
        if archive_dir.exists():
            for file_path in archive_dir.glob('*.md'):
                doc_id = str(file_path)
                if not self.storage_context.docstore.document_exists(doc_id):
                    result['missing_in_index'].append(doc_id)

        # 检查索引中存在但磁盘上缺少的文件
        doc_ids = self.storage_context.docstore.get_all_document_ids()
        for doc_id in doc_ids:
            if not os.path.exists(doc_id):
                result['missing_on_disk'].append(doc_id)

        # 检查磁盘文件已修改但索引未更新的文件
        for file_path in archive_dir.glob('*.md'):
            doc_id = str(file_path)
            if self.storage_context.docstore.document_exists(doc_id):
                indexed_doc = self.storage_context.docstore.get_document(doc_id)
                disk_mtime = os.path.getmtime(file_path)
                indexed_mtime = indexed_doc.metadata.get('last_modified')

                if indexed_mtime and disk_mtime > indexed_mtime:
                    result['outdated_in_index'].append(doc_id)

        return result

    def repair_consistency(self) -> Dict[str, int]:
        """修复一致性异常

        Returns:
            修复统计字典：
            - added: 新增的文件数量
            - updated: 更新的文件数量
            - deleted: 删除的文件数量
        """
        stats = {'added': 0, 'updated': 0, 'deleted': 0}

        # 检查一致性
        issues = self.check_consistency()

        # 修复缺失的文件
        for file_path in issues['missing_in_index']:
            if self.update_document(file_path, Path(file_path).read_text()):
                stats['added'] += 1

        # 删除过期的索引记录
        for file_path in issues['missing_on_disk']:
            if self.delete_document(file_path):
                stats['deleted'] += 1

        # 更新过期的索引记录
        for file_path in issues['outdated_in_index']:
            if self.update_document(file_path, Path(file_path).read_text()):
                stats['updated'] += 1

        return stats
```

#### 3.3.5 文件监听机制

**FileWatcher 实现**：
```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
from collections import defaultdict

class FileWatcher(FileSystemEventHandler):
    """文件监听器（watchdog 实现）"""

    def __init__(self, callback, debounce_time: int = 2):
        """初始化文件监听器

        Args:
            callback: 文件变化回调函数
            debounce_time: 防抖时间（秒）
        """
        self.callback = callback
        self.debounce_time = debounce_time
        self.last_events = defaultdict(float)  # {file_path: last_event_time}
        self.pending_timers = {}  # {file_path: Timer}

    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return

        file_path = event.src_path

        # 防抖处理
        now = time.time()
        if file_path in self.last_events:
            if now - self.last_events[file_path] < self.debounce_time:
                return

        self.last_events[file_path] = now

        # 取消之前的定时器（如果有）
        if file_path in self.pending_timers:
            self.pending_timers[file_path].cancel()

        # 创建新的定时器
        timer = Timer(self.debounce_time, lambda: self._process_change(file_path))
        self.pending_timers[file_path] = timer
        timer.start()

    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
        self._process_change(event.src_path)

    def on_deleted(self, event):
        """文件删除事件处理"""
        if event.is_directory:
            return
        self._process_change(event.src_path, is_delete=True)

    def _process_change(self, file_path: str, is_delete: bool = False):
        """处理文件变化"""
        try:
            self.callback(file_path, is_delete)
        except Exception as e:
            logging.error(f"Failed to process file change {file_path}: {e}")
        finally:
            # 清理定时器
            if file_path in self.pending_timers:
                del self.pending_timers[file_path]
```

#### 3.3.6 RAG 模块接口设计

**Agent 工具接口**：
```python
from langchain.tools import tool
from typing import Optional, Tuple

@tool
def search_memory(
    query: str,
    top_k: int = 5,
    date_range: Optional[Tuple[str, str]] = None
) -> str:
    """检索长期记忆，支持日期范围过滤

    Args:
        query: 搜索查询内容
        top_k: 返回结果数量，默认 5（从配置文件读取）
        date_range: 日期范围过滤，格式为 (start_date, end_date)，
                    日期使用 YYYY-MM-DD 格式

    Returns:
        格式化的字符串，包含每个片段的来源、类型和内容

    示例：
        search_memory("用户偏好设置", top_k=3)
        search_memory("项目讨论", date_range=("2026-03-01", "2026-03-15"))
    """
    # 调用 MemoryIndexManager 进行检索
    from rag import MemoryIndexManager
    from config import get_config

    config = get_config()
    manager = MemoryIndexManager(config)

    # 从配置读取 top_k
    if top_k == 5:
        top_k = config['rag']['top_k']

    # 执行检索
    if date_range:
        results = manager._search_with_filters(query, top_k, date_range)
    else:
        results = manager.search(query, top_k)

    # 格式化输出
    if not results:
        return "未找到相关的记忆片段。"

    formatted_results = []
    for i, segment in enumerate(results, 1):
        formatted_results.append(
            f"[来源: {segment.source} | 类型: {segment.file_type}]\n"
            f"{segment.content}"
        )

    return "\n\n".join(formatted_results)
```

**配置项**（从配置文件读取）：
```python
# config.yaml 中的 RAG 配置
rag:
  indexes:
    memory:                              # 记忆知识库（MemoryIndexManager）
      index_path: "~/.smartclaw/store/rag/memory"
      watch_dir: "~/.smartclaw/sessions/archive"
      top_k: 5
      chunk_size: 1024
      chunk_overlap: 128
      generate_queries: 3                # QuestionsAnsweredExtractor 生成的问题数
    knowledge:                           # 外部知识库（KnowledgeIndexManager，预留）
      index_path: "~/.smartclaw/store/rag/knowledge"
      watch_dir: null                    # 外部导入，不监听
      top_k: 5

retrieval:
  rrf:
    k: 60  # RRF 模型参数
    rank_discount: 0.5  # 秩衰减因子
    vector_weight: 0.5  # 向量检索权重
    bm25_weight: 0.5  # BM25 检索权重
  fusion_mode: "reciprocal_rank"

llm:
  # LLM 配置（用于 QuestionsAnsweredExtractor）
  model: "gpt-4"
  max_retries: 3
  timeout: 30

embedding:
  # Embedding 配置（用于向量生成）
  model: "text-embedding-ada-002"
  max_retries: 3
  timeout: 30

watch:
  debounce_seconds: 2  # 文件监听防抖时间
```

**扩展性设计**：

IndexManager抽象基类的设计使得系统可以轻松扩展以支持不同类型的索引。以下是扩展示例：

```python
# 示例：创建外部知识库索引管理器
class KnowledgeIndexManager(IndexManager):
    """外部知识库索引管理器

    继承自 IndexManager，实现所有核心接口方法。
    可以用于连接外部知识库（如数据库、API 等）。
    """

    def __init__(self, config):
        """初始化知识库索引管理器"""
        self.config = config
        self._init_knowledge_source()

    def search(self, query: str, top_k: int = 5) -> List[Segment]:
        """检索外部知识库"""
        # 实现外部知识库的检索逻辑
        pass

    def update_document(self, doc_id: str, content: str,
                       metadata: Optional[Dict] = None) -> bool:
        """添加或更新知识库文档"""
        # 实现知识库文档的更新逻辑
        pass

    def delete_document(self, doc_id: str) -> bool:
        """从知识库删除文档"""
        # 实现知识库文档的删除逻辑
        pass

    def build_index(self, force: bool = False) -> bool:
        """构建知识库索引"""
        # 实现知识库索引的构建逻辑
        pass

    def check_consistency(self) -> Dict[str, List[str]]:
        """检查知识库一致性"""
        # 实现知识库一致性检查
        pass

    def repair_consistency(self) -> Dict[str, int]:
        """修复知识库一致性"""
        # 实现知识库一致性修复
        pass
```

**设计意图与架构哲学**：

内置工具模块的设计核心是为 SmartClaw Agent 提供安全、高效、可控的执行能力。该模块遵循以下设计原则：

1. **容器化隔离与安全执行**：使用 Docker 容器隔离敏感操作
   - **terminal 工具**：基于 alpine:3.19 镜像（仅 5MB），提供命令行执行环境
   - **python_repl 工具**：基于 python:3.11-slim 镜像，提供 Python 代码执行环境
   - **会话级持久容器**：每个会话创建独立容器，会话期间复用，会话结束时清理
   - **文件系统隔离**：仅挂载用户指定的 root_dir 到容器 /workspace，其他路径不可见
   - **非 root 用户**：容器内使用固定 UID 1000，降低安全风险
   - **设计目的**：在保证执行能力的同时，提供强大的安全隔离和资源限制

2. **资源限制与崩溃恢复**：确保系统稳定性
   - **资源限制**：terminal 256MB 内存、python_repl 512MB 内存，CPU 限制 25%
   - **自动重启机制**：容器崩溃时自动重启，最多重试 3 次，指数退避（1秒、2秒、4秒）
   - **崩溃记录**：日志记录到 logs/container_crashes.log
   - **用户提示**：返回"工具执行环境需要重建，请重试"信息
   - **设计目的**：防止单个工具执行失败影响整体系统，提供自动恢复机制

3. **多层安全防护机制**：全面的命令和文件操作安全检查
   - **命令分类**：分为直接禁止、每次确认、正常执行、网络请求四类
   - **命令确认**：所有需要确认的命令都需要用户确认，禁止直接跳过
   - **路径安全检查**：防止路径遍历攻击（`../`、符号链接逃逸）
   - **文件类型过滤**：仅允许文本文件（md, txt, py, js, json, yaml, yml 等）
   - **设计目的**：防止误操作和恶意操作，保护用户系统和数据安全

4. **LangChain 原生工具优先**：最大化利用成熟工具
   - **fetch_url 工具**：基于 langchain_community.tools.RequestsGetTool，封装 HTML 清洗和 Markdown 转换
   - **read_file/write_file 工具**：基于 langchain_community.tools.ReadFileTool/WriteFileTool，增强安全检查
   - **设计目的**：减少自研工具的维护成本，利用 LangChain 生态的成熟实现

5. **工具注册与容器绑定机制**：统一的工具管理接口
   - **ToolRegistry 类**：统一管理所有工具的注册、获取和绑定
   - **容器绑定**：需要容器的工具（terminal、python_repl）在调用时自动绑定对应容器
   - **动态绑定**：根据 session_id 获取或创建对应容器实例
   - **设计目的**：提供简洁统一的工具调用接口，隐藏容器管理复杂性

6. **状态清理与输出截断**：确保每次执行环境干净
   - **状态清理**：每次命令/代码执行后清理临时文件和僵尸进程
   - **输出截断**：超过 1MB 的输出进行截断，添加 ...[truncated] 标识
   - **超时控制**：python_repl 代码执行超时限制 30 秒，超时后返回 TimeoutError
   - **设计目的**：防止资源耗尽和输出过大，保证系统响应性

**扩展使用示例**：

```python
# 在 Agent 工具注册时切换索引管理器
def get_index_manager(index_type: str, config: dict) -> IndexManager:
    """根据类型返回索引管理器实例"""
    if index_type == "memory":
        return MemoryIndexManager(config)
    elif index_type == "knowledge":
        return KnowledgeIndexManager(config)
    else:
        raise ValueError(f"Unknown index type: {index_type}")
```

### 3.4 内置工具模块

#### 3.4.1 工具列表与功能

**工具分类架构**：

SmartClaw 的工具分为两大类，按照依赖关系和职责边界进行组织：

| 分类 | 数量 | 特点 | 依赖模块 |
|------|------|------|---------|
| **基础工具** | 5 | 独立运行，无模块依赖 | 无 |
| **记忆工具** | 3 | 依赖 Memory/RAG 模块 | Memory, RAG |

**基础工具清单（5个）**：

| 工具名称 | 类型 | 功能描述 | 容器类型 | 实现来源 |
|---------|------|---------|---------|---------|
| terminal | Docker | 命令行操作 | alpine:3.19 | 自研 |
| python_repl | Docker | Python 代码执行 | python:3.11-slim | 自研 |
| fetch_url | LangChain | 网页内容获取 | - | RequestsGetTool |
| read_file | LangChain | 文件读取 | - | ReadFileTool |
| write_file | LangChain | 文件写入 | - | WriteFileTool |

**记忆工具清单（3个）**：

| 工具名称 | 功能描述 | 实现来源 | 依赖模块 |
|---------|---------|---------|---------|
| search_memory | 长期记忆检索（混合检索） | RAG 模块提供 | RAG |
| write_near_memory | 写入近端记忆 | Memory 模块提供 | Memory |
| write_core_memory | 写入核心记忆 | Memory 模块提供 | Memory |

**预留工具**：

| 工具名称 | 功能描述 | 状态 |
|---------|---------|------|
| search_knowledge | 外部知识库检索 | 接口预留，暂不实现 |

**工具注册机制**：
```python
class ToolRegistry:
    def __init__(self, config, memory_manager, rag_manager):
        self.tools = {}
        self.config = config
        self.container_manager = ContainerManager(config)
        self.memory_manager = memory_manager  # Memory 模块实例
        self.rag_manager = rag_manager        # RAG 模块实例

    def register_tools(self):
        """注册所有工具"""
        # 1. 基础工具（5个，独立运行）
        self.tools['terminal'] = self._create_terminal_tool()
        self.tools['python_repl'] = self._create_python_repl_tool()
        self.tools['fetch_url'] = self._create_fetch_url_tool()
        self.tools['read_file'] = self._create_read_file_tool()
        self.tools['write_file'] = self._create_write_file_tool()

        # 2. 记忆工具（3个，依赖 Memory/RAG 模块）
        # search_memory 由 RAG 模块提供
        self.tools['search_memory'] = self.rag_manager.get_search_tool()
        # write_near_memory 和 write_core_memory 由 Memory 模块提供
        self.tools['write_near_memory'] = self.memory_manager.get_write_near_memory_tool()
        self.tools['write_core_memory'] = self.memory_manager.get_write_core_memory_tool()

        # 3. 预留工具（暂不实现）
        # self.tools['search_knowledge'] = self._create_search_knowledge_tool()

    def get_tool(self, tool_name):
        """获取工具实例"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")

        # 需要容器的工具进行特殊处理
        if tool_name in ['terminal', 'python_repl']:
            container = self.container_manager.get_container(tool_name)
            return self.tools[tool_name].bind(container=container)

        return self.tools[tool_name]
```

#### 3.4.2 容器管理策略

**ContainerManager 实现**：
```python
class ContainerManager:
    def __init__(self, config):
        self.config = config
        self.containers = {}  # {(tool_type, session_id): container}
        self.docker_client = docker.from_env()

    def get_container(self, tool_type, session_id):
        """获取或创建容器"""
        key = (tool_type, session_id)

        if key not in self.containers:
            # 创建新容器
            container = self._create_container(tool_type)
            self.containers[key] = container

        # 检查容器状态
        if self.containers[key].status != 'running':
            self._restart_container(self.containers[key])

        return self.containers[key]

    def _create_container(self, tool_type):
        """创建容器"""
        tool_config = self.config.tools[tool_type]

        container = self.docker_client.containers.create(
            image=tool_config.image,
            memory=tool_config.memory_limit,
            cpu_quota=int(tool_config.cpu_limit * 100000),
            detach=True,
            user=str(tool_config.user_uid),
            labels={
                'tool_type': tool_type,
                'session_id': session_id,
                'auto_restart': str(tool_config.auto_restart)
            }
        )

        container.start()
        return container

    def _restart_container(self, container, attempt=1):
        """重启容器"""
        if attempt > self.config.tools[container.labels['tool_type']].max_retries:
            raise ContainerError(f"Failed to restart container after {attempt} attempts")

        # 指数退避
        backoff = self.config.tools[container.labels['tool_type']].retry_backoff[attempt-1]
        time.sleep(backoff)

        try:
            container.restart()
        except Exception as e:
            self.logger.warning(f"Container restart failed (attempt {attempt}): {e}")
            # 递归重试
            self._restart_container(container, attempt + 1)
```

#### 3.4.3 安全限制机制

**工具安全策略**：

| 工具 | 安全措施 | 限制类型 |
|------|---------|---------|
| terminal | 命令白名单/黑名单 | 命令执行 |
| python_repl | subprocess 禁用、超时控制 | 代码执行 |
| fetch_url | 域名白名单/黑名单 | 网络访问 |
| read_file | 路径遍历检查 | 文件访问 |
| write_file | 路径限制、类型过滤 | 文件写入 |

**安全检查实现**：
```python
class SecurityChecker:
    def __init__(self, config):
        self.config = config
        self.banned_commands = self._load_banned_commands()

    def check_command_safety(self, command):
        """检查命令安全性"""
        # 1. 检查黑名单命令
        if any(cmd in command.lower() for cmd in self.banned_commands['direct']):
            return False, "Command is in the banned list"

        # 2. 检查危险组合
        if any(cmd in command for cmd in ['sudo rm', 'mkfs', 'dd', 'reboot']):
            return False, "Dangerous command combination"

        # 3. 检查管道命令
        if '|' in command and any(cmd in command for cmd in ['sh', 'bash', 'python']):
            return False, "Pipe execution not allowed"

        return True, "Command safe"

    def check_path_safety(self, file_path):
        """检查路径安全性"""
        import os.path

        # 1. 规范化路径
        normalized = os.path.normpath(file_path)

        # 2. 检查路径遍历
        if '../' in normalized or normalized.startswith('/'):
            return False, "Path traversal not allowed"

        # 3. 检查文件类型
        allowed_extensions = self.config.tools.allowed_extensions
        if not any(normalized.endswith(ext) for ext in allowed_extensions):
            return False, "File type not allowed"

        return True, "Path safe"
```

#### 3.4.4 内置工具模块接口设计

**工具实现接口**：
```python
from langchain.tools import tool

@tool
def terminal(command: str) -> str:
    """命令行操作工具（Docker 沙箱）

    Args:
        command: 要执行的命令字符串

    Returns:
        命令执行结果
    """
    # 工具调用逻辑
    pass

@tool
def python_repl(code: str) -> str:
    """Python 代码解释器（Docker 沙箱）

    Args:
        code: 要执行的 Python 代码

    Returns:
        代码执行结果或错误信息
    """
    # 工具调用逻辑
    pass

@tool
def fetch_url(url: str) -> str:
    """网络信息获取工具

    Args:
        url: 要获取的网页 URL

    Returns:
        网页内容（清洗后的 Markdown 格式）
    """
    # 工具调用逻辑
    pass

@tool
def read_file(file_path: str) -> str:
    """文件读取工具

    Args:
        file_path: 要读取的文件路径

    Returns:
        文件内容
    """
    # 工具调用逻辑
    pass

@tool
def write_file(file_path: str, content: str) -> str:
    """文件写入工具

    Args:
        file_path: 要写入的文件路径
        content: 要写入的内容

    Returns:
        写入结果
    """
    # 工具调用逻辑
    pass

@tool
def write_near_memory(
    date: Optional[str] = None,
    content: str = "",
    category: Optional[str] = None
) -> str:
    """写入近端记忆

    Args:
        date: 日期（YYYY-MM-DD 格式），默认为当天
        content: 要写入的内容（Markdown 格式）
        category: 内容类别（对话摘要/重要事实/决策记录）

    Returns:
        操作结果消息
    """
    # 工具调用逻辑
    pass

@tool
def write_core_memory(
    file_key: str,
    content: str,
    mode: str = "append"
) -> str:
    """写入核心记忆

    Args:
        file_key: 文件标识（soul/identity/user/memory）
        content: 要写入的内容（Markdown 格式）
        mode: 写入模式（append/replace）

    Returns:
        操作结果消息
    """
    # 工具调用逻辑
    pass

@tool
def search_memory(
    query: str,
    top_k: int = 5,
    date_range: Optional[tuple[str, str]] = None
) -> str:
    """检索长期记忆

    Args:
        query: 查询文本
        top_k: 返回结果数量，默认 5
        date_range: 日期范围 (start_date, end_date)，格式 YYYY-MM-DD

    Returns:
        检索结果
    """
    # 工具调用逻辑
    pass
```

**Docker 容器管理接口**：
```python
class ContainerManager:
    """容器生命周期管理器"""

    def __init__(self, config):
        self.config = config
        self.containers = {}  # {(tool_type, session_id): container}
        self.docker_client = None

    def get_container(self, tool_type: str, session_id: str) -> Container:
        """获取或创建容器

        Args:
            tool_type: 工具类型（terminal/python_repl）
            session_id: 会话 ID

        Returns:
            Docker 容器实例
        """
        pass

    def cleanup_session_containers(self, session_id: str):
        """清理会话相关的所有容器

        Args:
            session_id: 会话 ID
        """
        pass

    def _create_container(self, tool_type: str, session_id: str) -> Container:
        """创建新容器

        Args:
            tool_type: 工具类型
            session_id: 会话 ID

        Returns:
            Docker 容器实例
        """
        pass

    def _restart_container(self, container: Container, attempt: int = 1):
        """重启容器（带重试机制）

        Args:
            container: 容器实例
            attempt: 重试次数
        """
        pass
```

**安全检查接口**：
```python
class SecurityChecker:
    """安全检查器"""

    def __init__(self, config):
        self.config = config
        self._init_security_rules()

    def _init_security_rules(self):
        """初始化安全规则"""
        self.banned_commands = {
            'direct': ['rm -rf', 'sudo rm', 'mkfs', 'dd', 'reboot', 'shutdown'],
            'confirm': ['rm', 'mv', 'cp', 'chmod', 'chown']
        }
        self.allowed_extensions = ['.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml']

    def check_command(self, command: str, tool_type: str) -> tuple[bool, str]:
        """检查命令安全性

        Args:
            command: 命令字符串
            tool_type: 工具类型

        Returns:
            (是否允许, 错误信息)
        """
        if tool_type == 'terminal':
            return self._check_terminal_command(command)
        elif tool_type == 'python_repl':
            return self._check_python_code(command)
        return True, "OK"

    def check_file_access(self, file_path: str, operation: str) -> tuple[bool, str]:
        """检查文件访问权限

        Args:
            file_path: 文件路径
            operation: 操作类型（read/write）

        Returns:
            (是否允许, 错误信息)
        """
        if operation == 'read':
            return self._check_read_path(file_path)
        elif operation == 'write':
            return self._check_write_path(file_path)
        return True, "OK"

    def _check_terminal_command(self, command: str) -> tuple[bool, str]:
        """检查终端命令"""
        # 检查黑名单命令
        for banned in self.banned_commands['direct']:
            if banned in command:
                return False, f"Command contains banned operation: {banned}"

        # 需要确认的命令
        for need_confirm in self.banned_commands['confirm']:
            if need_confirm in command:
                return False, f"Command requires confirmation: {need_confirm}"

        return True, "Command safe"

    def _check_python_code(self, code: str) -> tuple[bool, str]:
        """检查 Python 代码安全性"""
        # 检查危险模块导入
        dangerous_imports = ['os.system', 'subprocess', 'eval', 'exec']
        for imp in dangerous_imports:
            if imp in code:
                return False, f"Dangerous import not allowed: {imp}"

        return True, "Code safe"
```

## 4. 配置模块设计

### 4.1 设计原则

SmartClaw 配置模块遵循以下设计原则：

1. **统一配置源**：所有模块配置集中管理，避免配置分散
2. **层级结构**：配置项按模块层级组织，便于维护和理解
3. **环境变量支持**：敏感信息通过环境变量注入，支持 `.env` 文件
4. **配置验证**：使用 Pydantic 进行配置验证，启动时检查配置有效性
5. **不可变配置**：配置在启动时加载，运行时不可修改

### 4.2 配置文件结构

配置文件位于 `~/.smartclaw/config.yaml`，采用 YAML 格式。

```yaml
# config.yaml
# SmartClaw 配置文件
# 版本：1.0

version: "1.0"

# ============================================
# 存储配置（统一基础路径）
# ============================================
storage:
  base_path: "~/.smartclaw"

# ============================================
# LLM 模型配置
# ============================================
llm:
  # 默认模型（Agent 主模型）
  default:
    provider: "anthropic"  # anthropic / openai / qwen / ollama / vllm
    model: "claude-sonnet-4-20250514"
    api_key: "${ANTHROPIC_API_KEY}"  # 从环境变量读取
    base_url: ""  # 可选，自定义 API 端点
    max_tokens: 4096
    temperature: 0.7

  # RAG 专用模型（用于 QuestionsAnsweredExtractor）
  rag:
    provider: "openai"
    model: "gpt-4o-mini"
    api_key: "${OPENAI_API_KEY}"
    max_tokens: 1000
    temperature: 0.3

# ============================================
# Embedding 模型配置
# ============================================
embedding:
  provider: "openai"  # openai / qwen / ollama / vllm
  model: "text-embedding-3-small"
  api_key: "${OPENAI_API_KEY}"
  dimensions: 1536

# ============================================
# Agent 配置
# ============================================
agent:
  # 会话配置
  session:
    token_threshold: 3000      # 预压缩触发阈值
    flush_ratio: 0.5           # 冲刷比例（最旧的 50%）
    max_session_messages: 100  # 单次会话最大消息数

  # System Prompt 配置
  system_prompt:
    max_tokens: 30000          # System Prompt 最大 token 数
    near_memory_days: 2        # 加载近端记忆的天数

# ============================================
# Memory 模块配置
# ============================================
memory:
  # 路径配置（继承 storage.base_path）
  base_path: "${storage.base_path}"

  # 近端记忆配置
  near_memory:
    days: 2                    # 近端记忆保留天数
    pre_compress_threshold: 3000  # 预压缩阈值
    flush_ratio: 0.5           # 冲刷比例

  # 核心记忆配置
  core_memory:
    max_tokens: 30000          # 核心记忆最大 token 数
    files:                     # 核心记忆文件列表
      - "soul"
      - "identity"
      - "user"
      - "memory"
      - "agents"
      - "skills_snapshot"

  # 会话配置
  session:
    compression_threshold: 8000   # 会话压缩阈值
    summary_ratio: 0.2            # 摘要保留比例
    archive_path: "sessions/archive"
    current_path: "sessions/current"

# ============================================
# RAG 模块配置
# ============================================
rag:
  # 路径配置
  index_path: "${storage.base_path}/store/memory"

  # 向量存储配置
  vector_store:
    provider: "chroma"
    path: "${storage.base_path}/store/chroma"

  # BM25 索引配置
  bm25:
    path: "${storage.base_path}/store/bm25"

  # 分块配置
  chunk_size: 1024
  chunk_overlap: 100

  # 检索配置
  top_k: 5

  # 问题生成配置（QuestionsAnsweredExtractor）
  generate_queries: 3

  # 检索融合配置
  retrieval:
    rrf:
      k: 60                    # RRF 模型参数
      rank_discount: 0.5       # 秩衰减因子
      vector_weight: 0.5       # 向量检索权重
      bm25_weight: 0.5         # BM25 检索权重
    fusion_mode: "reciprocal_rank"  # 融合策略

  # 文件监听配置
  watch:
    dir: "sessions/archive"    # 监听目录
    debounce_seconds: 2        # 防抖时间

# ============================================
# 内置工具配置
# ============================================
tools:
  # 文件操作根目录（独立配置，不与记忆共享）
  root_dir: "./workspace"

  # terminal 工具配置
  terminal:
    image: "alpine:3.19"
    memory_limit: "256m"
    cpu_limit: "0.25"
    user_uid: 1000
    auto_restart: true
    max_retries: 3
    retry_backoff: [1, 2, 4]   # 指数退避间隔（秒）
    output_limit: 1048576      # 输出截断限制（1MB）

  # python_repl 工具配置
  python_repl:
    image: "python:3.11-slim"
    memory_limit: "512m"
    cpu_limit: "0.25"
    user_uid: 1000
    auto_restart: true
    max_retries: 3
    retry_backoff: [1, 2, 4]
    output_limit: 1048576
    execution_timeout: 30      # 代码执行超时（秒）
    preinstalled_packages:     # 预装包列表
      - "pandas"
      - "numpy"
      - "requests"
      - "matplotlib"
      - "beautifulsoup4"

  # fetch_url 工具配置
  fetch_url:
    timeout: 30                # 请求超时（秒）
    max_retries: 3
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

  # 文件操作工具配置
  file_ops:
    allowed_extensions:        # 允许的文件类型
      - "md"
      - "txt"
      - "py"
      - "js"
      - "json"
      - "yaml"
      - "yml"
      - "toml"
      - "xml"
      - "html"
      - "css"

# ============================================
# Skills 配置
# ============================================
skills:
  directory: "${storage.base_path}/skills"
  snapshot_file: "${storage.base_path}/store/core/SKILLS_SNAPSHOT.md"
  watch_debounce: 2            # 技能变更防抖时间（秒）

# ============================================
# 日志配置
# ============================================
logging:
  level: "INFO"                # DEBUG / INFO / WARNING / ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "${storage.base_path}/logs/smartclaw.log"
  max_size: "10MB"
  backup_count: 5

  # 模块日志级别覆盖
  modules:
    agent: "INFO"
    memory: "INFO"
    rag: "INFO"
    tools: "INFO"
    container: "WARNING"
```

### 4.3 配置管理机制

#### 4.3.1 配置加载流程

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Optional, List, Dict
import yaml
import os

class Settings(BaseSettings):
    """SmartClaw 配置管理类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # 存储配置
    storage_base_path: Path = Field(default=Path("~/.smartclaw"))

    # LLM 配置
    llm_default_provider: str = "anthropic"
    llm_default_model: str = "claude-sonnet-4-20250514"
    llm_default_max_tokens: int = 4096
    llm_default_temperature: float = 0.7

    # Agent 配置
    agent_session_token_threshold: int = 3000
    agent_session_flush_ratio: float = 0.5
    agent_system_prompt_near_memory_days: int = 2

    # RAG 配置
    rag_top_k: int = 5
    rag_chunk_size: int = 1024
    rag_chunk_overlap: int = 100

    # 工具配置
    tools_root_dir: Path = Field(default=Path("./workspace"))
    tools_terminal_image: str = "alpine:3.19"
    tools_python_repl_image: str = "python:3.11-slim"

    @field_validator("storage_base_path", "tools_root_dir", mode="before")
    @classmethod
    def expand_path(cls, v):
        """展开路径中的 ~ 和环境变量"""
        if isinstance(v, str):
            v = os.path.expandvars(v)
        return Path(v).expanduser()


class ConfigManager:
    """配置管理器"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        config_path = Path("~/.smartclaw/config.yaml").expanduser()

        if not config_path.exists():
            # 使用默认配置
            return self._get_default_config()

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 展开环境变量引用
        config = self._expand_env_vars(config)

        # 验证配置
        self._validate_config(config)

        return config

    def _expand_env_vars(self, config: dict) -> dict:
        """递归展开配置中的环境变量引用"""
        if isinstance(config, dict):
            return {k: self._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 展开 ${var} 格式的环境变量
            if config.startswith("${") and config.endswith("}"):
                var_name = config[2:-1]
                # 处理嵌套引用（如 ${storage.base_path}）
                if "." in var_name:
                    return self._resolve_nested_ref(var_name)
                return os.environ.get(var_name, "")
            return os.path.expandvars(config)
        return config

    def _resolve_nested_ref(self, ref: str) -> str:
        """解析嵌套配置引用"""
        keys = ref.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return ""
        return str(value)

    def _validate_config(self, config: dict):
        """验证配置有效性"""
        errors = []

        # 验证必需的配置项
        required_keys = ["storage.base_path", "llm.default.provider"]
        for key in required_keys:
            if not self._get_nested_value(config, key):
                errors.append(f"Missing required config: {key}")

        # 验证数值范围
        if config.get("agent", {}).get("session", {}).get("flush_ratio", 0) > 1:
            errors.append("flush_ratio must be <= 1")

        if errors:
            raise ValueError(f"Config validation failed:\n" + "\n".join(errors))

    def _get_nested_value(self, config: dict, key: str):
        """获取嵌套配置值"""
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value

    def get(self, key: str, default=None):
        """获取配置项"""
        return self._get_nested_value(self._config, key) or default

    def get_config(self) -> dict:
        """获取完整配置"""
        return self._config.copy()


def get_config() -> dict:
    """全局配置获取函数"""
    return ConfigManager().get_config()
```

#### 4.3.2 配置访问方式

各模块通过统一接口访问配置：

```python
# Agent 模块
config = get_config()
token_threshold = config.get("agent.session.token_threshold", 3000)

# Memory 模块
base_path = config.get("memory.base_path", "~/.smartclaw")

# RAG 模块
top_k = config.get("rag.top_k", 5)

# 工具模块
terminal_image = config.get("tools.terminal.image", "alpine:3.19")
```

### 4.4 环境变量支持

#### 4.4.1 环境变量文件 (.env)

```bash
# ~/.smartclaw/.env
# SmartClaw 环境变量配置

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 存储路径（可选覆盖）
SMARTCLAW_HOME=~/.smartclaw

# 日志级别（可选覆盖）
SMARTCLAW_LOG_LEVEL=INFO

# Docker 配置（可选）
DOCKER_HOST=unix:///var/run/docker.sock
```

#### 4.4.2 环境变量优先级

配置加载优先级（从高到低）：

1. **环境变量**：直接设置的环境变量
2. **.env 文件**：从 `.env` 文件加载的环境变量
3. **config.yaml**：YAML 配置文件中的值
4. **默认值**：代码中的默认值

```python
# 环境变量命名规则
# {MODULE}_{SECTION}_{KEY} 格式
SMARTCLAW_LLM_DEFAULT_MODEL=gpt-4
SMARTCLAW_RAG_TOP_K=10
SMARTCLAW_TOOLS_TERMINAL_MEMORY_LIMIT=512m
```

### 4.5 配置验证规则

#### 4.5.1 类型验证

```python
from pydantic import BaseModel, field_validator
from typing import Literal

class LLMConfig(BaseModel):
    provider: Literal["anthropic", "openai", "qwen", "ollama", "vllm"]
    model: str
    api_key: str
    max_tokens: int = Field(ge=1, le=100000)
    temperature: float = Field(ge=0, le=2)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or v == "your_api_key_here":
            raise ValueError("API key must be configured")
        return v


class ContainerConfig(BaseModel):
    image: str
    memory_limit: str
    cpu_limit: str

    @field_validator("memory_limit")
    @classmethod
    def validate_memory(cls, v):
        # 验证内存格式：256m, 512m, 1g 等
        import re
        if not re.match(r"^\d+[mg]?$", v):
            raise ValueError(f"Invalid memory format: {v}")
        return v
```

#### 4.5.2 依赖关系验证

```python
def validate_config_dependencies(config: dict) -> List[str]:
    """验证配置项之间的依赖关系"""
    warnings = []

    # RAG 模块需要 LLM 和 Embedding 配置
    if config.get("rag"):
        if not config.get("llm", {}).get("rag"):
            warnings.append("RAG module requires llm.rag configuration")
        if not config.get("embedding"):
            warnings.append("RAG module requires embedding configuration")

    # Docker 工具需要 Docker 环境
    docker_tools = ["terminal", "python_repl"]
    for tool in docker_tools:
        if config.get("tools", {}).get(tool):
            # 检查 Docker 是否可用
            import subprocess
            try:
                subprocess.run(["docker", "info"], capture_output=True, check=True)
            except:
                warnings.append(f"Tool '{tool}' requires Docker to be running")

    return warnings
```

### 4.6 配置热更新说明

**重要**：SmartClaw 不支持运行时配置热更新。

- **原因**：配置涉及 LLM 客户端、Docker 容器、向量存储等资源，运行时修改可能导致不一致
- **修改配置后**：需要重启服务才能生效
- **动态调整**：部分参数（如 `top_k`）可通过 Agent 工具参数在调用时覆盖

### 4.7 默认配置模板

首次启动时，系统自动创建默认配置文件：

```python
DEFAULT_CONFIG = {
    "version": "1.0",
    "storage": {
        "base_path": "~/.smartclaw"
    },
    "llm": {
        "default": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key": "${ANTHROPIC_API_KEY}",
            "max_tokens": 4096,
            "temperature": 0.7
        }
    },
    "embedding": {
        "provider": "openai",
        "model": "text-embedding-3-small",
        "api_key": "${OPENAI_API_KEY}"
    },
    "agent": {
        "session": {
            "token_threshold": 3000,
            "flush_ratio": 0.5
        }
    },
    "memory": {
        "base_path": "${storage.base_path}",
        "near_memory": {"days": 2},
        "core_memory": {"max_tokens": 30000}
    },
    "rag": {
        "index_path": "${storage.base_path}/store/memory",
        "top_k": 5,
        "chunk_size": 1024
    },
    "tools": {
        "root_dir": "./workspace",
        "terminal": {"image": "alpine:3.19"},
        "python_repl": {"image": "python:3.11-slim"}
    },
    "logging": {
        "level": "INFO"
    }
}

def init_default_config():
    """初始化默认配置文件"""
    config_path = Path("~/.smartclaw/config.yaml").expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True)
        print(f"Created default config at {config_path}")
```

### 4.8 配置项索引

| 配置路径 | 说明 | 默认值 |
|---------|------|--------|
| `storage.base_path` | 存储根目录 | `~/.smartclaw` |
| `llm.default.provider` | 默认 LLM 提供商 | `anthropic` |
| `llm.default.model` | 默认模型 | `claude-sonnet-4-20250514` |
| `llm.default.max_tokens` | 最大输出 token | `4096` |
| `llm.rag.provider` | RAG 专用 LLM 提供商 | `openai` |
| `embedding.provider` | Embedding 提供商 | `openai` |
| `embedding.model` | Embedding 模型 | `text-embedding-3-small` |
| `agent.session.token_threshold` | 预压缩阈值 | `3000` |
| `agent.session.flush_ratio` | 冲刷比例 | `0.5` |
| `memory.near_memory.days` | 近端记忆天数 | `2` |
| `memory.core_memory.max_tokens` | 核心记忆最大 token | `30000` |
| `rag.indexes.memory.index_path` | 记忆知识库索引路径 | `~/.smartclaw/store/rag/memory` |
| `rag.indexes.memory.watch_dir` | 记忆知识库监听目录 | `~/.smartclaw/sessions/archive` |
| `rag.indexes.memory.top_k` | 记忆检索返回数量 | `5` |
| `rag.indexes.memory.chunk_size` | 记忆分块大小 | `1024` |
| `rag.indexes.knowledge.index_path` | 外部知识库索引路径（预留） | `~/.smartclaw/store/rag/knowledge` |
| `rag.retrieval.rrf.k` | RRF 参数 | `60` |
| `tools.terminal.memory_limit` | Terminal 容器内存 | `256m` |
| `tools.python_repl.memory_limit` | Python REPL 容器内存 | `512m` |
| `skills.watch_debounce` | 技能变更防抖时间 | `2` |
| `logging.level` | 日志级别 | `INFO` |

## 5. 日志模块设计

### 5.1 设计目标

SmartClaw 日志模块旨在为系统提供完整、可追溯的运行记录，支持问题诊断、性能监控和审计需求。设计遵循以下原则：

1. **分级记录**：根据重要程度区分日志级别，便于筛选和过滤
2. **模块隔离**：各模块拥有独立的日志命名空间，便于定位问题来源
3. **结构化输出**：统一日志格式，包含时间戳、模块名、级别和详细信息
4. **持久化存储**：支持日志轮转和归档，避免日志文件无限增长
5. **性能友好**：异步写入机制，不影响主流程性能

### 5.2 日志级别与使用场景

系统采用标准五级日志体系，各级别含义和使用场景如下：

| 级别 | 含义 | 使用场景 |
|-----|------|---------|
| **DEBUG** | 调试信息 | 开发阶段追踪详细执行流程，生产环境默认关闭 |
| **INFO** | 常规信息 | 记录关键操作完成状态，如会话创建、工具调用、记忆写入 |
| **WARNING** | 警告信息 | 非预期但可恢复的情况，如配置使用默认值、容器重启重试 |
| **ERROR** | 错误信息 | 影响功能但系统可继续运行，如工具调用失败、LLM 请求超时 |
| **CRITICAL** | 严重错误 | 导致系统无法继续运行，如配置加载失败、核心模块初始化失败 |

**级别选择原则**：
- DEBUG 用于临时调试，不应出现在生产日志中
- INFO 记录"发生了什么"，而非"如何发生的"
- WARNING 表示需要关注但不影响当前操作
- ERROR 表示操作失败，需要记录完整上下文
- CRITICAL 仅用于系统级故障

### 5.3 日志格式规范

所有日志采用统一格式，确保可读性和可解析性：

```
{时间戳} - {模块名} - {级别} - {消息内容}
```

**格式说明**：
- **时间戳**：ISO 8601 格式（`YYYY-MM-DD HH:MM:SS,mmm`），精确到毫秒
- **模块名**：采用点分命名（如 `smartclaw.agent.session`），便于过滤
- **级别**：大写英文（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- **消息内容**：人类可读的描述性文本，必要时包含结构化数据

**示例输出**：
```
2026-03-18 14:30:15,123 - smartclaw.agent - INFO - Session created: session_abc123
2026-03-18 14:30:18,456 - smartclaw.tools.terminal - INFO - Tool invoked: terminal, command="ls -la"
2026-03-18 14:30:18,789 - smartclaw.tools.terminal - INFO - Tool completed: terminal, duration=333ms
2026-03-18 14:30:25,012 - smartclaw.memory - WARNING - Memory write retry: attempt 1/2
2026-03-18 14:30:32,345 - smartclaw.rag - ERROR - Index update failed: LLM timeout after 30s
```

### 5.4 模块日志记录点

#### 5.4.1 Agent 模块

Agent 模块负责整体会话管理，需记录以下关键事件：

**会话生命周期**：
- 会话创建：记录 session_key、session_id、创建时间
- 会话开始：记录 System Prompt 拼接完成状态、token 数量
- 会话结束：记录结束原因（用户关闭/超时/错误）、总消息数、总耗时
- 会话归档：记录归档路径、文件大小

**消息处理**：
- 用户消息接收：记录消息长度、token 估算值
- LLM 请求发送：记录模型名称、请求 token 数
- LLM 响应接收：记录响应 token 数、耗时、是否触发工具调用
- 响应返回用户：记录总处理时间

**预压缩冲刷**：
- 触发检测：记录当前 token 数、阈值
- 冲刷执行：记录冲刷消息数、冲刷比例
- 压缩完成：记录压缩前后的消息数对比、摘要长度

#### 5.4.2 工具模块

工具模块执行用户命令和代码，需详细记录操作过程：

**工具调用通用记录**：
- 调用开始：工具名称、参数摘要（敏感参数脱敏）
- 调用结束：执行结果状态、耗时、输出长度
- 调用失败：错误类型、错误消息、重试次数

**Terminal 工具特殊记录**：
- 容器创建：容器 ID、镜像版本、资源限制
- 命令执行：命令内容（敏感命令脱敏）、执行目录
- 命令确认：需要用户确认的命令、用户决策
- 容器重启：重启原因、重试次数、恢复状态

**Python REPL 工具特殊记录**：
- 代码执行：代码长度、执行超时设置
- 执行结果：输出长度、是否截断、错误信息（如有）
- 禁止操作检测：检测到的危险操作类型

**Fetch URL 工具特殊记录**：
- 请求发起：目标 URL、超时设置
- 响应接收：HTTP 状态码、内容大小、内容类型
- 内容清洗：清洗前后大小对比、保留元素数量

**文件操作工具特殊记录**：
- 路径检查：请求路径、规范化路径、是否在允许范围内
- 操作类型：读取/写入、文件大小
- 安全检查：检查结果（通过/拒绝）、拒绝原因

#### 5.4.3 Memory 模块

Memory 模块管理记忆的读写和归档，需确保操作可追溯：

**记忆读取**：
- 近端记忆加载：加载天数、文件数量、总 token 数
- 核心记忆加载：加载的文件列表、各文件大小
- 长期记忆检索：查询内容、返回结果数、检索耗时

**记忆写入**：
- 近端记忆写入：写入日期、内容类别、内容长度
- 核心记忆写入：目标文件、写入模式、内容长度
- 写入失败：失败原因、重试次数、最终状态

**会话归档**：
- 归档触发：触发原因（新建会话/手动归档）
- 归档过程：源路径、目标路径、文件大小
- 归档完成：归档耗时、是否触发 RAG 索引更新

#### 5.4.4 RAG 模块

RAG 模块负责索引构建和检索，需记录异步操作状态：

**文件监听**：
- 监听启动：监听目录、防抖时间设置
- 变更检测：变更类型（创建/修改/删除）、文件路径
- 事件去重：去重前后的事件数量

**索引构建**：
- 构建触发：触发源（文件监听/手动/启动初始化）
- 构建过程：处理的文件数、生成的节点数、LLM 调用次数
- 构建完成：总耗时、索引大小、是否有降级

**检索操作**：
- 检索请求：查询内容、top_k 设置、是否有过滤条件
- 检索过程：向量检索耗时、BM25 检索耗时、融合耗时
- 检索结果：返回片段数、最高相关性得分

**错误与降级**：
- LLM 调用失败：失败阶段、重试次数、降级策略
- 向量存储错误：错误类型、是否切换到仅 BM25 模式

#### 5.4.5 容器管理

容器管理涉及 Docker 操作，需详细记录生命周期：

**容器生命周期**：
- 容器创建：容器 ID、工具类型、镜像版本、会话 ID
- 容器启动：启动参数、资源限制、挂载目录
- 容器停止：停止原因、优雅关闭尝试、强制终止
- 容器清理：清理触发源、清理结果

**容器异常**：
- 崩溃检测：崩溃时间、退出码、最后输出
- 自动重启：重启次数、退避间隔、恢复状态
- 资源超限：超限类型（内存/CPU）、当前使用量、限制值

### 5.5 日志存储与轮转

#### 5.5.1 存储位置

日志文件统一存储在 `{storage.base_path}/logs/` 目录下：

```
~/.smartclaw/logs/
├── smartclaw.log          # 主日志文件
├── smartclaw.log.1        # 轮转备份 1
├── smartclaw.log.2        # 轮转备份 2
├── smartclaw.log.3        # 轮转备份 3
├── smartclaw.log.4        # 轮转备份 4
├── container_crashes.log  # 容器崩溃专用日志
└── archive/               # 归档日志目录
    └── smartclaw-2026-03.log.gz
```

#### 5.5.2 轮转策略

日志轮转采用大小+时间混合策略：

**基于大小的轮转**：
- 单个日志文件最大 10MB
- 达到大小限制时触发轮转
- 保留最近 5 个备份文件
- 超出数量的旧文件自动删除

**基于时间的归档**：
- 每月将轮转备份压缩归档
- 归档文件命名格式：`smartclaw-YYYY-MM.log.gz`
- 归档文件保留 12 个月（可配置）

**轮转触发时机**：
- 每次写入日志前检查文件大小
- 达到阈值时立即执行轮转
- 轮转操作原子性，不丢失日志

#### 5.5.3 特殊日志文件

**容器崩溃日志**（`container_crashes.log`）：
- 专门记录容器异常事件
- 独立于主日志，便于问题追踪
- 包含完整的崩溃上下文：容器 ID、工具类型、会话 ID、错误输出、重启记录

**格式示例**：
```
[2026-03-18 14:30:15] CRASH - terminal container abc123 crashed
  Exit Code: 137 (OOM Killed)
  Session: session_xyz789
  Memory Usage: 260MB / 256MB limit
  Last Output: [truncated]...
  Restart Attempt: 1/3
  Restart Result: SUCCESS
```

### 5.6 敏感信息处理

日志系统需保护敏感信息，避免泄露：

**脱敏规则**：
- API Key：记录前 4 位和后 4 位，中间用 `****` 替换（如 `sk-a****1234`）
- 用户数据：命令参数中的密码、密钥等使用 `[REDACTED]` 替换
- 文件内容：仅记录内容长度，不记录实际内容
- URL 参数：移除敏感查询参数（如 `token=`, `key=`, `password=`）

**敏感命令检测**：
- 包含密码的命令：`mysql -p password` → `mysql -p [REDACTED]`
- 包含密钥的 URL：`?api_key=secret` → `?api_key=[REDACTED]`
- 环境变量赋值：`export PASSWORD=xxx` → `export PASSWORD=[REDACTED]`

**脱敏实现位置**：
- 日志记录前统一调用脱敏函数
- 各模块不需要单独处理脱敏逻辑
- 脱敏规则集中配置，便于更新

### 5.7 日志级别配置

#### 5.7.1 全局级别

通过配置文件设置全局日志级别：

```yaml
logging:
  level: "INFO"  # DEBUG / INFO / WARNING / ERROR / CRITICAL
```

全局级别影响所有模块，低于该级别的日志不会输出。

#### 5.7.2 模块级别覆盖

可为特定模块设置不同的日志级别，便于调试：

```yaml
logging:
  level: "INFO"
  modules:
    agent: "DEBUG"        # Agent 模块详细日志
    tools: "INFO"
    memory: "INFO"
    rag: "INFO"
    container: "WARNING"  # 容器模块仅记录警告以上
```

**模块命名空间**：
- `smartclaw.agent`：Agent 主模块
- `smartclaw.agent.session`：会话管理子模块
- `smartclaw.tools`：工具模块
- `smartclaw.tools.terminal`：Terminal 工具子模块
- `smartclaw.tools.python_repl`：Python REPL 子模块
- `smartclaw.memory`：Memory 模块
- `smartclaw.rag`：RAG 模块
- `smartclaw.container`：容器管理模块

#### 5.7.3 运行时调整

日志级别支持通过环境变量临时覆盖：

```bash
# 临时开启调试模式
export SMARTCLAW_LOG_LEVEL=DEBUG
python -m smartclaw

# 仅调试特定模块
export SMARTCLAW_LOG_MODULE_AGENT=DEBUG
```

此方式优先级高于配置文件，便于生产环境临时排查问题。

### 5.8 日志访问接口

#### 5.8.1 获取器函数

各模块通过统一的日志获取器获取 Logger 实例：

```python
from smartclaw.logging import get_logger

logger = get_logger(__name__)  # 使用模块名自动命名
logger.info("Operation completed", extra={"duration_ms": 150})
```

#### 5.8.2 结构化日志字段

对于需要结构化记录的信息，使用 `extra` 参数传递：

| 字段名 | 说明 | 示例 |
|-------|------|------|
| `session_key` | 前端客户端 ID | `client_xyz789` |
| `session_id` | 后端会话标识 | `2026-03-16-abc123` |
| `tool_name` | 工具名称 | `terminal` |
| `duration_ms` | 耗时（毫秒） | `150` |
| `token_count` | Token 数量 | `2048` |
| `container_id` | 容器标识 | `abc123` |
| `retry_count` | 重试次数 | `2` |
| `error_type` | 错误类型 | `LLMTimeoutError` |

这些字段会被附加到日志消息中，便于后续分析和过滤。

### 5.9 日志分析支持

#### 5.9.1 日志统计

系统提供日志统计功能，帮助了解运行状态：

- 每小时/每天日志量统计
- 各级别日志数量分布
- 错误日志类型聚合
- 工具调用频率排名
- 平均响应时间统计

#### 5.9.2 问题定位

日志设计支持快速问题定位：

- 通过 `session_id` 过滤追踪完整会话
- 通过时间范围定位问题发生时段
- 通过级别过滤快速定位错误
- 通过模块名定位问题来源

#### 5.9.3 告警集成（预留）

未来可集成告警系统：

- ERROR 级别日志超过阈值时触发告警
- 容器连续崩溃触发告警
- 关键操作失败触发告警

## 6. 接口规范

### 6.1 接口设计原则

SmartClaw 的接口设计遵循以下原则：

1. **模块化边界**：每个模块通过明确的接口暴露功能，内部实现细节对外不可见
2. **依赖注入**：模块间通过构造函数注入依赖，便于测试和替换实现
3. **异步优先**：I/O 密集型操作采用异步接口，提高并发性能
4. **错误透明**：接口返回明确的错误类型和描述，便于调用方处理异常
5. **版本兼容**：接口变更遵循语义化版本规范，保持向后兼容

### 6.2 Agent 模块接口

#### 6.2.1 AgentManager 接口

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

#### 6.2.2 Session 接口

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

#### 6.2.3 SystemPromptBuilder 接口

SystemPromptBuilder 负责 System Prompt 的拼接和管理。

**职责范围**：
- 按顺序加载核心记忆文件
- 加载近端记忆内容
- 加载 Skills Snapshot
- 处理 token 限制和截断

**加载顺序**（严格遵循）：
1. AGENTS.md — Agent 基础定义
2. SKILLS_SNAPSHOT.md — 可用技能列表
3. SOUL.md — 人格与边界
4. IDENTITY.md — 名称与风格
5. USER.md — 用户画像
6. MEMORY.md — 用户偏好与重要决策
7. 近端记忆 — 最近 N 天的对话摘要

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `build(session_id: str) -> str` | 构建完整的 System Prompt |
| `load_core_memory() -> str` | 加载核心记忆内容 |
| `load_near_memory(days: int) -> str` | 加载近端记忆内容 |
| `estimate_tokens(content: str) -> int` | 估算内容的 token 数 |
| `truncate_to_limit(content: str, max_tokens: int) -> str` | 截断内容到指定 token 限制 |

### 6.3 Memory 模块接口

#### 6.3.1 MemoryManager 接口

MemoryManager 是 Memory 模块的统一入口，协调三种记忆类型的管理。

**职责范围**：
- 管理近端记忆、核心记忆、长期记忆的读写
- 提供记忆加载接口供 SystemPromptBuilder 使用
- 处理会话归档流程
- 提供 Agent 工具的工厂方法

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `load_core_memory() -> Dict[str, str]` | 加载所有核心记忆文件 |
| `load_near_memory(days: int) -> List[str]` | 加载近端记忆内容 |
| `write_near_memory(content: str, category: str, date: str) -> bool` | 写入近端记忆 |
| `write_core_memory(file_key: str, content: str, mode: str) -> bool` | 写入核心记忆 |
| `archive_session(session_id: str) -> str` | 归档会话，返回归档路径 |
| `get_write_near_memory_tool() -> Tool` | 获取近端记忆写入工具 |
| `get_write_core_memory_tool() -> Tool` | 获取核心记忆写入工具 |

#### 6.3.2 NearMemoryManager 接口

NearMemoryManager 管理近端记忆的读写操作。

**职责范围**：
- 按日期管理近端记忆文件
- 实现仅追加写入策略
- 清理过期的近端记忆

**文件路径**：`{base_path}/memory/{YYYY-MM-DD}.md`

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `load(days: int) -> List[NearMemoryEntry]` | 加载最近 N 天的记忆 |
| `append(content: str, category: str, date: str) -> bool` | 追加内容到指定日期 |
| `cleanup(keep_days: int) -> int` | 清理超过保留天数的文件 |

**文件格式**：每个近端记忆文件采用统一的 Markdown 格式，包含日期标题和分类区块（对话摘要、重要事实、决策记录）。

#### 6.3.3 CoreMemoryManager 接口

CoreMemoryManager 管理核心记忆文件的读写。

**职责范围**：
- 管理四个核心记忆文件（soul/identity/user/memory）
- 支持 append 和 replace 两种写入模式
- 禁止修改 AGENTS.md 和 SKILLS_SNAPSHOT.md

**文件映射**：

| file_key | 文件名 | 用途 |
|----------|--------|------|
| `soul` | SOUL.md | 人格、语气、边界 |
| `identity` | IDENTITY.md | 名称、风格、表情 |
| `user` | USER.md | 用户画像、称呼方式 |
| `memory` | MEMORY.md | 用户偏好、重要决策 |

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `load(file_key: str) -> str` | 加载指定核心记忆文件 |
| `load_all() -> Dict[str, str]` | 加载所有核心记忆文件 |
| `write(file_key: str, content: str, mode: str) -> bool` | 写入核心记忆 |
| `validate_file_key(file_key: str) -> bool` | 验证 file_key 是否合法 |

**安全限制**：
- 禁止修改 `agents` 和 `skills_snapshot` 文件
- 尝试修改时抛出 `SecurityError`

### 6.4 RAG 模块接口

#### 6.4.1 RAGManager 接口

RAGManager 是 RAG 模块的统一入口，协调索引管理和检索服务。

**职责范围**：
- 管理索引的构建、更新和删除
- 提供混合检索接口
- 管理文件监听服务
- 提供 Agent 检索工具的工厂方法

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `search(query: str, top_k: int, date_range: tuple) -> List[Segment]` | 执行混合检索 |
| `update_index(file_path: str) -> bool` | 更新单个文件的索引 |
| `rebuild_index() -> bool` | 全量重建索引 |
| `start_watcher() -> None` | 启动文件监听服务 |
| `stop_watcher() -> None` | 停止文件监听服务 |
| `get_search_tool() -> Tool` | 获取检索工具 |

#### 6.4.2 IndexManager 抽象基类

IndexManager 是索引管理器的抽象基类，定义所有索引管理器必须实现的接口。

**设计意图**：
- 为未来扩展外部知识库索引预留接口
- 确保不同索引实现具有一致的行为
- 支持多种索引类型的统一调用

**抽象方法**：

| 方法签名 | 说明 |
|---------|------|
| `search(query: str, top_k: int) -> List[Segment]` | 执行检索 |
| `update_document(doc_id: str, content: str, metadata: dict) -> bool` | 添加或更新文档 |
| `delete_document(doc_id: str) -> bool` | 删除文档 |
| `build_index(force: bool) -> bool` | 全量重建索引 |
| `check_consistency() -> Dict[str, List[str]]` | 检查索引一致性 |
| `repair_consistency() -> Dict[str, int]` | 修复一致性问题 |

#### 6.4.3 MemoryIndexManager 接口

MemoryIndexManager 继承 IndexManager，实现长期记忆的索引管理。

**职责范围**：
- 管理 Chroma 向量存储和 BM25 索引
- 实现 RRF 融合检索算法
- 支持日期范围过滤
- 处理增量索引更新

**扩展方法**（超出基类）：

| 方法签名 | 说明 |
|---------|------|
| `_search_with_filters(query: str, top_k: int, date_range: tuple) -> List[Segment]` | 带过滤条件的检索 |
| `_extract_date_from_path(path: str) -> Optional[str]` | 从文件路径提取日期 |
| `_vector_search(query: str, top_k: int) -> List[Segment]` | 执行向量检索 |
| `_bm25_search(query: str, top_k: int) -> List[Segment]` | 执行 BM25 检索 |
| `_rrf_fusion(vector_results: List, bm25_results: List, k: int) -> List[Segment]` | RRF 结果融合 |

#### 6.4.4 FileWatcher 接口

FileWatcher 负责监听文件系统变更，触发索引更新。

**职责范围**：
- 监听 sessions/archive/ 目录的文件变更
- 实现防抖机制避免频繁触发
- 事件去重避免重复处理

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `start() -> None` | 启动监听服务 |
| `stop() -> None` | 停止监听服务 |
| `on_file_created(path: str) -> None` | 文件创建事件处理 |
| `on_file_modified(path: str) -> None` | 文件修改事件处理 |
| `on_file_deleted(path: str) -> None` | 文件删除事件处理 |

**配置参数**：
- `watch.dir`：监听目录，默认 `sessions/archive/`
- `watch.debounce_seconds`：防抖时间，默认 2 秒

### 6.5 内置工具模块接口

#### 6.5.1 ToolRegistry 接口

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

#### 6.5.2 ContainerManager 接口

ContainerManager 管理 Docker 容器的生命周期。

**职责范围**：
- 创建和管理会话级容器
- 实现容器自动重启机制
- 清理会话结束后的容器
- 监控容器资源使用

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `get_container(tool_type: str, session_id: str) -> Container` | 获取或创建容器 |
| `cleanup_session_containers(session_id: str) -> None` | 清理会话的所有容器 |
| `restart_container(container: Container, attempt: int) -> bool` | 重启容器 |
| `get_container_stats(container_id: str) -> Dict` | 获取容器资源使用统计 |

**容器生命周期**：
- 创建时机：首次调用需要容器的工具时
- 复用策略：同一会话内复用同一容器
- 销毁时机：会话结束时（关闭、切换、删除）

**重启机制**：
- 最大重试次数：3 次
- 退避策略：指数退避（1s, 2s, 4s）
- 失败处理：记录日志并返回错误信息

#### 6.5.3 SecurityChecker 接口

SecurityChecker 负责工具调用的安全检查。

**职责范围**：
- 检查文件路径安全性
- 检查命令安全性
- 检查代码安全性
- 检查网络请求安全性

**主要方法**：

| 方法签名 | 说明 |
|---------|------|
| `check_file_path(path: str, operation: str) -> Tuple[bool, str]` | 检查文件路径 |
| `check_terminal_command(command: str) -> Tuple[bool, str]` | 检查终端命令 |
| `check_python_code(code: str) -> Tuple[bool, str]` | 检查 Python 代码 |
| `check_url(url: str) -> Tuple[bool, str]` | 检查 URL 合法性 |

**命令分类处理**：

| 类型 | 处理方式 | 示例 |
|-----|---------|------|
| 直接禁止 | 返回拒绝提示 | dd, mkfs, sudo, ssh |
| 每次确认 | 弹窗请求用户确认 | rm, git push, pip install |
| 正常执行 | 直接执行 | ls, cat, python, git status |
| 网络请求 | 检测数据上传时确认 | curl, wget, git push |

### 6.6 Agent 工具接口规范

所有供 Agent 调用的工具必须遵循 LangChain 的 `@tool` 装饰器规范。

#### 6.6.1 工具定义规范

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

#### 6.6.2 工具列表

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

### 6.7 数据模型接口

#### 6.7.1 Message 数据模型

Message 表示对话中的单条消息。

**字段**：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `role` | str | 角色（user/assistant/system/tool） |
| `content` | str | 消息内容 |
| `timestamp` | datetime | 消息时间戳 |
| `token_count` | int | 消息的 token 数量 |
| `tool_calls` | Optional[List] | 工具调用记录（如有） |
| `tool_results` | Optional[List] | 工具返回结果（如有） |

#### 6.7.2 Segment 数据模型

Segment 是 RAG 检索结果的数据载体。

**字段**：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `content` | str | 节点文本内容 |
| `source` | str | 来源文件路径 |
| `file_type` | str | 记忆类型（near/long_term/core） |
| `timestamp` | Optional[str] | 时间戳（ISO 格式） |
| `score` | float | 相关性得分 |

#### 6.7.3 NearMemoryEntry 数据模型

NearMemoryEntry 表示近端记忆的单条记录。

**字段**：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `date` | str | 日期（YYYY-MM-DD） |
| `category` | str | 类别（对话摘要/重要事实/决策记录） |
| `content` | str | 记忆内容 |
| `timestamp` | datetime | 写入时间戳 |

### 6.8 错误类型定义

#### 6.8.1 基础错误类型

所有 SmartClaw 错误继承自 `SmartClawError` 基类：

| 错误类型 | 说明 | 典型场景 |
|---------|------|---------|
| `ConfigError` | 配置相关错误 | 配置文件缺失、格式错误、验证失败 |
| `SessionError` | 会话相关错误 | 会话不存在、会话已关闭 |
| `MemoryError` | 记忆相关错误 | 记忆文件读写失败、文件格式错误 |
| `RAGError` | RAG 相关错误 | 索引构建失败、检索失败 |
| `ToolError` | 工具相关错误 | 工具不存在、工具调用失败 |
| `ContainerError` | 容器相关错误 | 容器创建失败、容器崩溃 |
| `SecurityError` | 安全相关错误 | 路径遍历攻击、危险命令检测 |

#### 6.8.2 错误信息规范

所有错误应包含以下信息：

- **错误代码**：唯一标识错误类型（如 `MEM_001`）
- **错误消息**：人类可读的错误描述
- **错误详情**：导致错误的具体原因
- **修复建议**：用户可采取的解决措施

**错误响应格式示例**：
```
Error Code: MEM_001
Message: Failed to write near memory
Details: Permission denied: /root/.smartclaw/memory/2026-03-18.md
Suggestion: Check file permissions or run with appropriate user privileges
```

## 7. 错误处理与监控

### 7.1 错误处理设计原则

SmartClaw 的错误处理遵循以下原则：

1. **快速失败与优雅降级**：启动阶段的关键错误应快速失败，运行时错误应尽可能优雅降级
2. **错误隔离**：单个组件的错误不应影响其他组件的正常运行
3. **信息透明**：错误信息应包含足够的上下文，便于问题定位和用户理解
4. **自动恢复**：对于可恢复的错误，系统应自动尝试恢复，减少人工干预
5. **错误追踪**：所有错误都应有唯一的追踪标识，便于日志关联

### 7.2 错误分类与处理策略

#### 7.2.1 按严重程度分类

**致命错误（Fatal）**：
- 导致系统无法启动或无法继续运行
- 需要人工干预才能恢复
- 示例：配置文件损坏、核心模块初始化失败、Docker 服务不可用
- 处理：记录详细日志，显示用户友好提示，终止程序

**严重错误（Critical）**：
- 核心功能不可用，但系统可继续运行
- 可能影响部分或全部用户体验
- 示例：LLM API 密钥无效、数据库连接失败、索引完全损坏
- 处理：记录错误，通知用户，尝试自动恢复或进入降级模式

**一般错误（Error）**：
- 单个操作失败，不影响系统整体运行
- 用户可以重试或选择其他操作
- 示例：工具调用超时、文件读取失败、单个检索失败
- 处理：返回错误信息给用户，记录日志，提供重试选项

**警告（Warning）**：
- 非预期情况，但不影响当前操作
- 可能需要关注或后续处理
- 示例：配置使用默认值、容器需要重启、索引轻微不一致
- 处理：记录日志，不中断用户操作

#### 7.2.2 按错误来源分类

| 来源 | 典型错误 | 恢复策略 |
|-----|---------|---------|
| 配置系统 | 配置缺失、格式错误、验证失败 | 使用默认值或终止启动 |
| LLM 调用 | 超时、API 错误、配额耗尽 | 重试机制、降级模型 |
| 容器系统 | 创建失败、崩溃、资源超限 | 自动重启、指数退避 |
| 文件系统 | 权限不足、磁盘满、文件损坏 | 记录错误、提示用户 |
| 记忆系统 | 写入失败、读取失败、格式错误 | 重试机制、跳过损坏文件 |
| RAG 系统 | 索引损坏、检索失败、LLM 调用失败 | 重建索引、降级检索 |

### 7.3 核心模块错误处理

#### 7.3.1 Agent 模块错误处理

**会话创建失败**：
- 原因：Memory 模块初始化失败、RAG 模块初始化失败
- 处理：记录详细错误日志，返回用户友好提示，建议检查配置
- 恢复：用户可重试创建会话

**消息处理失败**：
- 原因：LLM 调用超时、工具调用异常、token 超限
- 处理：
  - LLM 超时：重试最多 3 次，间隔递增（1s, 2s, 4s）
  - 工具异常：返回工具错误信息，Agent 可选择重试或换方案
  - Token 超限：触发预压缩冲刷后重试
- 恢复：大多数情况可自动恢复

**预压缩冲刷失败**：
- 原因：LLM 调用失败、记忆写入失败
- 处理：记录警告日志，跳过冲刷继续处理消息
- 影响：可能导致上下文过长，但不影响功能

#### 7.3.2 Memory 模块错误处理

**记忆读取失败**：
- 原因：文件不存在、权限不足、文件格式损坏
- 处理：
  - 核心记忆文件缺失：使用空内容继续，记录警告
  - 近端记忆文件损坏：跳过该文件，记录警告
  - 权限问题：记录错误，提示用户检查权限
- 影响：部分记忆内容不可用，但不影响会话

**记忆写入失败**：
- 原因：磁盘空间不足、权限问题、文件锁定
- 处理策略：
  1. 首次失败：等待 100ms 后重试
  2. 第二次失败：等待 200ms 后重试
  3. 两次均失败：记录错误日志，返回错误信息给 Agent
- 影响：记忆未持久化，但会话可继续

**会话归档失败**：
- 原因：磁盘空间不足、权限问题、目标路径已存在
- 处理：记录错误日志，保留当前会话不归档，下次会话切换时再次尝试
- 影响：会话无法归档到长期记忆，RAG 索引不会更新

#### 7.3.3 RAG 模块错误处理

**索引构建失败**：
- 原因：LLM 调用超时、嵌入生成失败、文档解析错误
- 处理策略：
  - LLM 调用失败：降级为不生成问题，继续构建索引
  - 嵌入生成失败：跳过该节点，记录警告，继续处理其他节点
  - 文档解析失败：跳过该文档，记录错误，继续处理其他文档
- 降级模式：仅 BM25 检索（向量索引不可用时）

**检索失败**：
- 原因：索引未初始化、向量存储连接失败、BM25 索引损坏
- 处理：
  - 索引未初始化：触发紧急初始化，返回提示信息
  - 向量检索失败：降级为仅 BM25 检索
  - BM25 检索失败：降级为仅向量检索
  - 全部失败：返回空结果和提示信息
- 恢复：下次检索可能自动恢复

**文件监听异常**：
- 原因：目录不存在、权限问题、监听器崩溃
- 处理：
  - 目录不存在：自动创建目录
  - 权限问题：记录错误，禁用文件监听
  - 监听器崩溃：自动重启监听器，最多 3 次
- 影响：索引需要手动更新或下次启动时重建

### 7.4 容器错误处理

#### 7.4.1 容器创建失败

**失败原因**：
- Docker 服务未运行
- 镜像不存在或拉取失败
- 资源不足（内存、CPU）
- 端口冲突（网络模式需要时）

**处理流程**：
1. 记录详细错误日志，包括 Docker 返回的错误信息
2. 检查失败原因并分类
3. 对于可恢复错误（如镜像不存在），尝试自动拉取镜像
4. 对于不可恢复错误，返回用户友好提示

**用户提示示例**：
- Docker 未运行："Docker 服务未启动，请先启动 Docker 后重试"
- 镜像拉取失败："无法拉取容器镜像，请检查网络连接或手动执行 docker pull"
- 资源不足："系统资源不足，请关闭其他应用后重试"

#### 7.4.2 容器崩溃处理

**崩溃检测**：
- 通过 Docker 事件监听检测容器退出
- 监控容器退出码判断崩溃原因
- 常见退出码：
  - 137：OOM Killed（内存超限）
  - 139：Segmentation Fault
  - 1：应用错误
  - 0：正常退出（非崩溃）

**自动重启机制**：
- 最大重试次数：3 次
- 退避策略：指数退避（1秒、2秒、4秒）
- 重启条件：非正常退出且未超过最大重试次数
- 放弃条件：连续 3 次重启后仍崩溃

**重启流程**：
1. 检测到容器崩溃
2. 记录崩溃日志（时间、退出码、最后输出）
3. 等待退避时间
4. 创建新容器（使用相同配置）
5. 更新容器映射表
6. 记录重启结果

**崩溃记录**：
- 所有崩溃事件记录到专用日志文件 `container_crashes.log`
- 包含完整上下文：会话 ID、工具类型、容器 ID、崩溃时间、退出码、重启结果

#### 7.4.3 容器资源超限

**内存超限**：
- 检测：容器退出码为 137（OOM Killed）
- 处理：记录警告，建议用户简化操作
- 预防：设置合理的内存限制（terminal 256MB，python_repl 512MB）

**CPU 超限**：
- 检测：容器响应极慢或无响应
- 处理：设置执行超时（30秒），超时后强制终止
- 预防：CPU 限制为 25%，避免占用过多宿主机资源

**输出超限**：
- 检测：命令输出超过 1MB
- 处理：截断输出，添加 `[truncated]` 标识
- 原因：避免大量输出占用内存和网络带宽

### 7.5 重试机制设计

#### 7.5.1 重试策略分类

**指数退避重试**：
- 适用场景：网络请求、LLM 调用、外部服务
- 实现方式：重试间隔呈指数增长
- 典型间隔：1秒、2秒、4秒
- 最大次数：3 次

**固定间隔重试**：
- 适用场景：文件操作、内存操作
- 实现方式：每次重试间隔相同
- 典型间隔：100ms 或 200ms
- 最大次数：2 次

**立即重试**：
- 适用场景：瞬时错误、竞态条件
- 实现方式：不等待立即重试
- 最大次数：1 次

#### 7.5.2 各操作重试配置

| 操作类型 | 重试策略 | 间隔序列 | 最大次数 | 失败后处理 |
|---------|---------|---------|---------|-----------|
| LLM 调用 | 指数退避 | 1s, 2s, 4s | 3 | 返回错误，记录日志 |
| 嵌入生成 | 指数退避 | 1s, 2s, 4s | 3 | 跳过节点，降级处理 |
| 记忆写入 | 固定间隔 | 100ms, 200ms | 2 | 返回错误，记录日志 |
| 容器重启 | 指数退避 | 1s, 2s, 4s | 3 | 返回错误，提示用户 |
| 文件监听重启 | 指数退避 | 1s, 2s, 4s | 3 | 禁用监听，记录警告 |
| HTTP 请求 | 指数退避 | 1s, 2s, 4s | 3 | 返回错误信息 |

#### 7.5.3 不重试的场景

以下场景不进行重试，直接返回错误：

- **认证错误**：API 密钥无效、权限被拒绝
- **配置错误**：参数格式错误、必填项缺失
- **资源不存在**：文件不存在、会话不存在
- **用户取消**：用户主动取消操作
- **安全违规**：检测到危险操作、路径遍历攻击

### 7.6 监控指标设计

#### 7.6.1 系统健康指标

**服务可用性**：
- Agent 服务状态（运行/停止）
- Docker 服务状态（可用/不可用）
- 文件监听状态（运行/停止）

**资源使用**：
- 内存使用量（MB）
- CPU 使用率（%）
- 磁盘使用量（GB）
- 活跃容器数量

**启动检查**：
- 配置加载成功/失败
- 核心目录创建成功/失败
- Docker 连接成功/失败
- 索引初始化成功/失败

#### 7.6.2 性能指标

**响应时间**：
- 消息处理时间（P50/P95/P99）
- 工具调用时间（按工具类型分类）
- LLM 响应时间
- 检索响应时间

**吞吐量**：
- 每分钟处理的消息数
- 每分钟工具调用次数
- 每分钟检索次数

**队列积压**：
- 待处理消息数
- 待更新索引数
- 待归档会话数

#### 7.6.3 错误指标

**错误率**：
- 错误消息占比（错误消息数/总消息数）
- 工具调用失败率（失败次数/总调用次数）
- LLM 调用失败率
- 检索失败率

**错误分布**：
- 按错误类型分布（ConfigError, ToolError 等）
- 按模块分布（Agent, Memory, RAG, Tools）
- 按时间分布（每小时的错误数量）

**重试统计**：
- 重试触发次数
- 重试成功次数
- 重试后仍失败的次数

#### 7.6.4 容器指标

**容器状态**：
- 活跃容器数（按工具类型分类）
- 容器总运行时间
- 平均容器生命周期

**崩溃统计**：
- 容器崩溃次数（按类型分类）
- 崩溃原因分布（OOM/错误/未知）
- 自动重启成功次数
- 重启失败次数

**资源消耗**：
- 容器平均内存使用
- 容器峰值内存使用
- 容器 CPU 使用率

### 7.7 告警机制（预留）

#### 7.7.1 告警规则

以下情况应触发告警（未来实现）：

**严重告警**：
- Agent 服务停止响应超过 1 分钟
- Docker 服务不可用
- 连续 5 次 LLM 调用失败
- 容器连续崩溃 3 次且无法恢复

**警告告警**：
- 错误率超过 10%
- 内存使用超过 80%
- 磁盘使用超过 85%
- 索引更新队列积压超过 10 个

**提示告警**：
- 配置使用默认值
- 单个工具调用失败（可恢复）
- 容器触发自动重启

#### 7.7.2 告警通知渠道

- 控制台输出：所有告警级别
- 日志文件：所有告警级别
- 邮件通知：严重告警（可配置）
- Webhook：严重告警（可配置）

### 7.8 故障恢复指南

#### 7.8.1 常见问题与解决方案

**问题：Docker 容器无法创建**
- 检查 Docker 服务是否运行
- 检查镜像是否存在（`docker images`）
- 手动拉取镜像（`docker pull alpine:3.19`）
- 检查磁盘空间是否充足

**问题：LLM 调用持续失败**
- 检查 API 密钥是否有效
- 检查网络连接是否正常
- 检查 API 配额是否耗尽
- 尝试切换到备用模型

**问题：记忆写入失败**
- 检查目录权限（`ls -la ~/.smartclaw/`）
- 检查磁盘空间
- 检查文件是否被锁定

**问题：检索结果为空或异常**
- 检查索引是否存在
- 尝试手动重建索引
- 检查归档会话文件是否存在
- 查看 RAG 模块日志

#### 7.8.2 紧急恢复操作

**重置会话状态**：
- 删除当前会话数据（`rm -rf ~/.smartclaw/sessions/current/*`）
- 重新创建会话

**重建索引**：
- 删除现有索引（`rm -rf ~/.smartclaw/store/chroma`）
- 删除 BM25 索引（`rm -rf ~/.smartclaw/store/bm25`）
- 重启服务触发索引重建

**清理容器**：
- 停止所有容器（`docker stop $(docker ps -q)`）
- 清理悬空容器（`docker container prune`）
- 重启服务

## 8. 性能优化（可选）

> **注意**：本章内容为可选优化项，第一版实现中可暂不考虑。系统基本功能已能正常运行，以下优化可在后续版本中根据实际使用情况逐步实施。

### 8.1 性能优化目标

SmartClaw 的性能优化旨在提供流畅的用户体验，同时保持系统的稳定性和资源效率。优化目标分为三个层次：

**基础目标（第一版必须达成）**：
- 消息响应无明显延迟感
- 系统在正常负载下稳定运行
- 资源使用在合理范围内

**进阶目标（后续优化）**：
- 首次响应时间 < 2 秒
- 完整响应时间 < 5 秒（简单查询）
- 内存占用 < 1GB（空闲状态）
- 检索响应时间 < 200ms

**理想目标（长期优化）**：
- 支持多用户并发
- 支持长时间运行无性能衰减
- 支持大规模知识库（10万+文档）

### 8.2 响应时间优化（后续优化）

#### 8.2.1 LLM 调用优化

**当前方案**：
- 直接调用 LLM API，无额外优化
- 同步等待响应完成

**后续可优化方向**：

1. **流式输出**：采用 Server-Sent Events 或 WebSocket 实现流式返回，用户可提前看到部分响应，提升感知速度

2. **并行工具调用**：当 Agent 需要调用多个独立工具时，可并行执行，减少总等待时间

3. **请求合并**：对于多个小请求，可考虑合并为一个批量请求，减少网络往返

4. **模型选择策略**：
   - 简单查询使用轻量模型（如 gpt-4o-mini）
   - 复杂推理使用高级模型（如 claude-sonnet-4）
   - 根据查询复杂度自动选择

5. **预热机制**：首次请求前预先建立连接，减少冷启动延迟

#### 8.2.2 检索优化

**当前方案**：
- 混合检索（向量 + BM25）+ RRF 融合
- 每次检索实时计算

**后续可优化方向**：

1. **检索结果缓存**：对相同或相似查询的检索结果进行缓存，减少重复计算

2. **向量预计算**：对于常见查询，预先计算并存储向量表示

3. **索引分片**：当文档数量较大时，将索引分片存储，减少单次检索的扫描范围

4. **分层检索**：先使用 BM25 快速筛选候选集，再对候选集进行精确的向量检索

### 8.3 内存优化（后续优化）

#### 8.3.1 当前内存使用分析

**主要内存消耗点**：
- LLM 客户端连接池
- 向量索引（Chroma）
- BM25 索引（内存中）
- 会话消息历史
- Docker 容器

**预计内存占用**：
- 空闲状态：约 100-200MB
- 活跃会话：约 300-500MB
- 大规模索引：可能超过 1GB

#### 8.3.2 优化方向

1. **消息历史压缩**：
   - 当前：保留完整消息内容
   - 优化：定期压缩旧消息为摘要，释放内存
   - 实现：通过现有的预压缩冲刷机制实现

2. **索引懒加载**：
   - 当前：启动时加载全部索引
   - 优化：按需加载索引，不活跃的索引可卸载
   - 适用：大规模知识库场景

3. **向量索引量化**：
   - 当前：使用完整精度向量
   - 优化：采用产品量化或标量量化减少内存占用
   - 代价：轻微降低检索精度

4. **容器资源共享**：
   - 当前：每个会话独立容器
   - 优化：考虑容器池复用，减少容器数量
   - 风险：安全性权衡

### 8.4 并发处理（后续优化）

#### 8.4.1 当前并发模型

**现状**：
- 单用户设计，不强调并发
- 同步处理模型，逻辑简单
- 无并发控制机制

**适用场景**：个人使用、低频交互

#### 8.4.2 未来并发扩展方向

1. **异步 I/O 模型**：
   - 使用 async/await 改写 I/O 密集操作
   - 提高单进程并发处理能力
   - 适用于多用户场景

2. **会话级隔离**：
   - 每个会话独立的内存空间
   - 避免会话间资源竞争
   - 单个会话异常不影响其他会话

3. **连接池管理**：
   - LLM API 连接池
   - 数据库连接池（如需要）
   - 复用连接减少开销

4. **请求队列**：
   - 请求优先级排序
   - 超时请求自动清理
   - 防止请求堆积

### 8.5 启动性能（后续优化）

#### 8.5.1 当前启动流程

**启动阶段**：
1. 加载配置文件
2. 初始化日志系统
3. 创建必要目录
4. 初始化 Memory 模块
5. 初始化 RAG 模块（包括索引加载）
6. 初始化 Docker 连接
7. 启动文件监听服务

**预计启动时间**：5-10 秒（取决于索引大小）

#### 8.5.2 优化方向

1. **延迟初始化**：
   - 非关键组件延迟到首次使用时初始化
   - 如 RAG 索引可在首次检索时加载
   - 减少启动等待时间

2. **并行初始化**：
   - 独立模块并行初始化
   - 如 Memory 和 RAG 模块可同时初始化
   - 需要处理初始化依赖关系

3. **索引增量加载**：
   - 大型索引分块加载
   - 优先加载热点数据
   - 后台完成完整加载

4. **状态持久化**：
   - 保存上次运行状态
   - 快速恢复工作状态
   - 避免重复初始化

### 8.6 资源限制与保护

#### 8.6.1 当前资源限制

| 资源类型 | 限制方式 | 限制值 |
|---------|---------|--------|
| 容器内存 | Docker 配置 | terminal: 256MB, python_repl: 512MB |
| 容器 CPU | Docker 配置 | 25% |
| 代码执行超时 | 超时机制 | 30 秒 |
| 命令输出 | 截断机制 | 1MB |
| 检索结果 | top_k 限制 | 默认 5 |

#### 8.6.2 资源保护机制

1. **内存保护**：
   - 容器内存限制防止无限增长
   - OOM 时自动重启容器
   - 监控宿主机内存使用

2. **CPU 保护**：
   - 容器 CPU 限制防止资源抢占
   - 执行超时防止死循环
   - 闲置容器自动清理

3. **存储保护**：
   - 定期清理过期日志
   - 限制索引最大大小
   - 监控磁盘使用率

4. **网络保护**：
   - HTTP 请求超时限制
   - 重试次数限制
   - 避免无限等待

### 8.7 性能监控（后续优化）

#### 8.7.1 关键性能指标

**响应时间指标**：
- 消息首字响应时间（TTFT）
- 消息完整响应时间
- 工具调用耗时
- 检索耗时

**资源使用指标**：
- 内存使用量（当前/峰值）
- CPU 使用率
- 磁盘 I/O
- 网络 I/O

**吞吐量指标**：
- 每分钟处理消息数
- 每分钟检索次数
- 每分钟工具调用次数

#### 8.7.2 性能分析工具

**内置监控**：
- 日志中的耗时记录
- 错误统计和分布

**外部工具**（可选集成）：
- Python profiler 分析热点代码
- 内存分析工具检测内存泄漏
- Docker stats 监控容器资源

### 8.8 性能优化实施建议

#### 8.8.1 优化优先级

**第一阶段（必要）**：
- 确保基本功能稳定
- 设置合理的资源限制
- 实现基本的错误处理

**第二阶段（推荐）**：
- 实现流式输出提升体验
- 优化检索性能
- 添加性能监控日志

**第三阶段（可选）**：
- 支持并发场景
- 实现高级缓存机制
- 大规模知识库优化

#### 8.8.2 性能测试建议

**基准测试**：
- 测量各操作的基线性能
- 建立性能回归检测
- 定期执行性能测试

**负载测试**：
- 模拟长时间运行场景
- 检测内存泄漏
- 验证资源限制有效性

**边界测试**：
- 大文件处理测试
- 长会话测试
- 高频操作测试

## 9. 安全设计

### 9.1 安全定位与威胁模型

SmartClaw 是部署在个人电脑上的单用户 AI Agent 系统，其安全设计与企业级多租户系统有本质区别。本章基于实际使用场景，识别真实威胁并提供可落地的防护措施。

#### 9.1.1 项目安全定位

**信任边界**：
- 用户信任自己的电脑环境
- 用户信任自己配置的 LLM 服务
- 用户信任自己提供的文件和代码

**不信任边界**：
- Agent 从网络获取的内容
- Agent 执行的代码和命令
- 第三方库和依赖

**安全目标**：
- 防止意外损坏：避免 Agent 无意中删除重要文件或执行危险命令
- 防止数据泄露：保护 API Key 等敏感配置
- 防止资源滥用：限制 Agent 对系统资源的占用
- 提供可控性：用户能够审核和干预 Agent 的操作

#### 9.1.2 威胁模型

| 威胁类型 | 可能性 | 影响程度 | 防护优先级 |
|---------|--------|---------|-----------|
| Agent 误删用户文件 | 中 | 高 | 高 |
| Agent 执行危险命令 | 低 | 高 | 高 |
| API Key 泄露到日志 | 中 | 中 | 高 |
| 恶意网页内容注入 | 低 | 中 | 中 |
| 容器逃逸 | 极低 | 高 | 低 |
| 依赖库供应链攻击 | 极低 | 高 | 低 |

**说明**：
- Agent 误操作是主要风险，需要重点防护
- 恶意攻击风险较低（个人电脑、单用户），但仍需基本防护
- 容器逃逸和供应链攻击属于极端情况，依赖基础安全措施即可

### 9.2 敏感信息保护

#### 9.2.1 API Key 管理

**存储方式**：
- API Key 存储在环境变量或 `.env` 文件中
- 配置文件中使用 `${ANTHROPIC_API_KEY}` 格式引用
- `.env` 文件添加到 `.gitignore`，避免提交到版本控制

**使用规范**：
- 代码中不硬编码 API Key
- 日志输出时自动脱敏（显示 `sk-a****1234` 格式）
- 错误消息中不暴露完整 Key

**用户操作建议**：
- 定期轮换 API Key
- 为不同环境使用不同的 Key
- 监控 API 使用量，发现异常及时处理

#### 9.2.2 日志脱敏

**脱敏规则**：

| 信息类型 | 脱敏方式 | 示例 |
|---------|---------|------|
| API Key | 保留前4位和后4位 | `sk-a****1234` |
| 密码 | 完全替换 | `[REDACTED]` |
| Token | 保留前8位 | `ghp_xxxxxxxx****` |
| 私钥内容 | 完全替换 | `[PRIVATE_KEY_REDACTED]` |

**脱敏时机**：
- 日志写入前统一处理
- 不依赖各模块单独脱敏
- 脱敏函数集中维护

#### 9.2.3 用户数据保护

**文件内容**：
- 日志中不记录完整文件内容
- 仅记录文件路径、大小、操作类型
- 必要时记录内容摘要（前 100 字符）

**对话内容**：
- 对话历史存储在本地，不上传到第三方
- 归档文件存储在用户目录下
- 用户可自行管理和删除

### 9.3 文件系统安全

#### 9.3.1 路径访问控制

**root_dir 限制**：
- 工具只能访问用户指定的 `root_dir` 目录
- 默认为 `./workspace`，用户可配置
- 记忆文件存储在独立的 `~/.smartclaw` 目录，不与工作目录共享

**路径安全检查**：

```
用户请求路径: /Users/zhy/workspace/../etc/passwd
规范化路径: /etc/passwd
检查结果: 拒绝（超出 root_dir 范围）
```

**检查流程**：
1. 将请求路径规范化（解析 `..`、符号链接等）
2. 检查规范化后的路径是否在 `root_dir` 内
3. 检查路径是否指向敏感文件（如 `.env`、`.ssh`）
4. 通过检查则允许访问，否则拒绝并记录日志

#### 9.3.2 文件类型限制

**允许的文件类型**：
- 文本文件：`.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`, `.xml`
- 代码文件：`.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, `.c`, `.cpp`
- 配置文件：`.conf`, `.cfg`, `.ini`
- 其他：`.csv`, `.log`, `.sh`

**禁止的文件类型**：
- 可执行文件：`.exe`, `.bin`, `.dll`, `.so`
- 压缩文件：`.zip`, `.tar`, `.gz`（可读取但需确认）
- 加密文件：`.enc`, `.key`, `.pem`

**处理方式**：
- 禁止类型直接拒绝，返回错误信息
- 可疑类型提示用户确认
- 大文件（>10MB）提示用户确认

#### 9.3.3 写入保护

**写入前检查**：
- 目标文件是否存在（覆盖需要确认）
- 目标路径是否在允许范围内
- 写入内容大小是否合理（<10MB）

**敏感文件保护**：
- 禁止写入 `.env` 文件
- 禁止写入 `.git` 目录
- 禁止写入系统目录

**用户确认机制**：
- 覆盖现有文件时弹窗确认
- 删除文件时弹窗确认
- 批量操作时汇总确认

### 9.4 命令执行安全

#### 9.4.1 命令分类与处理

**直接禁止的命令**：

| 命令/模式 | 风险说明 |
|----------|---------|
| `dd` | 磁盘直接写入，可能损坏数据 |
| `mkfs` | 格式化磁盘 |
| `sudo`, `su` | 提权操作 |
| `reboot`, `shutdown`, `poweroff` | 系统关机/重启 |
| `ssh`, `scp`, `sftp`, `rsync` | 远程访问 |
| `\| sh`, `\| bash`, `\| python` | 管道执行脚本 |
| `:(){ :\|:& };:` | Fork 炸弹 |
| `insmod`, `rmmod`, `modprobe` | 内核模块操作 |
| `chroot`, `mount`, `umount` | 系统级操作 |

**需要确认的命令**：

| 命令/模式 | 确认原因 |
|----------|---------|
| `rm -rf` | 批量删除 |
| `mv` (覆盖) | 可能覆盖重要文件 |
| `cp` (覆盖) | 可能覆盖重要文件 |
| `chmod`, `chown` | 权限修改 |
| `git push`, `git reset --hard` | Git 危险操作 |
| `pip install`, `npm install` | 安装第三方包 |
| `curl`, `wget` (带上传) | 数据外传 |
| `docker run`, `docker exec` | Docker 操作 |
| `crontab` | 定时任务 |
| `ln -s` | 符号链接 |

**正常执行的命令**：
- 文件查看：`ls`, `cat`, `head`, `tail`, `wc`, `find`
- 文本处理：`grep`, `sed`, `awk`, `sort`, `uniq`
- 开发相关：`python`, `node`, `git status`, `git diff`, `git log`
- 目录操作：`mkdir`, `cd`, `pwd`

#### 9.4.2 容器隔离

**隔离机制**：
- 所有命令在 Docker 容器内执行
- 容器与宿主机文件系统隔离
- 仅挂载用户指定的 `root_dir`

**容器安全配置**：
- 使用非 root 用户运行（UID 1000）
- 禁止特权模式
- 禁止访问宿主机 Docker socket
- 限制网络出站（允许但不推荐敏感操作）

**容器资源限制**：
- 内存限制：256MB（terminal），512MB（python_repl）
- CPU 限制：25%
- 无磁盘限制（容器内临时文件）

#### 9.4.3 用户确认机制

**确认流程**：
1. 检测到需要确认的命令
2. 暂停执行，向用户展示命令详情
3. 用户选择：允许/拒绝/修改
4. 根据用户选择继续或终止

**确认界面示例**：
```
⚠️  需要确认的操作

命令: rm -rf ./build
风险: 将删除 build 目录及其所有内容
建议: 请确认 build 目录可以安全删除

[允许执行] [拒绝] [修改命令]
```

**记住选择**：
- 用户可选择"本次会话不再询问"
- 同类命令自动通过
- 会话结束后重置

### 9.5 代码执行安全

#### 9.5.1 Python 代码安全

**禁止的操作**：
- `subprocess` 模块（执行外部命令）
- `os.system()`, `os.popen()`（执行 Shell 命令）
- `eval()`, `exec()`（动态执行代码）
- `__import__()`（动态导入）

**实现方式**：
- 在代码执行前扫描禁止的模式
- 检测到禁止操作时抛出 `SecurityError`
- 提示用户使用 `terminal` 工具替代

**示例错误**：
```
SecurityError: 代码中包含禁止的操作 'subprocess.run'
建议：如需执行命令，请使用 terminal 工具
```

#### 9.5.2 执行超时与资源限制

**超时机制**：
- 代码执行超时：30 秒
- 超时后强制终止
- 返回超时错误和已执行部分输出

**资源限制**：
- 容器内存限制防止内存炸弹
- CPU 限制防止死循环占用
- 输出截断防止大量输出（1MB）

### 9.6 网络安全

#### 9.6.1 URL 访问控制

**允许的协议**：
- `http://`, `https://`（需确认）
- `file://`（仅限 root_dir 内）

**禁止的协议**：
- `ftp://`, `sftp://`
- `ssh://`
- `data:`, `javascript:`

**域名过滤（可选）**：
- 支持配置域名白名单
- 支持配置域名黑名单
- 默认不限制

#### 9.6.2 网络请求安全

**请求限制**：
- 超时时间：30 秒
- 响应大小限制：10MB
- 仅获取静态内容，不执行 JavaScript

**内容检查**：
- 检测响应内容类型
- 拒绝下载二进制文件（视频、图片等）
- 清洗 HTML 内容，移除脚本

**用户确认**：
- 首次访问新域名时提示用户
- 检测到可能的敏感数据上传时确认

### 9.7 Skills 安全

#### 9.7.1 Skills 来源

**可信来源**：
- 用户自己创建的 Skills
- 官方提供的 Skills 模板

**不可信来源**：
- 从网络下载的 Skills
- 他人分享的 Skills

**安全建议**：
- 使用前检查 Skills 内容
- 了解 Skills 会调用的工具
- 不使用来源不明的 Skills

#### 9.7.2 Skills 执行

**Skills 本身不执行代码**：
- Skills 只是说明文档
- Agent 通过内置工具执行操作
- Skills 无法绕过安全限制

**Skills 调用受限**：
- 必须先读取 SKILL.md 了解内容
- 所有操作仍需通过安全检查
- 用户可随时终止执行

### 9.8 安全审计与日志

#### 9.8.1 安全相关日志

**记录内容**：
- 所有被拒绝的操作及原因
- 所有需要用户确认的操作及用户决策
- 所有容器创建、崩溃、重启事件
- 所有文件写入操作

**日志格式示例**：
```
[SECURITY] Command rejected: rm -rf / (path traversal attempt)
[SECURITY] User confirmed: git push origin main
[SECURITY] Container crashed: terminal, exit_code=137 (OOM)
```

#### 9.8.2 用户可审计性

**审计能力**：
- 用户可查看完整日志
- 可追溯每个操作的来源
- 可了解 Agent 的完整行为

**隐私保护**：
- 日志存储在本地
- 用户完全控制日志数据
- 可随时删除日志

### 9.9 安全最佳实践建议

#### 9.9.1 用户安全建议

**配置安全**：
- 不要在配置文件中硬编码 API Key
- 使用 `.env` 文件管理敏感信息
- 定期检查和更新配置

**操作安全**：
- 审阅 Agent 的操作再确认
- 不要盲目允许所有操作
- 定期检查工作目录变化

**数据安全**：
- 重要文件定期备份
- 不要让 Agent 访问敏感目录
- 定期清理不需要的会话数据

#### 9.9.2 开发安全建议

**代码安全**：
- 不信任任何外部输入
- 验证所有路径和命令
- 使用参数化方式执行操作

**依赖安全**：
- 定期更新依赖库
- 关注安全公告
- 使用可信的依赖源

### 9.10 安全配置清单

| 配置项 | 建议值 | 说明 |
|-------|--------|------|
| `tools.root_dir` | `./workspace` | 限制文件访问范围 |
| `tools.terminal.memory_limit` | `256m` | 容器内存限制 |
| `tools.terminal.cpu_limit` | `25%` | 容器 CPU 限制 |
| `tools.python_repl.execution_timeout` | `30` | 代码执行超时 |
| `logging.level` | `INFO` | 记录关键操作 |
| 环境变量存储 API Key | 必需 | 避免硬编码 |

---

## 10. 开发指南

本章面向参与 SmartClaw 项目开发的贡献者，提供项目结构、开发环境搭建、编码规范和提交规范等指导。

### 10.1 项目结构

#### 10.1.1 目录组织

SmartClaw 项目采用清晰的模块化目录结构，遵循 TDD（测试驱动开发）原则：

```
smartclaw/                      # 项目根目录（源代码）
├── backend/                    # 后端核心代码
│   ├── __init__.py
│   ├── agent/                  # Agent 核心模块
│   │   ├── __init__.py
│   │   ├── agent.py                 # SmartClawAgent 主类
│   │   ├── graph.py                 # AgentGraph 状态图
│   │   └── prompt_builder.py        # SystemPromptBuilder
│   ├── memory/                 # Memory 模块
│   │   ├── __init__.py
│   │   ├── base.py                  # MemoryManager 抽象基类
│   │   ├── near_memory.py           # NearMemoryManager
│   │   ├── core_memory.py           # CoreMemoryManager
│   │   └── session.py               # SessionManager
│   ├── rag/                    # RAG 模块
│   │   ├── __init__.py
│   │   ├── models.py                # Document, Node, Segment 数据模型
│   │   ├── index_manager.py         # IndexManager 抽象基类
│   │   ├── memory_index.py          # MemoryIndexManager
│   │   ├── cache.py                 # SQLiteCache
│   │   └── file_watcher.py          # FileWatcher
│   ├── tools/                  # 内置工具模块
│   │   ├── __init__.py
│   │   ├── registry.py              # ToolRegistry
│   │   ├── security.py              # SecurityChecker
│   │   ├── container.py             # ContainerManager
│   │   ├── terminal.py              # terminal 工具
│   │   ├── python_repl.py           # python_repl 工具
│   │   ├── fetch_url.py             # fetch_url 工具
│   │   └── file_ops.py              # read_file/write_file 工具
│   ├── config/                 # 配置模块
│   │   ├── __init__.py
│   │   ├── models.py                # LLMConfig, Settings 等 Pydantic 模型
│   │   └── manager.py               # ConfigManager
│   ├── api/                    # FastAPI 接口模块
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI 应用入口
│   │   ├── routes/                  # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py          # 会话 API
│   │   │   ├── messages.py          # 消息 API
│   │   │   ├── memory.py            # 记忆 API
│   │   │   ├── search.py            # 搜索 API
│   │   │   └── health.py            # 健康检查 API
│   │   └── models/                  # 请求/响应模型
│   │       ├── __init__.py
│   │       ├── requests.py          # 请求模型
│   │       └── responses.py         # 响应模型
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py                # 日志配置
│   │   └── errors.py                # 错误类型定义
│   ├── init.py                 # 初始化脚本
│   └── main.py                 # 服务启动入口
│
├── tests/                       # 测试目录（TDD 分层结构）
│   ├── __init__.py
│   ├── conftest.py              # pytest 共享 fixtures
│   │
│   ├── unit/                    # 单元测试（与源码镜像对应）
│   │   ├── __init__.py
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── test_agent.py         # SmartClawAgent 测试
│   │   │   ├── test_graph.py         # AgentGraph 测试
│   │   │   └── test_prompt_builder.py # SystemPromptBuilder 测试
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── test_base.py          # MemoryManager 基类测试
│   │   │   ├── test_near_memory.py   # NearMemoryManager 测试
│   │   │   ├── test_core_memory.py   # CoreMemoryManager 测试
│   │   │   └── test_session.py       # SessionManager 测试
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py        # 数据模型测试
│   │   │   ├── test_index_manager.py # IndexManager 基类测试
│   │   │   ├── test_cache.py         # SQLiteCache 测试
│   │   │   └── test_file_watcher.py  # FileWatcher 测试
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── test_registry.py      # ToolRegistry 测试
│   │   │   ├── test_security.py      # SecurityChecker 测试
│   │   │   └── test_container.py     # ContainerManager 测试
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py        # 配置模型测试
│   │   │   └── test_manager.py       # ConfigManager 测试
│   │   └── api/
│   │       ├── __init__.py
│   │       └── test_models.py        # API 数据模型测试
│   │
│   ├── api/                     # API 端点测试（使用 TestClient）
│   │   ├── __init__.py
│   │   ├── conftest.py              # API 测试 fixtures
│   │   ├── test_sessions.py         # 会话 API 测试
│   │   ├── test_messages.py         # 消息 API 测试
│   │   ├── test_memory.py           # 记忆 API 测试
│   │   ├── test_search.py           # 搜索 API 测试
│   │   └── test_health.py           # 健康检查 API 测试
│   │
│   ├── integration/             # 集成测试（模块间协作）
│   │   ├── __init__.py
│   │   ├── test_memory_integration.py  # Memory 模块集成
│   │   ├── test_rag_integration.py     # RAG 模块集成
│   │   ├── test_tools_integration.py   # Tools 模块集成
│   │   └── test_agent_integration.py   # Agent 模块集成
│   │
│   ├── e2e/                     # 端到端测试（完整流程）
│   │   ├── __init__.py
│   │   ├── test_conversation_flow.py   # 完整对话流程
│   │   ├── test_memory_system.py       # 记忆系统 E2E
│   │   ├── test_tool_execution.py      # 工具执行 E2E
│   │   └── test_session_lifecycle.py   # 会话生命周期
│   │
│   └── boundary/                # 边界条件测试
│       ├── __init__.py
│       ├── test_config_boundary.py        # 配置边界
│       ├── test_near_memory_boundary.py   # 近端记忆边界
│       ├── test_core_memory_boundary.py   # 核心记忆边界
│       ├── test_session_boundary.py       # 会话边界
│       ├── test_cache_boundary.py         # 缓存边界
│       ├── test_index_manager_boundary.py # 索引管理边界
│       ├── test_file_watcher_boundary.py  # 文件监听边界
│       ├── test_security_boundary.py      # 安全检查边界
│       ├── test_container_boundary.py     # 容器边界
│       ├── test_registry_boundary.py      # 工具注册边界
│       ├── test_prompt_builder_boundary.py # Prompt 构建边界
│       ├── test_graph_boundary.py         # Agent 图边界
│       ├── test_agent_boundary.py         # Agent 边界
│       └── test_api_boundary.py           # API 边界
│
├── docs/                        # 文档目录
│   ├── Agent.md                 # 本开发规范文档
│   ├── Memory.md                # Memory 模块规范
│   ├── RAG.md                   # RAG 模块规范
│   └── 内置工具.md               # 内置工具规范
│
├── pytest.ini                   # pytest 配置
├── pyproject.toml               # 项目配置（含 pytest 插件）
├── config.example.yaml          # 配置文件模板
├── requirements.txt             # 依赖清单
├── requirements-dev.txt         # 开发依赖
├── .env.example                 # 环境变量模板
├── .gitignore                   # Git 忽略配置
├── README.md                    # 项目说明
└── LICENSE                      # 许可证
```

**测试目录分层说明**：

| 目录 | 用途 | 对应开发项 | 运行命令 |
|-----|------|----------|---------|
| `tests/unit/` | 单元测试，测试单个类/函数 | Ax-Hx 开发项 | `pytest tests/unit/` |
| `tests/api/` | API 端点测试 | F4-F19 API测试 | `pytest tests/api/` |
| `tests/integration/` | 模块集成测试 | I1-I4 集成验证项 | `pytest tests/integration/` |
| `tests/e2e/` | 端到端完整流程测试 | G1-G7 E2E测试 | `pytest tests/e2e/` |
| `tests/boundary/` | 边界条件和异常测试 | T1-T14 边界测试 | `pytest tests/boundary/` |

#### 10.1.2 用户数据目录

运行时产生的数据存储在用户目录，与源代码分离：

```
~/.smartclaw/                   # 用户数据目录（运行时）
├── logs/                       # 日志文件
│   ├── smartclaw.log           # 主日志
│   └── container_crashes.log   # 容器崩溃日志
├── store/                      # 数据存储
│   ├── core_memory/            # 核心记忆文件
│   │   ├── SOUL.md
│   │   ├── IDENTITY.md
│   │   ├── USER.md
│   │   ├── MEMORY.md
│   │   ├── AGENTS.md
│   │   └── SKILLS_SNAPSHOT.md
│   ├── memory/                 # 近端记忆（按日期）
│   │   └── YYYY-MM-DD.md
│   └── rag/                    # RAG 索引根目录
│       ├── memory/             # 记忆知识库（MemoryIndexManager）
│       │   ├── chroma/         # Chroma 向量索引
│       │   ├── bm25/           # BM25 索引
│       │   ├── docstore.json   # 文档存储
│       │   └── cache.db        # SQLite 缓存
│       └── knowledge/          # 外部知识库（KnowledgeIndexManager，预留）
│           ├── chroma/
│           ├── bm25/
│           ├── docstore.json
│           └── cache.db
├── sessions/                   # 会话数据
│   ├── sessions.json           # 会话映射表（session_key → session_id）
│   ├── current/                # 当前会话
│   │   └── {YYYY-MM-DD}-{random}.md
│   └── archive/                # 归档会话
│       └── {YYYY-MM-DD}-{random}.md
├── skills/                     # 用户自定义技能
└── config.yaml                 # 用户配置
```

**设计理由**：

| 考量 | 说明 |
|-----|------|
| 代码与数据分离 | 升级代码不影响用户数据 |
| 多环境支持 | 同一份代码，不同用户独立数据 |
| 备份简单 | 只需备份 `~/.smartclaw/` |
| Git 整洁 | 运行时数据不会污染版本控制 |
| 知识库扩展 | `store/rag/` 下可添加多种知识库类型 |

**目录用途说明**：

| 目录 | 用途 | 管理器 |
|-----|------|--------|
| `store/core_memory/` | 核心记忆文件 | `CoreMemoryManager` |
| `store/memory/` | 近端记忆文件 | `NearMemoryManager` |
| `store/rag/memory/` | 记忆知识库索引 | `MemoryIndexManager` |
| `store/rag/knowledge/` | 外部知识库索引 | `KnowledgeIndexManager`（预留） |
| `sessions/sessions.json` | 会话映射表 | `SessionManager` |

#### 10.1.3 核心记忆文件默认模板

系统首次启动时，会自动创建以下核心记忆文件。用户可以直接编辑这些文件来自定义 Agent 行为。

**文件权限说明**：

| 文件名 | 说明 | 修改权限 |
|-------|------|---------|
| SOUL.md | Agent 人格、语气、边界 | ✅ 可修改 |
| IDENTITY.md | Agent 名称、风格、表情 | ✅ 可修改 |
| USER.md | 用户画像、称呼方式 | ✅ 可修改 |
| MEMORY.md | 用户偏好、决策、长期事项 | ✅ 可修改 |
| AGENTS.md | 操作指令、记忆使用规则、内置工具 | ❌ 禁止修改 |
| SKILLS_SNAPSHOT.md | 技能快照（XML 格式） | ❌ 禁止修改 |

**SKILLS_SNAPSHOT.md 格式示例**：

```xml
<available_skills>
    <skill>
        <name>weather</name>
        <description>Get weather information</description>
        <location>/users/user/.smartclaw/skills/weather/SKILL.md</location>
    </skill>
    <skill>
        <name>gemini</name>
        <description>Use Gemini CLI for coding assistance and Google search lookups.</description>
        <location>/users/user/.smartclaw/skills/gemini/SKILL.md</location>
    </skill>
</available_skills>
```

**SOUL.md 默认模板**：

```markdown
## 人格（Persona）
- **友好、专业、严谨**：SmartClaw 以一种既友好又专业的语气与用户进行交互，确保交流内容既具有人性化，又不失严谨性。它的目标是通过提供高质量的反馈和建议来协助用户解决问题，而非取代用户的决策过程。
- **适应性强**：根据用户的需求和情境，SmartClaw 能够调整其回应的语气和内容，既能轻松互动，也能严肃地处理复杂任务。它始终保持尊重、礼貌，并具备处理紧急、敏感情况的能力。

## 语气（Tone）
- **友好而专业**：SmartClaw 的语气始终保持温和、友好，但又不失专业性。在处理技术问题时，它会避免使用过于复杂的术语，确保用户能轻松理解。对于较为复杂的任务，它会逐步引导用户，以清晰、简洁的方式说明每个步骤。
- **正向鼓励**：在协助用户的过程中，SmartClaw 会积极鼓励用户的努力，提供建设性反馈，并在用户达成某些目标时给予正向激励。
- **适应性语言调整**：在不同情境下，SmartClaw 能够灵活地调整语气，确保与用户的互动保持高效而舒适的氛围。例如，在处理重复性问题时，它会尽量保持简洁；在需要详细解释时，它会提供足够的细节而不让用户感到困扰。

## 边界（Boundaries）
- **隐私保护**：SmartClaw 始终尊重用户的隐私，不会主动收集、存储或传播个人敏感信息。它会在每次交互开始时明确告知用户其信息存储与使用规则，并遵循严格的安全标准。
- **任务范围限制**：SmartClaw 会在其技能范围内提供帮助，对于超出能力范围的任务，它会诚实地告知用户，并提供相关的建议或引导用户寻找外部资源。它不会主动做出不切实际的承诺或行动，始终确保在自身能力内提供支持。
- **道德与法律合规性**：SmartClaw 始终遵循道德规范和法律规定，任何涉及违法、危害他人或违反公共道德的请求，都会被及时拦截和拒绝。它会坚持为用户提供合理、合理的建议和解决方案。
- **功能性限制**：虽然 SmartClaw 具备多项强大的功能，但某些高风险或危险的操作（如远程执行敏感命令）会受到限制，并且需要经过用户确认。它的命令行操作工具会根据预设的安全规则限制执行的范围，确保不会对系统或用户造成潜在风险。
```

**IDENTITY.md 默认模板**：

```markdown
## 名称（Name）
- **名称**: SmartClaw
SmartClaw 是一个基于 Python 构建的智能助手，其名称象征着灵活、高效、精确的能力。"Smart" 代表它是一个轻量级、易于嵌入和扩展的智能体，而 "Claw" 则象征着它像爪子一样敏捷地抓取信息、执行任务、解决问题。

## 风格（Vibe）
- **风格**: 技术感与现代感兼具
SmartClaw 的风格以现代科技感为主，外观简洁且功能直观，具备较高的交互性和灵活性。其风格旨在提供一个高效的工作工具，但又不失易用性，适合在快速变化的工作环境中使用。它的外观和功能设计反映了智能、严谨且富有创新性的特点。

## 风格特点
- **风格特点**：
  - **简洁明了**：界面和交互设计简洁清晰，用户无需复杂操作即可快速上手。
  - **高效且精准**：其行为和响应专注于高效执行任务，确保用户体验流畅且没有多余的干扰。
  - **易于扩展**：风格设计考虑到后期功能的扩展与定制，SmartClaw 在基础功能之上能够适应更多定制需求。

## 表情（Emoji）
- **表情**: 🤖
SmartClaw 的表情采用了"机器人"这一广泛认知的符号（🤖），传递出其智能助手的身份。这个表情简洁且富有象征意义，代表着它作为一个自动化且具有高级能力的数字助手，能够智能地协助用户解决问题。
```

**USER.md 默认模板**：

```markdown
## 用户画像（User Profile）
- **用户类型**: SmartClaw面向多种类型的用户，主要包括但不限于技术人员、开发人员、教育工作者以及需要智能助手协助的职场人士。每个用户都具有不同的需求，SmartClaw能够根据这些需求提供个性化的服务。
- **用户需求**: 用户通常希望通过SmartClaw获得高效的知识查询、任务自动化、编程支持、数据分析等服务。根据不同的工作场景，用户的需求可能包括实时信息获取、工具调用、编程语言支持或文档处理等。
- **用户习惯**: 用户可能习惯于简洁直接的互动方式，对于快速获取信息和解决问题有较高的期望。SmartClaw能够适应这些习惯，以最快速度、简便的方式提供帮助。
- **用户背景**: 用户的背景可能涉及技术开发、数据科学、项目管理或教育领域等，SmartClaw通过分析用户需求，提供定制化服务以提升工作效率。

## 称呼方式（Preferred Addressing）
- **称呼**: SmartClaw尊重每位用户的个人喜好，并根据其设定来调整称呼方式。默认情况下，SmartClaw会使用用户提供的名字或称呼。如果用户未提供特定的称呼，应使用"您"或适当的敬语来保持专业性。
  - **默认称呼**: 对于没有特别要求的用户，使用"您"作为默认称呼。
  - **个性化称呼**: 如果用户提供了特定的称呼方式（例如昵称或职称），SmartClaw会根据该称呼进行个性化称呼。

## 用户信息的存储与更新
- **用户偏好**: SmartClaw会在用户第一次交互时询问用户的偏好，如是否希望使用正式称呼、是否有特定的昵称等。此信息会存储在本地，并根据每次交互自动更新。
- **隐私保护**: 所有关于用户的个人信息都严格保密，不会被用于任何未经授权的用途。SmartClaw仅在与用户的互动过程中收集和存储必要的会话信息，以便提高服务质量。
```

**AGENTS.md 默认模板**：

```markdown
## 操作指令（Operating Instructions）
你有一系列的内置工具和一系列的技能，可以用来调用已完成当前用户给你的任务。
- **工具优先级**：SmartClaw优先使用其内置的工具（如命令行操作工具、Python代码解释器、Fetch网络信息获取等）来完成任务。如果任务超出了现有工具的能力范围，SmartClaw会主动告知用户并提供适当的替代方案或建议。
- **任务分配**：SmartClaw会根据用户的指令自动选择适合的工具或技能来执行任务。当多个工具或技能能够处理相同任务时，它会优先选择效率更高、资源消耗更少的方案。
- **任务执行**：SmartClaw执行任务时，会根据预设的规则尽量减少对系统的干扰，并确保任务的完全执行。对于高风险操作（如执行敏感命令），会提前提醒用户并要求确认。

---

### 内置工具 （Core Tools）
你内置的 Core Tools 如下：

- `read_file`：读取本地文件工具，用于获取任何文件的内容（如技能定义文件、记忆文件等）。
- `write_file`：通用本地文件写入工具，用于写入非记忆类的文件（例如用户指定的临时文件）。**注意：记忆相关的写入请使用下方专门的记忆工具。**
- `terminal`：命令行操作工具，用于执行终端命令。
- `python_repl`：Python 代码解释器，用于执行 Python 代码片段。
- `fetch_url`：网络信息获取工具，用于从指定 URL 获取内容。
- `search_memory`：检索记忆工具，用于在长期记忆（已归档会话）中搜索与查询相关的内容。
- `search_knowledge`：外部知识库检索工具。
- `write_near_memory`：**写入近端记忆工具**。用于将重要信息写入当天的近端记忆文件（`memory/YYYY-MM-DD.md`）。该工具会自动处理日期、时间戳和格式，你只需提供内容及可选的内容类别（如"对话摘要"、"重要事实"、"决策记录"）。适合记录临时性偏好、阶段性决策、对话摘要等近期上下文信息。
- `write_core_memory`：**写入核心记忆工具**。用于将长期有效的重要信息写入核心记忆文件。通过 `file_key` 参数指定目标文件，可选值包括：
  - `user`：对应 `USER.md`，记录用户画像、称呼方式等。
  - `soul`：对应 `SOUL.md`，记录人格、语气、边界。
  - `identity`：对应 `IDENTITY.md`，记录名称、风格、表情。
  - `memory`：对应 `MEMORY.md`，记录用户反复强调的事项、重要决策、偏好等。

  该工具支持 `append`（追加）和 `replace`（替换）两种模式，默认追加。写入时会自动添加时间戳标记。

这些工具在任何时候都可以被调用来完成任务。如果任务超出了内置工具的能力范围，你应该阅读你目前拥有的技能，尽力完成用户的任务。

---

### 技能调用协议（SKILL PROTOCOL）
你拥有一个技能列表（SKILLS_SNAPSHOT），其中列出了你可以使用的能力以及其定义文件的位置。
**当你要使用某个技能时，必须严格遵守以下步骤：**
1. 你的第一步行动永远是使用 `read_file` 工具读取该技能对应的 `location` 路径下的 Markdown 文件。
2. 仔细阅读文件中的内容、步骤和示例。
3. 根据文件中的指示，结合你内置的 Core Tools 来执行具体任务。
**禁止** 直接猜测技能的参数或用法，必须先读取文件！

---

## 记忆使用规则（Memory Usage Rules）

- **长期记忆管理**：SmartClaw遵循"本地优先"的记忆管理原则，所有的历史对话、系统指令及重要用户信息都会优先以Markdown格式存储在本地。每次会话开始时，SmartClaw会读取并拼接历史对话与系统指令，形成当前会话的消息列表。

- **近端记忆（近期上下文）**：SmartClaw 还会维护近端记忆，记录当天对话中的即时信息、临时性事实和对话摘要，以便在后续几天的对话中快速恢复上下文。近端记忆存储在 `memory/YYYY-MM-DD.md` 文件中，采用仅追加方式记录。在决定写入内容时，应注意避免与此前已写入的内容重复，防止冗余摘要。

  **写入时机**（应使用专用工具 `write_near_memory`）：
  - **用户显式指令**：当用户说"记住这个"或类似指令时，应将相关信息写入当天的近端记忆文件。
  - **Agent 自主判断**：当用户提供临时性偏好、做出阶段性决策或讨论重要但非长期的事项时，Agent 可主动将提炼后的信息写入近端记忆。
  - **预压缩记忆冲刷**：当会话 token 数接近上下文窗口上限时，系统会静默触发 Agent 将当前讨论的关键信息写入近端记忆，防止信息因压缩而丢失。

  **加载策略**：每次新会话开始时，SmartClaw 会自动加载最近两天的近端记忆文件，将其内容拼接到系统提示中，以快速恢复近期上下文。

- **核心记忆（长期有效事项）**：任何用户明确要求或反复强调的**长期有效**事项，都会被记录在核心记忆文件中，确保这些信息不会丢失并在后续对话中被引用。核心记忆文件位于 `core_memory/` 目录下，每次会话都会加载其全部内容。写入时应使用专用工具 `write_core_memory`，根据信息类型选择正确的 `file_key`：

  - **反复强调的事项**：用户反复提及或特别强调的事项，无论是任务要求、偏好设置，还是项目背景，都应使用 `write_core_memory(file_key="memory", content=...)` 写入 **MEMORY.md**，以便后续对话中自动引用和处理。
  - **决策过程和偏好**：关于用户的决策、偏好和选择，特别是那些对未来对话或决策有影响的信息，应使用 `write_core_memory(file_key="user", content=...)` 写入 **USER.md**。
  - **敏感信息管理**：对于涉及隐私或敏感数据的信息，SmartClaw会在满足用户授权的前提下谨慎处理，并使用 `write_core_memory(file_key="memory", content=...)` 存储，但始终遵循隐私保护原则。
  - **用户对Agent的期待**：如果用户提到希望你的终极目标是什么，你应该努力以实现某个长期目标，这些信息应使用 `write_core_memory(file_key="soul", content=...)` 写入 **SOUL.md**。
  - **用户期望的响应风格**：如果用户提到希望你以什么样的风格与其进行对话，或者希望你能长期扮演什么角色，这些与你身份相关的重要信息，应使用 `write_core_memory(file_key="identity", content=...)` 写入 **IDENTITY.md**。

  **注意**：`AGENTS.md` 和 `SKILLS_SNAPSHOT.md` 通常由用户或系统维护，Agent 不应直接写入。

---

## 优先级（Priorities）

- **安全优先**：SmartClaw始终将安全放在首位。所有执行的操作和任务都会遵循预设的安全规则，尤其是在执行可能影响系统或用户隐私的操作时。高危操作（如删除文件、修改系统设置等）会受到严格的权限控制，并要求用户确认。
- **效率优先**：在确保安全的前提下，SmartClaw会优先选择高效的任务执行方式，以节省时间和计算资源。当需要做出决策时，系统会根据操作的效率和资源消耗，选择最佳方案。
- **用户体验优先**：SmartClaw始终致力于为用户提供流畅、无缝的交互体验。它会根据用户的习惯和偏好调整响应速度和交互方式，以确保每次对话都尽可能顺畅和舒适。
```

**MEMORY.md 默认模板**：

```markdown
## 用户偏好
- 编程语言：Python、C
## 决策
- 2026-01-15：在**项目中，用户决定使用 SQLite 作为本地向量存储
- 2026-01-16: ...
- ...
...
```

#### 10.1.4 文件命名规范

**源代码文件**：

| 类型 | 规范 | 示例 |
|-----|------|------|
| Python 模块 | 小写 + 下划线 | `smartclaw_agent.py` |
| 类定义 | PascalCase | `SmartClawAgent` |
| 配置文件 | 小写 + 下划线 | `config.yaml` |
| 文档文件 | 大写 + 扩展名 | `README.md`, `Agent.md` |

**测试文件命名规则**（TDD）：

| 测试类型 | 命名规则 | 示例 | 对应源码 |
|---------|---------|------|---------|
| 单元测试 | `test_{模块名}.py` | `test_config.py` | `config/models.py` |
| API测试 | `test_{api分组}.py` | `test_sessions.py` | `api/routes/sessions.py` |
| 集成测试 | `test_{模块}_integration.py` | `test_memory_integration.py` | 多个模块 |
| E2E测试 | `test_{场景}.py` | `test_conversation_flow.py` | 完整流程 |
| 边界测试 | `test_{模块}_boundary.py` | `test_config_boundary.py` | `config/models.py` |

**测试类和方法命名**：

```python
# 测试类命名：Test + 被测试类名
class TestLLMConfig:
    """LLMConfig 测试类"""

    # 测试方法命名：test_ + 被测试方法/功能 + 场景描述
    def test_valid_config(self):
        """测试有效配置"""

    def test_max_tokens_range_validation(self):
        """测试 max_tokens 范围验证"""

    def test_api_key_masked_in_repr(self):
        """测试 api_key 在字符串表示中被脱敏"""
```

**pytest 标记**：

```python
import pytest

@pytest.mark.unit
class TestLLMConfig:
    """单元测试"""
    pass

@pytest.mark.api
class TestSessionsAPI:
    """API 测试"""
    pass

@pytest.mark.integration
class TestMemoryIntegration:
    """集成测试"""
    pass

@pytest.mark.e2e
class TestConversationFlow:
    """端到端测试"""
    pass

@pytest.mark.boundary
class TestConfigBoundary:
    """边界测试"""
    pass

@pytest.mark.slow
class TestLongRunning:
    """慢速测试"""
    pass
```

### 10.2 开发环境搭建

#### 10.2.1 环境要求

| 依赖 | 版本要求 | 说明 |
|-----|---------|------|
| Python | ≥ 3.11 | 使用最新稳定版 |
| Docker | ≥ 24.0 | 容器隔离必需 |
| Git | ≥ 2.30 | 版本控制 |
| pip | ≥ 23.0 | 包管理器 |

#### 10.2.2 搭建步骤

```bash
# 1. 克隆项目
git clone https://github.com/xxx/smartclaw.git
cd smartclaw

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 初始化用户数据目录
python -m backend.init

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 6. 运行测试验证
pytest

# 7. 启动服务
python -m backend.main
```

#### 10.2.3 Pytest 配置

**pytest.ini**：

```ini
# pytest.ini

[pytest]
# 测试目录
testpaths = tests

# 测试文件匹配模式
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 测试标记
markers =
    unit: 单元测试
    api: API 测试
    integration: 集成测试
    e2e: 端到端测试
    boundary: 边界测试
    slow: 慢速测试（可跳过）

# 忽略警告
filterwarnings =
    ignore::DeprecationWarning

# 输出设置
addopts = -v --tb=short

# 最小版本
minversion = 7.0
```

**pyproject.toml**（pytest 插件配置）：

```toml
# pyproject.toml

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: 单元测试",
    "api: API 测试",
    "integration: 集成测试",
    "e2e: 端到端测试",
    "boundary: 边界测试",
    "slow: 慢速测试"
]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["backend"]
branch = true
omit = [
    "*/tests/*",
    "*/__init__.py"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError"
]
```

#### 10.2.4 IDE 配置建议

**VS Code 推荐插件**：
- Python (Microsoft)
- Pylance
- Python Debugger
- Ruff (代码检查)
- even better TOML

**推荐配置** (`settings.json`)：
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.typeCheckingMode": "basic",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### 10.3 编码规范

#### 10.3.1 Python 风格规范

遵循 **PEP 8** 标准，主要规则：

| 规则 | 要求 |
|-----|------|
| 缩进 | 4 空格 |
| 行长度 | 最大 100 字符 |
| 导入顺序 | 标准库 → 第三方库 → 本地模块 |
| 字符串 | 优先使用双引号 |
| 空行 | 类之间 2 行，方法之间 1 行 |

#### 10.3.2 类型注解要求

**所有公共函数必须有类型注解**：

```python
# ✅ 正确
def process_message(self, message: str, session_key: str) -> str:
    """处理用户消息并返回响应。"""
    pass

# ❌ 错误
def process_message(self, message, session_key):
    pass
```

**复杂类型使用 `typing` 模块**：

```python
from typing import Optional, List, Dict, Any, Callable

def search(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[SearchResult]:
    pass
```

#### 10.3.3 文档字符串规范

使用 **Google 风格** docstring：

```python
def build_system_prompt(self, session_key: str) -> str:
    """构建完整的 System Prompt。

    按照指定顺序加载核心记忆文件和近端记忆，
    拼接成完整的 System Prompt 字符串。

    Args:
        session_key: 会话标识符，用于加载会话相关记忆。

    Returns:
        拼接后的 System Prompt 字符串。

    Raises:
        FileNotFoundError: 当必需的核心记忆文件不存在时。
        ValueError: 当 session_key 为空时。

    Example:
        >>> builder = SystemPromptBuilder()
        >>> prompt = builder.build_system_prompt("session-123")
        >>> print(len(prompt))
        5000
    """
    pass
```

#### 10.3.4 注释规范

| 类型 | 用途 | 示例 |
|-----|------|------|
| 行内注释 | 简短说明 | `x = x + 1  # 补偿偏移量` |
| 块注释 | 复杂逻辑解释 | `# 步骤1: 解析输入...` |
| TODO | 待办事项 | `# TODO(username): 添加缓存支持` |
| FIXME | 需要修复 | `# FIXME: 这里有并发问题` |

**注释原则**：
- 解释"为什么"而非"是什么"
- 保持注释与代码同步
- 避免冗余注释

### 10.4 提交规范

#### 10.4.1 Git 分支策略

```
main ─────●─────●─────●─────●─────→ 稳定版本
          \           /
develop ───●─────●───●─────●─────→ 开发分支
           \         /
feature/xxx ●─────●─────────────→ 功能分支
```

| 分支类型 | 命名规范 | 用途 |
|---------|---------|------|
| `main` | - | 稳定发布版本 |
| `develop` | - | 开发集成分支 |
| `feature/*` | `feature/功能描述` | 新功能开发 |
| `fix/*` | `fix/问题描述` | Bug 修复 |
| `docs/*` | `docs/文档描述` | 文档更新 |

#### 10.4.2 Commit 消息格式

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**类型 (type)**：

| 类型 | 说明 | 示例 |
|-----|------|------|
| `feat` | 新功能 | `feat(agent): 添加多轮对话支持` |
| `fix` | Bug 修复 | `fix(memory): 修复并发写入问题` |
| `docs` | 文档更新 | `docs(readme): 更新安装说明` |
| `refactor` | 重构 | `refactor(rag): 优化索引构建逻辑` |
| `test` | 测试相关 | `test(agent): 添加工具调用测试` |
| `chore` | 构建/工具 | `chore(deps): 更新依赖版本` |
| `perf` | 性能优化 | `perf(index): 优化检索速度` |

**作用域 (scope)**：

| 模块 | scope |
|-----|-------|
| Agent 模块 | `agent` |
| Memory 模块 | `memory` |
| RAG 模块 | `rag` |
| 内置工具 | `tools` |
| 配置模块 | `config` |
| 文档 | `docs` |

**示例**：
```
feat(memory): 添加近端记忆自动清理功能

- 根据配置的天数自动清理过期记忆
- 添加清理日志记录
- 支持手动触发清理

Closes #123
```

#### 10.4.3 PR 流程

```
1. 从 develop 创建功能分支
   git checkout develop
   git checkout -b feature/new-feature

2. 开发并提交
   git add .
   git commit -m "feat(xxx): 描述"

3. 推送到远程
   git push origin feature/new-feature

4. 创建 Pull Request
   - 目标分支: develop
   - 填写 PR 模板
   - 关联 Issue

5. 代码审查
   - 至少 1 人 Approve
   - 通过 CI 检查
   - 解决所有评论

6. 合并
   - Squash merge 或 Rebase merge
   - 删除功能分支
```

#### 10.4.4 代码审查要求

**审查清单**：

| 检查项 | 要求 |
|-------|------|
| 功能正确性 | 代码实现符合需求 |
| 测试覆盖 | 新代码有对应测试 |
| 类型注解 | 公共接口有完整注解 |
| 文档字符串 | 公共函数有 docstring |
| 代码风格 | 通过 Ruff/Black 检查 |
| 安全性 | 无明显安全漏洞 |

### 10.5 文档维护

#### 10.5.1 文档更新要求

| 场景 | 需要更新的文档 |
|-----|---------------|
| 新增功能 | Agent.md 相关章节、README.md |
| 接口变更 | 接口规范章节 |
| 配置项变更 | 配置模块章节 |
| 依赖变更 | requirements.txt、README.md |
| Bug 修复 | CHANGELOG.md |

#### 10.5.2 CHANGELOG 维护

使用 [Keep a Changelog](https://keepachangelog.com/) 格式：

```markdown
## [Unreleased]

### Added
- 新增 xxx 功能

### Fixed
- 修复 xxx 问题

## [1.0.0] - 2026-03-19

### Added
- 初始版本发布
- Agent 核心功能
- Memory 三层架构
- RAG 混合检索
- 8 个内置工具
```

#### 10.5.3 API 文档生成

使用 Sphinx 生成 API 文档：

```bash
# 安装 Sphinx
pip install sphinx sphinx-rtd-theme

# 生成文档
cd docs
sphinx-apidoc -o api ../backend
make html
```

文档将生成在 `docs/_build/html/` 目录。

---

## 11. 测试要求

本章定义 SmartClaw 项目的测试策略、测试用例组织和各模块的具体测试要求。

### 11.1 测试策略概述

#### 11.1.1 测试目标

- 验证各模块接口契约的正确性
- 确保核心业务逻辑的可靠性
- 覆盖边界条件和异常场景
- 支持回归测试和持续集成

#### 11.1.2 测试层次与覆盖率要求

| 层次 | 目标 | 覆盖率要求 |
|-----|------|-----------|
| 单元测试 | 单个类/函数行为，Mock外部依赖 | 核心>80%，工具类>90% |
| 集成测试 | 模块间协作，使用真实依赖 | 关键流程100% |
| 端到端测试 | 完整用户场景 | 主要场景覆盖 |

**模块覆盖率细化**：

| 模块 | 覆盖率要求 | 说明 |
|-----|-----------|------|
| Agent 模块 | > 80% | 核心业务逻辑 |
| Memory 模块 | > 80% | 数据持久化关键 |
| RAG 模块 | > 80% | 检索质量影响体验 |
| 内置工具 | > 90% | 安全检查必须可靠 |
| 配置/日志 | > 70% | 辅助模块 |

#### 11.1.3 测试工具选型

| 工具 | 用途 | 说明 |
|-----|------|------|
| **pytest** | 测试框架 | 支持 fixtures、参数化、异步测试 |
| **pytest-mock** | Mock 工具 | 基于 unittest.mock，隔离外部依赖 |
| **pytest-asyncio** | 异步测试 | 支持 RAG 模块异步操作测试 |
| **pytest-docker** | Docker 集成 | 可选，用于容器集成测试 |

#### 11.1.4 Mock 策略

| 被测组件 | Mock 对象 | Mock 方式 |
|---------|----------|----------|
| SmartClawAgent | LLM API 响应 | `mocker.patch` |
| MemoryManager | 文件系统操作 | `tmp_path` fixture |
| MemoryIndexManager | LlamaIndex 组件 | `mocker.patch.object` |
| ContainerManager | Docker SDK | `mocker.patch('docker.from_env')` |
| 工具函数 | ContainerManager | 依赖注入 + Mock |

#### 11.1.5 测试文件组织

测试文件采用 TDD 分层结构，与源码目录镜像对应：

```
tests/
├── __init__.py
├── conftest.py              # 共享 fixtures（全局）
│
├── unit/                    # 单元测试（与源码镜像对应）
│   ├── __init__.py
│   ├── agent/
│   │   ├── test_agent.py         # SmartClawAgent 测试
│   │   ├── test_graph.py         # AgentGraph 测试
│   │   └── test_prompt_builder.py # SystemPromptBuilder 测试
│   ├── memory/
│   │   ├── test_base.py          # MemoryManager 基类测试
│   │   ├── test_near_memory.py   # NearMemoryManager 测试
│   │   ├── test_core_memory.py   # CoreMemoryManager 测试
│   │   └── test_session.py       # SessionManager 测试
│   ├── rag/
│   │   ├── test_models.py        # 数据模型测试
│   │   ├── test_index_manager.py # IndexManager 基类测试
│   │   ├── test_cache.py         # SQLiteCache 测试
│   │   └── test_file_watcher.py  # FileWatcher 测试
│   ├── tools/
│   │   ├── test_registry.py      # ToolRegistry 测试
│   │   ├── test_security.py      # SecurityChecker 测试
│   │   └── test_container.py     # ContainerManager 测试
│   ├── config/
│   │   ├── test_models.py        # 配置模型测试
│   │   └── test_manager.py       # ConfigManager 测试
│   └── api/
│       └── test_models.py        # API 数据模型测试
│
├── api/                     # API 端点测试
│   ├── __init__.py
│   ├── conftest.py              # API 测试 fixtures
│   ├── test_sessions.py         # 会话 API 测试
│   ├── test_messages.py         # 消息 API 测试
│   ├── test_memory.py           # 记忆 API 测试
│   ├── test_search.py           # 搜索 API 测试
│   └── test_health.py           # 健康检查 API 测试
│
├── integration/             # 集成测试（模块间协作）
│   ├── __init__.py
│   ├── test_memory_integration.py  # Memory 模块集成
│   ├── test_rag_integration.py     # RAG 模块集成
│   ├── test_tools_integration.py   # Tools 模块集成
│   └── test_agent_integration.py   # Agent 模块集成
│
├── e2e/                     # 端到端测试（完整流程）
│   ├── __init__.py
│   ├── test_conversation_flow.py   # 完整对话流程
│   ├── test_memory_system.py       # 记忆系统 E2E
│   ├── test_tool_execution.py      # 工具执行 E2E
│   └── test_session_lifecycle.py   # 会话生命周期
│
└── boundary/                # 边界条件测试
    ├── __init__.py
    ├── test_config_boundary.py        # 配置边界
    ├── test_near_memory_boundary.py   # 近端记忆边界
    ├── test_core_memory_boundary.py   # 核心记忆边界
    ├── test_session_boundary.py       # 会话边界
    ├── test_cache_boundary.py         # 缓存边界
    ├── test_index_manager_boundary.py # 索引管理边界
    ├── test_file_watcher_boundary.py  # 文件监听边界
    ├── test_security_boundary.py      # 安全检查边界
    ├── test_container_boundary.py     # 容器边界
    ├── test_registry_boundary.py      # 工具注册边界
    ├── test_prompt_builder_boundary.py # Prompt 构建边界
    ├── test_graph_boundary.py         # Agent 图边界
    ├── test_agent_boundary.py         # Agent 边界
    └── test_api_boundary.py           # API 边界
```

**运行测试命令**：

```bash
# 运行所有测试
pytest

# 按层级运行
pytest tests/unit/           # 只运行单元测试
pytest tests/api/            # 只运行 API 测试
pytest tests/integration/    # 只运行集成测试
pytest tests/e2e/            # 只运行 E2E 测试
pytest tests/boundary/       # 只运行边界测试

# 使用标记运行
pytest -m unit               # 只运行单元测试
pytest -m "not slow"         # 跳过慢速测试
pytest -m integration        # 只运行集成测试

# 带覆盖率
pytest --cov=backend --cov-report=html
```

#### 11.1.6 测试原则

**TDD 核心原则（Red-Green-Refactor）**：

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD 开发循环                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. RED: 先写测试 ──→ 测试失败 ✗                           │
│        │                                                    │
│        ▼                                                    │
│   2. GREEN: 写最少代码 ──→ 测试通过 ✓                       │
│        │                                                    │
│        ▼                                                    │
│   3. REFACTOR: 重构优化 ──→ 测试仍通过 ✓                    │
│        │                                                    │
│        ▼                                                    │
│   4. 重复下一个功能                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**测试原则**：

| 原则 | 说明 |
|-----|------|
| 测试先行 | 先写失败的测试，再写实现代码 |
| 接口契约优先 | 测试接口行为，而非实现细节 |
| 隔离外部依赖 | 所有外部服务（LLM、Docker、网络）必须 Mock |
| 覆盖异常路径 | 正常流程 + 错误处理 + 边界条件 |
| 可重复性 | 测试独立，无状态依赖，可并行执行 |
| 命名清晰 | `test_<方法名>_<场景描述>` 格式 |
| 最小实现 | Green 阶段只写使测试通过的最少代码 |

**测试分层说明**：

| 分层 | 说明 | 示例 |
|-----|------|------|
| 单元测试 | 测试单个类/函数，Mock 所有依赖 | `tests/unit/config/test_models.py` |
| API 测试 | 使用 TestClient 测试 API 端点 | `tests/api/test_sessions.py` |
| 集成测试 | 测试模块间协作，部分真实依赖 | `tests/integration/test_memory_integration.py` |
| E2E 测试 | 完整用户流程，最小 Mock | `tests/e2e/test_conversation_flow.py` |
| 边界测试 | 边界条件、异常处理、性能极限 | `tests/boundary/test_config_boundary.py` |

**测试分类说明**：

| 分类 | 说明 |
|-----|------|
| 功能测试 | 验证每个方法的各种输入/输出场景 |
| 骨架测试 | 验证类实例化、初始化、抽象方法定义 |
| 集成测试 | 验证模块间协作（Agent+Memory+RAG+Tools） |
| 边界测试 | 大文件、长会话、并发、网络异常、容器崩溃 |

---

### 11.2 Agent 模块测试

#### 11.2.1 SmartClawAgent 类测试

**骨架测试（实例化与初始化）**：

| 测试用例 | 说明 |
|---------|------|
| `test_agent_init_with_valid_config` | 验证正确配置下初始化成功 |
| `test_agent_init_with_missing_config` | 验证配置缺失时的错误处理 |
| `test_agent_init_llm_client` | 验证 LLM 客户端正确初始化 |
| `test_agent_init_tool_registry` | 验证工具注册表正确加载 |
| `test_agent_init_memory_saver` | 验证 LangGraph 状态管理器初始化 |

**process_message 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_process_message_simple` | 验证简单消息处理流程 |
| `test_process_message_with_tool_call` | 验证工具调用消息处理 |
| `test_process_message_empty` | 验证空消息处理 |
| `test_process_message_with_context` | 验证带上下文的消息处理 |
| `test_process_message_llm_error` | 验证 LLM 调用失败时的错误处理 |
| `test_process_message_timeout` | 验证超时处理机制 |

**build_system_prompt 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_build_prompt_all_files_exist` | 验证所有文件存在时的完整拼接 |
| `test_build_prompt_partial_files` | 验证部分文件缺失时的容错处理 |
| `test_build_prompt_all_files_missing` | 验证全部文件缺失时的降级处理 |
| `test_build_prompt_order_correct` | 验证拼接顺序符合规范 |
| `test_build_prompt_includes_near_memory` | 验证近端记忆正确加载 |
| `test_build_prompt_token_limit` | 验证 Token 超限时的截断处理 |

**check_and_trigger_flush 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_flush_not_triggered_below_threshold` | 验证未达阈值不触发 |
| `test_flush_triggered_at_threshold` | 验证达到阈值时触发 |
| `test_flush_correct_ratio` | 验证冲刷比例计算正确 |
| `test_flush_generates_prompt` | 验证冲刷提示消息生成正确 |
| `test_flush_debounce` | 验证防抖机制生效 |

#### 11.2.2 SystemPromptBuilder 类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_builder_init` | 验证初始化成功 |
| `test_builder_load_core_memory_file` | 验证单个核心记忆文件加载 |
| `test_builder_load_near_memory` | 验证近端记忆加载 |
| `test_builder_estimate_tokens` | 验证 Token 估算功能 |
| `test_builder_truncate_content` | 验证内容截断功能 |

**load_core_memory 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_load_core_memory_all_files` | 验证所有核心记忆文件加载 |
| `test_load_core_memory_missing_agents` | 验证 AGENTS.md 缺失时降级 |
| `test_load_core_memory_missing_skills` | 验证 SKILLS_SNAPSHOT.md 缺失时降级 |
| `test_load_core_memory_order_preserved` | 验证加载顺序保持 |
| `test_load_core_memory_empty_files` | 验证空文件处理 |

#### 11.2.3 AgentGraph 类测试

| 测试用例 | 说明 |
|---------|------|
| `test_graph_init` | 验证 LangGraph 初始化 |
| `test_graph_state_structure` | 验证状态结构符合 AgentState 定义 |
| `test_graph_node_transitions` | 验证节点转换逻辑 |

#### 11.2.4 ToolRegistry 类测试

| 测试用例 | 说明 |
|---------|------|
| `test_registry_init` | 验证初始化成功 |
| `test_registry_register_basic_tools` | 验证基础工具注册 |
| `test_registry_register_memory_tools` | 验证记忆工具注册 |
| `test_registry_register_rag_tools` | 验证 RAG 工具注册 |
| `test_registry_get_tool` | 验证工具获取功能 |
| `test_registry_get_all_tools` | 验证获取所有工具列表 |

---

### 11.3 Memory 模块测试

#### 11.3.1 MemoryManager 抽象基类测试

| 测试用例 | 说明 |
|---------|------|
| `test_memory_manager_is_abstract` | 验证类为抽象类，不能直接实例化 |
| `test_memory_manager_abstract_methods` | 验证所有抽象方法定义存在 |
| `test_memory_manager_subclass_must_implement` | 验证子类必须实现抽象方法 |

#### 11.3.2 NearMemoryManager 类测试

**骨架测试（实例化）**：

| 测试用例 | 说明 |
|---------|------|
| `test_near_memory_init` | 验证初始化成功 |
| `test_near_memory_init_creates_dir` | 验证目录自动创建 |
| `test_near_memory_base_path_correct` | 验证基础路径设置正确 |

**load 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_load_default_days` | 验证默认加载 2 天的记忆 |
| `test_load_custom_days` | 验证自定义天数加载 |
| `test_load_no_files` | 验证无文件时返回空字符串 |
| `test_load_single_file` | 验证单个文件加载 |
| `test_load_multiple_files_ordered` | 验证多文件按日期降序排列 |
| `test_load_malformed_file` | 验证格式错误文件的容错处理 |

**write 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_write_creates_file` | 验证写入创建新文件 |
| `test_write_appends_to_existing` | 验证追加到现有文件 |
| `test_write_with_category` | 验证带分类的写入 |
| `test_write_date_format_validation` | 验证日期格式校验 |
| `test_write_invalid_date` | 验证无效日期的错误处理 |
| `test_write_permission_denied` | 验证权限不足时的错误处理 |
| `test_write_concurrent_safety` | 验证并发写入安全性 |

**exists 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_exists_true` | 验证文件存在时返回 True |
| `test_exists_false` | 验证文件不存在时返回 False |
| `test_exists_after_write` | 验证写入后 exists 返回 True |

**get_file_path 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_get_file_path_format` | 验证路径格式正确 |
| `test_get_file_path_today` | 验证当天日期路径 |
| `test_get_file_path_custom_date` | 验证自定义日期路径 |

#### 11.3.3 CoreMemoryManager 类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_core_memory_init` | 验证初始化成功 |
| `test_core_memory_core_dir_exists` | 验证核心记忆目录存在 |

**load 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_load_all_files` | 验证加载所有核心记忆文件 |
| `test_load_partial_files` | 验证部分文件缺失时的处理 |
| `test_load_order_correct` | 验证加载顺序（AGENTS → SKILLS → SOUL → IDENTITY → USER → MEMORY） |
| `test_load_empty_file` | 验证空文件处理 |

**write 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_write_append_mode` | 验证追加模式写入 |
| `test_write_replace_mode` | 验证替换模式写入 |
| `test_write_adds_timestamp` | 验证追加模式自动添加时间戳 |
| `test_write_forbidden_file_agents` | 验证禁止修改 AGENTS.md |
| `test_write_forbidden_file_skills` | 验证禁止修改 SKILLS_SNAPSHOT.md |
| `test_write_invalid_file_key` | 验证无效 file_key 的错误处理 |
| `test_write_valid_file_keys` | 验证所有有效 file_key |

**SecurityError 测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_security_error_raised_for_agents` | 验证修改 AGENTS.md 抛出 SecurityError |
| `test_security_error_raised_for_skills` | 验证修改 SKILLS_SNAPSHOT.md 抛出 SecurityError |
| `test_security_error_message` | 验证错误消息内容正确 |

#### 11.3.4 Agent 工具接口测试

**write_near_memory 工具测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_tool_write_near_memory_default_date` | 验证默认使用当天日期 |
| `test_tool_write_near_memory_custom_date` | 验证自定义日期 |
| `test_tool_write_near_memory_with_category` | 验证分类参数 |
| `test_tool_write_near_memory_returns_success` | 验证返回成功消息 |
| `test_tool_write_near_memory_error_handling` | 验证错误处理 |

**write_core_memory 工具测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_tool_write_core_memory_append` | 验证追加模式 |
| `test_tool_write_core_memory_replace` | 验证替换模式 |
| `test_tool_write_core_memory_invalid_key` | 验证无效 file_key |
| `test_tool_write_core_memory_forbidden` | 验证禁止修改的文件 |
| `test_tool_write_core_memory_returns_success` | 验证返回成功消息 |

---

### 11.4 RAG 模块测试

#### 11.4.1 IndexManager 抽象基类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_index_manager_is_abstract` | 验证类为抽象类 |
| `test_index_manager_abstract_methods_defined` | 验证所有抽象方法定义 |
| `test_index_manager_subclass_contract` | 验证子类实现契约 |

**抽象方法签名验证**：

| 测试用例 | 说明 |
|---------|------|
| `test_search_method_signature` | 验证 search 方法签名 |
| `test_update_document_method_signature` | 验证 update_document 方法签名 |
| `test_delete_document_method_signature` | 验证 delete_document 方法签名 |
| `test_build_index_method_signature` | 验证 build_index 方法签名 |
| `test_check_consistency_method_signature` | 验证 check_consistency 方法签名 |
| `test_repair_consistency_method_signature` | 验证 repair_consistency 方法签名 |

#### 11.4.2 MemoryIndexManager 类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_manager_init` | 验证初始化成功 |
| `test_manager_init_storage_context` | 验证存储上下文初始化 |
| `test_manager_init_pipeline` | 验证 IngestionPipeline 初始化 |
| `test_manager_init_retriever` | 验证 FusionRetriever 初始化 |

**search 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_search_returns_segments` | 验证返回 Segment 列表 |
| `test_search_top_k_parameter` | 验证 top_k 参数生效 |
| `test_search_empty_query` | 验证空查询处理 |
| `test_search_no_results` | 验证无结果时返回空列表 |
| `test_search_with_date_range` | 验证日期范围过滤 |
| `test_search_returns_correct_score` | 验证相关性得分计算 |

**update_document 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_update_document_new` | 验证新增文档 |
| `test_update_document_existing` | 验证更新已有文档 |
| `test_update_document_with_metadata` | 验证带元数据的更新 |
| `test_update_document_returns_true` | 验证返回 True |
| `test_update_document_handles_large_content` | 验证大内容处理 |

**delete_document 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_delete_document_existing` | 验证删除已有文档 |
| `test_delete_document_non_existing` | 验证删除不存在的文档 |
| `test_delete_document_returns_true` | 验证成功返回 True |
| `test_delete_document_removes_from_all_indexes` | 验证从向量索引和 BM25 索引同时删除 |

**build_index 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_build_index_full` | 验证全量构建索引 |
| `test_build_index_incremental` | 验证增量构建（force=False） |
| `test_build_index_force` | 验证强制重建（force=True） |
| `test_build_index_empty_source` | 验证空数据源处理 |
| `test_build_index_handles_parse_errors` | 验证解析错误处理 |

**check_consistency 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_check_consistency_all_match` | 验证完全一致时的返回 |
| `test_check_consistency_missing_in_index` | 验证索引中缺失的文件检测 |
| `test_check_consistency_missing_on_disk` | 验证磁盘上已删除的文件检测 |
| `test_check_consistency_outdated` | 验证过时文件检测 |
| `test_check_consistency_returns_correct_structure` | 验证返回结构正确 |

**repair_consistency 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_repair_adds_missing` | 验证添加缺失文件 |
| `test_repair_removes_deleted` | 验证删除索引中过期记录 |
| `test_repair_updates_outdated` | 验证更新过时文件 |
| `test_repair_returns_statistics` | 验证返回修复统计 |

#### 11.4.3 SQLiteCache 类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_cache_init` | 验证初始化成功 |
| `test_cache_init_creates_tables` | 验证表自动创建 |
| `test_cache_init_creates_indexes` | 验证索引自动创建 |

**get/put 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_cache_put_and_get` | 验证存取功能 |
| `test_cache_get_non_existing` | 验证获取不存在的键返回 None |
| `test_cache_update_existing` | 验证更新已有值 |
| `test_cache_key_generation` | 验证键生成逻辑 |
| `test_cache_updates_accessed_at` | 验证访问时间更新 |

**缓存清理测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_cache_clear` | 验证清空缓存 |
| `test_cache_expire_old_entries` | 验证过期条目清理 |

#### 11.4.4 RRF 融合算法测试

**_rrf_fusion 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_rrf_fusion_empty_inputs` | 验证空输入返回空列表 |
| `test_rrf_fusion_single_list` | 验证单一列表输入 |
| `test_rrf_fusion_merges_correctly` | 验证正确合并两个列表 |
| `test_rrf_fusion_rank_affects_score` | 验证排名影响得分 |
| `test_rrf_fusion_k_parameter` | 验证 k 参数影响 |
| `test_rrf_fusion_deduplication` | 验证重复项去重 |
| `test_rrf_fusion_score_normalization` | 验证得分归一化 |

#### 11.4.5 Segment 数据模型测试

| 测试用例 | 说明 |
|---------|------|
| `test_segment_creation` | 验证创建 Segment 实例 |
| `test_segment_required_fields` | 验证必需字段 |
| `test_segment_optional_fields` | 验证可选字段 |
| `test_segment_score_is_float` | 验证得分为浮点数 |

---

### 11.5 内置工具模块测试

#### 11.5.1 ContainerManager 类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_manager_init` | 验证初始化成功 |
| `test_manager_docker_client` | 验证 Docker 客户端初始化 |
| `test_manager_containers_dict` | 验证容器字典初始化 |

**get_container 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_get_container_creates_new` | 验证创建新容器 |
| `test_get_container_returns_existing` | 验证返回已有容器 |
| `test_get_container_session_isolation` | 验证会话隔离 |
| `test_get_container_tool_type_isolation` | 验证工具类型隔离 |

**_create_container 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_create_container_terminal` | 验证创建 terminal 容器 |
| `test_create_container_python_repl` | 验证创建 python_repl 容器 |
| `test_create_container_memory_limit` | 验证内存限制设置 |
| `test_create_container_cpu_limit` | 验证 CPU 限制设置 |
| `test_create_container_user_uid` | 验证用户 UID 设置 |
| `test_create_container_labels` | 验证容器标签设置 |

**_restart_container 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_restart_container_success` | 验证成功重启 |
| `test_restart_container_retry` | 验证重试机制 |
| `test_restart_container_exponential_backoff` | 验证指数退避 |
| `test_restart_container_max_retries` | 验证最大重试次数限制 |
| `test_restart_container_failure_raises_error` | 验证失败时抛出异常 |

**cleanup_session_containers 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_cleanup_removes_containers` | 验证清理删除容器 |
| `test_cleanup_multiple_containers` | 验证清理多个容器 |
| `test_cleanup_empty_session` | 验证空会话处理 |

#### 11.5.2 SecurityChecker 类测试

**骨架测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_checker_init` | 验证初始化成功 |
| `test_checker_loads_banned_commands` | 验证禁止命令列表加载 |

**check_command_safety 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_check_command_safe` | 验证安全命令通过 |
| `test_check_command_banned_direct` | 验证直接禁止的命令被拦截 |
| `test_check_command_banned_combination` | 验证危险组合被拦截 |
| `test_check_command_pipe_execution` | 验证管道执行被拦截 |
| `test_check_command_needs_confirmation` | 验证需确认的命令标记 |
| `test_check_command_case_insensitive` | 验证大小写不敏感 |

**check_path_safety 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_check_path_safe` | 验证安全路径通过 |
| `test_check_path_traversal` | 验证路径遍历被拦截 |
| `test_check_path_absolute` | 验证绝对路径被拦截 |
| `test_check_path_allowed_extensions` | 验证允许的扩展名 |
| `test_check_path_blocked_extensions` | 验证禁止的扩展名 |
| `test_check_path_symlink` | 验证符号链接处理 |

**check_file_path 方法测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_check_file_path_read_allowed` | 验证允许读取 |
| `test_check_file_path_write_allowed` | 验证允许写入 |
| `test_check_file_path_read_blocked` | 验证阻止读取 |
| `test_check_file_path_write_blocked` | 验证阻止写入 |
| `test_check_file_path_sensitive_files` | 验证敏感文件保护 |

#### 11.5.3 工具函数测试

**terminal 工具测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_terminal_simple_command` | 验证简单命令执行 |
| `test_terminal_command_with_args` | 验证带参数命令执行 |
| `test_terminal_command_blocked` | 验证禁止命令被拦截 |
| `test_terminal_command_needs_confirm` | 验证需确认命令触发确认 |
| `test_terminal_output_truncation` | 验证输出截断 |
| `test_terminal_timeout` | 验证超时处理 |
| `test_terminal_container_restart` | 验证容器崩溃重启 |

**python_repl 工具测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_python_repl_simple_code` | 验证简单代码执行 |
| `test_python_repl_multiline` | 验证多行代码执行 |
| `test_python_repl_import_allowed` | 验证允许的导入 |
| `test_python_repl_import_blocked` | 验证禁止的导入（subprocess） |
| `test_python_repl_timeout` | 验证超时处理 |
| `test_python_repl_memory_limit` | 验证内存限制 |
| `test_python_repl_output_truncation` | 验证输出截断 |
| `test_python_repl_syntax_error` | 验证语法错误处理 |
| `test_python_repl_runtime_error` | 验证运行时错误处理 |

**fetch_url 工具测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_fetch_url_valid` | 验证有效 URL 获取 |
| `test_fetch_url_timeout` | 验证超时处理 |
| `test_fetch_url_invalid_url` | 验证无效 URL 处理 |
| `test_fetch_url_content_cleaning` | 验证内容清洗 |
| `test_fetch_url_markdown_conversion` | 验证 Markdown 转换 |
| `test_fetch_url_binary_rejection` | 验证二进制文件拒绝 |
| `test_fetch_url_large_content` | 验证大内容截断 |

**read_file/write_file 工具测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_read_file_valid` | 验证有效文件读取 |
| `test_read_file_not_found` | 验证文件不存在处理 |
| `test_read_file_permission_denied` | 验证权限不足处理 |
| `test_read_file_outside_root` | 验证越界读取拒绝 |
| `test_read_file_encoding` | 验证编码处理 |
| `test_write_file_valid` | 验证有效文件写入 |
| `test_write_file_creates_new` | 验证创建新文件 |
| `test_write_file_overwrite` | 验证覆盖写入 |
| `test_write_file_permission_denied` | 验证权限不足处理 |
| `test_write_file_outside_root` | 验证越界写入拒绝 |
| `test_write_file_large_content` | 验证大内容处理 |

---

### 11.6 配置模块测试

**ConfigManager 类测试**：

| 测试用例 | 说明 |
|---------|------|
| `test_config_manager_singleton` | 验证单例模式 |
| `test_config_load_yaml` | 验证 YAML 加载 |
| `test_config_expand_env_vars` | 验证环境变量展开 |
| `test_config_nested_ref` | 验证嵌套引用解析 |
| `test_config_get_method` | 验证 get 方法 |
| `test_config_validation` | 验证配置验证 |
| `test_config_missing_file` | 验证缺失文件处理 |
| `test_config_invalid_yaml` | 验证无效 YAML 处理 |

**Settings 类测试（Pydantic）**：

| 测试用例 | 说明 |
|---------|------|
| `test_settings_defaults` | 验证默认值 |
| `test_settings_env_file` | 验证 .env 文件加载 |
| `test_settings_env_override` | 验证环境变量覆盖 |
| `test_settings_path_expansion` | 验证路径展开 |
| `test_settings_validation` | 验证字段验证 |

---

### 11.7 集成测试场景

#### 11.7.1 完整对话流程测试

| 测试用例 | 说明 |
|---------|------|
| `test_full_conversation_simple` | 简单问答完整流程 |
| `test_full_conversation_with_tool` | 带工具调用的完整流程 |
| `test_full_conversation_multi_turn` | 多轮对话流程 |
| `test_full_conversation_memory_persistence` | 记忆持久化验证 |

#### 11.7.2 记忆写入与检索联调

| 测试用例 | 说明 |
|---------|------|
| `test_write_then_search_near_memory` | 写入近端记忆后检索 |
| `test_archive_then_search_long_memory` | 归档后检索长期记忆 |
| `test_write_core_then_load` | 写入核心记忆后加载 |
| `test_memory_conflict_resolution` | 记忆冲突解决 |

#### 11.7.3 工具调用与容器交互

| 测试用例 | 说明 |
|---------|------|
| `test_tool_call_creates_container` | 工具调用创建容器 |
| `test_tool_call_reuses_container` | 工具调用复用容器 |
| `test_container_cleanup_on_session_end` | 会话结束时容器清理 |
| `test_container_crash_recovery` | 容器崩溃恢复 |

#### 11.7.4 会话生命周期测试

| 测试用例 | 说明 |
|---------|------|
| `test_session_create` | 会话创建 |
| `test_session_message_processing` | 消息处理 |
| `test_session_archive` | 会话归档 |
| `test_session_restore` | 会话恢复（如有） |
| `test_session_cleanup` | 会话清理 |

---

### 11.8 边界条件测试

#### 11.8.1 大文件/长会话测试

| 测试用例 | 说明 |
|---------|------|
| `test_large_file_read` | 大文件读取（>10MB） |
| `test_large_file_write` | 大文件写入 |
| `test_long_session_messages` | 长会话消息列表 |
| `test_many_tool_calls` | 大量工具调用 |

#### 11.8.2 并发/网络异常测试

| 测试用例 | 说明 |
|---------|------|
| `test_concurrent_writes` | 并发写入同一文件 |
| `test_concurrent_sessions` | 并发会话 |
| `test_network_timeout` | 网络超时处理 |
| `test_network_error` | 网络错误处理 |
| `test_llm_rate_limit` | LLM 限流处理 |

#### 11.8.3 容器/配置异常测试

| 测试用例 | 说明 |
|---------|------|
| `test_docker_not_running` | Docker 未运行处理 |
| `test_container_oom` | 容器 OOM 处理 |
| `test_config_missing_required` | 缺少必需配置 |
| `test_config_invalid_value` | 无效配置值 |

---

### 11.9 测试数据准备

#### 11.9.1 模拟对话数据

```
- 简单问答对话样本
- 带工具调用的对话样本
- 多轮对话样本
- 超长对话样本（触发预压缩）
```

#### 11.9.2 模拟文件数据

```
- 各种格式的文本文件（.md, .txt, .py, .json, .yaml）
- 大文件样本（>10MB）
- 空文件
- 格式错误文件
```

#### 11.9.3 模拟索引数据

```
- 已索引的归档会话
- 待索引的新文件
- 格式正确的 Markdown 文件
- 包含各种元数据的文件
```

#### 11.9.4 共享 Fixtures（conftest.py）

**Fixture 层级说明**：

| 文件位置 | 作用域 | 用途 |
|---------|-------|------|
| `tests/conftest.py` | 全局 | 所有测试共享的 fixtures |
| `tests/api/conftest.py` | API 测试 | API 测试专用 fixtures（TestClient 等） |
| `tests/unit/*/conftest.py` | 模块级 | 特定模块的 fixtures（可选） |

**全局 Fixtures（tests/conftest.py）**：

```python
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_storage_dir():
    """创建临时存储目录，测试后自动清理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_memory_dir(temp_storage_dir):
    """创建临时近端记忆目录"""
    memory_dir = temp_storage_dir / "memory"
    memory_dir.mkdir()
    return memory_dir


@pytest.fixture
def temp_core_memory_dir(temp_storage_dir):
    """创建临时核心记忆目录，包含默认文件"""
    core_dir = temp_storage_dir / "core_memory"
    core_dir.mkdir()
    # 创建默认核心记忆文件
    (core_dir / "SOUL.md").write_text("# Soul\n")
    (core_dir / "IDENTITY.md").write_text("# Identity\n")
    (core_dir / "USER.md").write_text("# User\n")
    (core_dir / "MEMORY.md").write_text("# Memory\n")
    (core_dir / "AGENTS.md").write_text("# Agents\n")
    (core_dir / "SKILLS_SNAPSHOT.md").write_text("# Skills\n")
    return core_dir


@pytest.fixture
def temp_sessions_dir(temp_storage_dir):
    """创建临时会话目录"""
    sessions_dir = temp_storage_dir / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "current").mkdir()
    (sessions_dir / "archive").mkdir()
    return sessions_dir


@pytest.fixture
def sample_config(temp_storage_dir):
    """创建测试用配置"""
    from backend.config.models import Settings, LLMConfig

    return Settings(
        storage={"base_path": str(temp_storage_dir)},
        llm={"default": LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-6",
            api_key="test-api-key"
        )}
    )


@pytest.fixture
def mock_docker_client(mocker):
    """Mock Docker 客户端"""
    mock_client = mocker.MagicMock()
    mocker.patch('docker.from_env', return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_llm_response(mocker):
    """Mock LLM API 响应"""
    mock_response = mocker.MagicMock()
    mock_response.content = "这是测试响应"
    mocker.patch('langchain_openai.ChatOpenAI.invoke', return_value=mock_response)
    return mock_response
```

**API 测试 Fixtures（tests/api/conftest.py）**：

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(sample_config):
    """创建测试客户端"""
    from backend.api.main import create_app

    app = create_app(config=sample_config)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_session_key(test_client):
    """创建测试会话并返回 session_key"""
    response = test_client.post(
        "/api/sessions",
        json={"session_key": "test-session"}
    )
    return response.json()["session_key"]
```

## 12. FastAPI 接口设计

### 12.1 设计概述

SmartClaw 采用前后端分离架构，后端通过 FastAPI 提供 RESTful API 和 SSE 流式响应接口，支持 Web 前端和 CLI 前端的交互。

**设计决策**：

| 决策项 | 选择 | 说明 |
|-------|------|------|
| 流式响应方案 | **SSE** | Server-Sent Events，单向流，实现简单，适合 AI 响应场景 |
| 认证机制 | **不需要** | 个人电脑场景，无需认证 |
| 请求限流 | **不需要** | 单用户场景，无需限流 |

### 12.2 消息生命周期

当用户在前端发送一条消息后，整个消息的生命周期如下：

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              消息生命周期流程图                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

前端                                      后端                                    存储
 │                                          │                                      │
 │  1. 用户输入消息                          │                                      │
 │     点击发送                              │                                      │
 │         │                                 │                                      │
 │         ▼                                 │                                      │
 │  2. 生成/获取 session_key                 │                                      │
 │     (localStorage)                        │                                      │
 │         │                                 │                                      │
 │         │  POST /api/messages/stream      │                                      │
 │         │  {session_key, message}         │                                      │
 │         └────────────────────────────────►│                                      │
 │                                           │                                      │
 │                              3. 验证 session_key                      │
 │                                 │             │                                      │
 │                                 ▼             │                                      │
 │                              4. 查询 sessions.json                    │
 │                                 │             │─────────────────────────────────────►│
 │                                 │             │◄─────────────────────────────────────│
 │                                 │             │    返回 session_id 或创建新会话        │
 │                                 ▼             │                                      │
 │                              5. 加载 System Prompt                    │
 │                                 │             │                                      │
 │                                 │             │─────────────────────────────────────►│
 │                                 │             │    读取 core_memory/*.md              │
 │                                 │             │◄─────────────────────────────────────│
 │                                 │             │    读取 memory/YYYY-MM-DD.md          │
 │                                 ▼             │                                      │
 │                              6. 构建 Agent 输入                       │
 │                                 │             │                                      │
 │                                 │  System Prompt                        │
 │                                 │  + 历史消息                            │
 │                                 │  + 用户消息                            │
 │                                 ▼             │                                      │
 │                              7. 调用 LLM API                          │
 │                                 │             │                                      │
 │                                 │             │─────────► LLM Provider               │
 │                                 │             │◄───────── 流式返回                    │
 │                                 ▼             │                                      │
 │                              8. 处理工具调用（可选）                   │
 │                                 │             │                                      │
 │                                 │  如需调用工具：                        │
 │                                 │  - terminal/python_repl               │
 │                                 │  - read_file/write_file               │
 │                                 │  - write_near_memory                  │
 │                                 │  - write_core_memory                  │
 │                                 │  - search_memory                      │
 │                                 │             │                                      │
 │                                 │             │─────────────────────────────────────►│
 │                                 │             │    执行工具操作                        │
 │                                 │             │◄─────────────────────────────────────│
 │                                 │             │    返回结果                            │
 │                                 ▼             │                                      │
 │                              9. 流式返回响应                          │
 │                                 │             │                                      │
 │         SSE: data: {"content": "好的"}     │                                      │
 │         SSE: data: {"content": "，"}       │                                      │
 │         SSE: data: {"content": "我来"}     │                                      │
 │         ◄─────────────────────────────────│                                      │
 │         ...                               │                                      │
 │         SSE: data: [DONE]                  │                                      │
 │                                           │                                      │
 │                              10. 写入会话文件                         │
 │                                 │             │                                      │
 │                                 │             │─────────────────────────────────────►│
 │                                 │             │    更新 sessions/current/{id}.md     │
 │                                 │             │    追加用户消息和助手响应              │
 │                                 │             │                                      │
 │                              11. 检查预压缩冲刷                       │
 │                                 │             │                                      │
 │                                 │  if token_count > threshold:          │
 │                                 │    - 触发冲刷                          │
 │                                 │    - 写入近端记忆                      │
 │                                 │    - 压缩历史                          │
 │                                 │             │─────────────────────────────────────►│
 │                                 │             │    写入 memory/YYYY-MM-DD.md         │
 │                                           │                                      │
 │  12. 渲染完整消息                         │                                      │
 │      更新 UI                              │                                      │
 │                                          │                                      │
```

**各阶段说明**：

| 阶段 | 步骤 | 操作 | 说明 |
|-----|------|------|------|
| 请求发起 | 1-3 | 前端处理 | 用户输入、获取 session_key、发送请求 |
| 会话处理 | 4-6 | 后端 API 层 | 验证会话、加载 System Prompt、构建输入 |
| Agent 处理 | 7-9 | 核心模块 | 调用 LLM、工具调用、流式返回 |
| 后处理 | 10-11 | 存储层 | 写入会话文件、预压缩检查 |
| 渲染完成 | 12 | 前端处理 | 渲染消息、更新 UI |

### 12.3 API 路由结构

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

### 12.4 API 端点规范

#### 12.4.1 会话管理 API (`/api/sessions`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| POST | `/api/sessions` | 创建或获取会话 | `{session_key}` | `SessionInfo` |
| GET | `/api/sessions/{session_key}` | 获取会话信息 | - | `SessionInfo` |
| GET | `/api/sessions` | 列出所有会话 | - | `List[SessionInfo]` |
| POST | `/api/sessions/{session_key}/archive` | 归档会话 | - | `SuccessResponse` |
| DELETE | `/api/sessions/{session_key}` | 关闭并删除会话 | - | `SuccessResponse` |

#### 12.4.2 消息处理 API (`/api/messages`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| POST | `/api/messages` | 发送消息（同步响应） | `SendMessageRequest` | `MessageResponse` |
| POST | `/api/messages/stream` | 发送消息（SSE 流式） | `SendMessageRequest` | SSE 流 |
| GET | `/api/messages/{session_key}/history` | 获取消息历史 | - | `List[Message]` |

#### 12.4.3 记忆管理 API (`/api/memory`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| GET | `/api/memory/core` | 获取所有核心记忆 | - | `Dict[str, str]` |
| GET | `/api/memory/core/{file_key}` | 获取指定核心记忆 | - | `{content}` |
| PUT | `/api/memory/core/{file_key}` | 写入核心记忆 | `WriteCoreRequest` | `SuccessResponse` |
| GET | `/api/memory/near` | 获取近端记忆 | `?days=N` | `List[NearMemoryEntry]` |
| POST | `/api/memory/near` | 写入近端记忆 | `WriteNearRequest` | `SuccessResponse` |

#### 12.4.4 RAG 检索 API (`/api/search`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| POST | `/api/search` | 搜索长期记忆 | `SearchRequest` | `SearchResponse` |
| POST | `/api/search/index/rebuild` | 重建索引 | - | `SuccessResponse` |

#### 12.4.5 技能管理 API (`/api/skills`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| GET | `/api/skills` | 获取技能列表 | - | `List[SkillInfo]` |
| GET | `/api/skills/{skill_name}` | 获取技能详情 | - | `SkillInfo` |

#### 12.4.6 健康检查 API (`/api/health`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|-----|------|------|--------|------|
| GET | `/api/health` | 健康检查 | - | `HealthStatus` |

### 12.5 数据模型定义

#### 12.5.1 请求模型

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

#### 12.5.2 响应模型

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

### 12.6 SSE 流式响应

#### 12.6.1 请求格式

```http
POST /api/messages/stream
Content-Type: application/json

{
  "session_key": "client_abc123",
  "message": "帮我写一个 Python 脚本"
}
```

#### 12.6.2 响应格式

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

#### 12.6.3 实现代码

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

### 12.7 FastAPI 应用入口

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

### 12.8 依赖注入

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

### 12.9 异常处理

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

### 12.10 错误处理路径

| 错误场景 | HTTP 状态码 | 处理方式 |
|---------|------------|---------|
| session_key 无效 | 200 | 自动创建新会话 |
| LLM API 超时 | 500 | 重试 3 次，返回错误信息 |
| 工具执行失败 | 200 | 返回错误信息给 Agent，让 Agent 决定如何处理 |
| 文件写入失败 | 500 | 重试 3 次，记录日志 |
| 请求参数验证失败 | 422 | 返回详细验证错误 |
| 配置错误 | 500 | 返回配置错误信息 |

### 12.11 启动与测试

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

