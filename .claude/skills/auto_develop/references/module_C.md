# 模块 C：RAG 模块

## 1. 模块概述

### 1.1 技术选型

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 索引框架 | LlamaIndex | 提供文档解析、分块、索引构建 |
| 向量存储 | Chroma | 轻量级，支持持久化 |
| BM25 | LlamaIndex BM25Retriever | LlamaIndex 内建实现 |
| 文件监听 | watchdog | 跨平台文件系统监控 |
| LLM | OpenAI/Qwen/Ollama/vLLM/... | 从配置文件读取，使用 LLM Factory 进行实例化 |
| Embedding | OpenAI/Qwen/Ollama/vLLM/... | 从配置文件读取，使用 Embedding Factory 进行实例化 |

### 1.2 设计原则

1. **本地优先与轻量级**：所有索引数据存储在本地，使用轻量级技术栈
2. **混合检索策略**：结合语义相似性和关键词精确匹配
3. **增量索引更新**：高效的文件变更处理机制
4. **透明性与可审计性**：索引仅作为检索加速层
5. **可扩展性与抽象设计**：IndexManager 抽象基类支持未来扩展
6. **异步非阻塞**：索引构建不影响用户交互

## 2. 核心组件

### 2.1 组件职责

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

### 2.2 架构图

```
文件系统 (sessions/archive/*.md)
    │
    ▼
SimpleDirectoryReader
    │ 递归读取 .md 文件 → Document 对象
    ▼
IngestionPipeline
    │
    ├── MarkdownNodeParser（按标题层级分块）
    ├── QuestionsAnsweredExtractor（调用 LLM 生成可回答问题）
    ├── DocStore（记录文档哈希值）
    └── SQLite Cache（缓存节点+转换结果）
    │
    ├──→ SimpleDocumentStore (docstore.json)
    ├──→ ChromaVectorStore (chroma/)
    └──→ BM25 索引 (bm25/)
    │
    ▼
QueryFusionRetriever (RRF)
    │
    ├── Vector Retriever
    └── BM25 Retriever
    │
    ▼
融合后的 NodeWithScore 列表
```

## 3. 接口规范

### 3.1 RAGManager 接口

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

### 3.2 IndexManager 抽象基类

IndexManager 是索引管理器的抽象基类，定义所有索引管理器必须实现的接口。

**抽象方法**：

| 方法签名 | 说明 |
|---------|------|
| `search(query: str, top_k: int) -> List[Segment]` | 执行检索 |
| `update_document(doc_id: str, content: str, metadata: dict) -> bool` | 添加或更新文档 |
| `delete_document(doc_id: str) -> bool` | 删除文档 |
| `build_index(force: bool) -> bool` | 全量重建索引 |
| `check_consistency() -> Dict[str, List[str]]` | 检查索引一致性 |
| `repair_consistency() -> Dict[str, int]` | 修复一致性问题 |

**抽象基类定义**：

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
    """索引管理器抽象基类"""

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Segment]:
        """执行检索，返回相关片段列表"""
        pass

    @abstractmethod
    def update_document(self, doc_id: str, content: str,
                       metadata: Optional[Dict] = None) -> bool:
        """添加或更新单个文档"""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """从索引中删除指定文档"""
        pass

    @abstractmethod
    def build_index(self, force: bool = False) -> bool:
        """全量重建索引"""
        pass

    @abstractmethod
    def check_consistency(self) -> Dict[str, List[str]]:
        """检查索引与数据源的一致性"""
        pass

    @abstractmethod
    def repair_consistency(self) -> Dict[str, int]:
        """修复一致性异常"""
        pass
```

### 3.3 MemoryIndexManager 接口

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

**核心实现**：

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.extractors import QuestionsAnsweredExtractor

class MemoryIndexManager(IndexManager):
    """长期记忆索引管理器（LlamaIndex 实现）"""

    def __init__(self, config):
        self.config = config
        self._dir = config['rag']['index_path']
        self.storage_context = self._init_storage_context()
        self.pipeline = self._init_pipeline()
        self.fusion_retriever = None
        self._init_retriever()

    def _init_retriever(self):
        """初始化融合检索器"""
        vector_index = VectorStoreIndex.from_documents(
            [], storage_context=self.storage_context
        )
        vector_retriever = vector_index.as_retriever(
            similarity_top_k=self.config['rag']['top_k'] * 2
        )

        bm25_retriever = BM25Retriever.from_defaults(
            index=vector_index,
            similarity_top_k=self.config['rag']['top_k'] * 2
        )

        self.fusion_retriever = QueryFusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            mode="reciprocal_rank",
            query_gen_kwargs={
                "n_queries": self.config['rag']['generate_queries'],
                "use_async": True
            }
        )

    def search(self, query: str, top_k: int = 5) -> List[Segment]:
        """执行混合检索"""
        if not self.fusion_retriever:
            raise RuntimeError("Fusion retriever not initialized")

        nodes_with_score = self.fusion_retriever.retrieve(query)

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
```

