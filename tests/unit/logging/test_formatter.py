"""测试日志格式化器"""
import logging
import re
from datetime import datetime

import pytest


class TestLogFormatter:
    """日志格式化器测试类"""

    def test_log_format_contains_timestamp(self):
        """测试日志格式包含时间戳"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        record = logging.LogRecord(
            name="smartclaw.agent",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # 验证时间戳格式：YYYY-MM-DD HH:MM:SS,mmm
        timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}"
        assert re.search(timestamp_pattern, formatted), f"Timestamp not found in: {formatted}"

    def test_log_format_contains_module_name(self):
        """测试日志格式包含模块名"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        record = logging.LogRecord(
            name="smartclaw.agent.session",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "smartclaw.agent.session" in formatted

    def test_log_format_contains_level(self):
        """测试日志格式包含日志级别"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        record = logging.LogRecord(
            name="smartclaw.agent",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test warning",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "WARNING" in formatted

    def test_log_format_contains_message(self):
        """测试日志格式包含消息内容"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        record = logging.LogRecord(
            name="smartclaw.agent",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Session created successfully",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "Session created successfully" in formatted

    def test_log_format_complete_structure(self):
        """测试完整日志格式结构"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        record = logging.LogRecord(
            name="smartclaw.tools.terminal",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Tool invoked: terminal",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # 验证完整格式：{时间戳} - {模块名} - {级别} - {消息}
        # 格式示例：2026-03-18 14:30:15,123 - smartclaw.agent - INFO - Session created
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - [\w.]+ - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - .+"
        assert re.match(pattern, formatted), f"Format mismatch: {formatted}"

    def test_log_format_different_levels(self):
        """测试不同日志级别的格式"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, level_name in levels:
            record = logging.LogRecord(
                name="smartclaw.test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg=f"Test {level_name}",
                args=(),
                exc_info=None,
            )
            formatted = formatter.format(record)
            assert level_name in formatted, f"{level_name} not found in: {formatted}"

    def test_timestamp_precision_milliseconds(self):
        """测试时间戳精确到毫秒"""
        from backend.logging.formatter import SmartClawFormatter

        formatter = SmartClawFormatter()
        record = logging.LogRecord(
            name="smartclaw.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # 验证毫秒部分存在（,后跟3位数字）
        assert re.search(r",\d{3} -", formatted), f"Milliseconds not found in: {formatted}"
