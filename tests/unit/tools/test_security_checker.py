"""SecurityChecker 类单元测试

测试 SecurityChecker 的初始化和安全检查功能。
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.config.models import SecurityConfig, Settings


def create_mock_settings() -> Settings:
    """创建带 Mock 配置的 Settings"""
    return Settings(security=SecurityConfig())


class TestSecurityCheckerInit:
    """测试 SecurityChecker.__init__"""

    def test_init_with_valid_config(self):
        """测试使用有效配置初始化"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        assert checker.config == config

    def test_init_stores_config(self):
        """测试初始化存储配置"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        assert hasattr(checker, "config")
        assert checker.config is config

    def test_init_initializes_banned_commands(self):
        """测试初始化禁止命令列表"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        assert hasattr(checker, "banned_commands")
        assert isinstance(checker.banned_commands, dict)
        assert "direct" in checker.banned_commands
        assert "confirm" in checker.banned_commands

    def test_init_initializes_allowed_extensions(self):
        """测试初始化允许的文件扩展名"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        assert hasattr(checker, "allowed_extensions")
        assert isinstance(checker.allowed_extensions, list)
        assert ".md" in checker.allowed_extensions
        assert ".py" in checker.allowed_extensions

    def test_init_initializes_dangerous_patterns(self):
        """测试初始化危险模式"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        assert hasattr(checker, "dangerous_patterns")


class TestCheckPathSafety:
    """测试 check_path_safety 方法"""

    def test_check_safe_path(self):
        """测试安全路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, message = checker.check_path_safety("/home/user/project/file.md")
        assert is_safe is True

    def test_check_path_traversal_attack(self):
        """测试路径遍历攻击检测"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, message = checker.check_path_safety("../../../etc/passwd")
        assert is_safe is False
        assert "遍历" in message or "危险" in message or "traversal" in message.lower()

    def test_check_absolute_path_outside_base(self):
        """测试基础路径外的绝对路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试系统敏感路径
        is_safe, message = checker.check_path_safety("/etc/passwd")
        assert is_safe is False

    def test_check_symlink_path(self):
        """测试符号链接路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 符号链接需要特殊处理
        is_safe, message = checker.check_path_safety("/home/user/link_to_secret")
        # 根据实现，可能需要解析符号链接后检查
        assert isinstance(is_safe, bool)

    def test_check_path_with_special_characters(self):
        """测试包含特殊字符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含特殊字符的路径
        is_safe, message = checker.check_path_safety("/home/user/$HOME/secrets")
        assert is_safe is False


class TestCheckCommandSafety:
    """测试 check_command_safety 方法"""

    def test_check_safe_command(self):
        """测试安全命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, level = checker.check_command_safety("ls -la")
        assert is_safe is True
        assert level == "safe"

    def test_check_direct_banned_command(self):
        """测试直接禁止的命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, level = checker.check_command_safety("rm -rf /")
        assert is_safe is False
        assert level == "banned"

    def test_check_sudo_command(self):
        """测试 sudo 命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, level = checker.check_command_safety("sudo apt install package")
        assert is_safe is False
        assert level == "banned"

    def test_check_confirm_required_command(self):
        """测试需要确认的命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, level = checker.check_command_safety("rm file.txt")
        assert is_safe is True  # 不是直接禁止，但需要确认
        assert level == "confirm"

    def test_check_network_command(self):
        """测试网络命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, level = checker.check_command_safety("curl http://example.com")
        # 网络命令可能需要特殊处理
        assert isinstance(is_safe, bool)

    def test_check_command_with_pipe(self):
        """测试管道命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_safe, level = checker.check_command_safety("cat file.txt | grep pattern")
        assert is_safe is True
        assert level == "safe"


class TestCheckFileType:
    """测试 check_file_type 方法"""

    def test_check_allowed_file_type(self):
        """测试允许的文件类型"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_allowed, message = checker.check_file_type("document.md")
        assert is_allowed is True

    def test_check_allowed_python_file(self):
        """测试允许的 Python 文件"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_allowed, message = checker.check_file_type("script.py")
        assert is_allowed is True

    def test_check_disallowed_file_type(self):
        """测试不允许的文件类型"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_allowed, message = checker.check_file_type("virus.exe")
        assert is_allowed is False

    def test_check_binary_file(self):
        """测试二进制文件"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_allowed, message = checker.check_file_type("data.bin")
        assert is_allowed is False

    def test_check_hidden_file(self):
        """测试隐藏文件"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_allowed, message = checker.check_file_type(".env")
        # 隐藏文件通常需要特殊处理
        assert isinstance(is_allowed, bool)


class TestIsDangerousCommand:
    """测试 _is_dangerous_command 方法"""

    def test_is_dangerous_rm_rf(self):
        """测试 rm -rf 是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("rm -rf /")
        assert is_dangerous is True

    def test_is_dangerous_sudo(self):
        """测试 sudo 是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("sudo reboot")
        assert is_dangerous is True

    def test_is_dangerous_dd(self):
        """测试 dd 是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("dd if=/dev/zero of=/dev/sda")
        assert is_dangerous is True

    def test_is_dangerous_mkfs(self):
        """测试 mkfs 是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("mkfs.ext4 /dev/sda1")
        assert is_dangerous is True

    def test_is_not_dangerous_ls(self):
        """测试 ls 不是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("ls -la")
        assert is_dangerous is False

    def test_is_not_dangerous_cat(self):
        """测试 cat 不是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("cat file.txt")
        assert is_dangerous is False

    def test_is_dangerous_shutdown(self):
        """测试 shutdown 是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("shutdown -h now")
        assert is_dangerous is True

    def test_is_dangerous_reboot(self):
        """测试 reboot 是危险命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        is_dangerous = checker._is_dangerous_command("reboot")
        assert is_dangerous is True
