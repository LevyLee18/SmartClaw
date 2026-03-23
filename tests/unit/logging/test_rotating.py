"""测试日志轮转功能

测试要点：
1. 10MB 触发轮转
2. 保留 5 个备份文件
3. 轮转文件命名正确
4. 日志目录自动创建
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.logging.formatter import SmartClawFormatter


class TestRotatingFileHandler:
    """日志轮转测试类"""

    def test_rotating_handler_creation(self, tmp_path: Path) -> None:
        """测试轮转处理器创建"""
        from backend.logging.rotating import create_rotating_handler

        log_file = tmp_path / "logs" / "test.log"

        handler = create_rotating_handler(
            log_path=str(log_file),
            max_bytes=10 * 1024 * 1024,  # 10MB
            backup_count=5,
        )

        assert handler is not None
        assert isinstance(handler, logging.handlers.RotatingFileHandler)
        assert handler.maxBytes == 10 * 1024 * 1024
        assert handler.backupCount == 5

    def test_log_directory_auto_created(self, tmp_path: Path) -> None:
        """测试日志目录自动创建"""
        from backend.logging.rotating import create_rotating_handler

        log_dir = tmp_path / "logs"
        log_file = log_dir / "smartclaw.log"

        # 目录不存在
        assert not log_dir.exists()

        handler = create_rotating_handler(
            log_path=str(log_file),
            max_bytes=10 * 1024 * 1024,
            backup_count=5,
        )

        # 目录应该被自动创建
        assert log_dir.exists()
        handler.close()

    def test_rotating_handler_with_formatter(self, tmp_path: Path) -> None:
        """测试轮转处理器使用 SmartClaw 格式化器"""
        from backend.logging.rotating import create_rotating_handler

        log_file = tmp_path / "logs" / "test.log"

        handler = create_rotating_handler(
            log_path=str(log_file),
            max_bytes=10 * 1024 * 1024,
            backup_count=5,
        )

        # 验证格式化器类型
        assert isinstance(handler.formatter, SmartClawFormatter)
        handler.close()

    def test_rotation_triggered_at_max_bytes(self, tmp_path: Path) -> None:
        """测试达到 max_bytes 时触发轮转"""
        from backend.logging.rotating import create_rotating_handler

        log_file = tmp_path / "logs" / "test.log"

        # 使用很小的 max_bytes 以便测试
        handler = create_rotating_handler(
            log_path=str(log_file),
            max_bytes=100,  # 100 bytes for testing
            backup_count=3,
        )

        logger = logging.getLogger("test_rotation")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 写入足够多的日志以触发轮转
        for i in range(20):
            logger.info(f"Test message {i} - " + "x" * 10)

        handler.flush()

        # 检查备份文件是否创建
        backup_file = Path(str(log_file) + ".1")
        assert backup_file.exists(), "Rotation backup file should be created"

        # 清理
        logger.removeHandler(handler)
        handler.close()

    def test_backup_count_limit(self, tmp_path: Path) -> None:
        """测试备份数量限制"""
        from backend.logging.rotating import create_rotating_handler

        log_file = tmp_path / "logs" / "test.log"

        # 使用很小的 max_bytes 和 backup_count=3
        handler = create_rotating_handler(
            log_path=str(log_file),
            max_bytes=50,  # 50 bytes for testing
            backup_count=3,
        )

        logger = logging.getLogger("test_backup_limit")
        logger.handlers.clear()  # 清除之前的 handlers
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 写入足够多的日志以触发多次轮转
        for i in range(50):
            logger.info(f"Message {i} - " + "y" * 20)

        handler.flush()

        # 检查备份数量不超过 backup_count
        log_dir = log_file.parent
        backup_files = list(log_dir.glob("test.log.*"))

        # 应该最多只有 3 个备份文件
        assert len(backup_files) <= 3, f"Should have at most 3 backup files, got {len(backup_files)}"

        # 清理
        logger.removeHandler(handler)
        handler.close()

    def test_get_rotating_logger(self, tmp_path: Path) -> None:
        """测试获取带轮转功能的日志器"""
        from backend.logging.rotating import get_rotating_logger

        log_file = tmp_path / "logs" / "smartclaw.log"

        logger = get_rotating_logger(
            name="smartclaw.test",
            log_path=str(log_file),
            max_bytes=10 * 1024 * 1024,
            backup_count=5,
        )

        assert logger is not None
        assert logger.name == "smartclaw.test"
        assert logger.level == logging.DEBUG  # 默认允许所有级别

        # 验证有一个 RotatingFileHandler
        rotating_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(rotating_handlers) == 1

        # 清理
        for h in logger.handlers:
            h.close()
        logger.handlers.clear()

    def test_default_parameters(self, tmp_path: Path) -> None:
        """测试默认参数值"""
        from backend.logging.rotating import create_rotating_handler, DEFAULT_MAX_BYTES, DEFAULT_BACKUP_COUNT

        # 验证默认常量
        assert DEFAULT_MAX_BYTES == 10 * 1024 * 1024  # 10MB
        assert DEFAULT_BACKUP_COUNT == 5

        log_file = tmp_path / "logs" / "test.log"

        handler = create_rotating_handler(log_path=str(log_file))

        # 验证默认值
        assert handler.maxBytes == DEFAULT_MAX_BYTES
        assert handler.backupCount == DEFAULT_BACKUP_COUNT

        handler.close()

    def test_concurrent_logging_safety(self, tmp_path: Path) -> None:
        """测试并发日志写入安全性"""
        import threading

        from backend.logging.rotating import get_rotating_logger

        log_file = tmp_path / "logs" / "concurrent.log"

        logger = get_rotating_logger(
            name="smartclaw.concurrent",
            log_path=str(log_file),
            max_bytes=1024,
            backup_count=2,
        )

        errors = []
        write_count = 100

        def write_logs(thread_id: int) -> None:
            try:
                for i in range(write_count):
                    logger.info(f"Thread {thread_id} - Message {i}")
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时写入
        threads = [
            threading.Thread(target=write_logs, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证没有错误发生
        assert len(errors) == 0, f"Concurrent logging errors: {errors}"

        # 清理
        for h in logger.handlers:
            h.close()
        logger.handlers.clear()


class TestRotatingLoggerIntegration:
    """日志轮转集成测试"""

    def test_full_logging_workflow(self, tmp_path: Path) -> None:
        """测试完整日志工作流"""
        from backend.logging.rotating import get_rotating_logger

        log_file = tmp_path / "logs" / "workflow.log"

        # 创建日志器
        logger = get_rotating_logger(
            name="smartclaw.workflow",
            log_path=str(log_file),
            max_bytes=500,
            backup_count=3,
        )

        # 记录各种级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # 验证日志文件存在
        assert log_file.exists()

        # 验证日志内容包含格式化信息
        content = log_file.read_text()
        assert "smartclaw.workflow" in content
        assert "INFO" in content
        assert "Info message" in content

        # 清理
        for h in logger.handlers:
            h.close()
        logger.handlers.clear()

    def test_log_format_correctness(self, tmp_path: Path) -> None:
        """测试日志格式正确性"""
        import re

        from backend.logging.rotating import get_rotating_logger

        log_file = tmp_path / "logs" / "format.log"

        logger = get_rotating_logger(
            name="smartclaw.format",
            log_path=str(log_file),
        )

        logger.info("Test format message")

        content = log_file.read_text()

        # 验证格式：时间戳 - 模块名 - 级别 - 消息
        # 时间戳格式：YYYY-MM-DD HH:MM:SS,mmm
        pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - smartclaw\.format - INFO - Test format message"
        assert re.search(pattern, content), f"Log format incorrect: {content}"

        # 清理
        for h in logger.handlers:
            h.close()
        logger.handlers.clear()
