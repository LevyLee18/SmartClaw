"""测试 SystemPromptBuilder.__init__()

测试要点：
1. 验证 memory_manager 正确初始化
2. 验证 session_manager 正确初始化
3. 验证配置正确存储
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestSystemPromptBuilderInit:
    """SystemPromptBuilder.__init__ 测试类"""

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = str(temp_dir / "smartclaw_test")
        config.agent.max_tokens = 100000
        config.agent.near_memory_days = 7
        return config

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """创建临时目录"""
        (tmp_path / "smartclaw_test").mkdir()
        return tmp_path

    @pytest.fixture
    def mock_memory_manager(self) -> MagicMock:
        """创建模拟 MemoryManager"""
        manager = MagicMock()
        return manager

    @pytest.fixture
    def mock_session_manager(self) -> MagicMock:
        """创建模拟 SessionManager"""
        manager = MagicMock()
        return manager

    def test_init_with_all_params(self, mock_config: MagicMock, mock_memory_manager: MagicMock,
                                  mock_session_manager: MagicMock) -> None:
        """测试完整参数初始化"""
        from backend.agent.system_prompt import SystemPromptBuilder

        builder = SystemPromptBuilder(
            config=mock_config,
            memory_manager=mock_memory_manager,
            session_manager=mock_session_manager,
        )

        assert builder.config == mock_config
        assert builder.memory_manager == mock_memory_manager
        assert builder.session_manager == mock_session_manager

    def test_init_stores_config(self, mock_config: MagicMock, mock_memory_manager: MagicMock,
                                  mock_session_manager: MagicMock) -> None:
        """测试配置正确存储"""
        from backend.agent.system_prompt import SystemPromptBuilder

        builder = SystemPromptBuilder(
            config=mock_config,
            memory_manager=mock_memory_manager,
            session_manager=mock_session_manager,
        )

        # 验证配置属性可访问
        assert hasattr(builder, "config")
        assert builder.config.storage.base_path == mock_config.storage.base_path
        assert builder.config.agent.max_tokens == 100000

    def test_init_stores_managers(self, mock_config: MagicMock, mock_memory_manager: MagicMock,
                                    mock_session_manager: MagicMock) -> None:
        """测试管理器正确存储"""
        from backend.agent.system_prompt import SystemPromptBuilder

        builder = SystemPromptBuilder(
            config=mock_config,
            memory_manager=mock_memory_manager,
            session_manager=mock_session_manager,
        )

        # 验证管理器属性可访问
        assert hasattr(builder, "memory_manager")
        assert hasattr(builder, "session_manager")
        assert builder.memory_manager == mock_memory_manager
        assert builder.session_manager == mock_session_manager

    def test_init_with_default_config(self, mock_memory_manager: MagicMock,
                                       mock_session_manager: MagicMock) -> None:
        """测试默认配置"""
        from backend.agent.system_prompt import SystemPromptBuilder
        from backend.config.models import Settings

        # 使用默认配置
        config = Settings()
        builder = SystemPromptBuilder(
            config=config,
            memory_manager=mock_memory_manager,
            session_manager=mock_session_manager,
        )

        assert builder.config == config
