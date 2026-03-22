"""测试 backend.init 模块

测试初始化存储目录结构的功能。
"""

import os
import tempfile
from pathlib import Path

import pytest

from backend.init import (
    DEFAULT_BASE_PATH,
    REQUIRED_DIRS,
    CORE_MEMORY_FILES,
    ensure_directory,
    ensure_file,
    initialize_storage,
    is_initialized,
    _get_default_content,
)


class TestConstants:
    """测试常量定义"""

    def test_required_dirs_list(self):
        """验证必需目录列表完整"""
        expected_dirs = [
            "store/core_memory",
            "store/memory",
            "store/rag",
            "sessions",
            "sessions/archive",
            "logs",
            "skills",
        ]
        assert REQUIRED_DIRS == expected_dirs

    def test_core_memory_files_list(self):
        """验证核心记忆文件列表完整"""
        expected_files = [
            "SOUL.md",
            "IDENTITY.md",
            "USER.md",
            "MEMORY.md",
            "AGENTS.md",
            "SKILLS_SNAPSHOT.md",
        ]
        assert CORE_MEMORY_FILES == expected_files

    def test_default_base_path(self):
        """验证默认基础路径"""
        assert DEFAULT_BASE_PATH == Path.home() / ".smartclaw"


class TestEnsureDirectory:
    """测试 ensure_directory 函数"""

    def test_create_new_directory(self, tmp_path: Path):
        """测试创建新目录"""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        result = ensure_directory(new_dir)

        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path: Path):
        """测试已存在的目录"""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory(existing_dir)

        assert result is True
        assert existing_dir.exists()

    def test_create_nested_directories(self, tmp_path: Path):
        """测试创建嵌套目录"""
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        result = ensure_directory(nested_dir)

        assert result is True
        assert nested_dir.exists()

    def test_create_directory_with_permission_error(self, tmp_path: Path, monkeypatch):
        """测试创建目录时权限错误"""
        new_dir = tmp_path / "protected"

        def mock_mkdir(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "mkdir", mock_mkdir)

        result = ensure_directory(new_dir)

        assert result is False


