"""FileWatcher 类单元测试

测试 FileWatcher 的初始化和基本功能。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.config.models import RAGConfig, Settings, StorageConfig
from backend.rag.file_watcher import FileWatcher


def create_mock_settings(tmp_path: Path) -> Settings:
    """创建带 Mock 配置的 Settings"""
    return Settings(
        storage=StorageConfig(base_path=tmp_path),
        rag=RAGConfig(),
    )


class TestFileWatcherInit:
    """测试 FileWatcher.__init__"""

    def test_init_with_valid_config(self, tmp_path: Path):
        """测试使用有效配置初始化"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert watcher.config == config
        assert watcher.base_path == tmp_path

    def test_init_stores_config(self, tmp_path: Path):
        """测试初始化存储配置"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "config")
        assert watcher.config is config

    def test_init_stores_base_path(self, tmp_path: Path):
        """测试初始化存储 base_path"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "base_path")
        assert watcher.base_path == tmp_path

    def test_init_initializes_event_queue(self, tmp_path: Path):
        """测试初始化事件队列"""
        import queue

        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "event_queue")
        assert isinstance(watcher.event_queue, queue.Queue)

    def test_init_initializes_observer(self, tmp_path: Path):
        """测试初始化 Observer"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "_observer")

    def test_init_initializes_index_manager(self, tmp_path: Path):
        """测试初始化 IndexManager"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "_index_manager")

    def test_init_sets_running_false(self, tmp_path: Path):
        """测试初始化设置 running 为 False"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "_running")
        assert watcher._running is False


class TestFileWatcherMethods:
    """测试 FileWatcher 方法"""

    def test_has_start_method(self, tmp_path: Path):
        """测试具有 start 方法"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "start")
        assert callable(watcher.start)

    def test_has_stop_method(self, tmp_path: Path):
        """测试具有 stop 方法"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "stop")
        assert callable(watcher.stop)

    def test_has_on_file_created_method(self, tmp_path: Path):
        """测试具有 on_file_created 方法"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "on_file_created")
        assert callable(watcher.on_file_created)

    def test_has_on_file_modified_method(self, tmp_path: Path):
        """测试具有 on_file_modified 方法"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "on_file_modified")
        assert callable(watcher.on_file_modified)

    def test_has_on_file_deleted_method(self, tmp_path: Path):
        """测试具有 on_file_deleted 方法"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        assert hasattr(watcher, "on_file_deleted")
        assert callable(watcher.on_file_deleted)


