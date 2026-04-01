"""RAG 模块数据模型

定义 RAG 系统使用的核心数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Document:
    """文档数据类

    表示一个待索引的文档。

    Attributes:
        doc_id: 文档唯一标识符
        content: 文档文本内容
        metadata: 文档元数据（来源、类型等）
    """

    doc_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """节点数据类

    表示文档分块后的一个节点。

    Attributes:
        node_id: 节点唯一标识符
        content: 节点文本内容
        metadata: 节点元数据（标题、层级等）
        relationships: 节点关系（父节点、子节点等）
    """

    node_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, Any] = field(default_factory=dict)


@dataclass
class Segment:
    """检索结果数据类

    表示一个检索结果片段。

    Attributes:
        content: 片段文本内容
        source: 来源文件路径
        file_type: 记忆类型（long_term/near/core）
        timestamp: 时间戳（ISO 格式）
        score: 相关性得分
    """

    content: str
    source: str
    file_type: str
    score: float
    timestamp: Optional[str] = None
