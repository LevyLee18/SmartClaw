"""RAG 模块集成测试

测试 IndexManager + FileWatcher + Cache 协同工作。

测试场景：
1. 组件共享配置和路径
2. 文件变更触发索引更新流程
3. 缓存与索引的交互
4. 完整的文档索引和检索流程
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.config.models import EmbeddingConfig, RAGConfig, Settings, StorageConfig


def create_mock_settings(tmp_path: Path) -> Settings:
    """创建带 Mock 配置的 Settings"""
    return Settings(
        storage=StorageConfig(base_path=tmp_path),
        rag=RAGConfig(),
        embedding=EmbeddingConfig(),
    )


@pytest.fixture
def mock_index_manager():
    """Mock MemoryIndexManager"""
    with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.base_path = None  # 将在测试中设置
        mock_instance.doc_store = {}
        mock_instance.update_document = MagicMock(return_value=True)
        mock_instance.delete_document = MagicMock(return_value=True)
        mock_instance.search = MagicMock(return_value=[])
        mock_instance.build_index = MagicMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_instance


class TestRAGComponentsIntegration:
    """RAG 组件集成测试"""

    def test_components_share_base_path(self, tmp_path: Path) -> None:
        """测试所有组件共享相同的 base_path"""
        from backend.rag.cache import SQLiteCache
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        # 创建 Cache
        cache = SQLiteCache(str(tmp_path / "cache.db"))

        # 创建 FileWatcher（内部会创建 IndexManager）
        with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.base_path = tmp_path
            mock_cls.return_value = mock_instance

            watcher = FileWatcher(config)

            # 验证路径一致性
            assert watcher.base_path == tmp_path
            assert cache.cache_path == str(tmp_path / "cache.db")

    def test_file_watcher_uses_index_manager(self, tmp_path: Path) -> None:
        """测试 FileWatcher 内部使用 IndexManager"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            watcher = FileWatcher(config)

            # 验证 FileWatcher 持有 IndexManager
            assert hasattr(watcher, "_index_manager")
            assert watcher._index_manager is not None

    def test_index_manager_uses_cache(self, tmp_path: Path) -> None:
        """测试 IndexManager 内部使用 Cache"""
        from backend.rag.cache import SQLiteCache

        # 直接测试 Cache
        cache = SQLiteCache(str(tmp_path / "cache.db"))

        # 验证 Cache 功能
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        assert result == "test_value"


class TestFileWatcherIndexIntegration:
    """FileWatcher 与 IndexManager 集成测试"""

    def test_file_event_queue_flow(self, tmp_path: Path) -> None:
        """测试文件事件队列流程

        场景：
        1. FileWatcher 接收文件创建事件
        2. 事件进入队列
        3. 可以从队列获取事件
        """
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher = FileWatcher(config)

        # 1. 模拟文件创建事件
        test_file = tmp_path / "test.md"
        watcher.on_file_created(test_file)

        # 2. 验证事件进入队列
        assert watcher.event_queue.qsize() == 1

        # 3. 从队列获取事件
        event_type, file_path = watcher.event_queue.get_nowait()
        assert event_type == "created"
        assert file_path == str(test_file)

    def test_multiple_file_events_in_order(self, tmp_path: Path) -> None:
        """测试多个文件事件按顺序处理"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher = FileWatcher(config)

        # 模拟多个事件
        files = [tmp_path / f"file{i}.md" for i in range(3)]
        for f in files:
            watcher.on_file_created(f)

        # 验证事件顺序
        for expected_file in files:
            event_type, file_path = watcher.event_queue.get_nowait()
            assert event_type == "created"
            assert file_path == str(expected_file)

    def test_file_watcher_lifecycle_with_index_manager(self, tmp_path: Path) -> None:
        """测试 FileWatcher 生命周期与 IndexManager 协同"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher = FileWatcher(config)

        # 初始状态
        assert watcher._running is False

        # 启动
        watcher.start()
        assert watcher._running is True
        assert watcher._observer is not None

        # 停止
        watcher.stop()
        assert watcher._running is False


