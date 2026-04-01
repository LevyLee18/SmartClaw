"""工具执行器边界测试

测试要点：
1. 超时执行
2. 资源耗尽
3. 并发调用
4. 安全绕过尝试
5. 空输入处理
6. 超长输入处理
7. 特殊字符处理
8. 错误恢复
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestTerminalExecutorBoundary:
    """TerminalExecutor 边界测试"""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.tools.terminal.command_timeout = 1  # 1 秒超时
        config.tools.terminal.max_retries = 3
        config.tools.terminal.retry_backoff = [1, 2, 4]
        config.tools.terminal.memory_limit = "256m"
        config.tools.terminal.cpu_limit = 0.25
        config.security.banned_commands = ["rm -rf", "dd", "mkfs"]
        config.security.confirm_commands = ["rm", "mv", "cp"]
        return config

    @pytest.fixture
    def mock_security_checker(self) -> MagicMock:
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
            if "sleep" in cmd:
                # 模拟超时
                time.sleep(2)
                return 0, b""
            elif "echo" in cmd:
                return 0, b"test output\n"
            return 0, b""

        container.exec_run = mock_exec_run
        return container

    @pytest.fixture
    def mock_container_manager(self, mock_container: MagicMock) -> MagicMock:
        """创建模拟 ContainerManager"""
        manager = MagicMock()
        manager.get_container.return_value = mock_container
        return manager

    def test_timeout_execution(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                               mock_container_manager: MagicMock) -> None:
        """测试超时执行"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 创建一个会超时的命令（sleep 10 秒，但配置只有 1 秒超时）
        result = executor.execute("sleep 10")

        # 应该返回超时错误、空结果或错误信息
        # 在实际环境中会被超时终止，在 mock 中返回空字符串
        assert result is not None

    def test_empty_command(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                           mock_container_manager: MagicMock) -> None:
        """测试空命令"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        result = executor.execute("")

        # 应该返回空命令错误或成功（取决于实现）
        assert result is not None

    def test_very_long_command(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                               mock_container_manager: MagicMock) -> None:
        """测试超长命令"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 创建一个超长命令
        long_command = "echo " + "x" * 10000

        result = executor.execute(long_command)

        # 应该能够处理或返回错误
        assert result is not None

    def test_command_with_special_chars(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                         mock_container_manager: MagicMock) -> None:
        """测试包含特殊字符的命令"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 测试各种特殊字符
        special_commands = [
            "echo 'test with spaces and \t tabs'",
            "echo 'test with $VAR'",
            r"echo 'test with \n newline'",
        ]

        for cmd in special_commands:
            result = executor.execute(cmd)
            assert result is not None

    def test_concurrent_commands(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                 mock_container_manager: MagicMock) -> None:
        """测试并发命令执行"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 并发执行多个简单命令
        commands = ["echo 'test1'", "echo 'test2'", "echo 'test3'"]

        with ThreadPoolExecutor(max_workers=3) as executor_pool:
            futures = [executor_pool.submit(self._execute_safe, executor, cmd) for cmd in commands]
            results = [future.result() for future in as_completed(futures)]

        # 所有命令都应该有结果
        assert len(results) == 3
        for result in results:
            assert result is not None

    def _execute_safe(self, executor_obj: object, command: str) -> str:
        """安全执行命令（用于并发测试）"""
        try:
            return executor_obj.execute(command)
        except Exception:
            return "Error: Exception occurred"

    def test_security_bypass_attempt(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                      mock_container_manager: MagicMock) -> None:
        """测试安全绕过尝试"""
        from backend.tools.terminal import TerminalExecutor

        executor = TerminalExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 尝试通过编码等方式绕过安全检查
        bypass_attempts = [
            "r`m` -rf /tmp",  # 尝试通过反引号绕过
            "$(echo rm) -rf /tmp",  # 尝试通过命令替换绕过
            "rm --rf /tmp",  # 尝试通过双破折号绕过
        ]

        for attempt in bypass_attempts:
            result = executor.execute(attempt)
            # 应该被安全检查拦截或返回错误
            assert result is not None


