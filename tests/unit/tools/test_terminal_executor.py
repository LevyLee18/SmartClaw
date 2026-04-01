"""测试 TerminalExecutor

测试要点：
1. 正常命令执行成功
2. 禁止命令被拦截
3. 需确认命令被正确处理
4. 超时命令被终止
5. 返回正确的输出格式
"""

from pathlib import Path
from unittest.mock import MagicMock
from typing import Any

import pytest


class TestTerminalExecutor:
    """TerminalExecutor 测试类"""

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = temp_dir
        config.tools.terminal.memory_limit = "256m"
        config.tools.terminal.cpu_limit = "25%"
        config.tools.terminal.execution_timeout = 30
        config.security.banned_commands = ["rm -rf", "dd", "mkfs"]
        config.security.confirm_commands = ["reboot", "shutdown"]
        return config

    @pytest.fixture
    def mock_security_checker(self, mock_config: MagicMock) -> MagicMock:
        """创建模拟 SecurityChecker"""
        checker = MagicMock()
        checker.check_command_safety.return_value = (True, "safe")
        return checker

    @pytest.fixture
    def mock_container(self) -> MagicMock:
        """创建模拟 Docker 容器"""
        container = MagicMock()
        container.status = "running"

        # 模拟 exec_run 返回
        def mock_exec_run(cmd: str, **kwargs: Any) -> tuple[int, bytes]:
            # 简单的 echo 命令模拟
            if "echo" in cmd:
                return 0, b"test output\n"
            return 0, b""

        container.exec_run.side_effect = mock_exec_run
        return container

    @pytest.fixture
    def mock_container_manager(self, mock_container: MagicMock) -> MagicMock:
        """创建模拟 ContainerManager"""
        manager = MagicMock()
        manager.get_container.return_value = mock_container
        return manager

    def test_init(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                  mock_container_manager: MagicMock) -> None:
        """测试初始化"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        assert executor.config == mock_config
        assert executor.security_checker == mock_security_checker
        assert executor.container_manager == mock_container_manager
        assert executor.session_id == "test_session"

    def test_execute_command_success(self, mock_config: MagicMock,
                                      mock_security_checker: MagicMock,
                                      mock_container_manager: MagicMock) -> None:
        """测试正常命令执行"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("echo hello")

        assert "test output" in result or "hello" in result
        mock_container_manager.get_container.assert_called_once_with("terminal", "test_session")

    def test_execute_banned_command(self, mock_config: MagicMock,
                                     mock_security_checker: MagicMock,
                                     mock_container_manager: MagicMock) -> None:
        """测试禁止命令被拦截"""
        from backend.tools.terminal import TerminalExecutor

        # 配置 SecurityChecker 拒绝命令
        mock_security_checker.check_command_safety.return_value = (
            False,
            "banned"
        )

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("rm -rf /")

        # 应该返回错误信息
        assert "banned" in result.lower() or "security" in result.lower()
        # 不应该调用容器
        mock_container_manager.get_container.assert_not_called()

    def test_execute_confirm_command(self, mock_config: MagicMock,
                                      mock_security_checker: MagicMock,
                                      mock_container_manager: MagicMock) -> None:
        """测试需确认命令的处理"""
        from backend.tools.terminal import TerminalExecutor

        # 配置 SecurityChecker 返回需要确认
        mock_security_checker.check_command_safety.return_value = (
            True,
            "confirm"
        )

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        # 不提供确认标志
        result = executor.execute("reboot")

        # 应该返回需要确认的信息
        assert "confirm" in result.lower()

    def test_execute_with_confirmed_flag(self, mock_config: MagicMock,
                                          mock_security_checker: MagicMock,
                                          mock_container_manager: MagicMock) -> None:
        """测试带确认标志的命令执行"""
        from backend.tools.terminal import TerminalExecutor

        mock_security_checker.check_command_safety.return_value = (True, "safe")

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        # 提供确认标志
        _ = executor.execute("reboot", confirmed=True)

        # 即使是需要确认的命令，也应该执行
        mock_container_manager.get_container.assert_called_once()

    def test_execute_timeout(self, mock_config: MagicMock,
                             mock_security_checker: MagicMock,
                             mock_container_manager: MagicMock) -> None:
        """测试超时命令被终止"""
        from backend.tools.terminal import TerminalExecutor

        # 创建超时的模拟容器
        mock_container = MagicMock()
        mock_container.exec_run.side_effect = Exception("Command timed out")
        mock_container_manager.get_container.return_value = mock_container

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("sleep 100")

        # 应该返回超时错误信息
        assert "timeout" in result.lower() or "timed out" in result.lower()

    def test_execute_command_error(self, mock_config: MagicMock,
                                    mock_security_checker: MagicMock,
                                    mock_container_manager: MagicMock) -> None:
        """测试命令执行错误"""
        from backend.tools.terminal import TerminalExecutor

        # 创建返回非零退出码的模拟容器
        mock_container = MagicMock()
        mock_container.exec_run.return_value = (1, b"Error: command not found\n")
        mock_container_manager.get_container.return_value = mock_container

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("nonexistent_command")

        # 应该包含错误信息
        assert "error" in result.lower() or "not found" in result.lower()

    def test_execute_with_custom_timeout(self, mock_config: MagicMock,
                                         mock_security_checker: MagicMock,
                                         mock_container_manager: MagicMock) -> None:
        """测试自定义超时时间"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        # 使用较短的超时时间
        result = executor.execute("echo test", timeout=5)

        # 验证执行成功
        assert result is not None

    def test_execute_multiline_command(self, mock_config: MagicMock,
                                        mock_security_checker: MagicMock,
                                        mock_container_manager: MagicMock) -> None:
        """测试多行命令执行"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        # 执行多行命令
        result = executor.execute("echo 'line1'\necho 'line2'")

        # 验证返回结果
        assert result is not None

    def test_get_tool_adapter(self, mock_config: MagicMock,
                              mock_security_checker: MagicMock,
                              mock_container_manager: MagicMock) -> None:
        """测试获取 LangChain 工具适配器"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        tool = executor.get_tool_adapter()

        # 验证工具格式
        assert isinstance(tool, dict)
        assert "name" in tool
        assert "description" in tool
        assert "func" in tool
        assert tool["name"] == "terminal"
