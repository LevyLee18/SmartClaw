"""测试敏感信息脱敏功能

测试要点：
1. API Key 脱敏（保留前4位和后4位）
2. 用户数据路径脱敏
3. URL 敏感参数脱敏
4. 密码/密钥替换为 [REDACTED]
"""

import pytest

from backend.logging.redactor import (
    redact_api_key,
    redact_path,
    redact_url,
    redact_message,
    SmartClawRedactingFilter,
)


class TestRedactApiKey:
    """API Key 脱敏测试类"""

    def test_redact_anthropic_key(self) -> None:
        """测试 Anthropic API Key 脱敏"""
        key = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456"
        result = redact_api_key(key)

        # 应该保留前缀 sk-a 和后4位
        assert "sk-a" in result
        assert result.endswith("456")
        assert "****" in result
        assert "bcdefghijklmnopqrstuvwxyz123" not in result

    def test_redact_openai_key(self) -> None:
        """测试 OpenAI API Key 脱敏"""
        key = "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"
        result = redact_api_key(key)

        # 应该保留前缀 sk-p 和后4位
        assert "sk-p" in result
        assert result.endswith("wxyz")
        assert "****" in result

    def test_redact_short_key(self) -> None:
        """测试短 Key 的脱敏"""
        key = "sk-1234"
        result = redact_api_key(key)

        # 短 key 应该完全隐藏或部分隐藏
        assert "sk-" not in result or "****" in result

    def test_redact_empty_key(self) -> None:
        """测试空 Key"""
        assert redact_api_key("") == ""
        assert redact_api_key(None) == ""

    def test_redact_non_string_key(self) -> None:
        """测试非字符串类型"""
        assert redact_api_key(12345) == "12345"


class TestRedactPath:
    """路径脱敏测试类"""

    def test_redact_home_path(self) -> None:
        """测试用户主目录路径脱敏"""
        path = "/Users/john/.smartclaw/config.yaml"
        result = redact_path(path)

        # 用户名应该被脱敏
        assert "john" not in result
        assert "~" in result or "***" in result

    def test_redact_windows_path(self) -> None:
        """测试 Windows 路径脱敏"""
        path = "C:\\Users\\admin\\.smartclaw\\config.yaml"
        result = redact_path(path)

        # 用户名应该被脱敏
        assert "admin" not in result

    def test_redact_non_user_path(self) -> None:
        """测试非用户路径（不脱敏）"""
        path = "/var/log/smartclaw.log"
        result = redact_path(path)

        # 非用户路径保持不变
        assert path == result

    def test_redact_empty_path(self) -> None:
        """测试空路径"""
        assert redact_path("") == ""
        assert redact_path(None) == ""


class TestRedactUrl:
    """URL 敏感参数脱敏测试类"""

    def test_redact_url_with_token(self) -> None:
        """测试带 token 的 URL"""
        url = "https://api.example.com/data?token=secret123&id=123"
        result = redact_url(url)

        assert "secret123" not in result
        assert "[REDACTED]" in result
        assert "id=123" in result  # 非敏感参数保留

    def test_redact_url_with_api_key(self) -> None:
        """测试带 api_key 的 URL"""
        url = "https://api.openai.com/v1/chat?key=sk-abc123xyz"
        result = redact_url(url)

        assert "sk-abc123xyz" not in result
        assert "[REDACTED]" in result

    def test_redact_url_with_password(self) -> None:
        """测试带 password 的 URL"""
        url = "https://user:mypassword@example.com/api"
        result = redact_url(url)

        assert "mypassword" not in result
        assert "[REDACTED]" in result

    def test_redact_url_no_sensitive_params(self) -> None:
        """测试无敏感参数的 URL"""
        url = "https://api.example.com/data?page=1&limit=10"
        result = redact_url(url)

        # 无敏感参数，保持不变
        assert url == result

    def test_redact_empty_url(self) -> None:
        """测试空 URL"""
        assert redact_url("") == ""
        assert redact_url(None) == ""


class TestRedactMessage:
    """消息脱敏测试类"""

    def test_redact_message_with_api_key(self) -> None:
        """测试包含 API Key 的消息"""
        message = "Using API key sk-ant-1234567890abcdef to connect"
        result = redact_message(message)

        assert "sk-ant-1234567890abcdef" not in result
        assert "sk-a" in result  # 保留前缀

    def test_redact_message_with_password(self) -> None:
        """测试包含密码的消息"""
        message = "Login with password=secret123 failed"
        result = redact_message(message)

        assert "secret123" not in result
        assert "[REDACTED]" in result

    def test_redact_message_with_path(self) -> None:
        """测试包含路径的消息"""
        message = "Reading config from /Users/alice/.smartclaw/config.yaml"
        result = redact_message(message)

        assert "alice" not in result

    def test_redact_message_with_url(self) -> None:
        """测试包含 URL 的消息"""
        message = "Fetching https://api.example.com?token=mytoken"
        result = redact_message(message)

        assert "mytoken" not in result

    def test_redact_message_multiple_secrets(self) -> None:
        """测试包含多个敏感信息的消息"""
        message = "API key sk-abc123 and password=secret, token=xyz"
        result = redact_message(message)

        assert "sk-abc123" not in result
        assert "secret" not in result
        assert "xyz" not in result

    def test_redact_message_no_secrets(self) -> None:
        """测试无敏感信息的消息"""
        message = "Processing request for user session"
        result = redact_message(message)

        # 无敏感信息，保持不变
        assert message == result


class TestSmartClawRedactingFilter:
    """日志脱敏过滤器测试类"""

    def test_filter_creation(self) -> None:
        """测试过滤器创建"""
        filter_obj = SmartClawRedactingFilter()
        assert filter_obj is not None

    def test_filter_redacts_message(self) -> None:
        """测试过滤器脱敏日志消息"""
        import logging

        filter_obj = SmartClawRedactingFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API key sk-ant-1234567890abcdef",
            args=(),
            exc_info=None,
        )

        # 过滤器应该修改消息
        filter_obj.filter(record)

        assert "sk-ant-1234567890abcdef" not in record.msg
        assert "sk-a" in record.msg  # 保留前缀

    def test_filter_preserves_normal_message(self) -> None:
        """测试过滤器保留正常消息"""
        import logging

        filter_obj = SmartClawRedactingFilter()
        original_msg = "Processing user request"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=original_msg,
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        # 无敏感信息，消息应该保持不变
        assert record.msg == original_msg


class TestRedactorEdgeCases:
    """边界情况测试"""

    def test_unicode_message(self) -> None:
        """测试 Unicode 消息"""
        message = "用户 sk-ant-中文测试 登录成功"
        result = redact_message(message)

        # 应该处理 Unicode，但脱敏 API key
        assert "中文测试" not in result or "sk-ant" not in result

    def test_very_long_message(self) -> None:
        """测试超长消息"""
        message = "sk-ant-1234567890" * 1000
        result = redact_message(message)

        # 应该能处理超长消息
        assert len(result) > 0

    def test_nested_secrets(self) -> None:
        """测试嵌套的敏感信息"""
        message = "Config: {'api_key': 'sk-abc123', 'password': 'secret'}"
        result = redact_message(message)

        assert "sk-abc123" not in result
        assert "secret" not in result