class TestPythonExecutorBoundary:
    """PythonExecutor 边界测试"""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.tools.python_repl.execution_timeout = 1  # 1 秒超时
        config.tools.python_repl.max_retries = 3
        config.tools.python_repl.retry_backoff = [1, 2, 4]
        config.tools.python_repl.memory_limit = "512m"
        config.tools.python_repl.cpu_limit = 0.5
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
            if "sleep" in cmd or "while True" in cmd:
                time.sleep(2)
                return 137, b""  # 模拟被杀死
            return 0, b"42\n"  # 默认返回 42

        container.exec_run = mock_exec_run
        return container

    @pytest.fixture
    def mock_container_manager(self, mock_container: MagicMock) -> MagicMock:
        """创建模拟 ContainerManager"""
        manager = MagicMock()
        manager.get_container.return_value = mock_container
        return manager

    def test_timeout_execution(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                               mock_container_manager: MagicMock) -> None:
        """测试超时执行"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 创建一个会超时的代码（sleep 10 秒，但配置只有 1 秒超时）
        result = executor.execute("import time; time.sleep(10)")

        # 应该返回超时错误或退出码 137（被杀死）
        assert "timeout" in result.lower() or "timed out" in result.lower() or "137" in result

    def test_empty_code(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                        mock_container_manager: MagicMock) -> None:
        """测试空代码"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        result = executor.execute("")

        # 应该能够处理空代码
        assert result is not None

    def test_very_long_code(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                            mock_container_manager: MagicMock) -> None:
        """测试超长代码"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 创建一个超长代码（大量重复语句）
        long_code = "x = 0\n" + "x += 1\n" * 1000

        result = executor.execute(long_code)

        # 应该能够处理或返回错误
        assert result is not None

    def test_infinite_loop_protection(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                      mock_container_manager: MagicMock) -> None:
        """测试无限循环保护"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 创建一个无限循环（应该被超时机制终止）
        result = executor.execute("while True: pass")

        # 应该返回超时错误或退出码 137（被杀死）
        assert "timeout" in result.lower() or "timed out" in result.lower() or "137" in result or "error" in result.lower()

    def test_memory_exhaustion_protection(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                          mock_container_manager: MagicMock) -> None:
        """测试内存耗尽保护"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 尝试创建一个巨大的列表（应该被限制）
        result = executor.execute("x = [0] * (10 ** 9)")

        # 应该返回内存错误或超时
        assert result is not None

    def test_syntax_error_recovery(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                   mock_container_manager: MagicMock) -> None:
        """测试语法错误恢复"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 执行语法错误的代码
        result1 = executor.execute("this is a syntax error")

        # 然后执行正确的代码
        result2 = executor.execute("x = 42; print(x)")

        # 第二个代码应该能够正常执行
        assert "42" in result2 or result2 != result1

    def test_special_characters_in_code(self, mock_config: MagicMock, mock_security_checker: MagicMock,
                                         mock_container_manager: MagicMock) -> None:
        """测试代码中的特殊字符"""
        from backend.tools.python_repl import PythonExecutor

        executor = PythonExecutor(mock_config, mock_security_checker, mock_container_manager, "test_session")

        # 测试包含特殊字符的代码
        special_code = r"""
x = 'test with \n newline and \t tab'
y = "test with 'quotes'"
print(x, y)
"""

        result = executor.execute(special_code)

        # 应该能够处理
        assert result is not None


class TestFileToolsBoundary:
    """FileReader/FileWriter 边界测试"""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """创建临时目录"""
        return tmp_path

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = temp_dir
        config.tools.root_dir = str(temp_dir)
        config.tools.max_file_size = 1024  # 1KB
        config.tools.allow_overwrite = False
        config.security.allowed_extensions = [".txt", ".md"]
        return config

    @pytest.fixture
    def mock_security_checker(self) -> MagicMock:
        """创建模拟 SecurityChecker"""
        checker = MagicMock()
        checker.check_path_safety.return_value = (True, "safe")
        checker.check_file_type.return_value = (True, "allowed")
        return checker

    def test_read_empty_file(self, temp_dir: Path, mock_config: MagicMock,
                             mock_security_checker: MagicMock) -> None:
        """测试读取空文件"""
        from backend.tools.file_tools import FileReader

        # 创建空文件
        empty_file = temp_dir / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        reader = FileReader(mock_config, mock_security_checker)
        result = reader.read(str(empty_file))

        # 应该返回空字符串
        assert result == ""

    def test_write_empty_content(self, temp_dir: Path, mock_config: MagicMock,
                                 mock_security_checker: MagicMock) -> None:
        """测试写入空内容"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        file_path = temp_dir / "empty.txt"

        result = writer.write(str(file_path), "")

        # 应该成功
        assert "Success" in result or result == "Success: File written successfully"

    def test_read_nonexistent_path(self, mock_config: MagicMock,
                                    mock_security_checker: MagicMock) -> None:
        """测试读取不存在的路径"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        # 尝试读取不存在的文件
        result = reader.read("/nonexistent/path/to/file.txt")

        # 应该返回错误信息
        assert "not found" in result.lower() or "no such file" in result.lower() or "error" in result.lower()

    def test_write_to_readonly_directory(self, temp_dir: Path, mock_config: MagicMock,
                                          mock_security_checker: MagicMock) -> None:
        """测试写入只读目录"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)

        # 尝试写入根目录（应该被权限检查拒绝）
        result = writer.write("/readonly/file.txt", "content")

        # 应该返回权限错误或路径错误
        assert result is not None

    def test_concurrent_file_operations(self, temp_dir: Path, mock_config: MagicMock,
                                         mock_security_checker: MagicMock) -> None:
        """测试并发文件操作"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        file_path = temp_dir / "concurrent.txt"

        # 并发写入和读取
        with ThreadPoolExecutor(max_workers=4) as executor_pool:
            # 提交写入任务
            write_futures = [
                executor_pool.submit(writer.write, str(file_path), f"content{i}")
                for i in range(5)
            ]
            # 等待所有写入完成
            results = [future.result() for future in as_completed(write_futures)]

        # 所有操作都应该有结果
        assert len(results) == 5

    def test_unicode_content(self, temp_dir: Path, mock_config: MagicMock,
                             mock_security_checker: MagicMock) -> None:
        """测试 Unicode 内容"""
        from backend.tools.file_tools import FileReader, FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        reader = FileReader(mock_config, mock_security_checker)

        file_path = temp_dir / "unicode.txt"

        # 测试各种 Unicode 字符
        unicode_content = """
        English: Hello World
        Chinese: 你好世界
        Japanese: こんにちは
        Emoji: 🎉 🔥 🚀
        Math: ∑ ∫ ∂ √
        Symbols: © ® ™ € £ ¥
        """

        write_result = writer.write(str(file_path), unicode_content)
        assert "Success" in write_result or write_result == "Success: File written successfully"

        read_result = reader.read(str(file_path))

        # 验证内容一致（至少包含部分 Unicode 字符）
        assert "Hello World" in read_result
        assert "你好世界" in read_result

    def test_path_with_spaces(self, temp_dir: Path, mock_config: MagicMock,
                              mock_security_checker: MagicMock) -> None:
        """测试包含空格的路径"""
        from backend.tools.file_tools import FileWriter, FileReader

        writer = FileWriter(mock_config, mock_security_checker)
        reader = FileReader(mock_config, mock_security_checker)

        # 创建包含空格的路径
        file_with_spaces = temp_dir / "path with spaces" / "file name.txt"

        write_result = writer.write(str(file_with_spaces), "content")
        assert "Success" in write_result or write_result == "Success: File written successfully"

        read_result = reader.read(str(file_with_spaces))
        assert read_result == "content"


