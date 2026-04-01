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


class TestSessionManagerBoundary:
    """SessionManager 边界测试

    测试场景：
    1. 并发创建
    2. 重复 session_key
    3. 损坏的 JSON
    4. 其他边界情况
    """

    def test_create_session_with_duplicate_key_overwrites(self, temp_dir: Path) -> None:
        """测试重复 session_key 创建会覆盖原会话"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 第一次创建
        session1 = manager.create_session("duplicate-key")
        original_session_id = session1.session_id

        # 第二次创建（相同 key）
        session2 = manager.create_session("duplicate-key")

        # 应该返回新的 session（不同的 session_id）
        assert session2.session_key == "duplicate-key"
        # session_id 应该不同（因为是新生成的）
        assert session2.session_id != original_session_id

    def test_create_session_with_duplicate_key_updates_sessions_json(
        self, temp_dir: Path
    ) -> None:
        """测试重复 session_key 创建更新 sessions.json"""
        import json

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 第一次创建
        manager.create_session("duplicate-key")

        # 第二次创建（相同 key）
        manager.create_session("duplicate-key")

        # sessions.json 中应该只有一个条目
        with open(manager.sessions_json_path) as f:
            data = json.load(f)

        assert len(data["sessions"]) == 1
        assert "duplicate-key" in data["sessions"]

    def test_read_sessions_json_with_corrupted_json_raises_error(
        self, temp_dir: Path
    ) -> None:
        """测试损坏的 JSON 文件导致 JSONDecodeError"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建损坏的 sessions.json
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        manager.sessions_json_path.write_text("{ invalid json content")

        # 读取损坏的 JSON 应该抛出 JSONDecodeError
        import json

        with pytest.raises(json.JSONDecodeError):
            manager._read_sessions_json()

    def test_get_session_with_corrupted_json_raises_error(self, temp_dir: Path) -> None:
        """测试损坏的 JSON 文件时获取会话抛出 JSONDecodeError"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建损坏的 sessions.json
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        manager.sessions_json_path.write_text("{ invalid json content")

        # 获取会话应该抛出 JSONDecodeError
        import json

        with pytest.raises(json.JSONDecodeError):
            manager.get_session("any-key")

    def test_exists_with_corrupted_json_raises_error(self, temp_dir: Path) -> None:
        """测试损坏的 JSON 文件时 exists() 抛出 JSONDecodeError"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建损坏的 sessions.json
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        manager.sessions_json_path.write_text("{ invalid json content")

        # exists() 应该抛出 JSONDecodeError
        import json

        with pytest.raises(json.JSONDecodeError):
            manager.exists()

    def test_concurrent_create_sessions(self, temp_dir: Path) -> None:
        """测试并发创建会话

        使用文件锁确保并发写入安全。
        """
        import concurrent.futures

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        def create_session(key: str):
            return manager.create_session(key)

        # 并发创建 10 个会话
        keys = [f"concurrent-key-{i}" for i in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session, key) for key in keys]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有会话应该成功创建
        assert len(results) == 10

        # 验证所有会话都被记录
        for key in keys:
            session = manager.get_session(key)
            assert session is not None
            assert session.session_key == key

    def test_concurrent_update_last_active(self, temp_dir: Path) -> None:
        """测试并发更新活跃时间

        使用文件锁确保并发写入安全。
        """
        """测试并发更新活跃时间"""
        import concurrent.futures

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 先创建一个会话
        manager.create_session("test-key")

        def update_active():
            manager.update_last_active("test-key")
            return True

        # 并发更新 10 次
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_active) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有更新应该成功
        assert all(results)

        # 验证会话仍然存在
        session = manager.get_session("test-key")
        assert session is not None

    def test_sessions_json_with_missing_sessions_key(self, temp_dir: Path) -> None:
        """测试 sessions.json 缺少 sessions 键"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建缺少 sessions 键的 JSON
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        manager.sessions_json_path.write_text('{"version": "1.0"}')

        # get_session 应该正常处理（返回 None）
        result = manager.get_session("any-key")
        assert result is None

        # exists 应该正常处理（返回 False）
        assert manager.exists() is False

    def test_sessions_json_with_empty_sessions(self, temp_dir: Path) -> None:
        """测试 sessions.json 包含空 sessions"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建空 sessions
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        manager.sessions_json_path.write_text('{"version": "1.0", "sessions": {}}')

        # get_session 应该返回 None
        result = manager.get_session("any-key")
        assert result is None

        # exists 应该返回 False
        assert manager.exists() is False

    def test_archive_session_with_missing_file(self, temp_dir: Path) -> None:
        """测试归档会话时会话文件不存在"""
        import json

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 手动创建 sessions.json（不创建会话文件）
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        session_data = {
            "version": "1.0",
            "sessions": {
                "test-key": {
                    "session_id": "2026-03-25-abc123",
                    "created_at": "2026-03-25T10:00:00",
                    "last_active": "2026-03-25T10:00:00",
                    "status": "active",
                    "message_count": 0,
                    "token_count": 0,
                }
            },
        }
        manager.sessions_json_path.write_text(json.dumps(session_data))

        # 归档应该成功（即使文件不存在）
        manager.archive_session("test-key")

        # 验证状态已更新
        session = manager.get_session("test-key")
        assert session is not None
        assert session.status == "archived"

    def test_get_session_with_missing_required_fields(self, temp_dir: Path) -> None:
        """测试 sessions.json 缺少必需字段"""
        import json

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建缺少必需字段的 JSON
        manager.sessions_json_path.parent.mkdir(parents=True, exist_ok=True)
        session_data = {
            "version": "1.0",
            "sessions": {
                "test-key": {
                    "session_id": "2026-03-25-abc123",
                    # 缺少 created_at, last_active, status
                }
            },
        }
        manager.sessions_json_path.write_text(json.dumps(session_data))

        # get_session 应该抛出 KeyError
        with pytest.raises(KeyError):
            manager.get_session("test-key")

    def test_update_last_active_concurrent_with_create(
        self, temp_dir: Path
    ) -> None:
        """测试并发创建和更新

        使用文件锁确保并发写入安全。
        """
        import concurrent.futures

        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        def create_and_update(key: str):
            # 创建会话
            manager.create_session(key)
            # 立即更新
            manager.update_last_active(key)
            return key

        # 并发创建和更新 10 个会话
        keys = [f"concurrent-key-{i}" for i in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_and_update, key) for key in keys]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有操作应该成功
        assert len(results) == 10

        # 验证所有会话都被正确创建和更新
        for key in keys:
            session = manager.get_session(key)
            assert session is not None
            assert session.session_key == key

    def test_create_session_with_special_characters_in_key(self, temp_dir: Path) -> None:
        """测试 session_key 包含特殊字符"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建包含特殊字符的 session_key
        special_key = "test-key-特殊字符-🎉-unicode"
        session = manager.create_session(special_key)

        assert session.session_key == special_key

        # 验证可以正确获取
        retrieved = manager.get_session(special_key)
        assert retrieved is not None
        assert retrieved.session_key == special_key

    def test_create_session_with_very_long_key(self, temp_dir: Path) -> None:
        """测试非常长的 session_key"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建很长的 session_key
        long_key = "a" * 1000
        session = manager.create_session(long_key)

        assert session.session_key == long_key

        # 验证可以正确获取
        retrieved = manager.get_session(long_key)
        assert retrieved is not None
        assert retrieved.session_key == long_key

    def test_archive_session_already_archived(self, temp_dir: Path) -> None:
        """测试归档已经归档的会话"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建并归档
        manager.create_session("test-key")
        manager.archive_session("test-key")

        # 再次归档（应该成功，幂等操作）
        manager.archive_session("test-key")

        # 验证状态仍然是 archived
        session = manager.get_session("test-key")
        assert session is not None
        assert session.status == "archived"

    def test_multiple_sessions_same_day(self, temp_dir: Path) -> None:
        """测试同一天创建多个会话"""
        from backend.memory.session import SessionManager

        manager = SessionManager(base_path=temp_dir)

        # 创建多个会话
        sessions = [manager.create_session(f"key-{i}") for i in range(5)]

        # 所有 session_id 应该以相同日期开头
        today = sessions[0].session_id[:10]
        for session in sessions:
            assert session.session_id.startswith(today)

        # 所有 session_id 应该不同
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 5
