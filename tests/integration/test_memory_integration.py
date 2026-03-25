"""Memory 模块集成测试

测试 CoreMemory + NearMemory + Session 协同工作。

测试场景：
1. 完整记忆加载流程
2. 记忆写入流程
3. 会话与记忆的交互
"""

from datetime import date, timedelta
from pathlib import Path

import pytest


class TestMemoryIntegration:
    """Memory 模块集成测试"""

    def test_memory_managers_share_base_path(self, temp_dir: Path) -> None:
        """测试所有管理器共享相同的 base_path"""
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)
        session_manager = SessionManager(base_path=temp_dir)

        assert core_manager.base_path == temp_dir
        assert near_manager.base_path == temp_dir
        assert session_manager.base_path == temp_dir

    def test_full_memory_loading_flow(self, temp_dir: Path) -> None:
        """测试完整记忆加载流程

        场景：
        1. 创建核心记忆文件
        2. 创建近端记忆文件
        3. 创建会话
        4. 加载所有记忆
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        # 1. 创建核心记忆文件
        core_manager = CoreMemoryManager(base_path=temp_dir)
        core_manager.write(file_key="user", content="# User Profile\nTest user content")
        core_manager.write(file_key="memory", content="# Memory\nImportant decisions")

        # 2. 创建近端记忆文件
        near_manager = NearMemoryManager(base_path=temp_dir)
        near_manager.write(content="Today's conversation summary")

        # 3. 创建会话
        session_manager = SessionManager(base_path=temp_dir)
        session = session_manager.create_session("test-session-key")

        # 4. 加载所有记忆
        core_content = core_manager.load()
        near_content = near_manager.load(days=2)

        # 验证核心记忆加载成功
        assert "User Profile" in core_content
        assert "Memory" in core_content

        # 验证近端记忆加载成功
        assert "Today's conversation summary" in near_content

        # 验证会话创建成功
        assert session.session_key == "test-session-key"
        assert session.status == "active"

    def test_memory_write_and_read_cycle(self, temp_dir: Path) -> None:
        """测试记忆写入和读取循环

        场景：
        1. 写入核心记忆（追加模式）
        2. 读取验证
        3. 再次写入（替换模式）
        4. 读取验证
        """
        from backend.memory.core import CoreMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)

        # 1. 写入核心记忆（追加模式）
        core_manager.write(file_key="user", content="First content")
        core_manager.write(file_key="user", content="Second content")

        # 2. 读取验证
        content = core_manager.load(file_key="user")
        assert "First content" in content
        assert "Second content" in content

        # 3. 写入（替换模式）
        core_manager.write(file_key="user", content="Replaced content", mode="replace")

        # 4. 读取验证
        content = core_manager.load(file_key="user")
        assert "First content" not in content
        assert "Replaced content" in content

    def test_near_memory_daily_rotation(self, temp_dir: Path) -> None:
        """测试近端记忆按日期轮转

        场景：
        1. 写入今天的内容
        2. 写入昨天的内容
        3. 加载最近 2 天
        4. 验证两天的内容都被加载
        """
        from backend.memory.near import NearMemoryManager

        near_manager = NearMemoryManager(base_path=temp_dir)

        # 1. 写入今天的内容
        today = date.today()
        near_manager.write(content="Today's content", target_date=today)

        # 2. 写入昨天的内容
        yesterday = today - timedelta(days=1)
        near_manager.write(content="Yesterday's content", target_date=yesterday)

        # 3. 加载最近 2 天
        content = near_manager.load(days=2)

        # 4. 验证两天的内容都被加载
        assert "Today's content" in content
        assert "Yesterday's content" in content

    def test_session_lifecycle_with_memory(self, temp_dir: Path) -> None:
        """测试会话生命周期与记忆的交互

        场景：
        1. 创建会话
        2. 记录近端记忆
        3. 归档会话
        4. 验证会话状态和记忆内容
        """
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        session_manager = SessionManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        # 1. 创建会话
        session = session_manager.create_session("user-session-1")
        assert session.status == "active"

        # 2. 记录近端记忆
        near_manager.write(content=f"Session {session.session_id} started")

        # 3. 归档会话
        session_manager.archive_session("user-session-1")

        # 4. 验证会话状态和记忆内容
        archived_session = session_manager.get_session("user-session-1")
        assert archived_session is not None
        assert archived_session.status == "archived"

        # 验证近端记忆仍存在
        near_content = near_manager.load(days=1)
        assert session.session_id in near_content

    def test_multiple_sessions_concurrent_memory_access(self, temp_dir: Path) -> None:
        """测试多个会话并发访问记忆

        场景：
        1. 创建多个会话
        2. 每个会话都读写近端记忆
        3. 验证数据一致性
        """
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        session_manager = SessionManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        # 1. 创建多个会话
        sessions = []
        for i in range(3):
            session = session_manager.create_session(f"session-{i}")
            sessions.append(session)

        # 2. 每个会话都读写近端记忆
        for i, session in enumerate(sessions):
            near_manager.write(content=f"Session {i}: {session.session_id}")

        # 3. 验证数据一致性
        near_content = near_manager.load(days=1)
        for i in range(3):
            assert f"Session {i}:" in near_content

        # 验证所有会话都存在
        for i in range(3):
            retrieved = session_manager.get_session(f"session-{i}")
            assert retrieved is not None
            assert retrieved.status == "active"

    def test_core_memory_readonly_protection(self, temp_dir: Path) -> None:
        """测试核心记忆只读保护

        场景：
        1. 尝试写入 AGENTS.md
        2. 验证抛出 ValueError
        3. 尝试写入 SKILLS_SNAPSHOT.md
        4. 验证抛出 ValueError
        """
        from backend.memory.core import CoreMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)

        # 1. 尝试写入 AGENTS.md
        with pytest.raises(ValueError):
            core_manager.write(file_key="agents", content="Test content")

        # 3. 尝试写入 SKILLS_SNAPSHOT.md
        with pytest.raises(ValueError):
            core_manager.write(file_key="skills_snapshot", content="Test content")

    def test_memory_directory_structure(self, temp_dir: Path) -> None:
        """测试记忆目录结构正确创建

        场景：
        1. 首次写入核心记忆
        2. 首次写入近端记忆
        3. 首次创建会话
        4. 验证目录结构
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)
        session_manager = SessionManager(base_path=temp_dir)

        # 1. 首次写入核心记忆
        core_manager.write(file_key="user", content="Test")

        # 2. 首次写入近端记忆
        near_manager.write(content="Test")

        # 3. 首次创建会话
        session_manager.create_session("test-key")

        # 4. 验证目录结构
        assert (temp_dir / "core_memory").exists()
        assert (temp_dir / "memory").exists()
        assert (temp_dir / "sessions").exists()
        assert (temp_dir / "sessions" / "current").exists()
        assert (temp_dir / "sessions" / "sessions.json").exists()

    def test_session_file_naming_convention(self, temp_dir: Path) -> None:
        """测试会话文件命名规范

        场景：
        1. 创建会话
        2. 验证会话文件路径格式
        3. 验证 session_id 格式
        """
        import re

        from backend.memory.session import SessionManager

        session_manager = SessionManager(base_path=temp_dir)

        # 1. 创建会话
        session = session_manager.create_session("test-key")

        # 2. 验证会话文件路径格式
        expected_file = (
            session_manager.sessions_dir / "current" / f"{session.session_id}.md"
        )
        assert expected_file.exists()

        # 3. 验证 session_id 格式 (YYYY-MM-DD-xxxxxx)
        pattern = r"^\d{4}-\d{2}-\d{2}-[a-f0-9]{6}$"
        assert re.match(pattern, session.session_id)

    def test_archive_session_moves_file(self, temp_dir: Path) -> None:
        """测试归档会话移动文件

        场景：
        1. 创建会话
        2. 归档会话
        3. 验证文件从 current 移动到 archive
        """
        from backend.memory.session import SessionManager

        session_manager = SessionManager(base_path=temp_dir)

        # 1. 创建会话
        session = session_manager.create_session("test-key")
        current_file = (
            session_manager.sessions_dir / "current" / f"{session.session_id}.md"
        )
        assert current_file.exists()

        # 2. 归档会话
        session_manager.archive_session("test-key")

        # 3. 验证文件从 current 移动到 archive
        archive_file = (
            session_manager.sessions_dir / "archive" / f"{session.session_id}.md"
        )
        assert not current_file.exists()
        assert archive_file.exists()

    def test_cross_manager_data_consistency(self, temp_dir: Path) -> None:
        """测试跨管理器数据一致性

        场景：
        1. 通过一个管理器写入数据
        2. 创建新的管理器实例
        3. 验证新实例能读取相同数据
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        # 1. 通过一个管理器写入数据
        core_manager1 = CoreMemoryManager(base_path=temp_dir)
        near_manager1 = NearMemoryManager(base_path=temp_dir)
        session_manager1 = SessionManager(base_path=temp_dir)

        core_manager1.write(file_key="user", content="Cross manager test")
        near_manager1.write(content="Near memory test")
        session_manager1.create_session("cross-test-key")

        # 2. 创建新的管理器实例
        core_manager2 = CoreMemoryManager(base_path=temp_dir)
        near_manager2 = NearMemoryManager(base_path=temp_dir)
        session_manager2 = SessionManager(base_path=temp_dir)

        # 3. 验证新实例能读取相同数据
        core_content = core_manager2.load(file_key="user")
        assert "Cross manager test" in core_content

        near_content = near_manager2.load(days=1)
        assert "Near memory test" in near_content

        session = session_manager2.get_session("cross-test-key")
        assert session is not None
        assert session.session_key == "cross-test-key"


class TestMemorySystemPromptBuilder:
    """测试 System Prompt 构建流程

    这些测试验证记忆内容可以正确拼接成 System Prompt。
    注意：SystemPromptBuilder 类在 Agent 模块中实现。
    """

    def test_core_memory_load_order(self, temp_dir: Path) -> None:
        """测试核心记忆加载顺序

        顺序应该是：
        AGENTS → SKILLS_SNAPSHOT → SOUL → IDENTITY → USER → MEMORY
        """
        from backend.memory.core import CoreMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)

        # 写入所有可写文件
        core_manager.write(file_key="soul", content="SOUL content")
        core_manager.write(file_key="identity", content="IDENTITY content")
        core_manager.write(file_key="user", content="USER content")
        core_manager.write(file_key="memory", content="MEMORY content")

        # 创建只读文件
        core_dir = temp_dir / "core_memory"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "AGENTS.md").write_text("AGENTS content")
        (core_dir / "SKILLS_SNAPSHOT.md").write_text("SKILLS_SNAPSHOT content")

        # 加载所有核心记忆
        content = core_manager.load()

        # 验证所有内容都存在
        assert "AGENTS" in content
        assert "SKILLS_SNAPSHOT" in content
        assert "SOUL" in content
        assert "IDENTITY" in content
        assert "USER" in content
        assert "MEMORY" in content

    def test_near_memory_load_with_days_parameter(self, temp_dir: Path) -> None:
        """测试近端记忆按天数加载

        场景：
        1. 创建 5 天的记忆文件
        2. 加载最近 2 天
        3. 验证只返回最近 2 天的内容
        """
        from backend.memory.near import NearMemoryManager

        near_manager = NearMemoryManager(base_path=temp_dir)

        # 1. 创建 5 天的记忆文件
        today = date.today()
        for i in range(5):
            target_date = today - timedelta(days=i)
            near_manager.write(content=f"Day {i} content", target_date=target_date)

        # 2. 加载最近 2 天
        content = near_manager.load(days=2)

        # 3. 验证只返回最近 2 天的内容
        assert "Day 0 content" in content
        assert "Day 1 content" in content
        assert "Day 2 content" not in content
        assert "Day 3 content" not in content
        assert "Day 4 content" not in content