### 3.4 SQLiteCache 实现

SQLite 缓存实现，用于缓存节点转换结果。

```python
import sqlite3
import hashlib
import pickle
from typing import Any, Optional
from llama_index.core.cache.base import BaseCache

class SQLiteCache(BaseCache):
    """SQLite 缓存实现"""

    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.conn = self._init_database()
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                cache_value BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_accessed_at
            ON cache(accessed_at)
        ''')
        self.conn.commit()

    def get(self, key: str) -> Optional[Any]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT cache_value, accessed_at
            FROM cache WHERE cache_key = ?
        ''', (key,))
        row = cursor.fetchone()
        if row:
            cursor.execute('''
                UPDATE cache
                SET accessed_at = CURRENT_TIMESTAMP
                WHERE cache_key = ?
            ''', (key,))
            self.conn.commit()
            return pickle.loads(row[0])
        return None

    def put(self, key: str, value: Any, content: str = "") -> bool:
        serialized_value = pickle.dumps(value)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO cache (cache_key, cache_value)
            VALUES (?, ?)
        ''', (key, serialized_value))
        self.conn.commit()
        return True
```

### 3.5 FileWatcher 接口

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

**实现**：

```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
from collections import defaultdict

class FileWatcher(FileSystemEventHandler):
    """文件监听器（watchdog 实现）"""

    def __init__(self, callback, debounce_time: int = 2):
        self.callback = callback
        self.debounce_time = debounce_time
        self.last_events = defaultdict(float)
        self.pending_timers = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        now = time.time()
        if file_path in self.last_events:
            if now - self.last_events[file_path] < self.debounce_time:
                return
        self.last_events[file_path] = now
        if file_path in self.pending_timers:
            self.pending_timers[file_path].cancel()
        timer = Timer(self.debounce_time, lambda: self._process_change(file_path))
        self.pending_timers[file_path] = timer
        timer.start()

    def on_created(self, event):
        if event.is_directory:
            return
        self._process_change(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        self._process_change(event.src_path, is_delete=True)

    def _process_change(self, file_path: str, is_delete: bool = False):
        try:
            self.callback(file_path, is_delete)
        except Exception as e:
            logging.error(f"Failed to process file change {file_path}: {e}")
        finally:
            if file_path in self.pending_timers:
                del self.pending_timers[file_path]
```

### 3.6 Agent 工具接口

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

    if top_k == 5:
        top_k = config['rag']['top_k']

    if date_range:
        results = manager._search_with_filters(query, top_k, date_range)
    else:
        results = manager.search(query, top_k)

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

## 4. 数据模型

### 4.1 Segment 数据模型

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

### 4.2 Document 对象（LlamaIndex 自动生成）

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

### 4.3 Node 对象（LlamaIndex 自动生成）

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

## 5. 配置项

```yaml
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
```

## 6. 错误处理

### 6.1 索引构建失败

- **原因**：LLM 调用超时、嵌入生成失败、文档解析错误
- **处理策略**：
  - LLM 调用失败：降级为不生成问题，继续构建索引
  - 嵌入生成失败：跳过该节点，记录警告，继续处理其他节点
  - 文档解析失败：跳过该文档，记录错误，继续处理其他文档
- **降级模式**：仅 BM25 检索（向量索引不可用时）

### 6.2 检索失败

- **原因**：索引未初始化、向量存储连接失败、BM25 索引损坏
- **处理**：
  - 索引未初始化：触发紧急初始化，返回提示信息
  - 向量检索失败：降级为仅 BM25 检索
  - BM25 检索失败：降级为仅向量检索
  - 全部失败：返回空结果和提示信息
