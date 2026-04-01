# 模块 A：基础设施与配置

## 0. 依赖管理

### 0.1 使用 uv 进行依赖管理

SmartClaw 使用 uv 作为包管理器，所有依赖定义在 pyproject.toml 中。

| 文件 | 用途 | 说明 |
|-----|------|------|
| `pyproject.toml` | 项目配置和依赖 | 包含所有生产依赖和开发依赖 |
| `uv.lock` | 依赖锁定文件 | 确保依赖版本一致性（需加入版本控制） |

### 0.2 创建虚拟环境

```bash
# 创建虚拟环境（使用 uv）
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### 0.3 安装依赖

```bash
# 安装所有依赖（包括开发依赖）
uv pip install -e ".[dev]"

# 仅安装生产依赖
uv pip install -e .
```

### 0.4 依赖管理命令

```bash
# 添加新依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 更新依赖锁文件
uv lock --upgrade

# 同步依赖（根据 uv.lock）
uv sync
```

### 0.5 运行测试

```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行测试
pytest

# 或使用 uv run（自动激活环境）
uv run pytest
```

### 0.6 核心依赖清单

**生产依赖**（定义在 `pyproject.toml` 的 `[project.dependencies]`）：

| 依赖 | 版本 | 用途 |
|-----|------|------|
| pydantic | ≥2.0 | 数据验证和配置管理 |
| pydantic-settings | ≥2.0 | 环境变量和配置加载 |
| pyyaml | ≥6.0 | YAML 配置解析 |
| langchain | ≥1.0.0 | LLM 应用框架 |
| langgraph | ≥1.0.0 | 状态图工作流 |
| langchain-anthropic | latest | Anthropic LLM 集成 |
| langchain-openai | latest | OpenAI LLM 集成 |
| llama-index-core | latest | RAG 核心组件 |
| llama-index-embeddings-openai | latest | OpenAI Embedding |
| llama-index-vector-stores-chroma | latest | Chroma 向量存储 |
| fastapi | ≥0.109.0 | Web 框架 |
| uvicorn | ≥0.27.0 | ASGI 服务器 |
| chromadb | ≥0.4.0 | 向量数据库 |
| docker | ≥7.0.0 | Docker SDK |
| watchdog | ≥4.0.0 | 文件监听 |

**开发依赖**（定义在 `pyproject.toml` 的 `[project.optional-dependencies.dev]`）：

| 依赖 | 版本 | 用途 |
|-----|------|------|
| pytest | ≥8.0 | 测试框架 |
| pytest-mock | ≥3.12 | Mock 工具 |
| pytest-asyncio | ≥0.23 | 异步测试 |
| mypy | ≥1.8 | 类型检查 |
| ruff | ≥0.2.0 | 代码检查和格式化 |
| coverage | ≥7.4 | 测试覆盖率 |

### 0.7 项目目录结构

#### 源代码目录结构

```
smartclaw/                      # 项目根目录
├── backend/                    # 后端源代码
│   ├── __init__.py
│   ├── config/                 # 配置模块
│   │   ├── __init__.py
│   │   ├── models.py           # 配置数据模型（LLMConfig, ContainerConfig, Settings）
│   │   └── manager.py          # ConfigManager 实现
│   ├── memory/                 # Memory 模块
│   │   ├── __init__.py
│   │   ├── base.py             # MemoryManager 抽象基类
│   │   ├── near.py             # NearMemoryManager
│   │   ├── core.py             # CoreMemoryManager
│   │   └── session.py          # SessionManager
│   ├── rag/                    # RAG 模块
│   │   ├── __init__.py
│   │   ├── base.py             # IndexManager 抽象基类
│   │   ├── cache.py            # SQLiteCache
│   │   ├── manager.py          # MemoryIndexManager
│   │   └── watcher.py          # FileWatcher
│   ├── tools/                  # 内置工具模块
│   │   ├── __init__.py
│   │   ├── security.py         # SecurityChecker
│   │   ├── container.py        # ContainerManager
│   │   └── registry.py         # ToolRegistry
│   ├── agent/                  # Agent 模块
│   │   ├── __init__.py
│   │   ├── prompt.py           # SystemPromptBuilder
│   │   ├── graph.py            # AgentGraph
│   │   └── agent.py            # SmartClawAgent
│   ├── api/                    # FastAPI 接口
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 应用入口
│   │   ├── routers/            # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py
│   │   │   ├── messages.py
│   │   │   ├── memory.py
│   │   │   ├── search.py
│   │   │   └── health.py
│   │   ├── models/             # 请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   └── exceptions.py       # API 异常处理
│   ├── errors/                 # 错误类型定义
│   │   ├── __init__.py
│   │   └── base.py             # SmartClawError 及子类
│   ├── logging/                # 日志模块
│   │   ├── __init__.py
│   │   └── formatter.py        # 日志格式化
│   └── init.py                 # 初始化脚本
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures
│   ├── unit/                   # 单元测试
│   │   ├── config/
│   │   ├── memory/
│   │   ├── rag/
│   │   ├── tools/
│   │   ├── agent/
│   │   └── api/
│   ├── api/                    # API 端点测试
│   ├── integration/            # 集成测试
│   ├── e2e/                    # 端到端测试
│   └── boundary/               # 边界条件测试
│
├── pyproject.toml              # 项目配置
├── uv.lock                     # 依赖锁定
├── .env.example                # 环境变量模板
└── README.md
```

#### 用户数据目录结构

```
~/.smartclaw/                   # 用户数据目录
├── config.yaml                 # 用户配置文件
├── .env                        # 环境变量（API Key）
│
├── store/                      # 数据存储
│   ├── core_memory/            # 核心记忆文件
│   │   ├── SOUL.md             # 灵魂设定
│   │   ├── IDENTITY.md         # 身份定义
│   │   ├── USER.md             # 用户画像
│   │   ├── MEMORY.md           # 重要记忆
│   │   ├── AGENTS.md           # Agent 配置（只读）
│   │   └── SKILLS_SNAPSHOT.md  # 技能快照（只读）
│   │
│   ├── memory/                 # 近端记忆（按日期）
│   │   └── 2026-03-23.md
│   │
│   └── rag/                    # RAG 索引
│       └── memory/             # 记忆知识库
│           ├── chroma/         # Chroma 向量索引
│           └── docstore/       # 文档存储
│
├── sessions/                   # 会话目录
│   ├── sessions.json           # 会话映射表
│   ├── current/                # 当前会话文件
│   └── archive/                # 归档会话
│
├── logs/                       # 日志文件
│   ├── smartclaw.log           # 主日志
│   ├── smartclaw.log.1         # 轮转备份
│   └── container_crashes.log   # 容器崩溃日志
│
└── skills/                     # 技能目录
```

---

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

#### 1.3.1 Settings 类定义

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Optional, List, Dict
import os


class Settings(BaseSettings):
    """SmartClaw 配置管理类

    使用 pydantic-settings 实现配置管理，支持：
    - 从 .env 文件加载环境变量
    - 类型验证和默认值
    - 路径自动展开
    """

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
```

