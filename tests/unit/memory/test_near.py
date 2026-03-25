"""测试 NearMemoryManager 类

测试要点：
1. __init__() - 初始化方法，memory_dir = base_path / "memory"
2. load(days) - 加载最近 N 天的近端记忆
3. write(date, content, category) - 写入近端记忆
4. get_file_path(date) - 获取文件路径
"""

from datetime import date, timedelta
from pathlib import Path

import pytest


class TestNearMemoryManagerInit:
    """NearMemoryManager.__init__() 测试"""

    def test_init_sets_base_path(self, temp_dir: Path) -> None:
        """测试初始化设置 base_path"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        assert manager.base_path == temp_dir

    def test_init_sets_memory_dir(self, temp_dir: Path) -> None:
        """测试初始化设置 memory_dir = base_path / "memory" """
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        assert manager.memory_dir == temp_dir / "memory"

    def test_memory_dir_is_path_object(self, temp_dir: Path) -> None:
        """测试 memory_dir 是 Path 对象"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        assert isinstance(manager.memory_dir, Path)

    def test_inherits_from_memory_manager(self, temp_dir: Path) -> None:
        """测试 NearMemoryManager 继承自 MemoryManager"""
        from backend.memory.base import MemoryManager
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        assert isinstance(manager, MemoryManager)


class TestNearMemoryManagerLoad:
    """NearMemoryManager.load() 测试"""

    def test_load_returns_string(self, temp_dir: Path) -> None:
        """测试 load() 返回字符串"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert isinstance(content, str)

    def test_load_empty_directory_returns_empty_string(self, temp_dir: Path) -> None:
        """测试空目录返回空字符串"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert content == ""

    def test_load_single_file(self, temp_dir: Path) -> None:
        """测试加载单个文件"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和测试文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        file_path = memory_dir / f"{today.isoformat()}.md"
        file_path.write_text("# Today's memory\n\nTest content")

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load(days=1)

        assert "Today's memory" in content
        assert "Test content" in content

    def test_load_multiple_days(self, temp_dir: Path) -> None:
        """测试加载多天的记忆"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和测试文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        yesterday = today - timedelta(days=1)

        # 创建今天和昨天的文件
        (memory_dir / f"{today.isoformat()}.md").write_text("Today content")
        (memory_dir / f"{yesterday.isoformat()}.md").write_text("Yesterday content")

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load(days=2)

        assert "Today content" in content
        assert "Yesterday content" in content

    def test_load_default_days_is_two(self, temp_dir: Path) -> None:
        """测试默认加载 2 天"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        manager = NearMemoryManager(base_path=temp_dir)

        # 调用不带参数的 load()
        content = manager.load()

        # 应该成功执行（不抛出异常）
        assert isinstance(content, str)


class TestNearMemoryManagerWrite:
    """NearMemoryManager.write() 测试"""

    def test_write_creates_memory_dir(self, temp_dir: Path) -> None:
        """测试写入时自动创建 memory 目录"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        # memory 目录初始不存在
        assert not manager.memory_dir.exists()

        # 写入后应自动创建
        manager.write(content="Test content")

        assert manager.memory_dir.exists()

    def test_write_creates_file(self, temp_dir: Path) -> None:
        """测试写入创建文件"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        today = date.today()

        manager.write(content="Test content")

        expected_file = manager.memory_dir / f"{today.isoformat()}.md"
        assert expected_file.exists()

    def test_write_content_to_file(self, temp_dir: Path) -> None:
        """测试写入内容到文件"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        today = date.today()

        manager.write(content="My test content")

        expected_file = manager.memory_dir / f"{today.isoformat()}.md"
        file_content = expected_file.read_text()

        assert "My test content" in file_content

    def test_write_with_specific_date(self, temp_dir: Path) -> None:
        """测试写入指定日期"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        specific_date = date(2026, 3, 15)

        manager.write(content="Content for specific date", target_date=specific_date)

        expected_file = manager.memory_dir / "2026-03-15.md"
        assert expected_file.exists()
        assert "Content for specific date" in expected_file.read_text()

    def test_write_appends_to_existing_file(self, temp_dir: Path) -> None:
        """测试写入追加到现有文件"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        # 第一次写入
        manager.write(content="First content")

        # 第二次写入（同一天）
        manager.write(content="Second content")

        today = date.today()
        expected_file = manager.memory_dir / f"{today.isoformat()}.md"
        file_content = expected_file.read_text()

        assert "First content" in file_content
        assert "Second content" in file_content


class TestNearMemoryManagerGetFilePath:
    """NearMemoryManager.get_file_path() 测试"""

    def test_get_file_path_format(self, temp_dir: Path) -> None:
        """测试文件路径格式为 memory/YYYY-MM-DD.md"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        test_date = date(2026, 3, 15)

        file_path = manager.get_file_path(test_date)

        assert file_path == temp_dir / "memory" / "2026-03-15.md"

    def test_get_file_path_returns_path_object(self, temp_dir: Path) -> None:
        """测试返回 Path 对象"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        file_path = manager.get_file_path(date.today())

        assert isinstance(file_path, Path)


class TestNearMemoryManagerExists:
    """NearMemoryManager.exists() 测试"""

    def test_exists_returns_false_when_no_files(self, temp_dir: Path) -> None:
        """测试没有文件时 exists() 返回 False"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        assert manager.exists() is False

    def test_exists_returns_true_when_files_exist(self, temp_dir: Path) -> None:
        """测试有文件时 exists() 返回 True"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)
        today = date.today()
        (memory_dir / f"{today.isoformat()}.md").write_text("content")

        manager = NearMemoryManager(base_path=temp_dir)

        assert manager.exists() is True