class TestEnsureFile:
    """测试 ensure_file 函数"""

    def test_create_new_file(self, tmp_path: Path):
        """测试创建新文件"""
        file_path = tmp_path / "test.txt"
        content = "Hello, World!"

        result = ensure_file(file_path, content)

        assert result is True
        assert file_path.exists()
        assert file_path.read_text() == content

    def test_existing_file_not_overwritten(self, tmp_path: Path):
        """测试已存在的文件不被覆盖"""
        file_path = tmp_path / "existing.txt"
        original_content = "Original content"
        file_path.write_text(original_content)

        result = ensure_file(file_path, "New content")

        assert result is True
        assert file_path.read_text() == original_content

    def test_create_file_with_nested_directory(self, tmp_path: Path):
        """测试创建文件时自动创建父目录"""
        file_path = tmp_path / "nested" / "dir" / "file.txt"
        content = "Nested file"

        result = ensure_file(file_path, content)

        assert result is True
        assert file_path.exists()
        assert file_path.parent.exists()

    def test_create_file_with_permission_error(self, tmp_path: Path, monkeypatch):
        """测试创建文件时权限错误"""
        file_path = tmp_path / "protected.txt"

        def mock_write_text(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        result = ensure_file(file_path, "content")

        assert result is False


class TestGetDefaultContent:
    """测试 _get_default_content 函数"""

    def test_soul_md_content(self):
        """验证 SOUL.md 默认内容"""
        content = _get_default_content("SOUL.md")
        assert "# Soul" in content
        assert "personality" in content.lower()

    def test_identity_md_content(self):
        """验证 IDENTITY.md 默认内容"""
        content = _get_default_content("IDENTITY.md")
        assert "# Identity" in content
        assert "identity" in content.lower()

    def test_user_md_content(self):
        """验证 USER.md 默认内容"""
        content = _get_default_content("USER.md")
        assert "# User" in content
        assert "profile" in content.lower()

    def test_memory_md_content(self):
        """验证 MEMORY.md 默认内容"""
        content = _get_default_content("MEMORY.md")
        assert "# Memory" in content

    def test_agents_md_content(self):
        """验证 AGENTS.md 默认内容"""
        content = _get_default_content("AGENTS.md")
        assert "# Agents" in content
        assert "read-only" in content.lower()

    def test_skills_snapshot_md_content(self):
        """验证 SKILLS_SNAPSHOT.md 默认内容"""
        content = _get_default_content("SKILLS_SNAPSHOT.md")
        assert "# Skills Snapshot" in content
        assert "read-only" in content.lower()

    def test_unknown_file_returns_empty(self):
        """验证未知文件返回空字符串"""
        content = _get_default_content("unknown.txt")
        assert content == ""


class TestInitializeStorage:
    """测试 initialize_storage 函数"""

    def test_initialize_creates_all_directories(self, tmp_path: Path):
        """测试初始化创建所有目录"""
        result = initialize_storage(tmp_path)

        assert result["success"] is True
        for dir_name in REQUIRED_DIRS:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory not created: {dir_name}"
            assert str(dir_path) in result["created_dirs"]

    def test_initialize_creates_core_memory_files(self, tmp_path: Path):
        """测试初始化创建核心记忆文件"""
        result = initialize_storage(tmp_path)

        assert result["success"] is True
        core_memory_dir = tmp_path / "store" / "core_memory"
        for file_name in CORE_MEMORY_FILES:
            file_path = core_memory_dir / file_name
            assert file_path.exists(), f"File not created: {file_name}"
            assert str(file_path) in result["created_files"]

    def test_initialize_creates_sessions_json(self, tmp_path: Path):
        """测试初始化创建 sessions.json"""
        result = initialize_storage(tmp_path)

        assert result["success"] is True
        sessions_json = tmp_path / "sessions" / "sessions.json"
        assert sessions_json.exists()
        assert str(sessions_json) in result["created_files"]

        # 验证内容格式
        import json
        content = json.loads(sessions_json.read_text())
        assert "sessions" in content
        assert content["sessions"] == {}

    def test_initialize_is_idempotent(self, tmp_path: Path):
        """测试初始化幂等性（多次运行不报错）"""
        result1 = initialize_storage(tmp_path)
        result2 = initialize_storage(tmp_path)

        assert result1["success"] is True
        assert result2["success"] is True

        # 第二次运行不应创建新文件
        assert len(result2["created_files"]) == 0
        assert len(result2["created_dirs"]) == 1  # 只有 base_path

    def test_initialize_with_default_path(self, monkeypatch):
        """测试使用默认路径初始化"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_home = Path(tmp_dir)
            monkeypatch.setattr(
                "backend.init.DEFAULT_BASE_PATH",
                fake_home / ".smartclaw"
            )

            # 临时修改 DEFAULT_BASE_PATH
            from backend import init
            original_path = init.DEFAULT_BASE_PATH
            init.DEFAULT_BASE_PATH = fake_home / ".smartclaw"

            try:
                result = initialize_storage()

                assert result["success"] is True
                assert (fake_home / ".smartclaw").exists()
            finally:
                init.DEFAULT_BASE_PATH = original_path

    def test_initialize_returns_correct_structure(self, tmp_path: Path):
        """测试返回结果结构正确"""
        result = initialize_storage(tmp_path)

        assert "success" in result
        assert "created_dirs" in result
        assert "created_files" in result
        assert "errors" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["created_dirs"], list)
        assert isinstance(result["created_files"], list)
        assert isinstance(result["errors"], list)


class TestIsInitialized:
    """测试 is_initialized 函数"""

    def test_returns_false_for_nonexistent_path(self, tmp_path: Path):
        """测试不存在的路径返回 False"""
        nonexistent = tmp_path / "nonexistent"
        assert is_initialized(nonexistent) is False

    def test_returns_false_for_incomplete_structure(self, tmp_path: Path):
        """测试不完整的目录结构返回 False"""
        # 只创建部分目录
        (tmp_path / "store" / "core_memory").mkdir(parents=True)
        assert is_initialized(tmp_path) is False

    def test_returns_true_after_initialize(self, tmp_path: Path):
        """测试初始化后返回 True"""
        initialize_storage(tmp_path)
        assert is_initialized(tmp_path) is True

    def test_returns_true_for_complete_structure(self, tmp_path: Path):
        """测试完整目录结构返回 True"""
        # 手动创建所有必需目录
        (tmp_path / "store" / "core_memory").mkdir(parents=True)
        (tmp_path / "store" / "memory").mkdir(parents=True)
        (tmp_path / "sessions").mkdir()
        (tmp_path / "logs").mkdir()

        assert is_initialized(tmp_path) is True

    def test_with_default_path(self, monkeypatch):
        """测试使用默认路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_home = Path(tmp_dir)
            fake_base = fake_home / ".smartclaw"

            from backend import init
            original_path = init.DEFAULT_BASE_PATH
            init.DEFAULT_BASE_PATH = fake_base

            try:
                assert is_initialized() is False
                initialize_storage()
                assert is_initialized() is True
            finally:
                init.DEFAULT_BASE_PATH = original_path
