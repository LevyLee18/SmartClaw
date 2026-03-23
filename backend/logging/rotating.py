"""SmartClaw 日志轮转模块

提供基于大小的日志轮转功能，符合 SmartClaw 日志规范。

轮转策略：
- 单个日志文件最大 10MB
- 保留最近 5 个备份文件
- 使用 RotatingFileHandler 实现
"""

import logging
import logging.handlers
from pathlib import Path

from backend.logging.formatter import SmartClawFormatter

# 默认配置常量
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5


def create_rotating_handler(
    log_path: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.handlers.RotatingFileHandler:
    """创建带轮转功能的文件日志处理器

    Args:
        log_path: 日志文件路径
        max_bytes: 单个日志文件最大字节数，默认 10MB
        backup_count: 保留的备份文件数量，默认 5

    Returns:
        配置好的 RotatingFileHandler 实例
    """
    # 确保日志目录存在
    log_file = Path(log_path)
    log_dir = log_file.parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建 RotatingFileHandler
    handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    # 设置 SmartClaw 格式化器
    handler.setFormatter(SmartClawFormatter())

    return handler


def get_rotating_logger(
    name: str,
    log_path: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """获取带轮转功能的日志器

    创建一个配置了 RotatingFileHandler 的日志器，
    使用 SmartClaw 统一日志格式。

    Args:
        name: 日志器名称（如 smartclaw.agent）
        log_path: 日志文件路径
        max_bytes: 单个日志文件最大字节数，默认 10MB
        backup_count: 保留的备份文件数量，默认 5

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers):
        handler = create_rotating_handler(
            log_path=log_path,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )
        logger.addHandler(handler)

    # 设置日志级别为 DEBUG，让 handler 决定是否输出
    logger.setLevel(logging.DEBUG)

    return logger
