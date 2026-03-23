"""SmartClaw 日志模块

提供统一的日志格式化和配置功能。
"""

from backend.logging.formatter import SmartClawFormatter, get_logger
from backend.logging.redactor import (
    SmartClawRedactingFilter,
    redact_api_key,
    redact_message,
    redact_path,
    redact_url,
)
from backend.logging.rotating import (
    DEFAULT_BACKUP_COUNT,
    DEFAULT_MAX_BYTES,
    create_rotating_handler,
    get_rotating_logger,
)

__all__ = [
    "SmartClawFormatter",
    "get_logger",
    "create_rotating_handler",
    "get_rotating_logger",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_BACKUP_COUNT",
    "redact_api_key",
    "redact_path",
    "redact_url",
    "redact_message",
    "SmartClawRedactingFilter",
]
