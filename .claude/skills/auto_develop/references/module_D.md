# 模块 D：内置工具模块

## 1. 模块概述

内置工具模块的设计核心是为 SmartClaw Agent 提供安全、高效、可控的执行能力。

**设计原则**：
- 独立性：工具之间无依赖，可独立运行
- 安全性：所有操作经过安全检查
- 可控性：支持用户确认和干预
- 容错性：异常情况优雅处理

**工具分类架构**：

| 分类 | 数量 | 特点 | 依赖模块 |
|------|------|------|---------|
| **基础工具** | 5 | 独立运行，无模块依赖 | 无 |
| **记忆工具** | 3 | 依赖 Memory/RAG 模块 | Memory, RAG |

---

## 2. 核心组件

### 2.1 ToolRegistry

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

---

### 2.2 ContainerManager

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

**实现代码**：
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

---

### 2.3 SecurityChecker

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

**实现代码**：
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

---

## 3. 工具列表

### 3.1 基础工具清单（5个）

| 工具名称 | 类型 | 功能描述 | 容器类型 | 实现来源 |
|---------|------|---------|---------|---------|
| terminal | Docker | 命令行操作 | alpine:3.19 | 自研 |
| python_repl | Docker | Python 代码执行 | python:3.11-slim | 自研 |
| fetch_url | LangChain | 网页内容获取 | - | RequestsGetTool |
| read_file | LangChain | 文件读取 | - | ReadFileTool |
| write_file | LangChain | 文件写入 | - | WriteFileTool |

### 3.2 记忆工具清单（3个）

| 工具名称 | 功能描述 | 实现来源 | 依赖模块 |
|---------|---------|---------|---------|
| search_memory | 长期记忆检索（混合检索） | RAG 模块提供 | RAG |
| write_near_memory | 写入近端记忆 | Memory 模块提供 | Memory |
| write_core_memory | 写入核心记忆 | Memory 模块提供 | Memory |

### 3.3 预留工具

| 工具名称 | 功能描述 | 状态 |
|---------|---------|------|
| search_knowledge | 外部知识库检索 | 接口预留，暂不实现 |

### 3.4 工具接口定义

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

### 3.5 工具规范摘要

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

---

## 4. 安全规范

### 4.1 工具安全策略

| 工具 | 安全措施 | 限制类型 |
|------|---------|---------|
| terminal | 命令白名单/黑名单 | 命令执行 |
| python_repl | subprocess 禁用、超时控制 | 代码执行 |
| fetch_url | 域名白名单/黑名单 | 网络访问 |
| read_file | 路径遍历检查 | 文件访问 |
| write_file | 路径限制、类型过滤 | 文件写入 |

### 4.2 命令分类与处理

#### 4.2.1 直接禁止的命令

| 命令/模式 | 风险说明 |
|----------|---------|
| `dd` | 磁盘直接写入，可能损坏数据 |
| `mkfs` | 格式化磁盘 |
| `sudo`, `su` | 提权操作 |
| `reboot`, `shutdown`, `poweroff` | 系统关机/重启 |
| `ssh`, `scp`, `sftp`, `rsync` | 远程访问 |
| `| sh`, `| bash`, `| python` | 管道执行脚本 |
| `:(){ :|:& };:` | Fork 炸弹 |
| `insmod`, `rmmod`, `modprobe` | 内核模块操作 |
| `chroot`, `mount`, `umount` | 系统级操作 |

#### 4.2.2 需要确认的命令

| 命令/模式 | 确认原因 |
|----------|----------|
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

#### 4.2.3 正常执行的命令

- 文件查看：`ls`, `cat`, `head`, `tail`, `wc`, `find`
- 文本处理：`grep`, `sed`, `awk`, `sort`, `uniq`
- 开发相关：`python`, `node`, `git status`, `git diff`, `git log`
- 目录操作：`mkdir`, `cd`, `pwd`

### 4.3 文件系统安全

#### 4.3.1 路径访问控制

**root_dir 限制**：
- 工具只能访问用户指定的 `root_dir` 目录
- 默认为 `./workspace`，用户可配置
- 记忆文件存储在独立的 `~/.smartclaw` 目录，不与工作目录共享

**路径安全检查流程**：
1. 将请求路径规范化（解析 `..`、符号链接等）
2. 检查规范化后的路径是否在 `root_dir` 内
3. 检查路径是否指向敏感文件（如 `.env`、`.ssh`）
4. 通过检查则允许访问，否则拒绝并记录日志

