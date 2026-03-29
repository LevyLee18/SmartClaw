"""FileWatcher 实现

监控文件系统变化，触发索引更新。
"""

import queue
from pathlib import Path

from watchdog.observers import Observer

from backend.config.models import Settings
from backend.rag.memory_index_manager import MemoryIndexManager


class FileWatcher:
    """文件监控器

    监控指定目录的文件变化，触发索引更新。

    Attributes:
        config: SmartClaw 配置对象
        base_path: 监控的根目录
        event_queue: 文件事件队列
        _observer: Watchdog Observer
        _index_manager: 索引管理器
        _running: 是否正在运行
    """

    def __init__(self, config: Settings) -> None:
        """初始化文件监控器

        Args:
            config: SmartClaw 配置对象
        """
        self.config = config
        self.base_path = config.storage.base_path

        # 初始化事件队列
        self.event_queue: queue.Queue = queue.Queue()

        # Observer（在 start 时创建）
        self._observer: Observer | None = None

        # 初始化索引管理器
        self._index_manager = MemoryIndexManager(config)

        # 运行状态
        self._running = False

    def start(self) -> None:
        """启动文件监控"""
        if self._running:
            return

        # 每次启动创建新的 Observer（因为线程只能启动一次）
        self._observer = Observer()
        self._observer.schedule(self, str(self.base_path), recursive=True)
        self._observer.start()
        self._running = True

    def stop(self) -> None:
        """停止文件监控"""
        if not self._running:
            return

        self._observer.stop()
        self._observer.join()
        self._running = False

    def on_file_created(self, file_path: Path) -> None:
        """文件创建事件处理

        Args:
            file_path: 创建的文件路径
        """
        self.event_queue.put(("created", str(file_path)))

    def on_file_modified(self, file_path: Path) -> None:
        """文件修改事件处理

        Args:
            file_path: 修改的文件路径
        """
        self.event_queue.put(("modified", str(file_path)))

    def on_file_deleted(self, file_path: Path) -> None:
        """文件删除事件处理

        Args:
            file_path: 删除的文件路径
        """
        self.event_queue.put(("deleted", str(file_path)))
