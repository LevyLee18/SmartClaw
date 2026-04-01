"""SmartClaw 日志敏感信息脱敏模块

提供敏感信息脱敏功能，确保日志中不泄露敏感数据。

脱敏规则：
1. API Key：保留前 4 位和后 4 位，中间用 **** 替换
2. 路径：隐藏用户目录中的用户名
3. URL：敏感参数（token, key, password）替换为 [REDACTED]
4. 密码/密钥：替换为 [REDACTED]
"""

import logging
import re
from typing import Optional, Union

# 敏感参数名模式
SENSITIVE_PARAMS = ["token", "key", "password", "passwd", "secret", "api_key", "apikey", "auth"]

# API Key 模式：sk- 前缀 + 任意字母数字和连字符
# 匹配如 sk-ant-xxx, sk-proj-xxx, sk-xxx 等
API_KEY_PATTERN = re.compile(r"(sk-[a-z]{2,}-)?([a-zA-Z0-9-]+)")

# 短 API Key 模式（如 sk-abc123 或 sk-ant-abc123）
SHORT_API_KEY_PATTERN = re.compile(r"sk-[a-zA-Z0-9-]+")

# 用户路径模式
USER_PATH_PATTERN = re.compile(r"(/Users/|/home/|C:\\Users\\)([^/\\]+)")

# URL 敏感参数模式
URL_PARAM_PATTERN = re.compile(
    r"([?&])((" + "|".join(SENSITIVE_PARAMS) + r")=)([^&\s]+)",
    re.IGNORECASE,
)

# 密码赋值模式（包括字典中的形式）
PASSWORD_PATTERN = re.compile(
    r"(['\"]?(?:password|passwd|pwd|secret|token|api_key)['\"]?\s*[=:]\s*)['\"]?([^'\"]+)['\"]?",
    re.IGNORECASE,
)

# URL 中密码模式
URL_PASSWORD_PATTERN = re.compile(r"(://[^:]+:)([^@]+)(@)")


def redact_api_key(key: Optional[Union[str, int]]) -> str:
    """脱敏 API Key

    保留前 4 位和后 4 位，中间用 **** 替换。

    Args:
        key: API Key 字符串或数字

    Returns:
        脱敏后的字符串

    Examples:
        >>> redact_api_key("sk-ant-1234567890abcdef")
        "sk-a****cdef"
    """
    if key is None:
        return ""

    # 转换为字符串
    key_str = str(key)

    if not key_str:
        return ""

    # 如果不是 sk- 开头的，直接返回原值（对于非字符串数字等）
    if not key_str.startswith("sk-"):
        return key_str

    # 对于 sk-xxx 格式的 key
    if len(key_str) > 12:
        # 保留前4位和后4位
        return f"{key_str[:4]}****{key_str[-4:]}"
    elif len(key_str) > 6:
        # 短 key 保留前2位和后2位
        return f"{key_str[:2]}****{key_str[-2:]}"

    # 非常短的 key，完全隐藏
    return "****"


def redact_path(path: Optional[str]) -> str:
    """脱敏文件路径

    隐藏用户主目录中的用户名。

    Args:
        path: 文件路径

    Returns:
        脱敏后的路径

    Examples:
        >>> redact_path("/Users/john/.smartclaw/config.yaml")
        "/Users/***/.smartclaw/config.yaml"
    """
    if not path:
        return ""

    path_str = str(path)

    # 匹配用户路径并替换用户名
    def replace_user(match: re.Match[str]) -> str:
        prefix = match.group(1)
        return f"{prefix}***"

    return USER_PATH_PATTERN.sub(replace_user, path_str)


def redact_url(url: Optional[str]) -> str:
    """脱敏 URL 中的敏感参数

    将敏感参数值替换为 [REDACTED]。

    Args:
        url: URL 字符串

    Returns:
        脱敏后的 URL

    Examples:
        >>> redact_url("https://api.example.com?token=secret123&id=1")
        "https://api.example.com?token=[REDACTED]&id=1"
    """
    if not url:
        return ""

    url_str = str(url)

    # 替换 URL 中的密码
    url_str = URL_PASSWORD_PATTERN.sub(r"\1[REDACTED]\3", url_str)

    # 替换 URL 参数中的敏感值
    url_str = URL_PARAM_PATTERN.sub(r"\1\2[REDACTED]", url_str)

    return url_str


def redact_message(message: str) -> str:
    """脱敏消息中的所有敏感信息

    综合应用所有脱敏规则。

    Args:
        message: 原始消息

    Returns:
        脱敏后的消息
    """
    if not message:
        return message

    result = message

    # 1. 脱敏 API Keys（使用查找替换）
    def replace_api_key_in_msg(match: re.Match[str]) -> str:
        return redact_api_key(match.group(0))

    # 匹配所有 sk- 开头的 key
    result = SHORT_API_KEY_PATTERN.sub(replace_api_key_in_msg, result)

    # 2. 脱敏密码赋值
    def replace_password(match: re.Match[str]) -> str:
        prefix = match.group(1)
        return f"{prefix}[REDACTED]"

    result = PASSWORD_PATTERN.sub(replace_password, result)

    # 3. 脱敏 URL
    result = redact_url(result)

    # 4. 脱敏路径
    result = redact_path(result)

    return result


class SmartClawRedactingFilter(logging.Filter):
    """SmartClaw 日志脱敏过滤器

    自动脱敏日志记录中的敏感信息。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤并脱敏日志记录

        Args:
            record: 日志记录

        Returns:
            总是返回 True（允许记录），但会修改消息
        """
        # 脱敏消息
        if record.msg:
            record.msg = redact_message(str(record.msg))

        return True
