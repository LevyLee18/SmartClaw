"""测试 SmartClawError 基类

测试要点：
1. 错误属性：error_code, message, detail, suggestion
2. 错误消息格式化
3. 错误继承和异常捕获
"""

import pytest


class TestSmartClawError:
    """SmartClawError 基类测试"""

    def test_error_creation_with_all_attributes(self) -> None:
        """测试创建错误并设置所有属性"""
        from backend.errors.base import SmartClawError

        error = SmartClawError(
            message="Test error message",
            error_code="TEST_001",
            detail="This is the detail",
            suggestion="Try this fix",
        )

        assert error.error_code == "TEST_001"
        assert error.message == "Test error message"
        assert error.detail == "This is the detail"
        assert error.suggestion == "Try this fix"

    def test_error_creation_with_minimal_attributes(self) -> None:
        """测试创建错误仅设置消息"""
        from backend.errors.base import SmartClawError

        error = SmartClawError(message="Simple error")

        assert error.message == "Simple error"
        assert error.error_code == "UNKNOWN"  # 默认错误码
        assert error.detail == ""
        assert error.suggestion == ""

    def test_error_message_formatting(self) -> None:
        """测试错误消息格式化"""
        from backend.errors.base import SmartClawError

        error = SmartClawError(
            message="Config not found",
            error_code="CFG_001",
            detail="File: ~/.smartclaw/config.yaml",
            suggestion="Run 'smartclaw init' to create config",
        )

        formatted = str(error)

        assert "[CFG_001]" in formatted
        assert "Config not found" in formatted
        assert "Detail:" in formatted
        assert "~/.smartclaw/config.yaml" in formatted
        assert "Suggestion:" in formatted
        assert "Run 'smartclaw init'" in formatted

    def test_error_message_without_detail_and_suggestion(self) -> None:
        """测试没有详情和建议的错误消息"""
        from backend.errors.base import SmartClawError

        error = SmartClawError(
            message="Simple error",
            error_code="SIMPLE_001",
        )

        formatted = str(error)

        assert "[SIMPLE_001]" in formatted
        assert "Simple error" in formatted
        assert "Detail:" not in formatted
        assert "Suggestion:" not in formatted

    def test_error_is_exception(self) -> None:
        """测试错误是异常类的子类"""
        from backend.errors.base import SmartClawError

        assert issubclass(SmartClawError, Exception)

    def test_error_can_be_raised_and_caught(self) -> None:
        """测试错误可以被抛出和捕获"""
        from backend.errors.base import SmartClawError

        with pytest.raises(SmartClawError) as exc_info:
            raise SmartClawError(
                message="Test exception",
                error_code="TEST_002",
            )

        assert exc_info.value.error_code == "TEST_002"
        assert exc_info.value.message == "Test exception"

    def test_error_to_dict(self) -> None:
        """测试错误转换为字典"""
        from backend.errors.base import SmartClawError

        error = SmartClawError(
            message="Test error",
            error_code="TEST_003",
            detail="Some detail",
            suggestion="Some suggestion",
        )

        error_dict = error.to_dict()

        assert error_dict["error_code"] == "TEST_003"
        assert error_dict["message"] == "Test error"
        assert error_dict["detail"] == "Some detail"
        assert error_dict["suggestion"] == "Some suggestion"

    def test_error_repr(self) -> None:
        """测试错误的 repr 表示"""
        from backend.errors.base import SmartClawError

        error = SmartClawError(
            message="Test error",
            error_code="TEST_004",
        )

        repr_str = repr(error)

        assert "SmartClawError" in repr_str
        assert "TEST_004" in repr_str


class TestErrorSubclasses:
    """错误子类测试"""

    def test_config_error_exists(self) -> None:
        """测试 ConfigError 存在"""
        from backend.errors.base import ConfigError

        error = ConfigError(
            message="Invalid config",
            error_code="CFG_001",
        )

        assert error.error_code == "CFG_001"
        assert error.message == "Invalid config"

    def test_config_error_inherits_from_base(self) -> None:
        """测试 ConfigError 继承自 SmartClawError"""
        from backend.errors.base import ConfigError, SmartClawError

        assert issubclass(ConfigError, SmartClawError)

    def test_session_error(self) -> None:
        """测试 SessionError"""
        from backend.errors.base import SessionError

        error = SessionError(
            message="Session not found",
            error_code="SES_001",
        )

        assert error.error_code == "SES_001"
        assert isinstance(error, Exception)

    def test_memory_error(self) -> None:
        """测试 MemoryError"""
        from backend.errors.base import MemoryError as SmartClawMemoryError

        error = SmartClawMemoryError(
            message="Memory file not found",
            error_code="MEM_001",
        )

        assert error.error_code == "MEM_001"

    def test_rag_error(self) -> None:
        """测试 RAGError"""
        from backend.errors.base import RAGError

        error = RAGError(
            message="Index build failed",
            error_code="RAG_001",
        )

        assert error.error_code == "RAG_001"

    def test_tool_error(self) -> None:
        """测试 ToolError"""
        from backend.errors.base import ToolError

        error = ToolError(
            message="Tool execution failed",
            error_code="TOOL_001",
        )

        assert error.error_code == "TOOL_001"

    def test_container_error(self) -> None:
        """测试 ContainerError"""
        from backend.errors.base import ContainerError

        error = ContainerError(
            message="Container crashed",
            error_code="CTR_001",
        )

        assert error.error_code == "CTR_001"

    def test_security_error(self) -> None:
        """测试 SecurityError"""
        from backend.errors.base import SecurityError

        error = SecurityError(
            message="Path traversal detected",
            error_code="SEC_001",
        )

        assert error.error_code == "SEC_001"


class TestErrorCodes:
    """错误码格式测试"""

    def test_config_error_code_prefix(self) -> None:
        """测试 ConfigError 错误码前缀"""
        from backend.errors.base import ConfigError

        error = ConfigError(message="Test", error_code="CFG_001")
        assert error.error_code.startswith("CFG_")

    def test_session_error_code_prefix(self) -> None:
        """测试 SessionError 错误码前缀"""
        from backend.errors.base import SessionError

        error = SessionError(message="Test", error_code="SES_001")
        assert error.error_code.startswith("SES_")

    def test_memory_error_code_prefix(self) -> None:
        """测试 MemoryError 错误码前缀"""
        from backend.errors.base import MemoryError as SmartClawMemoryError

        error = SmartClawMemoryError(message="Test", error_code="MEM_001")
        assert error.error_code.startswith("MEM_")

    def test_rag_error_code_prefix(self) -> None:
        """测试 RAGError 错误码前缀"""
        from backend.errors.base import RAGError

        error = RAGError(message="Test", error_code="RAG_001")
        assert error.error_code.startswith("RAG_")

    def test_tool_error_code_prefix(self) -> None:
        """测试 ToolError 错误码前缀"""
        from backend.errors.base import ToolError

        error = ToolError(message="Test", error_code="TOOL_001")
        assert error.error_code.startswith("TOOL_")

    def test_container_error_code_prefix(self) -> None:
        """测试 ContainerError 错误码前缀"""
        from backend.errors.base import ContainerError

        error = ContainerError(message="Test", error_code="CTR_001")
        assert error.error_code.startswith("CTR_")

    def test_security_error_code_prefix(self) -> None:
        """测试 SecurityError 错误码前缀"""
        from backend.errors.base import SecurityError

        error = SecurityError(message="Test", error_code="SEC_001")
        assert error.error_code.startswith("SEC_")
