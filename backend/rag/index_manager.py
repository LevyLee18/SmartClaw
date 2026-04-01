"""IndexManager 抽象基类

定义索引管理器的统一接口，所有索引管理器必须实现此接口。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from backend.rag.models import Segment


class IndexManager(ABC):
    """索引管理器抽象基类

    定义所有索引管理器必须实现的接口。

    Attributes:
        base_path: 索引存储根路径
    """

    def __init__(self, base_path: Path) -> None:
        """初始化索引管理器

        Args:
            base_path: 索引存储根路径
        """
        self.base_path = base_path

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[Segment]:
        """执行检索

        Args:
            query: 查询文本
            top_k: 返回结果数量，默认 5

        Returns:
            相关片段列表，按相关性得分降序排列
        """
        pass

    @abstractmethod
    def update_document(
        self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """添加或更新文档

        Args:
            doc_id: 文档唯一标识符
            content: 文档文本内容
            metadata: 文档元数据（可选）

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档唯一标识符

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    def build_index(self, force: bool = False) -> bool:
        """全量重建索引

        Args:
            force: 是否强制重建（即使索引已存在）

        Returns:
            操作是否成功
        """
        pass
