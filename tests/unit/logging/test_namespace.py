"""测试日志模块命名空间

验证各模块命名空间独立、可过滤。
"""

import logging

import pytest

from backend.logging.formatter import get_logger


class TestModuleNamespace:
    """模块命名空间测试类"""

    def test_agent_namespace(self):
        """测试 Agent 模块命名空间"""
        logger = get_logger("smartclaw.agent")

        assert logger.name == "smartclaw.agent"
        assert isinstance(logger, logging.Logger)

    def test_agent_session_namespace(self):
        """测试 Agent Session 子模块命名空间"""
        logger = get_logger("smartclaw.agent.session")

        assert logger.name == "smartclaw.agent.session"
        # 应该是 smartclaw.agent 的子 logger
        parent = logger.parent
        assert parent is not None
        assert parent.name == "smartclaw.agent"

    def test_tools_namespace(self):
        """测试 Tools 模块命名空间"""
        logger = get_logger("smartclaw.tools")

        assert logger.name == "smartclaw.tools"

    def test_tools_terminal_namespace(self):
        """测试 Terminal 工具子模块命名空间"""
        logger = get_logger("smartclaw.tools.terminal")

        assert logger.name == "smartclaw.tools.terminal"
        # 应该是 smartclaw.tools 的子 logger
        parent = logger.parent
        assert parent is not None
        assert parent.name == "smartclaw.tools"

    def test_tools_python_repl_namespace(self):
        """测试 Python REPL 子模块命名空间"""
        logger = get_logger("smartclaw.tools.python_repl")

        assert logger.name == "smartclaw.tools.python_repl"
        # 应该是 smartclaw.tools 的子 logger
        parent = logger.parent
        assert parent is not None
        assert parent.name == "smartclaw.tools"

    def test_memory_namespace(self):
        """测试 Memory 模块命名空间"""
        logger = get_logger("smartclaw.memory")

        assert logger.name == "smartclaw.memory"

    def test_rag_namespace(self):
        """测试 RAG 模块命名空间"""
        logger = get_logger("smartclaw.rag")

        assert logger.name == "smartclaw.rag"

    def test_container_namespace(self):
        """测试 Container 模块命名空间"""
        logger = get_logger("smartclaw.container")

        assert logger.name == "smartclaw.container"


class TestNamespaceHierarchy:
    """命名空间层级测试类"""

    def test_hierarchy_structure(self):
        """测试命名空间层级结构"""
        # 创建层级结构的 logger
        agent_logger = get_logger("smartclaw.agent")
        session_logger = get_logger("smartclaw.agent.session")

        # 验证层级关系
        assert session_logger.parent == agent_logger

    def test_level_propagation(self):
        """测试日志级别传播"""
        # 设置父 logger 级别
        parent_logger = get_logger("smartclaw.tools")
        parent_logger.setLevel(logging.WARNING)

        # 子 logger 应该继承父 logger 的级别设置
        child_logger = get_logger("smartclaw.tools.terminal")

        # 子 logger 默认不设置级别时会使用父 logger 的级别
        assert child_logger.getEffectiveLevel() == logging.WARNING


class TestNamespaceFiltering:
    """命名空间过滤测试类"""

    def test_filter_by_namespace(self):
        """测试按命名空间过滤日志"""
        # 创建不同命名空间的 logger
        agent_logger = get_logger("smartclaw.agent")
        memory_logger = get_logger("smartclaw.memory")

        # 设置不同的级别
        agent_logger.setLevel(logging.DEBUG)
        memory_logger.setLevel(logging.WARNING)

        # 验证级别独立
        assert agent_logger.level == logging.DEBUG
        assert memory_logger.level == logging.WARNING

    def test_namespace_independence(self):
        """测试命名空间独立性"""
        # 创建两个不同命名空间的 logger
        logger1 = get_logger("smartclaw.agent")
        logger2 = get_logger("smartclaw.memory")

        # 设置不同的处理器
        assert logger1.handlers is not None
        assert logger2.handlers is not None

        # 每个 logger 应该有独立的处理器
        # 注意：由于 get_logger 的实现，同名 logger 会共享处理器
        # 但不同名 logger 应该有独立的处理器
        assert len(logger1.handlers) >= 1
        assert len(logger2.handlers) >= 1


class TestNamespaceWithLogging:
    """命名空间日志记录测试类"""

    def test_log_output_contains_namespace(self, caplog: pytest.LogCaptureFixture):
        """测试日志输出包含命名空间"""
        logger = get_logger("smartclaw.agent")
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG, logger="smartclaw.agent"):
            logger.info("Test message")

        # 验证日志记录
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.name == "smartclaw.agent"
        assert record.message == "Test message"

    def test_different_namespaces_log_independently(
        self, caplog: pytest.LogCaptureFixture
    ):
        """测试不同命名空间独立记录日志"""
        agent_logger = get_logger("smartclaw.agent")
        memory_logger = get_logger("smartclaw.memory")

        agent_logger.setLevel(logging.DEBUG)
        memory_logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            agent_logger.info("Agent message")
            memory_logger.info("Memory message")

        # 应该有两条日志记录
        assert len(caplog.records) == 2

        # 验证命名空间
        names = [r.name for r in caplog.records]
        assert "smartclaw.agent" in names
        assert "smartclaw.memory" in names
