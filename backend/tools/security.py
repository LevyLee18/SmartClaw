"""SecurityChecker 实现

负责工具调用的安全检查。
"""

import os
import re
from typing import Literal

from backend.config.models import Settings


class SecurityChecker:
    """安全检查器

    负责检查文件路径、命令、文件类型等的安全性。

    Attributes:
        config: SmartClaw 配置对象
        banned_commands: 禁止的命令分类
        allowed_extensions: 允许的文件扩展名
        dangerous_patterns: 危险模式列表
    """

    def __init__(self, config: Settings) -> None:
        """初始化安全检查器

        Args:
            config: SmartClaw 配置对象
        """
        self.config = config
        self._init_security_rules()

    def _init_security_rules(self) -> None:
        """初始化安全规则"""
        # 从配置获取规则
        security_config = self.config.security

        # 禁止的命令分类
        self.banned_commands: dict[str, list[str]] = {
            "direct": security_config.banned_commands,
            "confirm": security_config.confirm_commands,
        }

        # 允许的文件扩展名
        self.allowed_extensions: list[str] = security_config.allowed_extensions

        # 危险模式（用于检测更复杂的攻击）
        self.dangerous_patterns: list[str] = [
            r"\.\./",  # 路径遍历
            r"\$\{.*\}",  # 环境变量注入
            r"\$[A-Za-z_][A-Za-z0-9_]*",  # 变量引用
            r"[;&|]",  # 命令链接符
            r"`.*`",  # 命令替换
            r"\$\(.*\)",  # 命令替换
        ]

    def check_path_safety(self, path: str) -> tuple[bool, str]:
        """检查路径安全性

        Args:
            path: 要检查的路径

        Returns:
            (是否安全, 消息)
        """
        # 检查路径遍历攻击
        if "../" in path or "..\\" in path:
            return False, "路径遍历攻击被检测"

        # 检查危险模式
        for pattern in self.dangerous_patterns:
            if re.search(pattern, path):
                return False, f"路径包含危险模式: {pattern}"

        # 检查绝对路径是否指向系统敏感目录
        sensitive_paths = [
            "/etc",
            "/root",
            "/var/log",
            "/proc",
            "/sys",
            "/dev",
            "/boot",
            "/lib",
            "/usr/lib",
        ]

        abs_path = os.path.abspath(path)
        for sensitive in sensitive_paths:
            if abs_path.startswith(sensitive):
                return False, f"访问系统敏感目录: {sensitive}"

        return True, "路径安全"

    def check_command_safety(
        self, command: str
    ) -> tuple[bool, Literal["safe", "confirm", "banned"]]:
        """检查命令安全性

        Args:
            command: 要检查的命令

        Returns:
            (是否可执行, 安全级别)
            - safe: 安全，可直接执行
            - confirm: 需要用户确认
            - banned: 直接禁止
        """
        # 检查是否为直接禁止的命令
        if self._is_dangerous_command(command):
            return False, "banned"

        # 检查是否需要确认
        command_lower = command.lower()
        for confirm_cmd in self.banned_commands.get("confirm", []):
            if command_lower.startswith(confirm_cmd.lower()):
                return True, "confirm"

        # 检查网络命令
        network_commands = ["curl", "wget", "nc", "netcat", "telnet"]
        for net_cmd in network_commands:
            if command_lower.startswith(net_cmd):
                return True, "confirm"

        return True, "safe"

    def check_file_type(self, file_path: str) -> tuple[bool, str]:
        """检查文件类型

        Args:
            file_path: 文件路径

        Returns:
            (是否允许, 消息)
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # 检查隐藏文件
        if os.path.basename(file_path).startswith("."):
            # 隐藏文件需要特殊处理，某些允许某些不允许
            hidden_allowed = [".env.example", ".gitignore", ".editorconfig"]
            if file_path not in hidden_allowed:
                return False, "隐藏文件需要特殊处理"

        # 检查扩展名是否在允许列表中
        if ext in self.allowed_extensions:
            return True, f"文件类型 {ext} 允许"

        # 没有扩展名的文件
        if not ext:
            return True, "无扩展名文件允许"

        # 不在允许列表中的扩展名
        return False, f"文件类型 {ext} 不在允许列表中"

    def check_python_code(
        self, code: str
    ) -> tuple[bool, Literal["safe", "banned"]]:
        """检查 Python 代码安全性

        Args:
            code: 要检查的 Python 代码

        Returns:
            (是否可执行, 安全级别)
            - safe: 安全，可直接执行
            - banned: 直接禁止
        """
        # 危险模块和函数列表
        dangerous_patterns = [
            "import subprocess",
            "from subprocess",
            "os.system",
            "os.popen",
            "eval(",
            "exec(",
            "__import__",
            "compile(",
            "open(",
        ]

        code_lower = code.lower()

        # 检查危险模式
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                return False, "banned"

        return True, "safe"

    def check_url(self, url: str) -> tuple[bool, Literal["safe", "banned"]]:
        """检查 URL 安全性

        Args:
            url: 要检查的 URL

        Returns:
            (是否可访问, 安全级别)
            - safe: 安全，可访问
            - banned: 直接禁止
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # 检查禁止域名
            # 注意：这里需要从配置获取 banned_domains，但当前配置中没有
            # 暂时使用空列表
            banned_domains = getattr(self.config.security, 'banned_domains', [])

            for banned in banned_domains:
                if banned.lower() in domain:
                    return False, "banned"

            return True, "safe"

        except Exception:
            return False, "banned"

    def _is_dangerous_command(self, command: str) -> bool:
        """判断是否为危险命令

        Args:
            command: 要检查的命令

        Returns:
            是否为危险命令
        """
        command_lower = command.lower().strip()

        # 检查直接禁止的命令
        for banned in self.banned_commands.get("direct", []):
            if banned.lower() in command_lower:
                return True

        # 检查特定危险模式
        dangerous_patterns = [
            r"\brm\s+-rf\b",
            r"\bsudo\s+rm\b",
            r"\bmkfs\b",
            r"\bdd\s+if=",
            r"\breboot\b",
            r"\bshutdown\b",
            r"\bhalt\b",
            r"\binit\s+[06]\b",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return True

        return False
