"""测试 FileWriter

测试要点：
1. 正常文件写入成功
2. 路径安全检查生效（路径遍历攻击拦截）
3. 文件类型限制生效
4. 文件覆盖确认（默认拒绝覆盖）
5. 文件不存在时创建新文件
6. 超大内容处理
7. 敏感文件写入拦截
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestFileWriter:
    """FileWriter 测试类"""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """创建临时目录"""
        (tmp_path / "subdir").mkdir()
        return tmp_path

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = temp_dir
        config.tools.root_dir = str(temp_dir)
        config.tools.max_file_size = 1048576  # 1MB
        config.tools.allow_overwrite = False  # 默认不允许覆盖
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
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)

        assert writer.config == mock_config
        assert writer.security_checker == mock_security_checker

    def test_write_file_success(self, temp_dir: Path, mock_config: MagicMock,
                                 mock_security_checker: MagicMock) -> None:
        """测试正常文件写入（新文件）"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        file_path = temp_dir / "new_file.txt"

        result = writer.write(str(file_path), "Hello, World!")

        assert result == "Success: File written successfully"
        assert file_path.read_text(encoding="utf-8") == "Hello, World!"

    def test_write_file_path_traversal_attack(self, mock_config: MagicMock,
                                               mock_security_checker: MagicMock) -> None:
        """测试路径遍历攻击被拦截"""
        from backend.tools.file_tools import FileWriter

        # 配置 SecurityChecker 拦截路径遍历
        mock_security_checker.check_path_safety.return_value = (
            False,
            "Path traversal detected"
        )

        writer = FileWriter(mock_config, mock_security_checker)

        result = writer.write("/etc/malicious.txt", "content")

        # 应该返回错误信息
        assert "security" in result.lower() or "traversal" in result.lower() or "error" in result.lower()

    def test_write_file_type_not_allowed(self, temp_dir: Path, mock_config: MagicMock,
                                          mock_security_checker: MagicMock) -> None:
        """测试不允许的文件类型"""
        from backend.tools.file_tools import FileWriter

        # 配置 SecurityChecker 拒绝该类型
        mock_security_checker.check_file_type.return_value = (
            False,
            "File type .exe not allowed"
        )

        writer = FileWriter(mock_config, mock_security_checker)

        result = writer.write(str(temp_dir / "test.exe"), "content")

        # 应该返回错误信息
        assert "not allowed" in result.lower() or "error" in result.lower()

    def test_write_file_overwrite_default_rejected(self, temp_dir: Path, mock_config: MagicMock,
                                                    mock_security_checker: MagicMock) -> None:
        """测试文件覆盖默认被拒绝"""
        from backend.tools.file_tools import FileWriter

        # 创建已存在的文件
        existing_file = temp_dir / "existing.txt"
        existing_file.write_text("Original content", encoding="utf-8")

        writer = FileWriter(mock_config, mock_security_checker)

        result = writer.write(str(existing_file), "New content")

        # 应该返回覆盖拒绝错误
        assert "overwrite" in result.lower() or "exists" in result.lower() or "error" in result.lower()

        # 文件内容不应改变
        assert existing_file.read_text(encoding="utf-8") == "Original content"

    def test_write_file_overwrite_with_allow(self, temp_dir: Path, mock_config: MagicMock,
                                              mock_security_checker: MagicMock) -> None:
        """测试允许覆盖时写入成功"""
        from backend.tools.file_tools import FileWriter

        # 创建已存在的文件
        existing_file = temp_dir / "existing.txt"
        existing_file.write_text("Original content", encoding="utf-8")

        # 允许覆盖
        mock_config.tools.allow_overwrite = True

        writer = FileWriter(mock_config, mock_security_checker)

        result = writer.write(str(existing_file), "New content")

        assert result == "Success: File written successfully"
        assert existing_file.read_text(encoding="utf-8") == "New content"

    def test_write_file_content_size_limit(self, temp_dir: Path, mock_config: MagicMock,
                                            mock_security_checker: MagicMock) -> None:
        """测试超大内容处理"""
        from backend.tools.file_tools import FileWriter

        # 设置较小的文件大小限制
        mock_config.tools.max_file_size = 100  # 100 bytes

        writer = FileWriter(mock_config, mock_security_checker)

        large_content = "x" * 200
        result = writer.write(str(temp_dir / "large.txt"), large_content)

        # 应该返回大小限制错误
        assert "size" in result.lower() or "too large" in result.lower() or "limit" in result.lower()

    def test_write_file_creates_directory(self, temp_dir: Path, mock_config: MagicMock,
                                          mock_security_checker: MagicMock) -> None:
        """测试写入时创建不存在的目录"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        nested_path = temp_dir / "new_dir" / "sub_dir" / "file.txt"

        result = writer.write(str(nested_path), "Content in nested directory")

        assert result == "Success: File written successfully"
        assert nested_path.read_text(encoding="utf-8") == "Content in nested directory"

    def test_write_file_markdown(self, temp_dir: Path, mock_config: MagicMock,
                                  mock_security_checker: MagicMock) -> None:
        """测试写入 Markdown 文件"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        file_path = temp_dir / "test.md"

        result = writer.write(str(file_path), "# Test Markdown\n\nContent here.")

        assert result == "Success: File written successfully"
        assert "# Test Markdown" in file_path.read_text(encoding="utf-8")

    def test_write_file_python(self, temp_dir: Path, mock_config: MagicMock,
                                mock_security_checker: MagicMock) -> None:
        """测试写入 Python 文件"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)
        file_path = temp_dir / "test.py"

        result = writer.write(str(file_path), "print('hello world')")

        assert result == "Success: File written successfully"
        assert "print('hello world')" in file_path.read_text(encoding="utf-8")

    def test_get_tool_adapter(self, mock_config: MagicMock,
                              mock_security_checker: MagicMock) -> None:
        """测试获取 LangChain 工具适配器"""
        from backend.tools.file_tools import FileWriter

        writer = FileWriter(mock_config, mock_security_checker)

        tool = writer.get_tool_adapter()

        # 验证工具格式
        assert isinstance(tool, dict)
        assert "name" in tool
        assert "description" in tool
        assert "func" in tool
        assert tool["name"] == "write_file"