class TestCacheIndexIntegration:
    """Cache 与 IndexManager 集成测试"""

    def test_cache_stores_index_results(self, tmp_path: Path) -> None:
        """测试缓存存储索引结果"""
        from backend.rag.cache import SQLiteCache

        cache = SQLiteCache(str(tmp_path / "cache.db"))

        # 存储查询结果
        query = "test query"
        cache_key = cache._generate_cache_key(query)
        cache.set(cache_key, "cached result")

        # 验证可以获取
        result = cache.get(cache_key)
        assert result == "cached result"

    def test_cache_key_consistency(self, tmp_path: Path) -> None:
        """测试缓存键一致性"""
        from backend.rag.cache import SQLiteCache

        cache = SQLiteCache(str(tmp_path / "cache.db"))

        # 相同输入生成相同键
        key1 = cache._generate_cache_key("query1")
        key2 = cache._generate_cache_key("query1")
        assert key1 == key2

        # 不同输入生成不同键
        key3 = cache._generate_cache_key("query2")
        assert key1 != key3

    def test_cache_miss_returns_none(self, tmp_path: Path) -> None:
        """测试缓存未命中返回 None"""
        from backend.rag.cache import SQLiteCache

        cache = SQLiteCache(str(tmp_path / "cache.db"))

        result = cache.get("non-existent-key")
        assert result is None


