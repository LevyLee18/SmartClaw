"""SmartClaw 初始化模块

提供首次运行时的目录结构和默认文件创建功能。
"""

from pathlib import Path
from typing import Any, cast


# 默认存储路径
DEFAULT_BASE_PATH = Path.home() / ".smartclaw"

# 需要创建的子目录列表
REQUIRED_DIRS: list[str] = [
    "store/core_memory",
    "store/memory",
    "store/rag",
    "sessions",
    "sessions/archive",
    "logs",
    "skills",
]

# 核心记忆文件列表
CORE_MEMORY_FILES: list[str] = [
    "SOUL.md",
    "IDENTITY.md",
    "USER.md",
    "MEMORY.md",
    "AGENTS.md",
    "SKILLS_SNAPSHOT.md",
]


def ensure_directory(path: Path) -> bool:
    """确保目录存在，不存在则创建。

    Args:
        path: 目录路径

    Returns:
        True 如果目录已存在或创建成功，False 否则
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def ensure_file(path: Path, content: str = "") -> bool:
    """确保文件存在，不存在则创建。

    Args:
        path: 文件路径
        content: 文件内容（可选）

    Returns:
        True 如果文件已存在或创建成功，False 否则
    """
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def initialize_storage(base_path: Path | None = None) -> dict[str, Any]:
    """初始化 SmartClaw 存储目录结构。

    Args:
        base_path: 存储根目录，默认为 ~/.smartclaw

    Returns:
        初始化结果字典，包含 success, created_dirs, created_files, errors
    """
    if base_path is None:
        base_path = DEFAULT_BASE_PATH

    result: dict[str, Any] = {
        "success": True,
        "created_dirs": cast(list[str], []),
        "created_files": cast(list[str], []),
        "errors": cast(list[str], []),
    }

    # 创建基础目录
    if not ensure_directory(base_path):
        result["success"] = False
        result["errors"].append(f"Failed to create base directory: {base_path}")
        return result

    result["created_dirs"].append(str(base_path))

    # 创建所有子目录
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            if ensure_directory(dir_path):
                result["created_dirs"].append(str(dir_path))
            else:
                result["success"] = False
                result["errors"].append(f"Failed to create directory: {dir_path}")

    # 创建默认的核心记忆文件（空文件）
    core_memory_dir = base_path / "store" / "core_memory"
    for file_name in CORE_MEMORY_FILES:
        file_path = core_memory_dir / file_name
        if not file_path.exists():
            default_content = _get_default_content(file_name)
            if ensure_file(file_path, default_content):
                result["created_files"].append(str(file_path))
            else:
                result["success"] = False
                result["errors"].append(f"Failed to create file: {file_path}")

    # 创建默认的 sessions.json
    sessions_json_path = base_path / "sessions" / "sessions.json"
    if not sessions_json_path.exists():
        default_sessions = '{"sessions": {}}'
        if ensure_file(sessions_json_path, default_sessions):
            result["created_files"].append(str(sessions_json_path))
        else:
            result["success"] = False
            result["errors"].append(f"Failed to create file: {sessions_json_path}")

    return result


def _get_default_content(file_name: str) -> str:
    """获取核心记忆文件的默认内容。

    Args:
        file_name: 文件名

    Returns:
        默认文件内容
    """
    defaults = {
        "SOUL.md": "# Soul\n\nDefine the core personality and values of the agent.\n",
        "IDENTITY.md": "# Identity\n\nDefine the agent's identity and capabilities.\n",
        "USER.md": "# User\n\nUser profile and preferences.\n",
        "MEMORY.md": "# Memory\n\nImportant memories and learned information.\n",
        "AGENTS.md": "# Agents\n\nAgent configurations (read-only, auto-generated).\n",
        "SKILLS_SNAPSHOT.md": "# Skills Snapshot\n\nCurrent skills snapshot (read-only, auto-generated).\n",
    }
    return defaults.get(file_name, "")


def is_initialized(base_path: Path | None = None) -> bool:
    """检查存储目录是否已初始化。

    Args:
        base_path: 存储根目录，默认为 ~/.smartclaw

    Returns:
        True 如果已初始化，False 否则
    """
    if base_path is None:
        base_path = DEFAULT_BASE_PATH

    # 检查基础目录和关键子目录是否存在
    if not base_path.exists():
        return False

    required_paths = [
        base_path / "store" / "core_memory",
        base_path / "store" / "memory",
        base_path / "sessions",
        base_path / "logs",
    ]

    return all(p.exists() for p in required_paths)