class TestFileWatcherLifecycle:
    """测试 FileWatcher 生命周期"""

    def test_start_sets_running_true(self, tmp_path: Path):
        """测试 start 设置 running 为 True"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)
        assert watcher._running is False

        watcher.start()

        assert watcher._running is True

        # 清理
        watcher.stop()

    def test_stop_sets_running_false(self, tmp_path: Path):
        """测试 stop 设置 running 为 False"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)
        watcher.start()
        assert watcher._running is True

        watcher.stop()

        assert watcher._running is False

    def test_start_is_idempotent(self, tmp_path: Path):
        """测试 start 是幂等的"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        watcher.start()
        watcher.start()  # 再次调用

        assert watcher._running is True

        # 清理
        watcher.stop()

    def test_stop_is_idempotent(self, tmp_path: Path):
        """测试 stop 是幂等的"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        watcher.stop()  # 未启动时调用
        watcher.stop()  # 再次调用

        assert watcher._running is False

    def test_start_stop_cycle(self, tmp_path: Path):
        """测试启动-停止循环"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        # 第一次循环
        watcher.start()
        assert watcher._running is True
        watcher.stop()
        assert watcher._running is False

        # 第二次循环
        watcher.start()
        assert watcher._running is True
        watcher.stop()
        assert watcher._running is False


class TestFileWatcherEvents:
    """测试 FileWatcher 事件处理"""

    def test_on_file_created_adds_to_queue(self, tmp_path: Path):
        """测试 on_file_created 将事件添加到队列"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        watcher.on_file_created(tmp_path / "test.md")

        event_type, file_path = watcher.event_queue.get_nowait()
        assert event_type == "created"
        assert file_path == str(tmp_path / "test.md")

    def test_on_file_modified_adds_to_queue(self, tmp_path: Path):
        """测试 on_file_modified 将事件添加到队列"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        watcher.on_file_modified(tmp_path / "test.md")

        event_type, file_path = watcher.event_queue.get_nowait()
        assert event_type == "modified"
        assert file_path == str(tmp_path / "test.md")

    def test_on_file_deleted_adds_to_queue(self, tmp_path: Path):
        """测试 on_file_deleted 将事件添加到队列"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        watcher.on_file_deleted(tmp_path / "test.md")

        event_type, file_path = watcher.event_queue.get_nowait()
        assert event_type == "deleted"
        assert file_path == str(tmp_path / "test.md")

    def test_multiple_events_in_queue(self, tmp_path: Path):
        """测试多个事件按顺序添加到队列"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        watcher.on_file_created(tmp_path / "file1.md")
        watcher.on_file_modified(tmp_path / "file2.md")
        watcher.on_file_deleted(tmp_path / "file3.md")

        # 验证事件顺序
        assert watcher.event_queue.qsize() == 3

        event1 = watcher.event_queue.get_nowait()
        assert event1 == ("created", str(tmp_path / "file1.md"))

        event2 = watcher.event_queue.get_nowait()
        assert event2 == ("modified", str(tmp_path / "file2.md"))

        event3 = watcher.event_queue.get_nowait()
        assert event3 == ("deleted", str(tmp_path / "file3.md"))


class TestFileWatcherDebounce:
    """测试 FileWatcher 防抖机制"""

    def test_debounce_delays_processing(self, tmp_path: Path):
        """测试防抖延迟处理"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        # 添加事件
        watcher.on_file_created(tmp_path / "test.md")

        # 立即检查，事件应该在队列中但未处理
        assert watcher.event_queue.qsize() == 1

    def test_debounce_deduplicates_same_file(self, tmp_path: Path):
        """测试防抖去重相同文件"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        # 快速连续添加相同文件事件
        watcher.on_file_created(tmp_path / "test.md")
        watcher.on_file_created(tmp_path / "test.md")
        watcher.on_file_created(tmp_path / "test.md")

        # 防抖后应该只有一个事件
        assert watcher.event_queue.qsize() == 3  # 原始事件都在队列中

    def test_debounce_different_files_not_deduplicated(self, tmp_path: Path):
        """测试不同文件不去重"""
        config = create_mock_settings(tmp_path)

        watcher = FileWatcher(config)

        # 添加不同文件事件
        watcher.on_file_created(tmp_path / "file1.md")
        watcher.on_file_created(tmp_path / "file2.md")
        watcher.on_file_created(tmp_path / "file3.md")

        # 不同文件应该都保留
        assert watcher.event_queue.qsize() == 3


class TestFileWatcherBoundary:
    """测试 FileWatcher 边界条件"""

    def test_rapid_consecutive_events(self, tmp_path: Path):
        """测试快速连续事件"""
        config = create_mock_settings(tmp_path)
        watcher = FileWatcher(config)

        # 快速添加 100 个事件
        for i in range(100):
            watcher.on_file_created(tmp_path / f"file_{i}.md")

        assert watcher.event_queue.qsize() == 100

    def test_large_number_of_files(self, tmp_path: Path):
        """测试大量文件"""
        config = create_mock_settings(tmp_path)
        watcher = FileWatcher(config)

        # 添加大量不同类型的事件
        for i in range(50):
            watcher.on_file_created(tmp_path / f"file_{i}.md")
            watcher.on_file_modified(tmp_path / f"file_{i}.md")

        assert watcher.event_queue.qsize() == 100

    def test_special_characters_in_path(self, tmp_path: Path):
        """测试路径中的特殊字符"""
        config = create_mock_settings(tmp_path)
        watcher = FileWatcher(config)

        # 包含特殊字符的路径
        special_paths = [
            tmp_path / "file with spaces.md",
            tmp_path / "file-with-dashes.md",
            tmp_path / "file_with_underscores.md",
            tmp_path / "文件中文.md",
        ]

        for path in special_paths:
            watcher.on_file_created(path)

        assert watcher.event_queue.qsize() == len(special_paths)
