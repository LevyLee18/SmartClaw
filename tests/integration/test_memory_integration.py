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


class TestMemoryToolAdapters:
    """测试记忆工具适配器集成

    验证 CoreMemory + NearMemory + 工具适配器协同工作
    """

    def test_write_near_memory_tool_integration(self, temp_dir: Path) -> None:
        """测试 write_near_memory 工具适配器集成

        场景：
        1. 获取 NearMemoryManager 的工具
        2. 通过工具写入记忆
        3. 验证文件内容正确
        """
        from backend.memory.near import NearMemoryManager

        near_manager = NearMemoryManager(base_path=temp_dir)
        tool = near_manager.get_write_tool()

        # 通过工具写入
        result = tool["func"](
            content="User prefers dark mode",
            category="用户偏好"
        )

        # 验证返回值
        assert "成功" in result

        # 验证文件内容
        near_file = near_manager.memory_dir / f"{date.today().isoformat()}.md"
        content = near_file.read_text()
        assert "用户偏好" in content
        assert "User prefers dark mode" in content

    def test_write_core_memory_tool_integration(self, temp_dir: Path) -> None:
        """测试 write_core_memory 工具适配器集成

        场景：
        1. 获取 CoreMemoryManager 的工具
        2. 通过工具写入记忆
        3. 验证文件内容正确
        """
        from backend.memory.core import CoreMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)
        tool = core_manager.get_write_tool()

        # 通过工具写入
        result = tool["func"](
            file_key="memory",
            content="User decided to use Python for this project"
        )

        # 验证返回值
        assert "成功" in result

        # 验证文件内容
        memory_file = core_manager.core_memory_dir / "MEMORY.md"
        content = memory_file.read_text()
        assert "Python" in content
        assert "project" in content

    def test_both_tools_work_together(self, temp_dir: Path) -> None:
        """测试两个工具适配器协同工作

        场景：
        1. 同时使用近端和核心记忆工具
        2. 验证两者独立工作
        3. 验证数据写入正确位置
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        core_tool = core_manager.get_write_tool()
        near_tool = near_manager.get_write_tool()

        # 同时写入
        core_result = core_tool["func"](
            file_key="user",
            content="User is a software engineer"
        )

        near_result = near_tool["func"](
            content="Discussed API design patterns",
            category="对话摘要"
        )

        # 验证都成功
        assert "成功" in core_result
        assert "成功" in near_result

        # 验证数据在正确位置
        user_file = core_manager.core_memory_dir / "USER.md"
        assert "software engineer" in user_file.read_text()

        near_file = near_manager.memory_dir / f"{date.today().isoformat()}.md"
        near_content = near_file.read_text()
        assert "API design" in near_content
        assert "对话摘要" in near_content

    def test_tool_error_propagation(self, temp_dir: Path) -> None:
        """测试工具错误传播

        场景：
        1. 使用无效参数调用工具
        2. 验证错误信息正确返回
        3. 验证不会抛出异常
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        core_tool = core_manager.get_write_tool()
        near_tool = near_manager.get_write_tool()

        # 测试核心记忆工具的错误处理
        readonly_result = core_tool["func"](
            file_key="agents",
            content="Should fail"
        )
        assert "错误" in readonly_result or "readonly" in readonly_result.lower()

        # 测试近端记忆工具的错误处理
        invalid_date_result = near_tool["func"](
            content="Test",
            date="not-a-date"
        )
        assert "错误" in invalid_date_result

    def test_tool_multiple_calls_consistency(self, temp_dir: Path) -> None:
        """测试多次调用工具的一致性

        场景：
        1. 多次调用 get_write_tool()
        2. 验证每次返回独立的工具实例
        3. 验证所有工具都能正常工作
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager

        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        # 获取多个工具实例
        core_tools = [core_manager.get_write_tool() for _ in range(3)]
        near_tools = [near_manager.get_write_tool() for _ in range(3)]

        # 验证是独立的实例
        for i in range(3):
            for j in range(i + 1, 3):
                assert core_tools[i] is not core_tools[j]
                assert near_tools[i] is not near_tools[j]

        # 验证所有工具都能正常工作
        for tool in core_tools:
            result = tool["func"](
                file_key="memory",
                content=f"Test entry {tool}"
            )
            assert "成功" in result

        for tool in near_tools:
            result = tool["func"](
                content=f"Test entry {tool}"
            )
            assert "成功" in result

        # 验证所有内容都被写入
        core_file = core_manager.core_memory_dir / "MEMORY.md"
        core_content = core_file.read_text()
        assert core_content.count("Test entry") == 3

        near_file = near_manager.memory_dir / f"{date.today().isoformat()}.md"
        near_content = near_file.read_text()
        assert near_content.count("Test entry") == 3

    def test_tool_with_session_context(self, temp_dir: Path) -> None:
        """测试工具在会话上下文中工作

        场景：
        1. 创建会话
        2. 在会话中使用工具写入记忆
        3. 验证会话和记忆都能正常工作
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        session_manager = SessionManager(base_path=temp_dir)
        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        # 创建会话
        session = session_manager.create_session("test-session")

        # 在会话上下文中使用工具
        core_tool = core_manager.get_write_tool()
        near_tool = near_manager.get_write_tool()

        # 写入会话相关的记忆
        near_result = near_tool["func"](
            content=f"Session {session.session_id} discussion about Python"
        )

        core_result = core_tool["func"](
            file_key="user",
            content="User mentioned they are a Python developer"
        )

        # 验证都成功
        assert "成功" in near_result
        assert "成功" in core_result

        # 验证会话仍然活跃
        retrieved_session = session_manager.get_session("test-session")
        assert retrieved_session is not None
        assert retrieved_session.status == "active"

        # 验证记忆内容
        near_content = near_manager.load(days=1)
        assert session.session_id in near_content

    def test_complete_memory_workflow_with_tools(self, temp_dir: Path) -> None:
        """测试完整的记忆工作流程（使用工具）

        场景：
        1. 创建所有管理器
        2. 获取工具
        3. 模拟完整对话流程
        4. 验证所有记忆正确保存
        """
        from backend.memory.core import CoreMemoryManager
        from backend.memory.near import NearMemoryManager
        from backend.memory.session import SessionManager

        # 1. 创建所有管理器
        session_manager = SessionManager(base_path=temp_dir)
        core_manager = CoreMemoryManager(base_path=temp_dir)
        near_manager = NearMemoryManager(base_path=temp_dir)

        # 2. 获取工具
        core_tool = core_manager.get_write_tool()
        near_tool = near_manager.get_write_tool()

        # 3. 模拟完整对话流程

        # 3.1 创建会话
        session = session_manager.create_session("user-123")

        # 3.2 用户提到重要偏好（写入核心记忆）
        core_tool["func"](
            file_key="user",
            content="User prefers vim over emacs for editing"
        )

        # 3.3 记录对话摘要（写入近端记忆）
        near_tool["func"](
            content="User explained their editor preference",
            category="对话摘要"
        )

        # 3.4 用户做出决策（写入核心记忆）
        core_tool["func"](
            file_key="memory",
            content="Decision: Use vim for all future code editing tasks"
        )

        # 3.5 记录决策到近端记忆
        near_tool["func"](
            content="User decided to use vim for editing",
            category="决策记录"
        )

        # 4. 验证所有记忆正确保存

        # 验证核心记忆
        user_content = core_manager.load(file_key="user")
        assert "vim" in user_content
        assert "emacs" in user_content

        memory_content = core_manager.load(file_key="memory")
        assert "Decision" in memory_content

        # 验证近端记忆
        near_content = near_manager.load(days=1)
        assert "editor preference" in near_content
        assert "决策记录" in near_content

        # 验证会话
        assert session.session_key == "user-123"
        assert session.status == "active"