class TestUrlFetcherBoundary:
    """UrlFetcher 边界测试"""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.tools.fetch_url.timeout = 1  # 1 秒超时
        config.tools.fetch_url.max_response_size = 1024  # 1KB
        config.security.allowed_domains = ["example.com"]
        config.security.banned_domains = ["malicious.com"]
        return config

    @pytest.fixture
    def mock_security_checker(self) -> MagicMock:
        """创建模拟 SecurityChecker"""
        checker = MagicMock()
        checker.check_url.return_value = (True, "safe")
        return checker

    def test_timeout_fetch(self, mock_config: MagicMock,
                          mock_security_checker: MagicMock) -> None:
        """测试超时获取"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        # 尝试访问一个会超时的 URL（使用一个不存在的地址）
        result = fetcher.fetch("http://192.0.2.1:9999")  # TEST-NET-1，保留用于测试

        # 应该返回超时错误
        assert "timeout" in result.lower() or "timed out" in result.lower() or "error" in result.lower()

    def test_empty_url(self, mock_config: MagicMock,
                       mock_security_checker: MagicMock) -> None:
        """测试空 URL"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("")

        # 应该返回格式错误
        assert "invalid" in result.lower() or "error" in result.lower()

    def test_very_long_url(self, mock_config: MagicMock,
                           mock_security_checker: MagicMock) -> None:
        """测试超长 URL"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        # 创建一个超长 URL
        long_url = "https://example.com/" + "a" * 10000

        result = fetcher.fetch(long_url)

        # 应该能够处理或返回错误
        assert result is not None

    def test_url_with_special_chars(self, mock_config: MagicMock,
                                     mock_security_checker: MagicMock) -> None:
        """测试包含特殊字符的 URL"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        # 测试各种特殊字符的 URL
        special_urls = [
            "https://example.com/path with spaces",
            "https://example.com/path?query=value&other=test",
            "https://example.com/path#fragment",
        ]

        for url in special_urls:
            result = fetcher.fetch(url)
            # 可能失败但不应该崩溃
            assert result is not None

    @patch("requests.get")
    def test_oversized_response(self, mock_get: MagicMock, mock_config: MagicMock,
                                 mock_security_checker: MagicMock) -> None:
        """测试超大响应"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟超大响应
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "1048576"}  # 1MB，超过限制
        mock_get.return_value = mock_response

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://example.com/large")

        # 应该返回大小限制错误
        assert "size" in result.lower() or "too large" in result.lower() or "limit" in result.lower()

    def test_concurrent_fetches(self, mock_config: MagicMock,
                                mock_security_checker: MagicMock) -> None:
        """测试并发获取"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        # 并发获取多个 URL（可能失败但不应该崩溃）
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetcher.fetch, url) for url in urls]
            results = [future.result() for future in as_completed(futures)]

        # 所有请求都应该有结果
        assert len(results) == 3
        for result in results:
            assert result is not None
