"""测试 SessionManager 类

测试要点：
1. SessionInfo 模型 - 验证字段和默认值
2. SessionManager.__init__() - 初始化
3. SessionManager.get_session() - 获取会话
4. SessionManager.create_session() - 创建会话
5. SessionManager.update_last_active() - 更新活跃时间
6. SessionManager.archive_session() - 归档会话
"""

from datetime import datetime
from pathlib import Path

import pytest


class TestSessionInfoModel:
    """SessionInfo 模型测试"""

    def test_session_info_has_session_id(self) -> None:
        """测试 SessionInfo 包含 session_id 字段"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
        )

        assert session.session_id == "2026-03-25-abc123"

    def test_session_info_has_session_key(self) -> None:
        """测试 SessionInfo 包含 session_key 字段"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="my-session-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
        )

        assert session.session_key == "my-session-key"

    def test_session_info_has_created_at(self) -> None:
        """测试 SessionInfo 包含 created_at 字段"""
        from backend.memory.session import SessionInfo

        now = datetime.now()
        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=now,
            last_active=datetime.now(),
            status="active",
        )

        assert session.created_at == now

    def test_session_info_has_last_active(self) -> None:
        """测试 SessionInfo 包含 last_active 字段"""
        from backend.memory.session import SessionInfo

        now = datetime.now()
        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=now,
            status="active",
        )

        assert session.last_active == now

    def test_session_info_has_status(self) -> None:
        """测试 SessionInfo 包含 status 字段"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
        )

        assert session.status == "active"

    def test_session_info_default_message_count(self) -> None:
        """测试 SessionInfo message_count 默认值为 0"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
        )

        assert session.message_count == 0

    def test_session_info_default_token_count(self) -> None:
        """测试 SessionInfo token_count 默认值为 0"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
        )

        assert session.token_count == 0

    def test_session_info_custom_message_count(self) -> None:
        """测试 SessionInfo 可设置自定义 message_count"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
            message_count=10,
        )

        assert session.message_count == 10

    def test_session_info_custom_token_count(self) -> None:
        """测试 SessionInfo 可设置自定义 token_count"""
        from backend.memory.session import SessionInfo

        session = SessionInfo(
            session_id="2026-03-25-abc123",
            session_key="test-key",
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
            token_count=1500,
        )

        assert session.token_count == 1500


class TestSessionManagerInit:
    """SessionManager.__init__() 测试"""

    def test_init_sets_base_path(self, temp_dir: Path) -> None:
        """测试初始化设置 base_path"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        assert manager.base_path == temp_dir

    def test_init_sets_sessions_dir(self, temp_dir: Path) -> None:
        """测试初始化设置 sessions_dir = base_path / "sessions" """
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        assert manager.sessions_dir == temp_dir / "sessions"

    def test_init_sets_sessions_json_path(self, temp_dir: Path) -> None:
        """测试初始化设置 sessions_json_path"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        assert manager.sessions_json_path == temp_dir / "sessions" / "sessions.json"


class TestSessionManagerGetSession:
    """SessionManager.get_session() 测试"""

    def test_get_session_returns_none_when_not_exists(
        self, temp_dir: Path
    ) -> None:
        """测试获取不存在的会话返回 None"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        result = manager.get_session("non-existent-key")

        assert result is None

    def test_get_session_returns_session_info(self, temp_dir: Path) -> None:
        """测试获取存在的会话返回 SessionInfo"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 先创建会话
        created = manager.create_session("test-key")
        result = manager.get_session("test-key")

        assert result is not None
        assert result.session_key == "test-key"
        assert result.session_id == created.session_id


