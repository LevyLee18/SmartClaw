"""测试 PythonExecutor

测试要点：
1. 正常 Python 代码执行成功
2. 危险模块被拦截（subprocess, os.system 等）
3. 超时代码被终止
4. 返回正确的输出格式
5. 异常正确处理
"""

from pathlib import Path
from unittest.mock import MagicMock
from typing import Any

import pytest


class TestPythonExecutor:
    """PythonExecutor 测试类"""

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = temp_dir
        config.tools.python_repl.memory_limit = "512m"
        config.tools.python_repl.cpu_limit = "25%"
        config.tools.python_repl.execution_timeout = 30
        return config

    @pytest.fixture
    def mock_security_checker(self) -> MagicMock:
        """创建模拟 SecurityChecker"""
        checker = MagicMock()
        checker.check_python_code.return_value = (True, "safe")
        return checker

    @pytest.fixture
    def mock_container(self) -> MagicMock:
        """创建模拟 Docker 容器"""
        container = MagicMock()
        container.status = "running"

        # 模拟 exec_run 返回
        def mock_exec_run(cmd: str, **kwargs: Any) -> tuple[int, bytes]:
            # 简单的 Python 代码执行模拟
            if "print" in cmd:
                return 0, b"test output\n"
            return 0, b"None\n"

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
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        assert executor.config == mock_config
        assert executor.security_checker == mock_security_checker
        assert executor.container_manager == mock_container_manager
        assert executor.session_id == "test_session"

    def test_execute_code_success(self, mock_config: MagicMock,
                                   mock_security_checker: MagicMock,
                                   mock_container_manager: MagicMock) -> None:
        """测试正常代码执行"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("print('hello')")

        assert result is not None
        mock_container_manager.get_container.assert_called_once_with("python_repl", "test_session")

    def test_execute_dangerous_module(self, mock_config: MagicMock,
                                      mock_security_checker: MagicMock,
                                      mock_container_manager: MagicMock) -> None:
        """测试危险模块被拦截"""
        from backend.tools.python_repl import PythonExecutor

        # 配置 SecurityChecker 拒绝代码
        mock_security_checker.check_python_code.return_value = (
            False,
            "banned"
        )

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("import subprocess; subprocess.run(['rm', '-rf', '/'])")

        # 应该返回错误信息
        assert "banned" in result.lower() or "security" in result.lower()
        # 不应该调用容器
        mock_container_manager.get_container.assert_not_called()

    def test_execute_timeout(self, mock_config: MagicMock,
                             mock_security_checker: MagicMock,
                             mock_container_manager: MagicMock) -> None:
        """测试超时代码被终止"""
        from backend.tools.python_repl import PythonExecutor

        # 创建超时的模拟容器
        mock_container = MagicMock()
        mock_container.exec_run.side_effect = Exception("Command timed out")
        mock_container_manager.get_container.return_value = mock_container

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("import time; time.sleep(100)")

        # 应该返回超时错误信息
        assert "timeout" in result.lower() or "timed out" in result.lower()

    def test_execute_syntax_error(self, mock_config: MagicMock,
                                  mock_security_checker: MagicMock,
                                  mock_container_manager: MagicMock) -> None:
        """测试语法错误处理"""
        from backend.tools.python_repl import PythonExecutor

        # 创建返回语法错误的模拟容器
        mock_container = MagicMock()
        mock_container.exec_run.return_value = (1, b"SyntaxError: invalid syntax\n")
        mock_container_manager.get_container.return_value = mock_container

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("print('hello")

        # 应该包含错误信息
        assert "syntax" in result.lower() or "error" in result.lower()

    def test_execute_runtime_error(self, mock_config: MagicMock,
                                   mock_security_checker: MagicMock,
                                   mock_container_manager: MagicMock) -> None:
        """测试运行时错误处理"""
        from backend.tools.python_repl import PythonExecutor

        # 创建返回运行时错误的模拟容器
        mock_container = MagicMock()
        mock_container.exec_run.return_value = (1, b"NameError: name 'undefined_var' is not defined\n")
        mock_container_manager.get_container.return_value = mock_container

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("print(undefined_var)")

        # 应该包含错误信息
        assert "nameerror" in result.lower() or "error" in result.lower()

    def test_execute_with_custom_timeout(self, mock_config: MagicMock,
                                         mock_security_checker: MagicMock,
                                         mock_container_manager: MagicMock) -> None:
        """测试自定义超时时间"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        # 使用较短的超时时间
        result = executor.execute("print('test')", timeout=5)

        # 验证执行成功
        assert result is not None

    def test_execute_multiline_code(self, mock_config: MagicMock,
                                    mock_security_checker: MagicMock,
                                    mock_container_manager: MagicMock) -> None:
        """测试多行代码执行"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        # 执行多行代码
        result = executor.execute("x = 1\ny = 2\nprint(x + y)")

        # 验证返回结果
        assert result is not None

    def test_execute_import_safe_module(self, mock_config: MagicMock,
                                       mock_security_checker: MagicMock,
                                       mock_container_manager: MagicMock) -> None:
        """测试导入安全模块"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(
            mock_config,
            mock_security_checker,
            mock_container_manager,
            session_id="test_session"
        )

        result = executor.execute("import json\nprint(json.dumps({'key': 'value'}))")

        # 验证执行成功
        assert result is not None

    def test_get_tool_adapter(self, mock_config: MagicMock,
                              mock_security_checker: MagicMock,
                              mock_container_manager: MagicMock) -> None:
        """测试获取 LangChain 工具适配器"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(
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
        assert tool["name"] == "python_repl"
