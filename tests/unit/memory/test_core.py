"""测试 CoreMemoryFile 枚举和 CoreMemoryManager 类

测试要点：
1. CoreMemoryFile 枚举值
2. CoreMemoryManager 初始化
3. CoreMemoryManager.load() 加载所有核心记忆
4. CoreMemoryManager.load(file_key) 加载单个文件
5. CoreMemoryManager.write() 写入核心记忆
6. CoreMemoryManager._check_readonly() 只读检查
"""

from pathlib import Path

import pytest


class TestCoreMemoryFileEnum:
    """CoreMemoryFile 枚举测试"""

    def test_enum_has_soul(self) -> None:
        """测试枚举包含 SOUL"""
        from backend.memory.core import CoreMemoryFile

        assert CoreMemoryFile.SOUL.value == "SOUL.md"

    def test_enum_has_identity(self) -> None:
        """测试枚举包含 IDENTITY"""
        from backend.memory.core import CoreMemoryFile

        assert CoreMemoryFile.IDENTITY.value == "IDENTITY.md"

    def test_enum_has_user(self) -> None:
        """测试枚举包含 USER"""
        from backend.memory.core import CoreMemoryFile

        assert CoreMemoryFile.USER.value == "USER.md"

    def test_enum_has_memory(self) -> None:
        """测试枚举包含 MEMORY"""
        from backend.memory.core import CoreMemoryFile

        assert CoreMemoryFile.MEMORY.value == "MEMORY.md"

    def test_enum_has_agents(self) -> None:
        """测试枚举包含 AGENTS"""
        from backend.memory.core import CoreMemoryFile

        assert CoreMemoryFile.AGENTS.value == "AGENTS.md"

    def test_enum_has_skills_snapshot(self) -> None:
        """测试枚举包含 SKILLS_SNAPSHOT"""
        from backend.memory.core import CoreMemoryFile

        assert CoreMemoryFile.SKILLS_SNAPSHOT.value == "SKILLS_SNAPSHOT.md"

    def test_enum_count(self) -> None:
        """测试枚举值数量为 6"""
        from backend.memory.core import CoreMemoryFile

        assert len(CoreMemoryFile) == 6

    def test_enum_is_string_enum(self) -> None:
        """测试枚举继承自 str"""
        from backend.memory.core import CoreMemoryFile

        assert isinstance(CoreMemoryFile.SOUL.value, str)


class TestCoreMemoryWriteModeEnum:
    """CoreMemoryWriteMode 枚举测试"""

    def test_enum_has_append(self) -> None:
        """测试枚举包含 APPEND"""
        from backend.memory.core import CoreMemoryWriteMode

        assert CoreMemoryWriteMode.APPEND.value == "append"

    def test_enum_has_replace(self) -> None:
        """测试枚举包含 REPLACE"""
        from backend.memory.core import CoreMemoryWriteMode

        assert CoreMemoryWriteMode.REPLACE.value == "replace"

    def test_enum_count(self) -> None:
        """测试枚举值数量为 2"""
        from backend.memory.core import CoreMemoryWriteMode

        assert len(CoreMemoryWriteMode) == 2


class TestCoreMemoryManagerInit:
    """CoreMemoryManager.__init__() 测试"""

    def test_init_sets_base_path(self, temp_dir: Path) -> None:
        """测试初始化设置 base_path"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        assert manager.base_path == temp_dir

    def test_init_sets_core_dir(self, temp_dir: Path) -> None:
        """测试初始化设置 core_memory_dir = base_path / "core_memory" """
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        assert manager.core_memory_dir == temp_dir / "core_memory"

    def test_inherits_from_memory_manager(self, temp_dir: Path) -> None:
        """测试 CoreMemoryManager 继承自 MemoryManager"""
        from backend.memory.base import MemoryManager
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        assert isinstance(manager, MemoryManager)


class TestCoreMemoryManagerLoad:
    """CoreMemoryManager.load() 测试"""

    def test_load_returns_string(self, temp_dir: Path) -> None:
        """测试 load() 返回字符串"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert isinstance(content, str)

    def test_load_empty_directory_returns_empty_string(self, temp_dir: Path) -> None:
        """测试空目录返回空字符串"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert content == ""

    def test_load_single_file(self, temp_dir: Path) -> None:
        """测试加载单个文件"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录和测试文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        file_path = core_dir / CoreMemoryFile.SOUL.value
        file_path.write_text("# SOUL\n\nTest content")

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert "SOUL" in content
        assert "Test content" in content

    def test_load_all_files_in_order(self, temp_dir: Path) -> None:
        """测试按顺序加载所有文件"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录和所有测试文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        # 按加载顺序创建文件
        files_order = [
            CoreMemoryFile.AGENTS,
            CoreMemoryFile.SKILLS_SNAPSHOT,
            CoreMemoryFile.SOUL,
            CoreMemoryFile.IDENTITY,
            CoreMemoryFile.USER,
            CoreMemoryFile.MEMORY,
        ]

        for file_enum in files_order:
            file_path = core_dir / file_enum.value
            file_path.write_text(f"# {file_enum.name}\n\n{file_enum.name} content")

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        # 验证所有内容都存在
        for file_enum in files_order:
            assert file_enum.name in content
            assert f"{file_enum.name} content" in content

    def test_load_by_file_key(self, temp_dir: Path) -> None:
        """测试通过 file_key 加载单个文件"""
        from backend.memory.core import CoreMemoryManager

        # 创建 core_memory 目录和测试文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        (core_dir / "USER.md").write_text("# USER\n\nUser profile content")

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load(file_key="user")

        assert "USER" in content
        assert "User profile content" in content

    def test_load_by_file_key_case_insensitive(self, temp_dir: Path) -> None:
        """测试 file_key 大小写不敏感"""
        from backend.memory.core import CoreMemoryManager

        # 创建 core_memory 目录和测试文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        (core_dir / "MEMORY.md").write_text("# MEMORY\n\nMemory content")

        manager = CoreMemoryManager(base_path=temp_dir)

        # 小写
        content = manager.load(file_key="memory")
        assert "MEMORY" in content

    def test_load_by_invalid_file_key_raises_error(self, temp_dir: Path) -> None:
        """测试无效 file_key 抛出 ValueError"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        with pytest.raises(ValueError):
            manager.load(file_key="invalid_key")


