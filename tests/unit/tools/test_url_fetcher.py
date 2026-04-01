"""测试 UrlFetcher

测试要点：
1. 正常 URL 获取成功
2. URL 安全检查生效
3. 响应大小限制生效
4. 内容清洗为 Markdown
5. 异常正确处理
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests


class TestUrlFetcher:
    """UrlFetcher 测试类"""

    @pytest.fixture
    def mock_config(self, temp_dir: Path) -> MagicMock:
        """创建模拟配置"""
        config = MagicMock()
        config.storage.base_path = temp_dir
        config.tools.fetch_url.max_response_size = 1048576  # 1MB
        config.tools.fetch_url.timeout = 10
        config.security.allowed_domains = ["example.com", "test.com"]
        config.security.banned_domains = ["malicious.com", "spam.com"]
        return config

    @pytest.fixture
    def mock_security_checker(self) -> MagicMock:
        """创建模拟 SecurityChecker"""
        checker = MagicMock()
        checker.check_url.return_value = (True, "safe")
        return checker

    def test_init(self, mock_config: MagicMock, mock_security_checker: MagicMock) -> None:
        """测试初始化"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        assert fetcher.config == mock_config
        assert fetcher.security_checker == mock_security_checker

    @patch("requests.get")
    def test_fetch_url_success(self, mock_get: MagicMock, mock_config: MagicMock,
                               mock_security_checker: MagicMock) -> None:
        """测试正常 URL 获取"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://example.com")

        assert "Test content" in result
        mock_get.assert_called_once()

    def test_fetch_url_banned_domain(self, mock_config: MagicMock,
                                     mock_security_checker: MagicMock) -> None:
        """测试禁止域名被拦截"""
        from backend.tools.file_tools import UrlFetcher

        # 配置 SecurityChecker 拒绝 URL
        mock_security_checker.check_url.return_value = (
            False,
            "banned"
        )

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://malicious.com")

        # 应该返回错误信息
        assert "banned" in result.lower() or "security" in result.lower()

    @patch("requests.get")
    def test_fetch_url_timeout(self, mock_get: MagicMock, mock_config: MagicMock,
                               mock_security_checker: MagicMock) -> None:
        """测试超时处理"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟超时
        mock_get.side_effect = requests.Timeout("Connection timed out")

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://example.com")

        # 应该返回超时错误信息
        assert "timeout" in result.lower() or "timed out" in result.lower()

    @patch("requests.get")
    def test_fetch_url_http_error(self, mock_get: MagicMock, mock_config: MagicMock,
                                   mock_security_checker: MagicMock) -> None:
        """测试 HTTP 错误处理"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟 404 错误
        mock_get.side_effect = requests.HTTPError("404 Not Found")

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://example.com/notfound")

        # 应该返回错误信息
        assert "error" in result.lower() or "not found" in result.lower()

    @patch("requests.get")
    def test_fetch_url_size_limit(self, mock_get: MagicMock, mock_config: MagicMock,
                                   mock_security_checker: MagicMock) -> None:
        """测试响应大小限制"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟超过大小限制的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "2097152"}  # 2MB
        mock_get.return_value = mock_response

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://example.com/large")

        # 应该返回大小限制错误
        assert "size" in result.lower() or "too large" in result.lower()

    @patch("requests.get")
    def test_fetch_url_html_to_markdown(self, mock_get: MagicMock, mock_config: MagicMock,
                                         mock_security_checker: MagicMock) -> None:
        """测试 HTML 转 Markdown"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟 HTML 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>This is a paragraph.</p>
                <a href="/link">Click here</a>
            </body>
        </html>
        """
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://example.com")

        # 验证包含标题和段落
        assert "Main Heading" in result or "Test Page" in result

    @patch("requests.get")
    def test_fetch_url_json_response(self, mock_get: MagicMock, mock_config: MagicMock,
                                     mock_security_checker: MagicMock) -> None:
        """测试 JSON 响应处理"""
        from backend.tools.file_tools import UrlFetcher

        # 模拟 JSON 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value", "number": 123}'
        mock_response.headers = {"content-type": "application/json"}
        mock_get.return_value = mock_response

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("https://api.example.com/data")

        # 验证包含 JSON 数据
        assert "key" in result or "value" in result

    def test_fetch_url_invalid_url(self, mock_config: MagicMock,
                                    mock_security_checker: MagicMock) -> None:
        """测试无效 URL 处理"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        result = fetcher.fetch("not-a-valid-url")

        # 应该返回错误信息
        assert "invalid" in result.lower() or "error" in result.lower()

    def test_get_tool_adapter(self, mock_config: MagicMock,
                             mock_security_checker: MagicMock) -> None:
        """测试获取 LangChain 工具适配器"""
        from backend.tools.file_tools import UrlFetcher

        fetcher = UrlFetcher(mock_config, mock_security_checker)

        tool = fetcher.get_tool_adapter()

        # 验证工具格式
        assert isinstance(tool, dict)
        assert "name" in tool
        assert "description" in tool
        assert "func" in tool
        assert tool["name"] == "fetch_url"
