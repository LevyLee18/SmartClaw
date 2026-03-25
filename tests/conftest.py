"""pytest 配置和共享 fixtures

此文件包含所有测试共享的 pytest fixtures。
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录用于测试

    Yields:
        临时目录路径
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_storage_dir(temp_dir: Path) -> Path:
    """创建临时存储目录结构

    Args:
        temp_dir: 临时目录 fixture

    Returns:
        存储目录路径
    """
    storage_dir = temp_dir / "store"
    storage_dir.mkdir(parents=True, exist_ok=True)

    # 创建子目录
    (storage_dir / "core_memory").mkdir(exist_ok=True)
    (storage_dir / "memory").mkdir(exist_ok=True)
    (storage_dir / "rag").mkdir(exist_ok=True)

    return storage_dir


@pytest.fixture
def mock_home(monkeypatch: pytest.MonkeyPatch, temp_dir: Path) -> Path:
    """模拟用户主目录

    Args:
        monkeypatch: pytest monkeypatch fixture
        temp_dir: 临时目录 fixture

    Returns:
        模拟的主目录路径
    """
    smartclaw_dir = temp_dir / ".smartclaw"
    smartclaw_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setattr(Path, "home", lambda: temp_dir)

    return smartclaw_dir


@pytest.fixture
def sample_config_dict() -> dict:
    """提供示例配置字典

    Returns:
        示例配置字典
    """
    return {
        "storage": {
            "base_path": "~/.smartclaw/store",
        },
        "llm": {
            "default": {
                "provider": "anthropic",
                "model": "claude-3-opus",
                "max_tokens": 4096,
                "temperature": 0.7,
            }
        },
        "memory": {
            "near_memory_days": 7,
        },
        "rag": {
            "chunk_size": 512,
            "chunk_overlap": 50,
            "top_k": 5,
        },
    }


@pytest.fixture
def sample_core_memory_files(temp_storage_dir: Path) -> dict[str, Path]:
    """创建示例核心记忆文件

    Args:
        temp_storage_dir: 临时存储目录 fixture

    Returns:
        核心记忆文件路径字典
    """
    core_dir = temp_storage_dir / "core_memory"
    files = {}

    memory_contents = {
        "SOUL.md": "# Soul\n\nI am a helpful AI assistant.",
        "IDENTITY.md": "# Identity\n\nMy name is SmartClaw.",
        "USER.md": "# User\n\nUser profile information.",
        "MEMORY.md": "# Memory\n\nImportant memories.",
        "AGENTS.md": "# Agents\n\nAgent configurations.",
        "SKILLS_SNAPSHOT.md": "# Skills\n\nAvailable skills.",
    }

    for filename, content in memory_contents.items():
        file_path = core_dir / filename
        file_path.write_text(content)
        files[filename] = file_path

    return files