#### 1.3.2 ConfigManager 完整实现

```python
import yaml
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """配置管理器（单例模式）

    负责：
    - 从 config.yaml 加载配置
    - 展开环境变量引用
    - 验证配置有效性
    - 提供点分路径访问
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[dict] = None

    def __new__(cls) -> "ConfigManager":
        """单例模式：确保全局只有一个配置实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化时加载配置"""
        if self._config is None:
            self._config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件

        加载优先级：
        1. ~/.smartclaw/config.yaml（如果存在）
        2. 默认配置（如果配置文件不存在）

        Returns:
            配置字典
        """
        config_path = Path("~/.smartclaw/config.yaml").expanduser()

        if not config_path.exists():
            return self._get_default_config()

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 展开环境变量引用
        config = self._expand_env_vars(config)

        # 验证配置
        self._validate_config(config)

        return config

    def _expand_env_vars(self, config: Any) -> Any:
        """递归展开配置中的环境变量引用

        支持两种格式：
        - ${VAR_NAME}：直接引用环境变量
        - ${storage.base_path}：引用配置中的嵌套值

        Args:
            config: 配置值（可以是 dict、list、str 或其他类型）

        Returns:
            展开后的配置值
        """
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
        """解析嵌套配置引用

        将 ${storage.base_path} 解析为 config["storage"]["base_path"] 的值

        Args:
            ref: 点分格式的引用路径（如 "storage.base_path"）

        Returns:
            解析后的值（字符串格式）
        """
        keys = ref.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return ""
        return str(value)

    def _validate_config(self, config: dict) -> None:
        """验证配置有效性

        检查：
        - 必需的配置项是否存在
        - 数值范围是否合法
        - 依赖关系是否满足

        Args:
            config: 配置字典

        Raises:
            ValueError: 配置验证失败时抛出
        """
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
            raise ValueError("Config validation failed:\n" + "\n".join(errors))

    def _get_nested_value(self, config: dict, key: str) -> Any:
        """获取嵌套配置值

        支持点分路径访问，如 "llm.default.model"

        Args:
            config: 配置字典
            key: 点分格式的键（如 "llm.default.model"）

        Returns:
            配置值，如果不存在返回 None
        """
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        支持点分路径访问，如 "agent.session.token_threshold"

        Args:
            key: 点分格式的键
            default: 默认值（如果配置项不存在）

        Returns:
            配置值或默认值
        """
        return self._get_nested_value(self._config, key) or default

    def get_config(self) -> dict:
        """获取完整配置

        Returns:
            配置字典的副本
        """
        return self._config.copy() if self._config else {}

    def _get_default_config(self) -> dict:
        """获取默认配置

        Returns:
            默认配置字典
        """
        return DEFAULT_CONFIG.copy()


def get_config() -> dict:
    """全局配置获取函数

    Returns:
        完整配置字典
    """
    return ConfigManager().get_config()
```

