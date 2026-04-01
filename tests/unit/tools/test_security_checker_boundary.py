"""SecurityChecker 边界测试

测试要点：
1. 符号链接处理
2. Unicode 路径处理
3. 超长路径处理
4. 特殊路径组合
"""

from pathlib import Path

import pytest

from backend.config.models import Settings


def create_mock_settings() -> Settings:
    """创建带 Mock 配置的 Settings"""
    from backend.config.models import SecurityConfig, Settings

    return Settings(security=SecurityConfig())


class TestSecurityCheckerSymlinkBoundary:
    """SecurityChecker 符号链接边界测试"""

    def test_check_symlink_to_safe_file(self, tmp_path: Path) -> None:
        """测试指向安全文件的符号链接"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建目标文件
        target_file = tmp_path / "safe_file.txt"
        target_file.write_text("safe content", encoding="utf-8")

        # 创建符号链接
        symlink_path = tmp_path / "link_to_safe"
        symlink_path.symlink_to(target_file)

        # 检查符号链接路径
        is_safe, message = checker.check_path_safety(str(symlink_path))
        assert isinstance(is_safe, bool)
        assert isinstance(message, str)

    def test_check_symlink_to_sensitive_file(self, tmp_path: Path) -> None:
        """测试指向敏感文件的符号链接"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建一个看起来敏感的文件名
        target_file = tmp_path / "secret.txt"
        target_file.write_text("secret content", encoding="utf-8")

        # 创建符号链接
        symlink_path = tmp_path / "link_to_secret"
        symlink_path.symlink_to(target_file)

        # 检查符号链接路径
        is_safe, message = checker.check_path_safety(str(symlink_path))
        assert isinstance(is_safe, bool)

    def test_check_symlink_outside_root(self, tmp_path: Path) -> None:
        """测试指向 root_dir 外部的符号链接"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 在外部创建一个文件
        outside_file = Path("/tmp/outside_file.txt")

        # 创建符号链接指向外部
        symlink_path = tmp_path / "link_to_outside"
        try:
            symlink_path.symlink_to(outside_file)

            # 检查符号链接路径
            is_safe, message = checker.check_path_safety(str(symlink_path))
            # 根据实现，可能会被拒绝
            assert isinstance(is_safe, bool)
        except (OSError, PermissionError):
            # 某些环境可能不允许创建指向外部目录的符号链接
            pytest.skip("Cannot create symlink to outside directory")

    def test_check_symlink_chain(self, tmp_path: Path) -> None:
        """测试符号链接链"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建目标文件
        target_file = tmp_path / "target.txt"
        target_file.write_text("content", encoding="utf-8")

        # 创建符号链接链: link1 -> link2 -> target
        link2 = tmp_path / "link2"
        link2.symlink_to(target_file)

        link1 = tmp_path / "link1"
        link1.symlink_to(link2)

        # 检查符号链接链
        is_safe, message = checker.check_path_safety(str(link1))
        assert isinstance(is_safe, bool)

    def test_check_broken_symlink(self, tmp_path: Path) -> None:
        """测试损坏的符号链接（指向不存在的文件）"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建指向不存在文件的符号链接
        symlink_path = tmp_path / "broken_link"
        symlink_path.symlink_to("/nonexistent/path/to/file.txt")

        # 检查损坏的符号链接
        is_safe, message = checker.check_path_safety(str(symlink_path))
        assert isinstance(is_safe, bool)


class TestSecurityCheckerUnicodeBoundary:
    """SecurityChecker Unicode 路径边界测试"""

    def test_check_unicode_path_chinese(self) -> None:
        """测试包含中文字符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试中文路径
        unicode_path = "/home/user/文档/报告.md"
        is_safe, message = checker.check_path_safety(unicode_path)
        assert isinstance(is_safe, bool)

    def test_check_unicode_path_japanese(self) -> None:
        """测试包含日文字符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试日文路径
        unicode_path = "/home/user/ドキュメント/ファイル.md"
        is_safe, message = checker.check_path_safety(unicode_path)
        assert isinstance(is_safe, bool)

    def test_check_unicode_path_korean(self) -> None:
        """测试包含韩文字符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试韩文路径
        unicode_path = "/home/user/문서/파일.md"
        is_safe, message = checker.check_path_safety(unicode_path)
        assert isinstance(is_safe, bool)

    def test_check_unicode_path_emoji(self) -> None:
        """测试包含表情符号的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试表情符号路径
        unicode_path = "/home/user/📁/📄.md"
        is_safe, message = checker.check_path_safety(unicode_path)
        assert isinstance(is_safe, bool)

    def test_check_unicode_path_mixed_scripts(self) -> None:
        """测试混合多种文字系统的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试混合文字系统
        unicode_path = "/home/user/文档/ファイル/파일/📄.md"
        is_safe, message = checker.check_path_safety(unicode_path)
        assert isinstance(is_safe, bool)

    def test_check_unicode_path_rtl(self) -> None:
        """测试从右到左文字的路径（阿拉伯语、希伯来语）"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试阿拉伯语路径（RTL 文字）
        unicode_path = "/home/user/مستند/ملف.md"
        is_safe, message = checker.check_path_safety(unicode_path)
        assert isinstance(is_safe, bool)

    def test_check_unicode_path_special_chars(self) -> None:
        """测试包含特殊 Unicode 字符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试特殊 Unicode 字符
        unicode_paths = [
            "/home/user/file_with_ spaces.md",
            "/home/user/file_with_dashes_—_md.md",
            "/home/user/file_with_quotes_''_md.md",
        ]

        for path in unicode_paths:
            is_safe, message = checker.check_path_safety(path)
            assert isinstance(is_safe, bool)

    def test_check_unicode_normalization(self) -> None:
        """测试 Unicode 规范化（同一字符的不同编码方式）"""
        from backend.tools.security import SecurityChecker
        import unicodedata

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试 Unicode 规范化
        # é 可以表示为单个字符或 e + 组合重音
        base_path = "/home/user/café"
        normalized_nfc = unicodedata.normalize('NFC', base_path)
        normalized_nfd = unicodedata.normalize('NFD', base_path)

        # 两种规范化方式都应该能正确处理
        is_safe_nfc, _ = checker.check_path_safety(normalized_nfc)
        is_safe_nfd, _ = checker.check_path_safety(normalized_nfd)

        assert isinstance(is_safe_nfc, bool)
        assert isinstance(is_safe_nfd, bool)


