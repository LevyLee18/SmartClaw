# 模块 A：基础设施与配置

## 1. 配置模块

### 1.1 设计原则

1. **统一配置源**：所有模块配置集中管理，避免配置分散
2. **层级结构**：配置项按模块层级组织，便于维护和理解
3. **环境变量支持**：敏感信息通过环境变量注入，支持 `.env` 文件
4. **配置验证**：使用 Pydantic 进行配置验证，启动时检查配置有效性
5. **不可变配置**：配置在启动时加载，运行时不可修改

### 1.2 配置文件结构

配置文件位于 `~/.smartclaw/config.yaml`，采用 YAML 格式。

**主要配置区域**：

```yaml
# 存储配置
storage:
  base_path: "~/.smartclaw"

# LLM 模型配置
llm:
  default:
    provider: "anthropic"  # anthropic / openai / qwen / ollama / vllm
    model: "claude-sonnet-4-20250514"
    api_key: "${ANTHROPIC_API_KEY}"
    max_tokens: 4096
    temperature: 0.7
  rag:
    provider: "openai"
    model: "gpt-4o-mini"
    api_key: "${OPENAI_API_KEY}"
    max_tokens: 1000
    temperature: 0.3

# Embedding 模型配置
embedding:
  provider: "openai"
  model: "text-embedding-3-small"
  api_key: "${OPENAI_API_KEY}"
  dimensions: 1536

# Agent 配置
agent:
  session:
    token_threshold: 3000
    flush_ratio: 0.5
    max_session_messages: 100
  system_prompt:
    max_tokens: 30000
    near_memory_days: 2

# Memory 模块配置
memory:
  base_path: "${storage.base_path}"
  near_memory:
    days: 2
    pre_compress_threshold: 3000
    flush_ratio: 0.5
  core_memory:
    max_tokens: 30000
    files: ["soul", "identity", "user", "memory", "agents", "skills_snapshot"]
  session:
    compression_threshold: 8000
    summary_ratio: 0.2

# RAG 模块配置
rag:
  index_path: "${storage.base_path}/store/memory"
  vector_store:
    provider: "chroma"
    path: "${storage.base_path}/store/chroma"
  bm25:
    path: "${storage.base_path}/store/bm25"
  chunk_size: 1024
  chunk_overlap: 100
  top_k: 5
  generate_queries: 3
  retrieval:
    rrf:
      k: 60
      rank_discount: 0.5
      vector_weight: 0.5
      bm25_weight: 0.5
    fusion_mode: "reciprocal_rank"
  watch:
    dir: "sessions/archive"
    debounce_seconds: 2

# 内置工具配置
tools:
  root_dir: "./workspace"
  terminal:
    image: "alpine:3.19"
    memory_limit: "256m"
    cpu_limit: "0.25"
    user_uid: 1000
    auto_restart: true
    max_retries: 3
    retry_backoff: [1, 2, 4]
    output_limit: 1048576
  python_repl:
    image: "python:3.11-slim"
    memory_limit: "512m"
    cpu_limit: "0.25"
    execution_timeout: 30
    preinstalled_packages: ["pandas", "numpy", "requests", "matplotlib", "beautifulsoup4"]
  fetch_url:
    timeout: 30
    max_retries: 3
  file_ops:
    allowed_extensions: ["md", "txt", "py", "js", "json", "yaml", "yml", "toml", "xml", "html", "css"]

# Skills 配置
skills:
  directory: "${storage.base_path}/skills"
  snapshot_file: "${storage.base_path}/store/core/SKILLS_SNAPSHOT.md"
  watch_debounce: 2

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "${storage.base_path}/logs/smartclaw.log"
  max_size: "10MB"
  backup_count: 5
  modules:
    agent: "INFO"
    memory: "INFO"
    rag: "INFO"
    tools: "INFO"
    container: "WARNING"
```

### 1.3 配置管理接口

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

    @field_validator("storage_base_path", "tools_root_dir", mode="before")
    @classmethod
    def expand_path(cls, v):
        """展开路径中的 ~ 和环境变量"""
        if isinstance(v, str):
            v = os.path.expandvars(v)
        return Path(v).expanduser()


