"""MemoryManager 抽象基类

定义记忆管理器的通用接口，所有具体记忆管理器（近端记忆、核心记忆、会话）都继承此类。
"""

from abc import ABC, abstractmethod
from pathlib import Path


class MemoryManager(ABC):
    """记忆管理器抽象基类

    所有记忆管理器的基类，定义了通用的接口和基础功能。

    Attributes:
        base_path: 记忆存储根路径

    Abstract Methods:
        load(): 加载记忆内容
        exists(): 检查记忆是否存在
    """

    def __init__(self, base_path: Path) -> None:
        """初始化记忆管理器

        Args:
            base_path: 记忆存储根路径
        """
        self.base_path = base_path

    @abstractmethod
    def load(self) -> str:
        """加载记忆内容

        子类必须实现此方法，返回拼接后的记忆内容。

        Returns:
            拼接后的记忆内容字符串
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """检查记忆是否存在

        子类必须实现此方法，检查记忆文件或目录是否存在。

        Returns:
            如果记忆存在返回 True，否则返回 False
        """
        pass

    def write(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """写入记忆内容

        基类提供默认的空实现，子类应根据需要覆盖此方法。

        Args:
            **kwargs: 子类定义的写入参数

        Raises:
            IOError: 文件写入失败（子类实现时可能抛出）
        """
        pass
