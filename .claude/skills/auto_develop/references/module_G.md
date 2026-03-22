# 模块 G：系统集成测试

## 1. 测试策略

### 1.1 测试层次与覆盖率要求

| 层次 | 目标 | 覆盖率要求 |
|-----|------|-----------|
| 单元测试 | 单个类/函数行为，Mock外部依赖 | 核心>80%，工具类>90% |
| 集成测试 | 模块间协作，使用真实依赖 | 关键流程100% |
| 端到端测试 | 完整用户场景 | 主要场景覆盖 |

### 1.2 模块覆盖率细化

| 模块 | 覆盖率要求 | 说明 |
|-----|-----------|------|
| Agent 模块 | > 80% | 核心业务逻辑 |
| Memory 模块 | > 80% | 数据持久化关键 |
| RAG 模块 | > 80% | 检索质量影响体验 |
| 内置工具 | > 90% | 安全检查必须可靠 |
| 配置/日志 | > 70% | 辅助模块 |

### 1.3 测试工具选型

| 工具 | 用途 | 说明 |
|-----|------|------|
| **pytest** | 测试框架 | 支持 fixtures、参数化、异步测试 |
| **pytest-mock** | Mock 工具 | 基于 unittest.mock，隔离外部依赖 |
| **pytest-asyncio** | 异步测试 | 支持 RAG 模块异步操作测试 |
| **pytest-docker** | Docker 集成 | 可选，用于容器集成测试 |

### 1.4 Mock 策略

| 被测组件 | Mock 对象 | Mock 方式 |
|---------|----------|----------|
| SmartClawAgent | LLM API 响应 | `mocker.patch` |
| MemoryManager | 文件系统操作 | `tmp_path` fixture |
| MemoryIndexManager | LlamaIndex 组件 | `mocker.patch.object` |
| ContainerManager | Docker SDK | `mocker.patch('docker.from_env')` |
| 工具函数 | ContainerManager | 依赖注入 + Mock |

---

## 2. 模块集成验证 (I1-I4)

### 2.1 测试目录结构

```
tests/integration/             # 集成测试（模块间协作）
├── __init__.py
├── test_memory_integration.py  # Memory 模块集成
├── test_rag_integration.py     # RAG 模块集成
├── test_tools_integration.py   # Tools 模块集成
└── test_agent_integration.py   # Agent 模块集成
```

### 2.2 集成测试分类

| 分类 | 说明 |
|-----|------|
| 功能测试 | 验证每个方法的各种输入/输出场景 |
| 骨架测试 | 验证类实例化、初始化、抽象方法定义 |
| 集成测试 | 验证模块间协作（Agent+Memory+RAG+Tools） |

### 2.3 集成测试场景

#### 2.3.1 完整对话流程测试

| 测试用例 | 说明 |
|---------|------|
| `test_full_conversation_simple` | 简单问答完整流程 |
| `test_full_conversation_with_tool` | 带工具调用的完整流程 |
| `test_full_conversation_multi_turn` | 多轮对话流程 |
| `test_full_conversation_memory_persistence` | 记忆持久化验证 |

#### 2.3.2 记忆写入与检索联调

| 测试用例 | 说明 |
|---------|------|
| `test_write_then_search_near_memory` | 写入近端记忆后检索 |
| `test_archive_then_search_long_memory` | 归档后检索长期记忆 |
| `test_write_core_then_load` | 写入核心记忆后加载 |
| `test_memory_conflict_resolution` | 记忆冲突解决 |

#### 2.3.3 工具调用与容器交互

| 测试用例 | 说明 |
|---------|------|
| `test_tool_call_creates_container` | 工具调用创建容器 |
| `test_tool_call_reuses_container` | 工具调用复用容器 |
| `test_container_cleanup_on_session_end` | 会话结束时容器清理 |
| `test_container_crash_recovery` | 容器崩溃恢复 |

#### 2.3.4 会话生命周期测试

| 测试用例 | 说明 |
|---------|------|
| `test_session_create` | 会话创建 |
| `test_session_message_processing` | 消息处理 |
| `test_session_archive` | 会话归档 |
| `test_session_restore` | 会话恢复（如有） |
| `test_session_cleanup` | 会话清理 |

---

## 3. 端到端测试 (G1-G7)

### 3.1 测试目录结构

```
tests/e2e/                     # 端到端测试（完整流程）
├── __init__.py
├── test_conversation_flow.py   # 完整对话流程
├── test_memory_system.py       # 记忆系统 E2E
├── test_tool_execution.py      # 工具执行 E2E
└── test_session_lifecycle.py   # 会话生命周期
```

### 3.2 E2E 测试说明

| 测试文件 | 说明 |
|---------|------|
| `test_conversation_flow.py` | 完整用户流程，最小 Mock |
| `test_memory_system.py` | 记忆系统端到端测试 |
| `test_tool_execution.py` | 工具执行端到端测试 |
| `test_session_lifecycle.py` | 会话生命周期端到端测试 |

---

## 4. 系统边界测试

### 4.1 边界测试目录结构

```
tests/boundary/                # 边界条件测试
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

### 4.2 大文件/长会话测试

| 测试用例 | 说明 |
|---------|------|
| `test_large_file_read` | 大文件读取（>10MB） |
| `test_large_file_write` | 大文件写入 |
| `test_long_session_messages` | 长会话消息列表 |
| `test_many_tool_calls` | 大量工具调用 |

### 4.3 并发/网络异常测试

| 测试用例 | 说明 |
|---------|------|
| `test_concurrent_writes` | 并发写入同一文件 |
| `test_concurrent_sessions` | 并发会话 |
| `test_network_timeout` | 网络超时处理 |
| `test_network_error` | 网络错误处理 |
| `test_llm_rate_limit` | LLM 限流处理 |

### 4.4 容器/配置异常测试

| 测试用例 | 说明 |
|---------|------|
| `test_docker_not_running` | Docker 未运行处理 |
| `test_container_oom` | 容器 OOM 处理 |
| `test_config_missing_required` | 缺少必需配置 |
| `test_config_invalid_value` | 无效配置值 |

---

## 5. 测试数据准备

### 5.1 模拟对话数据

```
- 简单问答对话样本
- 带工具调用的对话样本
- 多轮对话样本
- 超长对话样本（触发预压缩）
```

### 5.2 模拟文件数据

```
- 各种格式的文本文件（.md, .txt, .py, .json, .yaml）
- 大文件样本（>10MB）
- 空文件
- 格式错误文件
```

### 5.3 模拟索引数据

```
- 已索引的归档会话
- 待索引的新文件
- 格式正确的 Markdown 文件
- 包含各种元数据的文件
```

---

## 6. 运行测试命令

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

---

## 7. 性能测试建议

### 7.1 基准测试

- 测量各操作的基线性能
- 建立性能回归检测
- 定期执行性能测试

### 7.2 负载测试

- 模拟长时间运行场景
- 检测内存泄漏
- 验证资源限制有效性

### 7.3 边界测试

- 大文件处理测试
- 长会话测试
- 高频操作测试

---

## 8. 验收标准

- 支持长时间运行无性能衰减
- 集成测试关键流程100%覆盖
- 端到端测试主要场景覆盖
- 所有边界条件有对应测试用例
