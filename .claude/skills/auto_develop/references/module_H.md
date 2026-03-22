# 模块 H：初始化与启动

## 1. 初始化流程

### 1.1 首次启动算法

**初始化命令**：
```bash
python -m backend.init
```

**首次启动时系统自动执行**：
1. 创建用户数据目录结构
2. 生成默认配置文件 `config.yaml`
3. 创建核心记忆文件默认模板
4. 初始化会话映射表 `sessions.json`

### 1.2 依赖清单

**环境要求**：

| 依赖 | 版本要求 | 说明 |
|-----|---------|------|
| Python | >= 3.11 | 使用最新稳定版 |
| Docker | >= 24.0 | 容器隔离必需 |
| Git | >= 2.30 | 版本控制 |
| pip | >= 23.0 | 包管理器 |

**依赖文件**：
- `requirements.txt` - 生产依赖
- `requirements-dev.txt` - 开发依赖

### 1.3 环境变量

**环境变量文件 (.env)**：
```bash
# ~/.smartclaw/.env
# SmartClaw 环境变量配置

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 可选配置
SMARTCLAW_LOG_LEVEL=INFO
SMARTCLAW_LLM_DEFAULT_MODEL=claude-sonnet-4-20250514

# Docker 配置（可选）
DOCKER_HOST=unix:///var/run/docker.sock
```

**环境变量优先级**（从高到低）：
1. **环境变量**：直接设置的环境变量
2. **.env 文件**：从 `.env` 文件加载的环境变量
3. **config.yaml**：YAML 配置文件中的值
4. **默认值**：代码中的默认值

**环境变量命名规则**：
```bash
# {MODULE}_{SECTION}_{KEY} 格式
SMARTCLAW_LLM_DEFAULT_MODEL=gpt-4
SMARTCLAW_RAG_TOP_K=10
SMARTCLAW_TOOLS_TERMINAL_MEMORY_LIMIT=512m
```

**配置文件中引用环境变量**：
```yaml
llm:
  default:
    api_key: "${ANTHROPIC_API_KEY}"  # 从环境变量读取
```

---

## 2. 目录创建

### 2.1 用户数据目录结构

**根目录**：`~/.smartclaw/`

```
~/.smartclaw/                       # 用户数据根目录
├── store/                          # 存储目录
│   ├── core_memory/                # 核心记忆文件
│   │   ├── SOUL.md
│   │   ├── IDENTITY.md
│   │   ├── USER.md
│   │   ├── MEMORY.md
│   │   ├── AGENTS.md
│   │   └── SKILLS_SNAPSHOT.md
│   ├── memory/                     # 近端记忆（按日期）
│   │   └── YYYY-MM-DD.md
│   └── rag/                        # RAG 索引根目录
│       ├── memory/                 # 记忆知识库
│       │   ├── chroma/             # Chroma 向量索引
│       │   ├── bm25/               # BM25 索引
│       │   ├── docstore.json       # 文档存储
│       │   └── cache.db            # SQLite 缓存
│       └── knowledge/              # 外部知识库（预留）
├── sessions/                       # 会话数据
│   ├── sessions.json               # 会话映射表
│   ├── current/                    # 当前会话
│   │   └── {YYYY-MM-DD}-{random}.md
│   └── archive/                    # 归档会话
│       └── {YYYY-MM-DD}-{random}.md
├── skills/                         # 用户自定义技能
├── config.yaml                     # 用户配置
└── .env                            # 环境变量
```

### 2.2 目录用途说明

| 目录 | 用途 | 管理器 |
|-----|------|--------|
| `store/core_memory/` | 核心记忆文件 | `CoreMemoryManager` |
| `store/memory/` | 近端记忆文件 | `NearMemoryManager` |
| `store/rag/memory/` | 记忆知识库索引 | `MemoryIndexManager` |
| `store/rag/knowledge/` | 外部知识库索引 | `KnowledgeIndexManager`（预留） |
| `sessions/sessions.json` | 会话映射表 | `SessionManager` |
| `sessions/current/` | 当前活跃会话 | `SessionManager` |
| `sessions/archive/` | 归档会话 | `SessionManager` |

