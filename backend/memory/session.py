"""SessionManager - 会话管理器

管理会话生命周期、归档和检索。
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import filelock

from backend.memory.base import MemoryManager


@dataclass
class SessionInfo:
    """会话信息数据类

    Attributes:
        session_id: 会话唯一标识（YYYY-MM-DD-{random}）
        session_key: 浏览器生成的匿名客户端 ID
        created_at: 创建时间
        last_active: 最后活跃时间
        status: 会话状态（active/archived）
        message_count: 消息数量
        token_count: Token 数量
    """

    session_id: str
    session_key: str
    created_at: datetime
    last_active: datetime
    status: str
    message_count: int = 0
    token_count: int = 0


class SessionManager(MemoryManager):
    """会话管理器

    管理会话生命周期、归档和检索。

    Attributes:
        base_path: 记忆存储根路径
        sessions_dir: 会话目录 (base_path/sessions)
        sessions_json_path: sessions.json 文件路径
    """

    def __init__(self, base_path: Path) -> None:
        """初始化会话管理器

        Args:
            base_path: 记忆存储根路径
        """
        super().__init__(base_path)
        self.sessions_dir = base_path / "sessions"
        self.sessions_json_path = self.sessions_dir / "sessions.json"

    def load(self) -> str:
        """加载所有会话信息（不适用，返回空字符串）

        Returns:
            空字符串
        """
        return ""

    def exists(self) -> bool:
        """检查是否存在任何会话

        Returns:
            如果有会话存在返回 True
        """
        data = self._read_sessions_json()
        return len(data.get("sessions", {})) > 0

    def get_session(self, session_key: str) -> Optional[SessionInfo]:
        """获取指定 session_key 对应的会话

        Args:
            session_key: 浏览器生成的匿名客户端 ID

        Returns:
            会话信息，如果不存在返回 None
        """
        data = self._read_sessions_json()
        sessions = data.get("sessions", {})

        if session_key not in sessions:
            return None

        session_data = sessions[session_key]
        return SessionInfo(
            session_id=session_data["session_id"],
            session_key=session_key,
            created_at=datetime.fromisoformat(session_data["created_at"]),
            last_active=datetime.fromisoformat(session_data["last_active"]),
            status=session_data["status"],
            message_count=session_data.get("message_count", 0),
            token_count=session_data.get("token_count", 0),
        )

    def create_session(self, session_key: str) -> SessionInfo:
        """创建新会话

        Args:
            session_key: 浏览器生成的匿名客户端 ID

        Returns:
            创建的会话信息

        Raises:
            IOError: 文件操作失败
        """
        now = datetime.now()
        session_id = self.generate_session_id()

        session_info = SessionInfo(
            session_id=session_id,
            session_key=session_key,
            created_at=now,
            last_active=now,
            status="active",
        )

        # 更新 sessions.json
        def update_func(data: dict) -> None:
            data["sessions"][session_key] = {
                "session_id": session_id,
                "created_at": now.isoformat(),
                "last_active": now.isoformat(),
                "status": "active",
                "message_count": 0,
                "token_count": 0,
            }

        self._update_sessions_json(update_func)

        # 创建会话文件目录
        current_dir = self.sessions_dir / "current"
        current_dir.mkdir(parents=True, exist_ok=True)

        # 创建空的会话文件
        session_file = current_dir / f"{session_id}.md"
        session_file.write_text(f"# 会话信息\n- sessionId: {session_id}\n- createdAt: {now}\n\n## 对话历史\n")

        return session_info

    def update_last_active(self, session_key: str) -> None:
        """更新会话最后活跃时间

        Args:
            session_key: 浏览器生成的匿名客户端 ID

        Raises:
            ValueError: 会话不存在
        """
        data = self._read_sessions_json()
        sessions = data.get("sessions", {})

        if session_key not in sessions:
            raise ValueError(f"Session not found: {session_key}")

        now = datetime.now()

        def update_func(data: dict) -> None:
            data["sessions"][session_key]["last_active"] = now.isoformat()

        self._update_sessions_json(update_func)

    def archive_session(self, session_key: str) -> None:
        """归档会话

        Args:
            session_key: 浏览器生成的匿名客户端 ID

        Raises:
            ValueError: 会话不存在
            IOError: 文件操作失败
        """
        session_info = self.get_session(session_key)
        if session_info is None:
            raise ValueError(f"Session not found: {session_key}")

        # 移动会话文件
        current_path = self.sessions_dir / "current" / f"{session_info.session_id}.md"
        archive_dir = self.sessions_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"{session_info.session_id}.md"

        if current_path.exists():
            current_path.rename(archive_path)

        # 更新 sessions.json
        def update_func(data: dict) -> None:
            data["sessions"][session_key]["status"] = "archived"

        self._update_sessions_json(update_func)

    def generate_session_id(self) -> str:
        """生成会话 ID

        Returns:
            格式为 YYYY-MM-DD-{random} 的会话 ID
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        random_suffix = uuid.uuid4().hex[:6]
        return f"{timestamp}-{random_suffix}"

    def _read_sessions_json(self, *, use_lock: bool = True) -> dict:
        """读取 sessions.json（带文件锁保护）

        Args:
            use_lock: 是否使用文件锁，默认 True。内部调用时可设为 False（已在锁内）。

        Returns:
            sessions.json 内容，如果不存在返回默认结构
        """
        if not self.sessions_json_path.exists():
            return {"version": "1.0", "sessions": {}}

        lock_path = str(self.sessions_json_path) + ".lock"

        def _read():
            with open(self.sessions_json_path, encoding="utf-8") as f:
                return json.load(f)

        if use_lock:
            with filelock.FileLock(lock_path, timeout=10):
                return _read()
        else:
            return _read()

    def _update_sessions_json(self, update_func) -> None:
        """更新 sessions.json（带文件锁）

        使用文件锁确保并发写入安全。

        Args:
            update_func: 更新函数，接收数据字典作为参数
        """
        # 确保目录存在
        self.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建锁文件路径
        lock_path = str(self.sessions_json_path) + ".lock"

        # 使用文件锁确保并发安全
        with filelock.FileLock(lock_path, timeout=10):
            # 读取现有数据（已在锁内，不需要再加锁）
            data = self._read_sessions_json(use_lock=False)

            # 应用更新
            update_func(data)

            # 写回文件
            with open(self.sessions_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