class ConfigManager:
    """配置管理器（单例模式）"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, key: str, default=None):
        """获取配置项（支持点分路径如 'agent.session.token_threshold'）"""
        return self._get_nested_value(self._config, key) or default

    def get_config(self) -> dict:
        """获取完整配置"""
        return self._config.copy()


def get_config() -> dict:
    """全局配置获取函数"""
    return ConfigManager().get_config()
```

### 1.4 配置访问示例

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

### 1.5 环境变量支持

**环境变量文件 (.env)**：
```bash
# ~/.smartclaw/.env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SMARTCLAW_HOME=~/.smartclaw
SMARTCLAW_LOG_LEVEL=INFO
DOCKER_HOST=unix:///var/run/docker.sock
```

**配置加载优先级（从高到低）**：
1. 环境变量（直接设置）
2. .env 文件
3. config.yaml
4. 代码默认值

### 1.6 配置验证规则

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
        import re
        if not re.match(r"^\d+[mg]?$", v):
            raise ValueError(f"Invalid memory format: {v}")
        return v
```

### 1.7 关键配置项索引

| 配置路径 | 说明 | 默认值 |
|---------|------|--------|
| `storage.base_path` | 存储根目录 | `~/.smartclaw` |
| `llm.default.provider` | 默认 LLM 提供商 | `anthropic` |
| `llm.default.model` | 默认模型 | `claude-sonnet-4-20250514` |
| `llm.default.max_tokens` | 最大输出 token | `4096` |
| `embedding.provider` | Embedding 提供商 | `openai` |
| `embedding.model` | Embedding 模型 | `text-embedding-3-small` |
| `agent.session.token_threshold` | 预压缩阈值 | `3000` |
| `agent.session.flush_ratio` | 冲刷比例 | `0.5` |
| `memory.near_memory.days` | 近端记忆天数 | `2` |
| `memory.core_memory.max_tokens` | 核心记忆最大 token | `30000` |
| `rag.top_k` | 检索返回数量 | `5` |
| `rag.chunk_size` | 分块大小 | `1024` |
| `rag.retrieval.rrf.k` | RRF 参数 | `60` |
| `tools.terminal.memory_limit` | Terminal 容器内存 | `256m` |
| `tools.python_repl.memory_limit` | Python REPL 容器内存 | `512m` |
| `logging.level` | 日志级别 | `INFO` |

---

## 2. 日志模块

### 2.1 设计目标

1. **分级记录**：根据重要程度区分日志级别，便于筛选和过滤
2. **模块隔离**：各模块拥有独立的日志命名空间，便于定位问题来源
3. **结构化输出**：统一日志格式，包含时间戳、模块名、级别和详细信息
4. **持久化存储**：支持日志轮转和归档，避免日志文件无限增长
5. **性能友好**：异步写入机制，不影响主流程性能

### 2.2 日志级别与使用场景

| 级别 | 含义 | 使用场景 |
|-----|------|---------|
| **DEBUG** | 调试信息 | 开发阶段追踪详细执行流程，生产环境默认关闭 |
| **INFO** | 常规信息 | 记录关键操作完成状态，如会话创建、工具调用、记忆写入 |
| **WARNING** | 警告信息 | 非预期但可恢复的情况，如配置使用默认值、容器重启重试 |
| **ERROR** | 错误信息 | 影响功能但系统可继续运行，如工具调用失败、LLM 请求超时 |
| **CRITICAL** | 严重错误 | 导致系统无法继续运行，如配置加载失败、核心模块初始化失败 |

### 2.3 日志格式规范

```
{时间戳} - {模块名} - {级别} - {消息内容}
```

**格式说明**：
- **时间戳**：ISO 8601 格式（`YYYY-MM-DD HH:MM:SS,mmm`），精确到毫秒
- **模块名**：采用点分命名（如 `smartclaw.agent.session`）
- **级别**：大写英文（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- **消息内容**：人类可读的描述性文本

**示例输出**：
```
2026-03-18 14:30:15,123 - smartclaw.agent - INFO - Session created: session_abc123
2026-03-18 14:30:18,456 - smartclaw.tools.terminal - INFO - Tool invoked: terminal, command="ls -la"
2026-03-18 14:30:18,789 - smartclaw.tools.terminal - INFO - Tool completed: terminal, duration=333ms
2026-03-18 14:30:25,012 - smartclaw.memory - WARNING - Memory write retry: attempt 1/2
2026-03-18 14:30:32,345 - smartclaw.rag - ERROR - Index update failed: LLM timeout after 30s
```

### 2.4 模块日志命名空间

- `smartclaw.agent`：Agent 主模块
- `smartclaw.agent.session`：会话管理子模块
- `smartclaw.tools`：工具模块
- `smartclaw.tools.terminal`：Terminal 工具子模块
- `smartclaw.tools.python_repl`：Python REPL 子模块
- `smartclaw.memory`：Memory 模块
- `smartclaw.rag`：RAG 模块
- `smartclaw.container`：容器管理模块

### 2.5 日志存储与轮转

**存储位置**：`{storage.base_path}/logs/`

```
~/.smartclaw/logs/
├── smartclaw.log          # 主日志文件
├── smartclaw.log.1        # 轮转备份 1
├── smartclaw.log.2        # 轮转备份 2
├── container_crashes.log  # 容器崩溃专用日志
└── archive/               # 归档日志目录
    └── smartclaw-2026-03.log.gz
```

**轮转策略**：
- 单个日志文件最大 10MB
- 保留最近 5 个备份文件
- 每月将轮转备份压缩归档
- 归档文件保留 12 个月

### 2.6 敏感信息处理

**脱敏规则**：
- API Key：记录前 4 位和后 4 位，中间用 `****` 替换（如 `sk-a****1234`）
- 用户数据：命令参数中的密码、密钥等使用 `[REDACTED]` 替换
- 文件内容：仅记录内容长度，不记录实际内容
- URL 参数：移除敏感查询参数（如 `token=`, `key=`, `password=`）

### 2.7 日志访问接口

```python
from smartclaw.logging import get_logger

logger = get_logger(__name__)  # 使用模块名自动命名
logger.info("Operation completed", extra={"duration_ms": 150})
```

**结构化日志字段**：

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

### 2.8 模块级别覆盖配置

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

**运行时调整**：
```bash
export SMARTCLAW_LOG_LEVEL=DEBUG
export SMARTCLAW_LOG_MODULE_AGENT=DEBUG
```

---

## 3. 错误类型

### 3.1 基础错误类型

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

### 3.2 错误信息规范

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

### 3.3 错误分类与处理策略

#### 按严重程度分类

**致命错误（Fatal）**：
- 导致系统无法启动或无法继续运行
- 示例：配置文件损坏、核心模块初始化失败、Docker 服务不可用
- 处理：记录详细日志，显示用户友好提示，终止程序

**严重错误（Critical）**：
- 核心功能不可用，但系统可继续运行
- 示例：LLM API 密钥无效、数据库连接失败、索引完全损坏
- 处理：记录错误，通知用户，尝试自动恢复或进入降级模式

**一般错误（Error）**：
- 单个操作失败，不影响系统整体运行
- 示例：工具调用超时、文件读取失败、单个检索失败
- 处理：返回错误信息给用户，记录日志，提供重试选项

**警告（Warning）**：
- 非预期情况，但不影响当前操作
- 示例：配置使用默认值、容器需要重启、索引轻微不一致
- 处理：记录日志，不中断用户操作

#### 按错误来源分类

| 来源 | 典型错误 | 恢复策略 |
|-----|---------|---------|
| 配置系统 | 配置缺失、格式错误、验证失败 | 使用默认值或终止启动 |
| LLM 调用 | 超时、API 错误、配额耗尽 | 重试机制、降级模型 |
| 容器系统 | 创建失败、崩溃、资源超限 | 自动重启、指数退避 |
| 文件系统 | 权限不足、磁盘满、文件损坏 | 记录错误、提示用户 |
| 记忆系统 | 写入失败、读取失败、格式错误 | 重试机制、跳过损坏文件 |
| RAG 系统 | 索引损坏、检索失败、LLM 调用失败 | 重建索引、降级检索 |

### 3.4 容器错误处理

#### 容器崩溃检测

常见退出码：
- 137：OOM Killed（内存超限）
- 139：Segmentation Fault
- 1：应用错误
- 0：正常退出（非崩溃）

#### 自动重启机制

- 最大重试次数：3 次
- 退避策略：指数退避（1秒、2秒、4秒）
- 重启条件：非正常退出且未超过最大重试次数
- 放弃条件：连续 3 次重启后仍崩溃