class TestCoreMemoryManagerWrite:
    """CoreMemoryManager.write() 测试"""

    def test_write_creates_core_memory_dir(self, temp_dir: Path) -> None:
        """测试写入时自动创建 core_memory 目录"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        # core_memory 目录初始不存在
        assert not manager.core_memory_dir.exists()

        # 写入后应自动创建
        manager.write(file_key="user", content="Test content")

        assert manager.core_memory_dir.exists()

    def test_write_creates_file(self, temp_dir: Path) -> None:
        """测试写入创建文件"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        manager.write(file_key="user", content="Test content")

        expected_file = manager.core_memory_dir / "USER.md"
        assert expected_file.exists()

    def test_write_content_to_file(self, temp_dir: Path) -> None:
        """测试写入内容到文件"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        manager.write(file_key="user", content="My test content")

        expected_file = manager.core_memory_dir / "USER.md"
        file_content = expected_file.read_text()

        assert "My test content" in file_content

    def test_write_append_mode(self, temp_dir: Path) -> None:
        """测试追加模式写入"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        # 第一次写入
        manager.write(file_key="user", content="First content")

        # 第二次写入（追加模式）
        manager.write(file_key="user", content="Second content")

        file_content = (manager.core_memory_dir / "USER.md").read_text()

        assert "First content" in file_content
        assert "Second content" in file_content

    def test_write_replace_mode(self, temp_dir: Path) -> None:
        """测试替换模式写入"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        # 第一次写入
        manager.write(file_key="user", content="First content")

        # 第二次写入（替换模式）
        manager.write(file_key="user", content="Second content", mode="replace")

        file_content = (manager.core_memory_dir / "USER.md").read_text()

        assert "First content" not in file_content
        assert "Second content" in file_content


class TestCoreMemoryManagerReadonly:
    """CoreMemoryManager 只读文件测试"""

    def test_write_to_agents_raises_error(self, temp_dir: Path) -> None:
        """测试写入 AGENTS.md 抛出 ValueError"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        with pytest.raises(ValueError) as exc_info:
            manager.write(file_key="agents", content="Test content")

        assert "readonly" in str(exc_info.value).lower() or "只读" in str(exc_info.value)

    def test_write_to_skills_snapshot_raises_error(self, temp_dir: Path) -> None:
        """测试写入 SKILLS_SNAPSHOT.md 抛出 ValueError"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        with pytest.raises(ValueError) as exc_info:
            manager.write(file_key="skills_snapshot", content="Test content")

        assert "readonly" in str(exc_info.value).lower() or "只读" in str(exc_info.value)


class TestCoreMemoryManagerExists:
    """CoreMemoryManager.exists() 测试"""

    def test_exists_returns_false_when_no_files(self, temp_dir: Path) -> None:
        """测试没有文件时 exists() 返回 False"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        assert manager.exists() is False

    def test_exists_returns_true_when_files_exist(self, temp_dir: Path) -> None:
        """测试有文件时 exists() 返回 True"""
        from backend.memory.core import CoreMemoryManager

        # 创建 core_memory 目录和文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)
        (core_dir / "SOUL.md").write_text("content")

        manager = CoreMemoryManager(base_path=temp_dir)

        assert manager.exists() is True