### 2.3 设计理由

| 考量 | 说明 |
|-----|------|
| 代码与数据分离 | 升级代码不影响用户数据 |
| 多环境支持 | 同一份代码，不同用户独立数据 |
| 备份简单 | 只需备份 `~/.smartclaw/` |
| Git 整洁 | 运行时数据不会污染版本控制 |
| 知识库扩展 | `store/rag/` 下可添加多种知识库类型 |

---

## 3. 默认文件创建

### 3.1 默认配置文件

**首次启动时自动创建** `~/.smartclaw/config.yaml`：

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

### 3.2 核心记忆文件

**文件权限说明**：

| 文件名 | 说明 | 修改权限 |
|-------|------|---------|
| SOUL.md | Agent 人格、语气、边界 | 可修改 |
| IDENTITY.md | Agent 名称、风格、表情 | 可修改 |
| USER.md | 用户画像、称呼方式 | 可修改 |
| MEMORY.md | 用户偏好、决策、长期事项 | 可修改 |
| AGENTS.md | 操作指令、记忆使用规则、内置工具 | 禁止修改 |
| SKILLS_SNAPSHOT.md | 技能快照（XML 格式） | 禁止修改 |

**加载顺序**（严格遵循）：
1. AGENTS.md - Agent 基础定义
2. SKILLS_SNAPSHOT.md - 可用技能列表
3. SOUL.md - 人格与边界
4. IDENTITY.md - 名称与风格
5. USER.md - 用户画像
6. MEMORY.md - 用户偏好与重要决策

### 3.3 核心记忆默认模板

#### SOUL.md 默认模板

```markdown
## 人格（Persona）
- **友好、专业、严谨**：SmartClaw 以一种既友好又专业的语气与用户进行交互。
- **适应性强**：根据用户的需求和情境，SmartClaw 能够调整其回应的语气和内容。

## 语气（Tone）
- **友好而专业**：SmartClaw 的语气始终保持温和、友好，但又不失专业性。
- **正向鼓励**：在协助用户的过程中，SmartClaw 会积极鼓励用户的努力。

## 边界（Boundaries）
- **隐私保护**：SmartClaw 始终尊重用户的隐私。
- **任务范围限制**：SmartClaw 会在其技能范围内提供帮助。
- **道德与法律合规性**：SmartClaw 始终遵循道德规范和法律规定。
- **功能性限制**：某些高风险或危险的操作会受到限制。
```

#### IDENTITY.md 默认模板

```markdown
## 名称（Name）
- **名称**: SmartClaw

## 风格（Vibe）
- **风格**: 技术感与现代感兼具

## 风格特点
- **简洁明了**：界面和交互设计简洁清晰
- **高效且精准**：其行为和响应专注于高效执行任务
- **易于扩展**：风格设计考虑到后期功能的扩展与定制

## 表情（Emoji）
- **表情**: :robot:
```

#### USER.md 默认模板

```markdown
## 用户画像（User Profile）
- **用户类型**: SmartClaw 面向多种类型的用户
- **用户需求**: 用户通常希望通过 SmartClaw 获得高效的知识查询、任务自动化等服务
- **用户习惯**: 用户可能习惯于简洁直接的互动方式
- **用户背景**: 用户的背景可能涉及技术开发、数据科学、项目管理或教育领域等

## 称呼方式（Preferred Addressing）
- **默认称呼**: 对于没有特别要求的用户，使用"您"作为默认称呼
- **个性化称呼**: 如果用户提供了特定的称呼方式，SmartClaw 会根据该称呼进行个性化称呼
```

#### MEMORY.md 默认模板

```markdown
## 用户偏好
- 编程语言：Python、C

## 决策
- 2026-01-15：在**项目中，用户决定使用 SQLite 作为本地向量存储
- 2026-01-16: ...
```

#### AGENTS.md 默认模板