class TestNearMemoryManagerBoundary:
    """NearMemoryManager 边界测试

    测试场景：
    1. 大文件
    2. 并发写入
    3. 空文件
    4. 无效日期
    """

    def test_load_large_file(self, temp_dir: Path) -> None:
        """测试加载大文件"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和大文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        file_path = memory_dir / f"{today.isoformat()}.md"

        # 创建 1MB 大小的内容
        large_content = "# Large File\n\n" + "x" * (1024 * 1024)
        file_path.write_text(large_content)

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load(days=1)

        # 验证能正确加载大文件
        assert len(content) > 1024 * 1024
        assert "Large File" in content

    def test_load_empty_file(self, temp_dir: Path) -> None:
        """测试加载空文件"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和空文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        file_path = memory_dir / f"{today.isoformat()}.md"
        file_path.write_text("")

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load(days=1)

        # 空文件应被跳过，返回空字符串
        assert content == ""

    def test_load_whitespace_only_file(self, temp_dir: Path) -> None:
        """测试加载只有空白字符的文件"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和只有空白字符的文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        file_path = memory_dir / f"{today.isoformat()}.md"
        file_path.write_text("   \n\n\t  \n  ")

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load(days=1)

        # 只有空白字符的文件应被跳过
        assert content == ""

    def test_load_file_with_special_characters(self, temp_dir: Path) -> None:
        """测试加载包含特殊字符的文件"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和包含特殊字符的文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        file_path = memory_dir / f"{today.isoformat()}.md"

        special_content = "# 特殊字符测试\n\nEmoji: 🎉🚀💡\n中文内容\n日本語\n한국어"
        file_path.write_text(special_content)

        manager = NearMemoryManager(base_path=temp_dir)
        content = manager.load(days=1)

        assert "特殊字符测试" in content
        assert "🎉" in content
        assert "中文内容" in content

    def test_load_days_exceeds_available(self, temp_dir: Path) -> None:
        """测试请求天数超过可用天数"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录，只有今天一个文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)

        today = date.today()
        (memory_dir / f"{today.isoformat()}.md").write_text("Today only")

        manager = NearMemoryManager(base_path=temp_dir)
        # 请求 30 天，但只有 1 个文件
        content = manager.load(days=30)

        # 应该只返回可用的文件
        assert "Today only" in content

    def test_load_negative_days(self, temp_dir: Path) -> None:
        """测试负数天数"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        # 负数天数应返回空字符串（没有文件会被加载）
        content = manager.load(days=-1)
        assert content == ""

    def test_load_zero_days(self, temp_dir: Path) -> None:
        """测试零天"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)
        today = date.today()
        (memory_dir / f"{today.isoformat()}.md").write_text("Today content")

        manager = NearMemoryManager(base_path=temp_dir)
        # 零天应返回空字符串
        content = manager.load(days=0)
        assert content == ""

    def test_write_empty_content(self, temp_dir: Path) -> None:
        """测试写入空内容"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        # 写入空内容
        manager.write(content="")

        today = date.today()
        expected_file = manager.memory_dir / f"{today.isoformat()}.md"

        # 文件应该被创建
        assert expected_file.exists()

    def test_write_unicode_content(self, temp_dir: Path) -> None:
        """测试写入 Unicode 内容"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        unicode_content = "中文测试 🎉 日本語テスト"
        manager.write(content=unicode_content)

        today = date.today()
        expected_file = manager.memory_dir / f"{today.isoformat()}.md"
        file_content = expected_file.read_text()

        assert "中文测试" in file_content
        assert "🎉" in file_content

    def test_write_multiline_content(self, temp_dir: Path) -> None:
        """测试写入多行内容"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        multiline_content = """# Title

First paragraph.

## Section

- Item 1
- Item 2
- Item 3

```python
def hello():
    print("Hello, World!")
```
"""
        manager.write(content=multiline_content)

        today = date.today()
        expected_file = manager.memory_dir / f"{today.isoformat()}.md"
        file_content = expected_file.read_text()

        assert "# Title" in file_content
        assert "## Section" in file_content
        assert "def hello():" in file_content

    def test_get_file_path_with_boundary_dates(self, temp_dir: Path) -> None:
        """测试边界日期的文件路径"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)

        # 年初
        new_year = date(2026, 1, 1)
        assert manager.get_file_path(new_year) == temp_dir / "memory" / "2026-01-01.md"

        # 年末
        year_end = date(2026, 12, 31)
        assert manager.get_file_path(year_end) == temp_dir / "memory" / "2026-12-31.md"

        # 闰年日期
        leap_day = date(2024, 2, 29)
        assert manager.get_file_path(leap_day) == temp_dir / "memory" / "2024-02-29.md"

    def test_exists_with_non_md_files(self, temp_dir: Path) -> None:
        """测试目录中有非 .md 文件时的 exists()"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和非 .md 文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "test.txt").write_text("text file")
        (memory_dir / "readme").write_text("no extension")

        manager = NearMemoryManager(base_path=temp_dir)

        # 只有非 .md 文件，exists() 应返回 False
        assert manager.exists() is False

    def test_exists_with_mixed_files(self, temp_dir: Path) -> None:
        """测试目录中有混合文件时的 exists()"""
        from backend.memory.near import NearMemoryManager

        # 创建 memory 目录和混合文件
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "test.txt").write_text("text file")
        today = date.today()
        (memory_dir / f"{today.isoformat()}.md").write_text("markdown file")

        manager = NearMemoryManager(base_path=temp_dir)

        # 有 .md 文件，exists() 应返回 True
        assert manager.exists() is True
