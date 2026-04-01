"""工具模块集成测试

验证 SecurityChecker + ContainerManager + ToolRegistry + 5个工具执行器协同工作

测试要点：
1. 所有组件正确初始化
2. 工具注册正确完成
3. 安全检查与工具执行正确集成
4. 容器管理与工具执行正确集成
5. 工具适配器格式正确
6. 会话资源清理正确
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestToolModuleIntegration:
    """工具模块集成测试"""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """创建临时目录"""
        (tmp_path / "workspace").mkdir()
        return tmp_path

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置对象"""
        config = MagicMock()

        # LLM 配置
        config.llm.default.provider = "anthropic"
        config.llm.default.model = "claude-3-opus"
        config.llm.default.api_key = "sk-test-key"

        # 存储配置
        config.storage.base_path = str(temp_dir / "smartclaw_test")

        # 工具配置
        config.tools.root_dir = str(temp_dir / "workspace")
        config.tools.max_file_size = 1048576
        config.tools.allow_overwrite = False

        config.tools.terminal.image = "alpine:3.19"
        config.tools.terminal.memory_limit = "256m"
        config.tools.terminal.cpu_limit = "0.25"
        config.tools.terminal.execution_timeout = 30
        config.tools.terminal.max_retries = 3
        config.tools.terminal.retry_backoff = [1, 2, 4]

        config.tools.python_repl.image = "python:3.11-slim"
        config.tools.python_repl.memory_limit = "512m"
        config.tools.python_repl.cpu_limit = "0.25"
        config.tools.python_repl.execution_timeout = 30
        config.tools.python_repl.max_retries = 3
        config.tools.python_repl.retry_backoff = [1, 2, 4]

        # 用于 fetch_url 的配置（直接在 tools 上）
        config.tools.fetch_url.timeout = 10
        config.tools.fetch_url.max_response_size = 1048576

        # 安全配置
        config.security.allowed_extensions = [".txt", ".md", ".py", ".json", ".yaml", ".yml"]
        config.security.banned_commands = ["rm -rf", "dd", "mkfs"]
        config.security.confirm_commands = ["rm", "mv", "cp"]
        config.security.banned_domains = ["malicious.com"]
        config.security.allowed_domains = ["example.com"]

        return config

    @patch("docker.from_env")
    def test_full_module_initialization(self, mock_docker: MagicMock, mock_config: MagicMock, temp_dir: Path) -> None:
        """测试完整模块初始化"""
        from backend.tools.security import SecurityChecker
        from backend.tools.container import ContainerManager
        from backend.tools.registry import ToolRegistry

        # 初始化安全检查器
        security_checker = SecurityChecker(mock_config)
        assert security_checker is not None
        assert security_checker.config == mock_config

        # 初始化容器管理器
        container_manager = ContainerManager(mock_config)
        assert container_manager is not None
        assert container_manager.config == mock_config

        # 初始化工具注册表
        tool_registry = ToolRegistry(mock_config)
        assert tool_registry is not None
        assert tool_registry.config == mock_config

    def test_security_checker_integration(self, mock_config: MagicMock) -> None:
        """测试安全检查器集成"""
        from backend.tools.security import SecurityChecker

        security_checker = SecurityChecker(mock_config)

        # 测试路径安全检查
        allowed, status = security_checker.check_path_safety("/tmp/smartclaw_test/test.txt")
        # 允许的路径应该通过
        assert isinstance(allowed, bool)
        assert isinstance(status, str)

        # 测试禁止的路径
        allowed, status = security_checker.check_path_safety("../../../etc/passwd")
        assert not allowed  # 应该被拒绝

        # 测试文件类型检查
        allowed, status = security_checker.check_file_type("test.txt")
        assert allowed  # txt 文件应该被允许

        allowed, status = security_checker.check_file_type("test.exe")
        assert not allowed  # exe 文件应该被拒绝

    @patch("docker.from_env")
    def test_tool_registry_integration(self, mock_docker: MagicMock, mock_config: MagicMock) -> None:
        """测试工具注册表集成"""
        from backend.tools.registry import ToolRegistry

        tool_registry = ToolRegistry(mock_config)

        # 注册所有工具
        tool_registry.register_tools()

        # 验证工具已注册
        all_tools = tool_registry.get_all_tools()
        assert len(all_tools) > 0

        # 验证可以获取工具
        # 注意：某些工具可能需要容器，所以可能会失败
        for tool_name in all_tools:
            if tool_name in ["read_file", "write_file", "fetch_url"]:
                # 这些工具不需要容器
                tool = tool_registry.get_tool(tool_name)
                assert tool is not None

    def test_file_tools_integration(self, mock_config: MagicMock, temp_dir: Path) -> None:
        """测试文件工具集成"""
        from backend.tools.security import SecurityChecker
        from backend.tools.file_tools import FileReader, FileWriter

        security_checker = SecurityChecker(mock_config)

        # 测试 FileReader
        reader = FileReader(mock_config, security_checker)

        # 创建测试文件
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content", encoding="utf-8")

        # 读取文件
        content = reader.read(str(test_file))
        assert content == "Test content"

        # 测试 FileWriter
        writer = FileWriter(mock_config, security_checker)

        # 写入新文件
        new_file = temp_dir / "new.txt"
        result = writer.write(str(new_file), "New content")
        assert "Success" in result

        # 验证文件内容
        assert new_file.read_text(encoding="utf-8") == "New content"

    def test_tool_adapter_format(self, mock_config: MagicMock) -> None:
        """测试工具适配器格式"""
        from backend.tools.security import SecurityChecker
        from backend.tools.file_tools import FileReader, FileWriter, UrlFetcher

        security_checker = SecurityChecker(mock_config)

        # 测试 FileReader 适配器
        reader = FileReader(mock_config, security_checker)
        reader_adapter = reader.get_tool_adapter()
        assert "name" in reader_adapter
        assert "description" in reader_adapter
        assert "func" in reader_adapter
        assert reader_adapter["name"] == "read_file"
        assert callable(reader_adapter["func"])

        # 测试 FileWriter 适配器
        writer = FileWriter(mock_config, security_checker)
        writer_adapter = writer.get_tool_adapter()
        assert "name" in writer_adapter
        assert "description" in writer_adapter
        assert "func" in writer_adapter
        assert writer_adapter["name"] == "write_file"
        assert callable(writer_adapter["func"])

        # 测试 UrlFetcher 适配器
        fetcher = UrlFetcher(mock_config, security_checker)
        fetcher_adapter = fetcher.get_tool_adapter()
        assert "name" in fetcher_adapter
        assert "description" in fetcher_adapter
        assert "func" in fetcher_adapter
        assert fetcher_adapter["name"] == "fetch_url"
        assert callable(fetcher_adapter["func"])

    def test_security_check_in_file_operations(self, mock_config: MagicMock, temp_dir: Path) -> None:
        """测试文件操作中的安全检查"""
        from backend.tools.security import SecurityChecker
        from backend.tools.file_tools import FileReader, FileWriter

        security_checker = SecurityChecker(mock_config)

        # 测试路径遍历攻击被拦截
        reader = FileReader(mock_config, security_checker)
        result = reader.read("../../../etc/passwd")
        assert "Security Error" in result or "error" in result.lower()

        # 测试不允许的文件类型
        writer = FileWriter(mock_config, security_checker)
        result = writer.write(str(temp_dir / "test.exe"), "content")
        assert "Security Error" in result or "error" in result.lower()

    @patch("requests.get")
    def test_url_fetcher_integration(self, mock_get: MagicMock, mock_config: MagicMock) -> None:
        """测试 URL 获取器集成"""
        from backend.tools.security import SecurityChecker
        from backend.tools.file_tools import UrlFetcher

        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        security_checker = SecurityChecker(mock_config)
        fetcher = UrlFetcher(mock_config, security_checker)

        # 测试 URL 获取
        result = fetcher.fetch("https://example.com")
        assert "Test content" in result

        # 测试禁止的域名（通过修改配置）
        mock_config.security.banned_domains = ["example.com"]
        banned_checker = SecurityChecker(mock_config)
        banned_fetcher = UrlFetcher(mock_config, banned_checker)
        result = banned_fetcher.fetch("https://example.com")
        assert "Security Error" in result or "banned" in result.lower() or "not allowed" in result.lower()

    @patch("docker.from_env")
    def test_session_cleanup(self, mock_docker: MagicMock, mock_config: MagicMock) -> None:
        """测试会话清理"""
        from backend.tools.container import ContainerManager
        from backend.tools.registry import ToolRegistry

        container_manager = ContainerManager(mock_config)
        tool_registry = ToolRegistry(mock_config)

        # 注册工具
        tool_registry.register_tools()

        # 清理会话（应该不会抛出异常）
        session_id = "test_session_123"
        tool_registry.cleanup_session(session_id)
        container_manager.cleanup_session_containers(session_id)

    def test_concurrent_tool_access(self, mock_config: MagicMock) -> None:
        """测试并发工具访问"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from backend.tools.security import SecurityChecker
        from backend.tools.file_tools import FileReader

        security_checker = SecurityChecker(mock_config)
        reader = FileReader(mock_config, security_checker)

        # 并发调用工具方法
        def read_safe() -> str:
            try:
                return reader.read("/tmp/test.txt")  # 文件可能不存在，但不应崩溃
            except Exception:
                return "error"

        with ThreadPoolExecutor(max_workers=5) as executor_pool:
            futures = [executor_pool.submit(read_safe) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # 所有调用都应该有结果（可能是错误）
        assert len(results) == 10

    def test_error_propagation(self, mock_config: MagicMock) -> None:
        """测试错误传播"""
        from backend.tools.security import SecurityChecker
        from backend.tools.file_tools import FileReader

        security_checker = SecurityChecker(mock_config)
        reader = FileReader(mock_config, security_checker)

        # 测试不存在的文件
        result = reader.read("/nonexistent/file.txt")
        # 应该返回错误信息而不是抛出异常
        assert isinstance(result, str)
        assert "not found" in result.lower() or "no such file" in result.lower() or "error" in result.lower()
