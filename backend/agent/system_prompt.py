"""SystemPromptBuilder 实现

System Prompt 拼接器，负责按顺序加载记忆文件。
"""

from typing import Any

from backend.config.models import Settings


class SystemPromptBuilder:
    """System Prompt 构建器

    负责按顺序加载核心记忆和近端记忆，构建完整的 System Prompt。

    加载顺序（严格遵循）：
    1. AGENTS.md — Agent 基础定义
    2. SKILLS_SNAPSHOT.md — 可用技能列表
    3. SOUL.md — 人格与边界
    4. IDENTITY.md — 名称与风格
    5. USER.md — 用户画像
    6. MEMORY.md — 用户偏好与重要决策
    7. 近端记忆 — 最近 N 天的对话摘要

    Attributes:
        config: SmartClaw 配置对象
        memory_manager: 记忆管理器
        session_manager: 会话管理器
    """

    def __init__(
        self,
        config: Settings,
        memory_manager: Any,
        session_manager: Any,
    ) -> None:
        """初始化 System Prompt 构建器

        Args:
            config: SmartClaw 配置对象
            memory_manager: 记忆管理器
            session_manager: 会话管理器
        """
        self.config = config
        self.memory_manager = memory_manager
        self.session_manager = session_manager

    def build(self, session_id: str) -> str:
        """构建完整的 System Prompt

        Args:
            session_id: 会话标识

        Returns:
            拼接后的 System Prompt 字符串
        """
        # TODO: 在后续任务中实现
        return ""

    def load_core_memory(self) -> str:
        """加载核心记忆内容

        Returns:
            核心记忆内容字符串
        """
        # TODO: 在后续任务中实现
        return ""

    def load_near_memory(self, days: int = 7) -> str:
        """加载近端记忆内容

        Args:
            days: 加载最近 N 天的记忆

        Returns:
            近端记忆内容字符串
        """
        # TODO: 在后续任务中实现
        return ""

    def estimate_tokens(self, content: str) -> int:
        """估算内容的 token 数

        Args:
            content: 要估算的内容

        Returns:
            估算的 token 数
        """
        # TODO: 在后续任务中实现
        return 0

    def truncate_to_limit(self, content: str, max_tokens: int) -> str:
        """截断内容到指定 token 限制

        Args:
            content: 要截断的内容
            max_tokens: 最大 token 数

        Returns:
            截断后的内容
        """
        # TODO: 在后续任务中实现
        return content
