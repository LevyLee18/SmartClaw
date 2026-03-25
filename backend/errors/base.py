"""SmartClaw 错误基类和子类定义

所有 SmartClaw 错误继承自 SmartClawError 基类，提供统一的错误信息格式。

错误类型：
- SmartClawError: 基类
- ConfigError: 配置相关错误 (CFG_XXX)
- SessionError: 会话相关错误 (SES_XXX)
- MemoryError: 记忆相关错误 (MEM_XXX)
- RAGError: RAG 相关错误 (RAG_XXX)
- ToolError: 工具相关错误 (TOOL_XXX)
- ContainerError: 容器相关错误 (CTR_XXX)
- SecurityError: 安全相关错误 (SEC_XXX)
"""

from typing import Any


class SmartClawError(Exception):
    """SmartClaw 错误基类

    所有 SmartClaw 自定义错误的基类，提供统一的错误信息格式。

    Attributes:
        error_code: 错误代码（如 CFG_001）
        message: 错误消息
        detail: 错误详情
        suggestion: 修复建议
    """

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.suggestion = suggestion
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息

        Returns:
            格式化后的错误消息字符串
        """
        parts = [f"[{self.error_code}] {self.message}"]
        if self.detail:
            parts.append(f"Detail: {self.detail}")
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """将错误转换为字典

        Returns:
            包含错误信息的字典
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail,
            "suggestion": self.suggestion,
        }

    def __repr__(self) -> str:
        """返回错误的 repr 表示

        Returns:
            错误的 repr 字符串
        """
        return f"SmartClawError(error_code={self.error_code!r}, message={self.message!r})"


class ConfigError(SmartClawError):
    """配置相关错误

    用于配置加载、验证、访问过程中的错误。

    错误码前缀: CFG_XXX
    典型场景: 配置文件缺失、格式错误、验证失败
    """

    def __init__(
        self,
        message: str,
        error_code: str = "CFG_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)


class SessionError(SmartClawError):
    """会话相关错误

    用于会话管理过程中的错误。

    错误码前缀: SES_XXX
    典型场景: 会话不存在、会话已关闭
    """

    def __init__(
        self,
        message: str,
        error_code: str = "SES_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)


class MemoryError(SmartClawError):
    """记忆相关错误

    用于记忆文件读写过程中的错误。

    错误码前缀: MEM_XXX
    典型场景: 记忆文件读写失败、文件格式错误
    """

    def __init__(
        self,
        message: str,
        error_code: str = "MEM_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)


class RAGError(SmartClawError):
    """RAG 相关错误

    用于 RAG 索引和检索过程中的错误。

    错误码前缀: RAG_XXX
    典型场景: 索引构建失败、检索失败
    """

    def __init__(
        self,
        message: str,
        error_code: str = "RAG_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)


class ToolError(SmartClawError):
    """工具相关错误

    用于工具调用过程中的错误。

    错误码前缀: TOOL_XXX
    典型场景: 工具不存在、工具调用失败
    """

    def __init__(
        self,
        message: str,
        error_code: str = "TOOL_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)


class ContainerError(SmartClawError):
    """容器相关错误

    用于 Docker 容器管理过程中的错误。

    错误码前缀: CTR_XXX
    典型场景: 容器创建失败、容器崩溃
    """

    def __init__(
        self,
        message: str,
        error_code: str = "CTR_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)


class SecurityError(SmartClawError):
    """安全相关错误

    用于安全检查过程中的错误。

    错误码前缀: SEC_XXX
    典型场景: 路径遍历攻击、危险命令检测
    """

    def __init__(
        self,
        message: str,
        error_code: str = "SEC_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        super().__init__(message, error_code, detail, suggestion)