class TestCoreMemoryManagerBoundary:
    """CoreMemoryManager 边界测试

    测试场景：
    1. 缺失文件
    2. 超大内容
    3. 空文件
    4. 特殊字符
    """

    def test_load_with_missing_some_files(self, temp_dir: Path) -> None:
        """测试加载时部分文件缺失"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录，只创建部分文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        # 只创建 SOUL.md 和 USER.md
        (core_dir / CoreMemoryFile.SOUL.value).write_text("# SOUL\n\nSoul content")
        (core_dir / CoreMemoryFile.USER.value).write_text("# USER\n\nUser content")

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        # 应该能加载存在的文件
        assert "SOUL" in content
        assert "USER" in content
        # 缺失的文件不应导致错误

    def test_load_with_all_files_missing(self, temp_dir: Path) -> None:
        """测试加载时所有文件都缺失"""
        from backend.memory.core import CoreMemoryManager

        # 创建空的 core_memory 目录
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        # 空目录应返回空字符串
        assert content == ""

    def test_load_with_empty_files(self, temp_dir: Path) -> None:
        """测试加载空文件"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录和空文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        for file_enum in CoreMemoryFile:
            file_path = core_dir / file_enum.value
            file_path.write_text("")

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        # 空文件应被跳过
        assert content == ""

    def test_load_with_whitespace_only_files(self, temp_dir: Path) -> None:
        """测试加载只有空白字符的文件"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录和只有空白字符的文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        for file_enum in CoreMemoryFile:
            file_path = core_dir / file_enum.value
            file_path.write_text("   \n\n\t  \n  ")

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        # 只有空白字符的文件应被跳过
        assert content == ""

    def test_load_large_file(self, temp_dir: Path) -> None:
        """测试加载大文件"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录和大文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        # 创建 1MB 大小的内容
        large_content = "# SOUL\n\n" + "x" * (1024 * 1024)
        (core_dir / CoreMemoryFile.SOUL.value).write_text(large_content)

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        # 验证能正确加载大文件
        assert len(content) > 1024 * 1024
        assert "SOUL" in content

    def test_load_file_with_special_characters(self, temp_dir: Path) -> None:
        """测试加载包含特殊字符的文件"""
        from backend.memory.core import CoreMemoryFile, CoreMemoryManager

        # 创建 core_memory 目录和包含特殊字符的文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        special_content = "# 特殊字符测试\n\nEmoji: 🎉🚀💡\n中文内容\n日本語\n한국어"
        (core_dir / CoreMemoryFile.USER.value).write_text(special_content)

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert "特殊字符测试" in content
        assert "🎉" in content
        assert "中文内容" in content

    def test_write_large_content(self, temp_dir: Path) -> None:
        """测试写入大内容"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        # 创建 1MB 大小的内容
        large_content = "x" * (1024 * 1024)
        manager.write(file_key="user", content=large_content)

        expected_file = manager.core_memory_dir / "USER.md"
        file_content = expected_file.read_text()

        assert len(file_content) > 1024 * 1024

    def test_write_unicode_content(self, temp_dir: Path) -> None:
        """测试写入 Unicode 内容"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        unicode_content = "中文测试 🎉 日本語テスト"
        manager.write(file_key="user", content=unicode_content)

        expected_file = manager.core_memory_dir / "USER.md"
        file_content = expected_file.read_text()

        assert "中文测试" in file_content
        assert "🎉" in file_content

    def test_write_multiline_content(self, temp_dir: Path) -> None:
        """测试写入多行内容"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

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
        manager.write(file_key="memory", content=multiline_content)

        expected_file = manager.core_memory_dir / "MEMORY.md"
        file_content = expected_file.read_text()

        assert "# Title" in file_content
        assert "## Section" in file_content
        assert "def hello():" in file_content

    def test_write_empty_content(self, temp_dir: Path) -> None:
        """测试写入空内容"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        # 写入空内容
        manager.write(file_key="user", content="")

        expected_file = manager.core_memory_dir / "USER.md"

        # 文件应该被创建
        assert expected_file.exists()

    def test_load_by_file_key_with_missing_file(self, temp_dir: Path) -> None:
        """测试通过 file_key 加载不存在的文件"""
        from backend.memory.core import CoreMemoryManager

        # 创建空的 core_memory 目录
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)

        manager = CoreMemoryManager(base_path=temp_dir)
        content = manager.load(file_key="user")

        # 不存在的文件应返回空字符串
        assert content == ""

    def test_exists_with_non_md_files(self, temp_dir: Path) -> None:
        """测试目录中有非 .md 文件时的 exists()"""
        from backend.memory.core import CoreMemoryManager

        # 创建 core_memory 目录和非 .md 文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)
        (core_dir / "test.txt").write_text("text file")
        (core_dir / "readme").write_text("no extension")

        manager = CoreMemoryManager(base_path=temp_dir)

        # 只有非 .md 文件，exists() 应返回 False
        assert manager.exists() is False

    def test_exists_with_mixed_files(self, temp_dir: Path) -> None:
        """测试目录中有混合文件时的 exists()"""
        from backend.memory.core import CoreMemoryManager

        # 创建 core_memory 目录和混合文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True)
        (core_dir / "test.txt").write_text("text file")
        (core_dir / "SOUL.md").write_text("markdown file")

        manager = CoreMemoryManager(base_path=temp_dir)

        # 有 .md 文件，exists() 应返回 True
        assert manager.exists() is True

    def test_multiple_append_writes(self, temp_dir: Path) -> None:
        """测试多次追加写入"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)

        # 多次追加写入
        for i in range(10):
            manager.write(file_key="memory", content=f"Content {i}")

        expected_file = manager.core_memory_dir / "MEMORY.md"
        file_content = expected_file.read_text()

        # 所有内容都应该存在
        for i in range(10):
            assert f"Content {i}" in file_content