```markdown
## 操作指令（Operating Instructions）
你有一系列的内置工具和一系列的技能，可以用来调用已完成当前用户给你的任务。

### 内置工具 （Core Tools）
- `read_file`：读取本地文件工具
- `write_file`：通用本地文件写入工具
- `terminal`：命令行操作工具
- `python_repl`：Python 代码解释器
- `fetch_url`：网络信息获取工具
- `search_memory`：检索记忆工具
- `search_knowledge`：外部知识库检索工具
- `write_near_memory`：写入近端记忆工具
- `write_core_memory`：写入核心记忆工具

### 技能调用协议（SKILL PROTOCOL）
当你要使用某个技能时，必须严格遵守以下步骤：
1. 使用 `read_file` 工具读取该技能对应的定义文件
2. 仔细阅读文件中的内容、步骤和示例
3. 根据文件中的指示，结合内置工具执行具体任务

## 记忆使用规则（Memory Usage Rules）
- **长期记忆管理**：SmartClaw 遵循"本地优先"的记忆管理原则
- **近端记忆**：记录当天对话中的即时信息、临时性事实和对话摘要
- **核心记忆**：任何用户明确要求或反复强调的长期有效事项

## 优先级（Priorities）
- **安全优先**：SmartClaw 始终将安全放在首位
- **效率优先**：在确保安全的前提下，优先选择高效的任务执行方式
- **用户体验优先**：SmartClaw 始终致力于提供流畅、无缝的交互体验
```

#### SKILLS_SNAPSHOT.md 格式示例

```xml
<available_skills>
    <skill>
        <name>weather</name>
        <description>Get weather information</description>
        <location>/users/user/.smartclaw/skills/weather/SKILL.md</location>
    </skill>
    <skill>
        <name>gemini</name>
        <description>Use Gemini CLI for coding assistance</description>
        <location>/users/user/.smartclaw/skills/gemini/SKILL.md</location>
    </skill>
</available_skills>
```

---

## 4. 启动入口

### 4.1 开发环境搭建步骤

```bash
# 1. 克隆项目
git clone https://github.com/xxx/smartclaw.git
cd smartclaw

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

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

### 4.2 FastAPI 应用入口

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

### 4.3 启动命令

```bash
# 开发模式
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4.4 API 文档访问

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4.5 项目目录结构

```
smartclaw/                      # 项目根目录（源代码）
├── backend/                    # 后端核心代码
│   ├── __init__.py
│   ├── agent/                  # Agent 核心模块
│   ├── memory/                 # Memory 模块
│   ├── rag/                    # RAG 模块
│   ├── tools/                  # 内置工具模块
│   ├── config/                 # 配置模块
│   ├── api/                    # FastAPI 接口模块
│   ├── utils/                  # 工具函数
│   ├── init.py                 # 初始化脚本
│   └── main.py                 # 服务启动入口
├── tests/                      # 测试目录
├── pytest.ini                  # pytest 配置
├── pyproject.toml              # 项目配置
├── config.example.yaml         # 配置文件模板
├── requirements.txt            # 依赖清单
├── requirements-dev.txt        # 开发依赖
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略配置
├── README.md                   # 项目说明
└── LICENSE                     # 许可证
```

---

## 5. 配置项索引

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
| `rag.indexes.memory.index_path` | 记忆知识库索引路径 | `~/.smartclaw/store/rag/memory` |
| `rag.indexes.memory.watch_dir` | 记忆知识库监听目录 | `~/.smartclaw/sessions/archive` |
| `rag.indexes.memory.top_k` | 记忆检索返回数量 | `5` |
| `rag.indexes.memory.chunk_size` | 记忆分块大小 | `1024` |
| `rag.retrieval.rrf.k` | RRF 参数 | `60` |
| `tools.terminal.memory_limit` | Terminal 容器内存 | `256m` |
| `tools.python_repl.memory_limit` | Python REPL 容器内存 | `512m` |
| `skills.watch_debounce` | 技能变更防抖时间 | `2` |
| `logging.level` | 日志级别 | `INFO` |
