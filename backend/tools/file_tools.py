"""文件工具实现

包含文件读取、写入和 URL 获取功能。
"""

import re
from typing import Any

import requests

from backend.config.models import Settings
from backend.tools.security import SecurityChecker


class UrlFetcher:
    """URL 内容获取器

    安全获取网页内容并转换为 Markdown 格式。

    Attributes:
        config: SmartClaw 配置对象
        security_checker: 安全检查器
    """

    def __init__(self, config: Settings, security_checker: SecurityChecker) -> None:
        """初始化 URL 获取器

        Args:
            config: SmartClaw 配置对象
            security_checker: 安全检查器
        """
        self.config = config
        self.security_checker = security_checker

    def fetch(self, url: str) -> str:
        """获取 URL 内容

        Args:
            url: 要获取的 URL

        Returns:
            清洗后的 Markdown 内容或错误信息
        """
        # 1. URL 安全检查
        allowed, status = self.security_checker.check_url(url)

        if not allowed:
            return f"Security Error: URL is not allowed - {status}"

        # 2. 验证 URL 格式
        if not self._is_valid_url(url):
            return "Error: Invalid URL format"

        # 3. 获取内容
        try:
            # 获取超时配置（如果存在则使用，否则使用默认值）
            timeout = getattr(self.config.tools, 'fetch_url', None)
            if timeout:
                timeout_value = timeout.timeout
            else:
                timeout_value = 10

            response = requests.get(
                url,
                timeout=timeout_value,
                headers={"User-Agent": "SmartClaw/1.0"},
            )
            response.raise_for_status()

        except requests.Timeout:
            return "Error: Request timed out"
        except requests.HTTPError as e:
            return f"Error: HTTP error occurred - {e}"
        except requests.RequestException as e:
            return f"Error: Failed to fetch URL - {e}"

        # 4. 检查响应大小
        max_size = 1048576  # 1MB 默认
        fetch_config = getattr(self.config.tools, 'fetch_url', None)
        if fetch_config:
            max_size = fetch_config.max_response_size

        content_length = response.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size > max_size:
                return f"Error: Response too large ({size} bytes, max {max_size} bytes)"

        # 5. 转换为 Markdown
        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            # JSON 响应直接返回
            return response.text

        elif "text/html" in content_type:
            # HTML 响应转换为 Markdown
            return self._html_to_markdown(response.text)

        else:
            # 其他类型直接返回文本
            return response.text

    def _is_valid_url(self, url: str) -> bool:
        """验证 URL 格式

        Args:
            url: 要验证的 URL

        Returns:
            是否为有效 URL
        """
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:\S+(?::\S*)?@)?"  # optional auth
            r"(?:[A-Za-z0-9-]+\.)+"  # domain
            r"[A-Za-z]{2,}"  # TLD
            r"(?:/[^\s]*)?$"  # optional path
        )
        return bool(url_pattern.match(url))

    def _html_to_markdown(self, html_content: str) -> str:
        """将 HTML 转换为 Markdown

        Args:
            html_content: HTML 内容

        Returns:
            Markdown 内容
        """
        from html import unescape

        # 简单的 HTML 到 Markdown 转换
        # 解码 HTML 实体
        text = unescape(html_content)

        # 移除 script 和 style 标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换标题
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换段落
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换链接
        text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换加粗
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换斜体
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换代码
        text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换列表
        text = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', text, flags=re.DOTALL | re.IGNORECASE)

        # 转换换行
        text = re.sub(r'<br[^>]*>', '\n', text, flags=re.IGNORECASE)

        # 移除剩余的 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)

        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def get_tool_adapter(self) -> dict[str, Any]:
        """获取 LangChain 工具适配器

        返回一个符合 LangChain 工具规范的字典，包含：
        - name: 工具名称
        - description: 工具描述
        - func: 可调用的工具函数

        Returns:
            工具配置字典
        """

        def fetch_url(url: str) -> str:
            """获取网页内容并转换为 Markdown

            安全获取指定 URL 的网页内容，并自动转换为 Markdown 格式。

            Args:
                url: 要获取的网页 URL

            Returns:
                转换后的 Markdown 内容或错误信息

            安全限制：
            - URL 安全检查（域名白名单/黑名单）
            - 响应大小限制
            - 请求超时限制
            """
            return self.fetch(url)

        return {
            "name": "fetch_url",
            "description": (
                "获取网页内容并转换为 Markdown 格式。"
                "安全获取指定 URL 的网页内容，并自动转换为 Markdown 格式。"
                "支持 HTML 和 JSON 响应。"
            ),
            "func": fetch_url,
        }
