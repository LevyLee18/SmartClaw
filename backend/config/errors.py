"""配置模块错误类型"""


class ConfigError(Exception):
    """配置错误基类

    用于配置加载、验证、访问过程中的错误。

    Attributes:
        error_code: 错误代码（如 CFG_001）
        message: 错误消息
        detail: 错误详情
        suggestion: 修复建议
    """

    def __init__(
        self,
        message: str,
        error_code: str = "CFG_000",
        detail: str = "",
        suggestion: str = "",
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.suggestion = suggestion
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        parts = [f"[{self.error_code}] {self.message}"]
        if self.detail:
            parts.append(f"Detail: {self.detail}")
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return "\n".join(parts)
