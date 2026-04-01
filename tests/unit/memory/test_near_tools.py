"""测试 NearMemoryManager 工具适配器

测试要点：
1. get_write_tool() - 返回 write_near_memory 工具适配器
2. 工具名称正确
3. 工具描述正确
4. 工具参数正确
5. 工具可调用
"""

from pathlib import Path
from typing import Any

import pytest


class TestNearMemoryManagerGetWriteTool:
    """NearMemoryManager.get_write_tool() 测试"""

    def test_get_write_tool_returns_dict(self, temp_dir: Path) -> None:
        """测试 get_write_tool() 返回字典"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert isinstance(tool, dict)

    def test_get_write_tool_has_name(self, temp_dir: Path) -> None:
        """测试工具包含 name 字段"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert "name" in tool
        assert tool["name"] == "write_near_memory"

    def test_get_write_tool_has_description(self, temp_dir: Path) -> None:
        """测试工具包含 description 字段"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert "description" in tool
        assert isinstance(tool["description"], str)
        assert len(tool["description"]) > 0

    def test_get_write_tool_has_callable(self, temp_dir: Path) -> None:
        """测试工具包含可调用的函数"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert "func" in tool
        assert callable(tool["func"])

    def test_get_write_tool_callable_writes_memory(self, temp_dir: Path) -> None:
        """测试工具函数可以写入近端记忆"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 调用工具函数
        result = tool["func"](content="Test memory content")

        # 验证返回值是字符串
        assert isinstance(result, str)

        # 验证文件被创建
        today = manager.get_file_path(manager._get_today())
        assert today.exists()

    def test_get_write_tool_callable_with_date(self, temp_dir: Path) -> None:
        """测试工具函数支持 date 参数"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 调用工具函数，指定日期
        result = tool["func"](content="Test content", date="2026-03-15")

        # 验证文件被创建在指定日期
        expected_file = manager.memory_dir / "2026-03-15.md"
        assert expected_file.exists()

    def test_get_write_tool_callable_with_category(self, temp_dir: Path) -> None:
        """测试工具函数支持 category 参数"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 调用工具函数，指定类别
        result = tool["func"](
            content="Important fact",
            category="重要事实"
        )

        # 验证返回值
        assert isinstance(result, str)
        assert "成功" in result or "success" in result.lower()

    def test_get_write_tool_returns_error_on_invalid_date(self, temp_dir: Path) -> None:
        """测试工具函数对无效日期返回错误"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 调用工具函数，使用无效日期
        result = tool["func"](content="Test", date="invalid-date")

        # 验证返回错误信息
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower()

    def test_get_write_tool_signature(self, temp_dir: Path) -> None:
        """测试工具函数签名正确"""
        from backend.memory.near import NearMemoryManager
        from inspect import signature

        manager = NearMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 获取函数签名
        sig = signature(tool["func"])
        params = list(sig.parameters.keys())

        # 验证参数包含 content, date, category
        assert "content" in params
        assert "date" in params
        assert "category" in params

    def test_get_write_tool_multiple_calls(self, temp_dir: Path) -> None:
        """测试多次调用 get_write_tool() 返回独立的工具实例"""
        from backend.memory.near import NearMemoryManager

        manager = NearMemoryManager(base_path=temp_dir)
        tool1 = manager.get_write_tool()
        tool2 = manager.get_write_tool()

        # 验证是独立的实例
        assert tool1 is not tool2
        assert tool1["name"] == tool2["name"]
        assert tool1["func"] is not tool2["func"]