#### 4.3.2 文件类型限制

**允许的文件类型**：
- 文本文件：`.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`, `.xml`
- 代码文件：`.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, `.c`, `.cpp`
- 配置文件：`.conf`, `.cfg`, `.ini`
- 其他：`.csv`, `.log`, `.sh`

**禁止的文件类型**：
- 可执行文件：`.exe`, `.bin`, `.dll`, `.so`
- 压缩文件：`.zip`, `.tar`, `.gz`（可读取但需确认）
- 加密文件：`.enc`, `.key`, `.pem`

#### 4.3.3 写入保护

**写入前检查**：
- 目标文件是否存在（覆盖需要确认）
- 目标路径是否在允许范围内
- 写入内容大小是否合理（<10MB）

**敏感文件保护**：
- 禁止写入 `.env` 文件
- 禁止写入 `.git` 目录
- 禁止写入系统目录

### 4.4 代码执行安全

#### 4.4.1 Python 代码禁止操作

- `subprocess` 模块（执行外部命令）
- `os.system()`, `os.popen()`（执行 Shell 命令）
- `eval()`, `exec()`（动态执行代码）
- `__import__()`（动态导入）

#### 4.4.2 执行超时与资源限制

**超时机制**：
- 代码执行超时：30 秒
- 超时后强制终止
- 返回超时错误和已执行部分输出

**资源限制**：
- 容器内存限制：256MB（terminal），512MB（python_repl）
- CPU 限制：25%
- 输出截断：1MB

### 4.5 容器安全配置

**隔离机制**：
- 所有命令在 Docker 容器内执行
- 容器与宿主机文件系统隔离
- 仅挂载用户指定的 `root_dir`

**安全配置**：
- 使用非 root 用户运行（UID 1000）
- 禁止特权模式
- 禁止访问宿主机 Docker socket
- 限制网络出站（允许但不推荐敏感操作）

**资源限制**：
- 内存限制：256MB（terminal），512MB（python_repl）
- CPU 限制：25%
- 无磁盘限制（容器内临时文件）

### 4.6 网络安全

#### 4.6.1 URL 访问控制

**允许的协议**：
- `http://`, `https://`（需确认）
- `file://`（仅限 root_dir 内）

**禁止的协议**：
- `ftp://`, `sftp://`
- `ssh://`
- `data:`, `javascript:`

#### 4.6.2 网络请求安全

**请求限制**：
- 超时时间：30 秒
- 响应大小限制：10MB
- 仅获取静态内容，不执行 JavaScript

### 4.7 安全配置清单

| 配置项 | 建议值 | 说明 |
|-------|--------|------|
| `tools.root_dir` | `./workspace` | 限制文件访问范围 |
| `tools.terminal.memory_limit` | `256m` | 容器内存限制 |
| `tools.terminal.cpu_limit` | `25%` | 容器 CPU 限制 |
| `tools.python_repl.execution_timeout` | `30` | 代码执行超时 |
| `logging.level` | `INFO` | 记录关键操作 |
| 环境变量存储 API Key | 必需 | 避免硬编码 |

---

## 5. 错误类型定义

### 5.1 工具相关错误

| 错误类型 | 说明 | 典型场景 |
|---------|------|---------|
| `ToolError` | 工具相关错误 | 工具不存在、工具调用失败 |
| `ContainerError` | 容器相关错误 | 容器创建失败、容器崩溃 |
| `SecurityError` | 安全相关错误 | 路径遍历攻击、危险命令检测 |

### 5.2 容器错误处理

#### 5.2.1 容器崩溃检测

常见退出码：
- 137：OOM Killed（内存超限）
- 139：Segmentation Fault
- 1：应用错误
- 0：正常退出（非崩溃）

#### 5.2.2 自动重启机制

- 最大重试次数：3 次
- 退避策略：指数退避（1秒、2秒、4秒）
- 重启条件：非正常退出且未超过最大重试次数
- 放弃条件：连续 3 次重启后仍崩溃

---

## 6. 目录结构

```
smartclaw/
│   ├── tools/                  # 内置工具模块
│   │   ├── __init__.py
│   │   ├── registry.py         # ToolRegistry
│   │   ├── container.py        # ContainerManager
│   │   ├── security.py         # SecurityChecker
│   │   ├── terminal.py         # terminal 工具
│   │   ├── python_repl.py      # python_repl 工具
│   │   └── file_tools.py       # read_file, write_file, fetch_url
```
