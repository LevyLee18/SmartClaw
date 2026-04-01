"""测试 MemoryIndexManager 工具适配器

测试要点：
1. get_search_tool() - 返回 search_memory 工具适配器
2. 工具名称正确
3. 工具描述正确
4. 工具参数正确
5. 工具可调用
6. 支持日期范围过滤
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest


class TestMemoryIndexManagerGetSearchTool:
    """MemoryIndexManager.get_search_tool() 测试"""

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> Mock:
        """创建模拟配置"""
        config = Mock()
        config.storage.base_path = temp_dir
        config.rag.top_k = 5
        config.rag.chunk_size = 1024
        config.rag.chunk_overlap = 128
        config.embedding.model = "text-embedding-3-small"
        config.embedding.dimensions = 1536
        config.embedding.api_key = "test-key"
        return config

    def test_get_search_tool_returns_dict(self, mock_config: Mock) -> None:
        """测试 get_search_tool() 返回字典"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        # 使用 mock 跳过真实的初始化
        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            tool = manager.get_search_tool()

            assert isinstance(tool, dict)

    def test_get_search_tool_has_name(self, mock_config: Mock) -> None:
        """测试工具包含 name 字段"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            tool = manager.get_search_tool()

            assert "name" in tool
            assert tool["name"] == "search_memory"

    def test_get_search_tool_has_description(self, mock_config: Mock) -> None:
        """测试工具包含 description 字段"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            tool = manager.get_search_tool()

            assert "description" in tool
            assert isinstance(tool["description"], str)
            assert len(tool["description"]) > 0

    def test_get_search_tool_has_callable(self, mock_config: Mock) -> None:
        """测试工具包含可调用的函数"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            tool = manager.get_search_tool()

            assert "func" in tool
            assert callable(tool["func"])

    def test_get_search_tool_callable_returns_results(self, mock_config: Mock) -> None:
        """测试工具函数返回检索结果"""
        from backend.rag.memory_index_manager import MemoryIndexManager
        from backend.rag.models import Segment

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            # Mock search 方法
            mock_segments = [
                Segment(
                    content="Test content 1",
                    source="test1.md",
                    file_type="long_term",
                    timestamp="2026-04-01",
                    score=0.9
                ),
                Segment(
                    content="Test content 2",
                    source="test2.md",
                    file_type="long_term",
                    timestamp="2026-04-01",
                    score=0.8
                )
            ]

            with patch.object(manager, "search", return_value=mock_segments):
                tool = manager.get_search_tool()
                result = tool["func"](query="test query")

                # 验证返回值是字符串
                assert isinstance(result, str)
                # 验证包含结果信息
                assert "test1.md" in result or "Test content 1" in result

    def test_get_search_tool_with_date_range(self, mock_config: Mock) -> None:
        """测试工具函数支持日期范围过滤"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            # Mock _search_with_filters 方法
            with patch.object(manager, "_search_with_filters", return_value=[]):
                tool = manager.get_search_tool()
                result = tool["func"](
                    query="test query",
                    date_range=("2026-03-01", "2026-03-31")
                )

                # 验证返回值是字符串
                assert isinstance(result, str)

    def test_get_search_tool_signature(self, mock_config: Mock) -> None:
        """测试工具函数签名正确"""
        from backend.rag.memory_index_manager import MemoryIndexManager
        from inspect import signature

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            tool = manager.get_search_tool()

            # 获取函数签名
            sig = signature(tool["func"])
            params = list(sig.parameters.keys())

            # 验证参数包含 query, top_k, date_range
            assert "query" in params
            assert "top_k" in params
            assert "date_range" in params

    def test_get_search_tool_empty_results(self, mock_config: Mock) -> None:
        """测试工具函数处理空结果"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            # Mock search 返回空列表
            with patch.object(manager, "search", return_value=[]):
                tool = manager.get_search_tool()
                result = tool["func"](query="test query")

                # 验证返回值包含未找到信息
                assert isinstance(result, str)

    def test_get_search_tool_multiple_calls(self, mock_config: Mock) -> None:
        """测试多次调用 get_search_tool() 返回独立的工具实例"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            tool1 = manager.get_search_tool()
            tool2 = manager.get_search_tool()

            # 验证是独立的实例
            assert tool1 is not tool2
            assert tool1["name"] == tool2["name"]
            assert tool1["func"] is not tool2["func"]

    def test_get_search_tool_with_custom_top_k(self, mock_config: Mock) -> None:
        """测试工具函数支持自定义 top_k"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, config: None
        ):
            manager = MemoryIndexManager(mock_config)
            manager.config = mock_config
            manager.rag_config = mock_config.rag

            # Mock search 方法
            with patch.object(manager, "search", return_value=[]) as mock_search:
                tool = manager.get_search_tool()
                tool["func"](query="test query", top_k=10)

                # 验证 search 被调用，且 top_k 参数传递正确
                mock_search.assert_called_once_with("test query", 10)