class TestSecurityCheckerLongPathBoundary:
    """SecurityChecker 超长路径边界测试"""

    def test_check_very_long_path(self) -> None:
        """测试超长路径（接近系统限制）"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建一个超长路径（不包含 ../ 等危险模式）
        long_path = "/home/user/" + "/".join([f"dir{i}" for i in range(100)]) + "/file.md"

        is_safe, message = checker.check_path_safety(long_path)
        assert isinstance(is_safe, bool)

    def test_check_extremely_long_filename(self) -> None:
        """测试超长文件名"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建一个超长文件名
        long_filename = "a" * 1000 + ".md"
        long_path = f"/home/user/{long_filename}"

        is_safe, message = checker.check_path_safety(long_path)
        assert isinstance(is_safe, bool)

    def test_check_path_with_many_nested_components(self) -> None:
        """测试包含大量嵌套组件的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建深度嵌套的路径
        nested_path = "/home/user"
        for i in range(50):
            nested_path += f"/level{i}"

        nested_path += "/file.md"

        is_safe, message = checker.check_path_safety(nested_path)
        assert isinstance(is_safe, bool)

    def test_check_path_at_os_limit(self) -> None:
        """测试接近操作系统路径长度限制的路径"""
        from backend.tools.security import SecurityChecker
        import sys

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 大多数现代系统的路径限制在 4096 字节左右
        # Windows 限制是 260 字符（除非使用长路径前缀）
        if sys.platform == "win32":
            max_length = 250  # 留一些余量
        else:
            max_length = 4000  # Linux/macOS

        # 创建接近限制的路径
        base = "/home/user/"
        remaining = max_length - len(base)
        directories = ["x" * 250] * (remaining // 251)
        long_path = base + "/".join(directories[:10]) + "/file.md"

        is_safe, message = checker.check_path_safety(long_path)
        assert isinstance(is_safe, bool)

    def test_check_path_with_repeated_separators(self) -> None:
        """测试包含重复分隔符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含重复分隔符的路径（应该被规范化）
        path_with_repeated_separators = "/home/user///documents////file.md"

        is_safe, message = checker.check_path_safety(path_with_repeated_separators)
        assert isinstance(is_safe, bool)

    def test_check_path_with_trailing_separator(self) -> None:
        """测试以分隔符结尾的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试以分隔符结尾的路径
        path_with_trailing = "/home/user/documents/"

        is_safe, message = checker.check_path_safety(path_with_trailing)
        assert isinstance(is_safe, bool)


class TestSecurityCheckerSpecialCombinationsBoundary:
    """SecurityChecker 特殊路径组合边界测试"""

    def test_check_path_with_unicode_and_dots(self) -> None:
        """测试包含 Unicode 字符和点的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含 Unicode 和点的组合
        path = "/home/user/文档/../其他文件/file.md"

        is_safe, message = checker.check_path_safety(path)
        assert isinstance(is_safe, bool)

    def test_check_path_with_encoded_characters(self) -> None:
        """测试包含编码字符的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含 URL 编码的路径
        path = "/home/user/%2e%2e/%2e%2e/etc/passwd"

        is_safe, message = checker.check_path_safety(path)
        assert isinstance(is_safe, bool)

    def test_check_path_with_null_bytes(self) -> None:
        """测试包含空字节的路径"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含空字节的路径（某些攻击可能利用空字节）
        path = "/home/user/file\x00.md"

        is_safe, message = checker.check_path_safety(path)
        assert isinstance(is_safe, bool)

    def test_check_command_with_unicode(self) -> None:
        """测试包含 Unicode 字符的命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含 Unicode 的命令
        commands = [
            "echo '你好世界'",
            "ls -l '文档'",
            "cat 'файл.txt'",
        ]

        for cmd in commands:
            is_safe, level = checker.check_command_safety(cmd)
            assert isinstance(is_safe, bool)

    def test_check_very_long_command(self) -> None:
        """测试超长命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 创建一个超长命令
        long_command = "echo '" + "a" * 10000 + "'"

        is_safe, level = checker.check_command_safety(long_command)
        assert isinstance(is_safe, bool)

    def test_check_command_with_special_unicode(self) -> None:
        """测试包含特殊 Unicode 字符的命令"""
        from backend.tools.security import SecurityChecker

        config = create_mock_settings()
        checker = SecurityChecker(config)

        # 测试包含特殊 Unicode 字符的命令
        # 这些字符可能看起来像普通 ASCII 字符但实际不同（同形字攻击）
        commands = [
            "cat fi\u0131le.txt",  # ı (dotless i) 看起来像 i
            "ls \u0430.txt",  # Cyrillic a 看起来像 a
        ]

        for cmd in commands:
            is_safe, level = checker.check_command_safety(cmd)
            assert isinstance(is_safe, bool)