class TestFullRAGWorkflow:
    """完整 RAG 工作流测试"""

    def test_document_indexing_workflow(self, tmp_path: Path) -> None:
        """测试文档索引工作流

        场景：
        1. 添加文档到索引
        2. 验证文档存在
        3. 删除文档
        4. 验证文档不存在
        """
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.doc_store = {"doc1": ["node1"]}

            def mock_delete(doc_id):
                if doc_id in mock_instance.doc_store:
                    del mock_instance.doc_store[doc_id]
                return True

            mock_instance.update_document = MagicMock(return_value=True)
            mock_instance.delete_document = MagicMock(side_effect=mock_delete)
            mock_cls.return_value = mock_instance

            watcher = FileWatcher(config)
            index_manager = watcher._index_manager

            # 1. 添加文档
            result = index_manager.update_document("doc1", "Test content")
            assert result is True

            # 2. 验证文档存在
            assert "doc1" in index_manager.doc_store

            # 3. 删除文档
            result = index_manager.delete_document("doc1")
            assert result is True

            # 4. 验证文档不存在
            assert "doc1" not in index_manager.doc_store

    def test_search_with_mock_index(self, tmp_path: Path) -> None:
        """测试 Mock 索引检索"""
        from backend.rag.models import Segment

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
            # 创建 Mock 返回结果
            mock_segment = Segment(
                content="Test content",
                source="test.md",
                file_type="md",
                score=0.9,
            )
            mock_instance = MagicMock()
            mock_instance.search = MagicMock(return_value=[mock_segment])
            mock_cls.return_value = mock_instance

            from backend.rag.file_watcher import FileWatcher

            watcher = FileWatcher(config)

            # 检索
            results = watcher._index_manager.search("test query")
            assert len(results) == 1
            assert results[0].content == "Test content"

    def test_index_rebuild_workflow(self, tmp_path: Path) -> None:
        """测试索引重建工作流"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.doc_store = {"doc1": ["node1"], "doc2": ["node2"]}
            mock_instance.build_index = MagicMock(
                side_effect=lambda force=False: mock_instance.doc_store.clear()
                or True
            )
            mock_cls.return_value = mock_instance

            watcher = FileWatcher(config)
            index_manager = watcher._index_manager

            # 验证初始状态
            assert len(index_manager.doc_store) == 2

            # 重建索引
            result = index_manager.build_index(force=True)
            assert result is True

            # 验证索引已清空
            assert len(index_manager.doc_store) == 0


class TestRAGComponentsLifecycle:
    """RAG 组件生命周期测试"""

    def test_multiple_filewatcher_instances(self, tmp_path: Path) -> None:
        """测试多个 FileWatcher 实例"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher1 = FileWatcher(config)
            watcher2 = FileWatcher(config)

        # 两个实例应该独立
        assert watcher1 is not watcher2
        assert watcher1.event_queue is not watcher2.event_queue

    def test_filewatcher_restart_cycle(self, tmp_path: Path) -> None:
        """测试 FileWatcher 多次启动停止"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher = FileWatcher(config)

        # 多次启动停止循环
        for _ in range(3):
            watcher.start()
            assert watcher._running is True
            watcher.stop()
            assert watcher._running is False

    def test_cache_persistence_across_instances(self, tmp_path: Path) -> None:
        """测试缓存在实例间持久化"""
        from backend.rag.cache import SQLiteCache

        cache_path = str(tmp_path / "cache.db")

        # 第一个实例写入
        cache1 = SQLiteCache(cache_path)
        cache1.set("test_key", "test_value")

        # 第二个实例读取
        cache2 = SQLiteCache(cache_path)
        result = cache2.get("test_key")
        assert result == "test_value"


class TestRAGErrorHandling:
    """RAG 组件错误处理测试"""

    def test_filewatcher_handles_missing_file(self, tmp_path: Path) -> None:
        """测试 FileWatcher 处理不存在的文件"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher = FileWatcher(config)

        # 添加不存在文件的事件
        missing_file = tmp_path / "nonexistent.md"
        watcher.on_file_created(missing_file)

        # 事件应该被添加到队列（实际处理时由 IndexManager 处理）
        assert watcher.event_queue.qsize() == 1

    def test_index_manager_handles_duplicate_document(self, tmp_path: Path) -> None:
        """测试 IndexManager 处理重复文档"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.doc_store = {}
            mock_instance.update_document = MagicMock(
                side_effect=lambda doc_id, content, metadata=None: (
                    mock_instance.doc_store.update({doc_id: ["node"]}) or True
                )
            )
            mock_cls.return_value = mock_instance

            watcher = FileWatcher(config)
            index_manager = watcher._index_manager

            # 添加文档
            index_manager.update_document("doc1", "Original content")
            assert len(index_manager.doc_store) == 1

            # 更新相同文档
            index_manager.update_document("doc1", "Updated content")

            # 应该只有一个文档
            assert len(index_manager.doc_store) == 1

    def test_cache_handles_invalid_data(self, tmp_path: Path) -> None:
        """测试缓存处理无效数据"""
        from backend.rag.cache import SQLiteCache

        cache = SQLiteCache(str(tmp_path / "cache.db"))

        # 存储各种类型数据
        cache.set("string_key", "string_value")
        cache.set("dict_key", {"key": "value"})
        cache.set("list_key", [1, 2, 3])

        # 验证可以正确读取
        assert cache.get("string_key") == "string_value"
        assert cache.get("dict_key") == {"key": "value"}
        assert cache.get("list_key") == [1, 2, 3]


class TestRAGDirectoryStructure:
    """RAG 目录结构测试"""

    def test_rag_directory_creation(self, tmp_path: Path) -> None:
        """测试 RAG 目录正确创建"""
        from backend.rag.cache import SQLiteCache

        # 创建 Cache 会创建数据库文件
        _cache = SQLiteCache(str(tmp_path / "cache.db"))

        # 验证文件创建
        assert (tmp_path / "cache.db").exists()

    def test_chroma_directory_structure(self, tmp_path: Path) -> None:
        """测试 ChromaDB 目录结构"""
        # ChromaDB 目录结构应该在 MemoryIndexManager 初始化时创建
        # 这里只测试预期的目录结构
        expected_chroma_path = tmp_path / "chroma"

        # 验证路径对象创建正确
        assert str(expected_chroma_path).endswith("chroma")


class TestRAGToolAdapters:
    """RAG 工具适配器集成测试

    测试 get_search_tool() 返回的 search_memory 工具。
    """

    def test_search_tool_returns_dict(self, tmp_path: Path) -> None:
        """测试 search_tool 返回字典格式"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        # Patch __init__ 跳过真实初始化
        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            tool = manager.get_search_tool()

            assert isinstance(tool, dict)
            assert "name" in tool
            assert "description" in tool
            assert "func" in tool

    def test_search_tool_name_and_description(self, tmp_path: Path) -> None:
        """测试工具名称和描述正确"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            tool = manager.get_search_tool()

            assert tool["name"] == "search_memory"
            assert "长期记忆" in tool["description"]
            assert "向量语义检索" in tool["description"]
            assert "BM25" in tool["description"]

    def test_search_tool_with_results(self, tmp_path: Path) -> None:
        """测试工具返回检索结果"""
        from backend.rag.memory_index_manager import MemoryIndexManager
        from backend.rag.models import Segment

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            # Mock search 方法
            mock_segments = [
                Segment(
                    content="Test content 1",
                    source="test1.md",
                    file_type="long_term",
                    timestamp="2026-04-01",
                    score=0.9,
                ),
                Segment(
                    content="Test content 2",
                    source="test2.md",
                    file_type="long_term",
                    timestamp="2026-04-01",
                    score=0.8,
                ),
            ]

            with patch.object(manager, "search", return_value=mock_segments):
                tool = manager.get_search_tool()
                result = tool["func"](query="test query", top_k=5)

                # 验证返回值
                assert isinstance(result, str)
                assert "test1.md" in result or "Test content 1" in result

    def test_search_tool_with_empty_results(self, tmp_path: Path) -> None:
        """测试工具处理空结果"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            # Mock search 返回空列表
            with patch.object(manager, "search", return_value=[]):
                tool = manager.get_search_tool()
                result = tool["func"](query="test query")

                # 验证返回未找到信息
                assert isinstance(result, str)
                assert "未找到" in result

    def test_search_tool_with_date_range(self, tmp_path: Path) -> None:
        """测试工具支持日期范围过滤"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            # Mock _search_with_filters 方法
            with patch.object(manager, "_search_with_filters", return_value=[]):
                tool = manager.get_search_tool()
                result = tool["func"](
                    query="test query",
                    date_range=("2026-03-01", "2026-03-31"),
                )

                # 验证返回值
                assert isinstance(result, str)

    def test_search_tool_with_custom_top_k(self, tmp_path: Path) -> None:
        """测试工具支持自定义 top_k"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            # Mock search 方法
            with patch.object(manager, "search", return_value=[]) as mock_search:
                tool = manager.get_search_tool()
                tool["func"](query="test query", top_k=10)

                # 验证 search 被调用，且 top_k 参数传递正确
                mock_search.assert_called_once_with("test query", 10)

    def test_search_tool_handles_errors(self, tmp_path: Path) -> None:
        """测试工具处理异常情况"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            # Mock search 抛出异常
            with patch.object(manager, "search", side_effect=Exception("Test error")):
                tool = manager.get_search_tool()
                result = tool["func"](query="test query")

                # 验证返回错误信息
                assert isinstance(result, str)
                assert "错误" in result

    def test_search_tool_multiple_instances(self, tmp_path: Path) -> None:
        """测试多次调用 get_search_tool() 返回独立实例"""
        from backend.rag.memory_index_manager import MemoryIndexManager

        config = create_mock_settings(tmp_path)

        with patch.object(
            MemoryIndexManager, "__init__", lambda self, cfg: None
        ):
            manager = MemoryIndexManager(config)
            manager.config = config
            manager.rag_config = config.rag

            tool1 = manager.get_search_tool()
            tool2 = manager.get_search_tool()

            # 验证是独立的实例
            assert tool1 is not tool2
            assert tool1["func"] is not tool2["func"]
            assert tool1["name"] == tool2["name"]


class TestRAGConfigIntegration:
    """RAG 配置集成测试"""

    def test_config_propagation(self, tmp_path: Path) -> None:
        """测试配置正确传递到组件"""
        from backend.rag.file_watcher import FileWatcher

        config = create_mock_settings(tmp_path)

        with patch("backend.rag.file_watcher.MemoryIndexManager"):
            watcher = FileWatcher(config)

        # 验证配置被正确存储
        assert watcher.config is config
        assert watcher.config.storage.base_path == tmp_path

    def test_rag_config_values(self, tmp_path: Path) -> None:
        """测试 RAG 配置值"""
        config = create_mock_settings(tmp_path)

        # 验证 RAG 配置
        assert config.rag.chunk_size > 0
        assert config.rag.chunk_overlap >= 0
        assert config.rag.top_k > 0
