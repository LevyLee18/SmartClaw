"""测试 FileReader

测试要点：
1. 正常文件读取成功
2. 路径安全检查生效（路径遍历攻击拦截）
3. 文件类型限制生效
4. 敏感文件访问拦截
5. 文件不存在处理
6. 超大文件处理
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestFileReader:
    """FileReader 测试类"""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """创建临时目录并添加测试文件"""
        # 创建测试文件
        (tmp_path / "test.txt").write_text("Hello, World!", encoding="utf-8")
        (tmp_path / "test.md").write_text("# Test Markdown\n\nContent here.", encoding="utf-8")
        (tmp_path / "test.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested.txt").write_text("Nested content", encoding="utf-8")

        # 创建敏感文件
        (tmp_path / ".env").write_text("SECRET_KEY=value", encoding="utf-8")

        return tmp_path

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = temp_dir
        config.tools.root_dir = str(temp_dir)
        config.tools.max_file_size = 1048576  # 1MB
        config.security.allowed_extensions = [
            ".txt", ".md", ".py", ".json", ".yaml", ".yml"
        ]
        config.security.banned_commands = []
        config.security.confirm_commands = []
        return config

    @pytest.fixture
    def mock_security_checker(self) -> MagicMock:
        """创建模拟 SecurityChecker"""
        checker = MagicMock()
        checker.check_path_safety.return_value = (True, "safe")
        checker.check_file_type.return_value = (True, "allowed")
        return checker

    def test_init(self, mock_config: MagicMock, mock_security_checker: MagicMock) -> None:
        """测试初始化"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        assert reader.config == mock_config
        assert reader.security_checker == mock_security_checker

    def test_read_file_success(self, temp_dir: Path, mock_config: MagicMock,
                                mock_security_checker: MagicMock) -> None:
        """测试正常文件读取"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read(str(temp_dir / "test.txt"))

        assert result == "Hello, World!"

    def test_read_file_path_traversal_attack(self, mock_config: MagicMock,
                                              mock_security_checker: MagicMock) -> None:
        """测试路径遍历攻击被拦截"""
        from backend.tools.file_tools import FileReader

        # 配置 SecurityChecker 拦绝路径遍历
        mock_security_checker.check_path_safety.return_value = (
            False,
            "Path traversal detected"
        )

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read("/etc/passwd")

        # 应该返回错误信息
        assert "security" in result.lower() or "traversal" in result.lower() or "error" in result.lower()

    def test_read_file_type_not_allowed(self, temp_dir: Path, mock_config: MagicMock,
                                         mock_security_checker: MagicMock) -> None:
        """测试不允许的文件类型"""
        from backend.tools.file_tools import FileReader

        # 创建不允许的文件类型
        (temp_dir / "test.exe").write_text("executable content", encoding="utf-8")

        # 配置 SecurityChecker 拒绝该类型
        mock_security_checker.check_file_type.return_value = (
            False,
            "File type .exe not allowed"
        )

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read(str(temp_dir / "test.exe"))

        # 应该返回错误信息
        assert "not allowed" in result.lower() or "error" in result.lower()

    def test_read_file_not_exists(self, mock_config: MagicMock,
                                   mock_security_checker: MagicMock) -> None:
        """测试文件不存在"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read("/nonexistent/path/to/file.txt")

        # 应该返回错误信息
        assert "not found" in result.lower() or "no such file" in result.lower() or "error" in result.lower()

    def test_read_file_size_limit(self, temp_dir: Path, mock_config: MagicMock,
                                   mock_security_checker: MagicMock) -> None:
        """测试超大文件处理"""
        from backend.tools.file_tools import FileReader

        # 设置较小的文件大小限制
        mock_config.tools.max_file_size = 100  # 100 bytes

        # 创建超过限制的文件
        large_content = "x" * 200
        (temp_dir / "large.txt").write_text(large_content, encoding="utf-8")

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read(str(temp_dir / "large.txt"))

        # 应该返回大小限制错误
        assert "size" in result.lower() or "too large" in result.lower() or "limit" in result.lower()

    def test_read_file_markdown(self, temp_dir: Path, mock_config: MagicMock,
                                 mock_security_checker: MagicMock) -> None:
        """测试读取 Markdown 文件"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read(str(temp_dir / "test.md"))

        assert "# Test Markdown" in result
        assert "Content here." in result

    def test_read_file_python(self, temp_dir: Path, mock_config: MagicMock,
                               mock_security_checker: MagicMock) -> None:
        """测试读取 Python 文件"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read(str(temp_dir / "test.py"))

        assert "print('hello')" in result

    def test_read_file_nested_path(self, temp_dir: Path, mock_config: MagicMock,
                                    mock_security_checker: MagicMock) -> None:
        """测试读取嵌套路径文件"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        result = reader.read(str(temp_dir / "subdir" / "nested.txt"))

        assert result == "Nested content"

    def test_get_tool_adapter(self, mock_config: MagicMock,
                              mock_security_checker: MagicMock) -> None:
        """测试获取 LangChain 工具适配器"""
        from backend.tools.file_tools import FileReader

        reader = FileReader(mock_config, mock_security_checker)

        tool = reader.get_tool_adapter()

        # 验证工具格式
        assert isinstance(tool, dict)
        assert "name" in tool
        assert "description" in tool
        assert "func" in tool
        assert tool["name"] == "read_file"
