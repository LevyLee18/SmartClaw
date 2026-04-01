"""NearMemoryManager - 近端记忆管理器

管理当天的对话摘要和临时性信息，按日期存储在 Markdown 文件中。
"""

from datetime import date as DateClass
from datetime import timedelta
from pathlib import Path
from typing import Any, Optional

from backend.memory.base import MemoryManager


class NearMemoryManager(MemoryManager):
    """近端记忆管理器

    管理近期对话摘要和临时性信息，按日期存储在 Markdown 文件中。
    文件命名格式：YYYY-MM-DD.md

    Attributes:
        base_path: 记忆存储根路径
        memory_dir: 近端记忆目录 (base_path/memory)
    """

    def __init__(self, base_path: Path) -> None:
        """初始化近端记忆管理器

        Args:
            base_path: 记忆存储根路径
        """
        super().__init__(base_path)
        self.memory_dir = base_path / "memory"

    def load(self, days: int = 2) -> str:
        """加载最近 N 天的近端记忆

        Args:
            days: 加载最近几天的记忆，默认 2 天

        Returns:
            拼接后的近端记忆内容，按日期降序排列
        """
        if not self.memory_dir.exists():
            return ""

        contents: list[str] = []
        today = DateClass.today()

        for i in range(days):
            target_date = today - timedelta(days=i)
            file_path = self.get_file_path(target_date)

            if file_path.exists():
                file_content = file_path.read_text(encoding="utf-8").strip()
                if file_content:
                    contents.append(f"## {target_date.isoformat()}\n\n{file_content}")

        return "\n\n---\n\n".join(contents) if contents else ""

    def write(  # type: ignore[override]
        self,
        content: str,
        target_date: Optional[DateClass] = None,
        **kwargs,  # type: ignore[no-untyped-def]
    ) -> None:
        """写入近端记忆

        Args:
            content: 要写入的内容
            target_date: 目标日期，默认为今天
            **kwargs: 额外参数（保留兼容性）
        """
        if target_date is None:
            target_date = DateClass.today()

        # 确保目录存在
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.get_file_path(target_date)

        # 追加模式写入
        if file_path.exists():
            existing_content = file_path.read_text(encoding="utf-8")
            new_content = f"{existing_content}\n\n{content}"
        else:
            new_content = content

        file_path.write_text(new_content, encoding="utf-8")

    def get_file_path(self, target_date: DateClass) -> Path:
        """获取指定日期的文件路径

        Args:
            target_date: 目标日期

        Returns:
            文件路径，格式为 memory/YYYY-MM-DD.md
        """
        return self.memory_dir / f"{target_date.isoformat()}.md"

    def exists(self) -> bool:
        """检查近端记忆是否存在

        Returns:
            如果 memory 目录中有任何 .md 文件返回 True
        """
        if not self.memory_dir.exists():
            return False

        return any(self.memory_dir.glob("*.md"))

    def get_write_tool(self) -> dict[str, Any]:
        """获取 write_near_memory 工具适配器

        返回一个符合 LangChain 工具规范的字典，包含：
        - name: 工具名称
        - description: 工具描述
        - func: 可调用的工具函数

        Returns:
            工具配置字典
        """
        def write_near_memory(
            content: str,
            date: Optional[str] = None,
            category: Optional[str] = None
        ) -> str:
            """写入近端记忆

            Args:
                content: 要写入的内容（Markdown 格式）
                date: 日期（YYYY-MM-DD 格式），默认为当天
                category: 内容类别（对话摘要/重要事实/决策记录）

            Returns:
                操作结果消息
            """
            try:
                # 解析日期
                target_date: DateClass
                if date:
                    try:
                        target_date = DateClass.fromisoformat(date)
                    except ValueError:
                        return f"错误：日期格式无效，应为 YYYY-MM-DD 格式，收到：{date}"
                else:
                    target_date = self._get_today()

                # 构建内容
                full_content = content
                if category:
                    full_content = f"## {category}\n\n{content}"

                # 写入记忆
                self.write(content=full_content, target_date=target_date)

                return f"成功：已写入近端记忆 ({target_date.isoformat()})"
            except Exception as e:
                return f"错误：写入近端记忆失败 - {e}"

        return {
            "name": "write_near_memory",
            "description": (
                "写入近端记忆。用于将重要信息写入当天的近端记忆文件。"
                "支持内容类别（对话摘要、重要事实、决策记录）。"
            ),
            "func": write_near_memory,
        }

    def _get_today(self) -> DateClass:
        """获取今天的日期

        Returns:
            今天的日期对象
        """
        return DateClass.today()