class TestSessionManagerCreateSession:
    """SessionManager.create_session() 测试"""

    def test_create_session_returns_session_info(self, temp_dir: Path) -> None:
        """测试创建会话返回 SessionInfo"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        session = manager.create_session("test-key")

        assert session is not None
        assert session.session_key == "test-key"

    def test_create_session_generates_session_id(self, temp_dir: Path) -> None:
        """测试创建会话生成 session_id"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        session = manager.create_session("test-key")

        # session_id 格式应为 YYYY-MM-DD-{random}
        assert session.session_id is not None
        assert len(session.session_id) > 10  # 至少 "2026-03-25-" + 随机字符

    def test_create_session_sets_status_active(self, temp_dir: Path) -> None:
        """测试创建会话状态为 active"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        session = manager.create_session("test-key")

        assert session.status == "active"

    def test_create_session_sets_created_at(self, temp_dir: Path) -> None:
        """测试创建会话设置 created_at"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        before = datetime.now()
        session = manager.create_session("test-key")
        after = datetime.now()

        assert before <= session.created_at <= after

    def test_create_session_creates_sessions_json(self, temp_dir: Path) -> None:
        """测试创建会话时创建 sessions.json"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        assert not manager.sessions_json_path.exists()

        manager.create_session("test-key")

        assert manager.sessions_json_path.exists()

    def test_create_session_updates_sessions_json(self, temp_dir: Path) -> None:
        """测试创建会话更新 sessions.json"""
        import json

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        manager.create_session("test-key")

        with open(manager.sessions_json_path) as f:
            data = json.load(f)

        assert "test-key" in data["sessions"]


class TestSessionManagerUpdateLastActive:
    """SessionManager.update_last_active() 测试"""

    def test_update_last_active_updates_timestamp(
        self, temp_dir: Path
    ) -> None:
        """测试更新最后活跃时间"""
        import time

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        session = manager.create_session("test-key")
        original_last_active = session.last_active

        # 等待一小段时间
        time.sleep(0.01)

        manager.update_last_active("test-key")
        updated = manager.get_session("test-key")

        assert updated is not None
        assert updated.last_active > original_last_active

    def test_update_last_active_raises_error_when_not_exists(
        self, temp_dir: Path
    ) -> None:
        """测试更新不存在的会话抛出 ValueError"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        with pytest.raises(ValueError):
            manager.update_last_active("non-existent-key")


class TestSessionManagerArchiveSession:
    """SessionManager.archive_session() 测试"""

    def test_archive_session_updates_status(self, temp_dir: Path) -> None:
        """测试归档会话更新状态为 archived"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        manager.create_session("test-key")

        manager.archive_session("test-key")
        session = manager.get_session("test-key")

        assert session is not None
        assert session.status == "archived"

    def test_archive_session_raises_error_when_not_exists(
        self, temp_dir: Path
    ) -> None:
        """测试归档不存在的会话抛出 ValueError"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        with pytest.raises(ValueError):
            manager.archive_session("non-existent-key")


class TestSessionManagerGenerateSessionId:
    """SessionManager.generate_session_id() 测试"""

    def test_generate_session_id_format(self, temp_dir: Path) -> None:
        """测试 session_id 格式为 YYYY-MM-DD-{random}"""
        import re

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        session_id = manager.generate_session_id()

        # 格式：YYYY-MM-DD-xxxxxx
        pattern = r"^\d{4}-\d{2}-\d{2}-[a-f0-9]{6}$"
        assert re.match(pattern, session_id)

    def test_generate_session_id_uniqueness(self, temp_dir: Path) -> None:
        """测试多次生成的 session_id 唯一"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        ids = [manager.generate_session_id() for _ in range(100)]
        unique_ids = set(ids)

        assert len(unique_ids) == 100  # 所有 ID 都应唯一


class TestSessionManagerExists:
    """SessionManager.exists() 测试"""

    def test_exists_returns_false_when_no_sessions(self, temp_dir: Path) -> None:
        """测试没有会话时 exists() 返回 False"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        assert manager.exists() is False

    def test_exists_returns_true_when_sessions_exist(self, temp_dir: Path) -> None:
        """测试有会话时 exists() 返回 True"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)
        manager.create_session("test-key")

        assert manager.exists() is True