#### 1.3.3 默认配置模板

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
        },
        "rag": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "${OPENAI_API_KEY}",
            "max_tokens": 1000,
            "temperature": 0.3
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
        },
        "system_prompt": {
            "max_tokens": 30000,
            "near_memory_days": 2
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


def init_default_config() -> None:
    """初始化默认配置文件

    如果配置文件不存在，则创建默认配置文件。
    """
    config_path = Path("~/.smartclaw/config.yaml").expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True)
        print(f"Created default config at {config_path}")
```

#### 1.3.4 依赖关系验证

```python
from typing import List
import subprocess


def validate_config_dependencies(config: dict) -> List[str]:
    """验证配置项之间的依赖关系

    检查：
    - RAG 模块需要 LLM 和 Embedding 配置
    - Docker 工具需要 Docker 环境可用

    Args:
        config: 配置字典

    Returns:
        警告消息列表（不阻止启动，仅提示）
    """
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
            try:
                subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                warnings.append(f"Tool '{tool}' requires Docker to be running")
                break  # 只提示一次

    return warnings
```

#### 1.3.5 配置热更新说明

**重要**：SmartClaw **不支持运行时配置热更新**。

- **原因**：配置涉及 LLM 客户端、Docker 容器、向量存储等资源，运行时修改可能导致不一致
- **修改配置后**：需要重启服务才能生效
- **动态调整**：部分参数（如 `top_k`）可通过 Agent 工具参数在调用时覆盖

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

### 1.8 初始化与环境配置

#### 1.8.1 初始化用户数据目录

首次使用 SmartClaw 时，需要初始化用户数据目录。调用 `backend.init.initialize_storage()` 函数：

```python
# backend/init.py
from pathlib import Path
from typing import List

# 默认存储路径
DEFAULT_BASE_PATH = Path.home() / ".smartclaw"

# 需要创建的子目录列表
REQUIRED_DIRS: List[str] = [
    "store/core_memory",
    "store/memory",
    "store/rag",
    "sessions",
    "sessions/archive",
    "logs",
    "skills",
]

# 核心记忆文件列表
CORE_MEMORY_FILES: List[str] = [
    "SOUL.md",
    "IDENTITY.md",
    "USER.md",
    "MEMORY.md",
    "AGENTS.md",
    "SKILLS_SNAPSHOT.md",
]


def initialize_storage(base_path: Path | None = None) -> dict:
    """初始化 SmartClaw 存储目录结构

    Args:
        base_path: 存储根目录，默认为 ~/.smartclaw

    Returns:
        初始化结果字典，包含 success, created_dirs, created_files, errors
    """
    if base_path is None:
        base_path = DEFAULT_BASE_PATH

    result = {
        "success": True,
        "created_dirs": [],
        "created_files": [],
        "errors": [],
    }

    # 创建基础目录和所有子目录
    # 创建默认的核心记忆文件
    # 创建默认的 sessions.json
    # ... 详细实现见 backend/init.py

    return result


def is_initialized(base_path: Path | None = None) -> bool:
    """检查存储目录是否已初始化

    Args:
        base_path: 存储根目录，默认为 ~/.smartclaw

    Returns:
        True 如果已初始化，False 否则
    """
    # 检查基础目录和关键子目录是否存在
    ...
```

**命令行初始化**：

```bash
# 方式 1：直接运行模块
python -m backend.init

# 方式 2：在代码中调用
from backend.init import initialize_storage, is_initialized

if not is_initialized():
    result = initialize_storage()
    print(result)
```

#### 1.8.2 环境变量模板文件

项目根目录下的 `.env.example` 文件模板：

```bash
# .env.example
# SmartClaw 环境变量配置模板
# 复制此文件到 ~/.smartclaw/.env 并填入真实值

# ============================================
# API Keys（必需）
# ============================================
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# ============================================
# 存储路径（可选覆盖）
# ============================================
SMARTCLAW_HOME=~/.smartclaw

# ============================================
# 日志配置（可选覆盖）
# ============================================
SMARTCLAW_LOG_LEVEL=INFO

# ============================================
# Docker 配置（可选）
# ============================================
DOCKER_HOST=unix:///var/run/docker.sock
```

#### 1.8.3 API Key 配置步骤

**⚠️ 重要**：完成环境配置后，需要填入真实的 API Key：

```bash
# 1. 复制模板文件
cp .env.example ~/.smartclaw/.env

# 2. 编辑文件，填入真实密钥
nano ~/.smartclaw/.env

# 3. 设置文件权限（仅当前用户可读写）
chmod 600 ~/.smartclaw/.env
```

**配置示例**：

```bash
# ~/.smartclaw/.env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-proj-xxxxx
```

**注意事项**：
- 后续涉及 LLM 调用的测试和开发将依赖这些密钥
- 不要将包含真实密钥的 `.env` 文件提交到版本控制
- `.gitignore` 已配置忽略 `.env` 文件

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
