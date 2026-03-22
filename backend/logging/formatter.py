"""SmartClaw 日志格式化器

提供统一的日志格式定义，符合 SmartClaw 日志规范。

日志格式：{时间戳} - {模块名} - {级别} - {消息内容}
- 时间戳：YYYY-MM-DD HH:MM:SS,mmm（精确到毫秒）
- 模块名：点分命名（如 smartclaw.agent.session）
- 级别：大写英文（DEBUG/INFO/WARNING/ERROR/CRITICAL）
"""

import logging
from datetime import datetime


class SmartClawFormatter(logging.Formatter):
    """SmartClaw 统一日志格式化器

    日志格式：{时间戳} - {模块名} - {级别} - {消息内容}

    示例输出：
        2026-03-18 14:30:15,123 - smartclaw.agent - INFO - Session created: session_abc123
    """

    # 日志格式模板
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 时间戳格式（精确到毫秒）
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S,%f"

    def __init__(self) -> None:
        """初始化格式化器"""
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)

    def formatTime(
        self, record: logging.LogRecord, datefmt: str | None = None
    ) -> str:
        """格式化时间戳，精确到毫秒

        Args:
            record: 日志记录
            datefmt: 日期格式字符串

        Returns:
            格式化后的时间戳字符串
        """
        ct = datetime.fromtimestamp(record.created)
        # 使用 %f 获取微秒，然后截取前 3 位作为毫秒
        formatted = ct.strftime("%Y-%m-%d %H:%M:%S")
        milliseconds = int(ct.microsecond / 1000)
        return f"{formatted},{milliseconds:03d}"

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        Args:
            record: 日志记录

        Returns:
            格式化后的日志字符串
        """
        # 使用自定义的时间格式化
        record.asctime = self.formatTime(record)
        # 使用父类的格式化方法
        return logging.Formatter.format(self, record)


def get_logger(name: str) -> logging.Logger:
    """获取带有 SmartClaw 格式的日志器

    Args:
        name: 日志器名称（通常使用 __name__）

    Returns:
        配置好格式的日志器
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(SmartClawFormatter())
        logger.addHandler(handler)
    return logger
