"""CoreMemoryManager - 核心记忆管理器

管理 Agent 人格、用户画像等长期有效信息，存储在 core_memory/ 目录下。
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from backend.memory.base import MemoryManager


class CoreMemoryFile(str, Enum):
    """核心记忆文件枚举

    定义核心记忆的 6 个文件及其文件名。
    """

    SOUL = "SOUL.md"
    IDENTITY = "IDENTITY.md"
    USER = "USER.md"
    MEMORY = "MEMORY.md"
    AGENTS = "AGENTS.md"
    SKILLS_SNAPSHOT = "SKILLS_SNAPSHOT.md"


class CoreMemoryWriteMode(str, Enum):
    """核心记忆写入模式枚举"""

    APPEND = "append"
    REPLACE = "replace"


class CoreMemoryManager(MemoryManager):
    """核心记忆管理器

    管理 Agent 人格、用户画像等长期有效信息。
    文件位于 base_path/core_memory/ 目录下。

    Attributes:
        base_path: 记忆存储根路径
        core_memory_dir: 核心记忆目录 (base_path/core_memory)
    """

    # 禁止修改的文件
    READONLY_FILES: set[CoreMemoryFile] = {
        CoreMemoryFile.AGENTS,
        CoreMemoryFile.SKILLS_SNAPSHOT,
    }

    # 文件加载顺序
    LOAD_ORDER: list[CoreMemoryFile] = [
        CoreMemoryFile.AGENTS,
        CoreMemoryFile.SKILLS_SNAPSHOT,
        CoreMemoryFile.SOUL,
        CoreMemoryFile.IDENTITY,
        CoreMemoryFile.USER,
        CoreMemoryFile.MEMORY,
    ]

    def __init__(self, base_path: Path) -> None:
        """初始化核心记忆管理器

        Args:
            base_path: 记忆存储根路径
        """
        super().__init__(base_path)
        self.core_memory_dir = base_path / "core_memory"

    def load(self, file_key: Optional[str] = None) -> str:
        """加载核心记忆内容

        Args:
            file_key: 文件标识（可选），如 "soul", "identity", "user", "memory"
                     如果为 None，加载所有文件

        Returns:
            拼接后的核心记忆内容

        Raises:
            ValueError: file_key 不合法
        """
        if file_key is not None:
            # 加载单个文件
            file_enum = self._get_file_enum(file_key)
            return self._load_single_file(file_enum)

        # 加载所有文件
        contents: list[str] = []

        for file_enum in self.LOAD_ORDER:
            file_content = self._load_single_file(file_enum)
            if file_content:
                contents.append(file_content)

        return "\n\n---\n\n".join(contents) if contents else ""

    def _load_single_file(self, file_enum: CoreMemoryFile) -> str:
        """加载单个核心记忆文件

        Args:
            file_enum: 核心记忆文件枚举

        Returns:
            文件内容，如果文件不存在则返回空字符串
        """
        file_path = self.core_memory_dir / file_enum.value

        if not file_path.exists():
            return ""

        return file_path.read_text(encoding="utf-8").strip()

    def write(  # type: ignore[override]
        self,
        content: str,
        file_key: str,
        mode: str = "append",
        **kwargs,  # type: ignore[no-untyped-def]
    ) -> None:
        """写入核心记忆

        Args:
            content: 要写入的内容（Markdown 格式）
            file_key: 文件标识（soul/identity/user/memory）
            mode: 写入模式（append/replace）

        Raises:
            ValueError: file_key 不合法或尝试修改只读文件
            IOError: 文件写入失败
        """
        # 转换 file_key 为枚举
        file_enum = self._get_file_enum(file_key)

        # 检查只读权限
        self._check_readonly(file_enum)

        # 确保目录存在
        self.core_memory_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.core_memory_dir / file_enum.value

        # 根据模式写入
        if mode == CoreMemoryWriteMode.REPLACE.value:
            # 替换模式：直接覆盖
            file_path.write_text(content, encoding="utf-8")
        else:
            # 追加模式：添加时间戳后追加
            timestamped_content = self._add_timestamp(content)
            if file_path.exists():
                existing = file_path.read_text(encoding="utf-8")
                new_content = f"{existing}\n\n{timestamped_content}"
            else:
                new_content = timestamped_content
            file_path.write_text(new_content, encoding="utf-8")

    def _get_file_enum(self, file_key: str) -> CoreMemoryFile:
        """将 file_key 转换为文件枚举

        Args:
            file_key: 文件标识（soul/identity/user/memory/agents/skills_snapshot）

        Returns:
            核心记忆文件枚举

        Raises:
            ValueError: file_key 不合法
        """
        key_mapping: dict[str, CoreMemoryFile] = {
            "soul": CoreMemoryFile.SOUL,
            "identity": CoreMemoryFile.IDENTITY,
            "user": CoreMemoryFile.USER,
            "memory": CoreMemoryFile.MEMORY,
            "agents": CoreMemoryFile.AGENTS,
            "skills_snapshot": CoreMemoryFile.SKILLS_SNAPSHOT,
        }

        # 大小写不敏感
        normalized_key = file_key.lower().strip()

        if normalized_key not in key_mapping:
            valid_keys = ", ".join(key_mapping.keys())
            raise ValueError(
                f"Invalid file_key: '{file_key}'. Valid keys are: {valid_keys}"
            )

        return key_mapping[normalized_key]

    def _check_readonly(self, file_enum: CoreMemoryFile) -> None:
        """检查文件是否为只读

        Args:
            file_enum: 核心记忆文件枚举

        Raises:
            ValueError: 文件为只读
        """
        if file_enum in self.READONLY_FILES:
            raise ValueError(
                f"Cannot modify readonly file: {file_enum.value}. "
                f"This file is protected and cannot be written."
            )

    def _add_timestamp(self, content: str) -> str:
        """为内容添加时间戳

        Args:
            content: 原始内容

        Returns:
            添加时间戳后的内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"\n\n---\n\n**更新时间: {timestamp}**\n\n{content}"

    def exists(self) -> bool:
        """检查核心记忆是否存在

        Returns:
            如果 core_memory 目录中有任何 .md 文件返回 True
        """
        if not self.core_memory_dir.exists():
            return False

        return any(self.core_memory_dir.glob("*.md"))
