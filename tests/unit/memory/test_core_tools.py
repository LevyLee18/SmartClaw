"""测试 CoreMemoryManager 工具适配器

测试要点：
1. get_write_tool() - 返回 write_core_memory 工具适配器
2. 工具名称正确
3. 工具描述正确
4. 工具参数正确
5. 工具可调用
6. 正确处理只读文件
"""

from pathlib import Path
from typing import Any

import pytest


class TestCoreMemoryManagerGetWriteTool:
    """CoreMemoryManager.get_write_tool() 测试"""

    def test_get_write_tool_returns_dict(self, temp_dir: Path) -> None:
        """测试 get_write_tool() 返回字典"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert isinstance(tool, dict)

    def test_get_write_tool_has_name(self, temp_dir: Path) -> None:
        """测试工具包含 name 字段"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert "name" in tool
        assert tool["name"] == "write_core_memory"

    def test_get_write_tool_has_description(self, temp_dir: Path) -> None:
        """测试工具包含 description 字段"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert "description" in tool
        assert isinstance(tool["description"], str)
        assert len(tool["description"]) > 0

    def test_get_write_tool_has_callable(self, temp_dir: Path) -> None:
        """测试工具包含可调用的函数"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        assert "func" in tool
        assert callable(tool["func"])

    def test_get_write_tool_callable_writes_memory(self, temp_dir: Path) -> None:
        """测试工具函数可以写入核心记忆"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 调用工具函数
        result = tool["func"](
            file_key="user",
            content="Test user profile"
        )

        # 验证返回值是字符串
        assert isinstance(result, str)
        assert "成功" in result or "success" in result.lower()

        # 验证文件被创建
        user_file = manager.core_memory_dir / "USER.md"
        assert user_file.exists()

    def test_get_write_tool_callable_with_mode(self, temp_dir: Path) -> None:
        """测试工具函数支持 mode 参数"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 先写入初始内容
        tool["func"](
            file_key="memory",
            content="Initial content",
            mode="append"
        )

        # 使用 replace 模式覆盖
        result = tool["func"](
            file_key="memory",
            content="Replaced content",
            mode="replace"
        )

        # 验证返回值
        assert isinstance(result, str)

        # 验证内容被替换
        memory_file = manager.core_memory_dir / "MEMORY.md"
        content = memory_file.read_text()
        assert "Replaced content" in content
        assert "Initial content" not in content

    def test_get_write_tool_rejects_readonly_file(self, temp_dir: Path) -> None:
        """测试工具函数拒绝写入只读文件"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 尝试写入只读文件
        result = tool["func"](
            file_key="agents",
            content="Should not work"
        )

        # 验证返回错误信息
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower() or "readonly" in result.lower()

    def test_get_write_tool_invalid_file_key(self, temp_dir: Path) -> None:
        """测试工具函数对无效 file_key 返回错误"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 调用工具函数，使用无效 file_key
        result = tool["func"](
            file_key="invalid_key",
            content="Test"
        )

        # 验证返回错误信息
        assert isinstance(result, str)
        assert "错误" in result or "error" in result.lower() or "invalid" in result.lower()

    def test_get_write_tool_signature(self, temp_dir: Path) -> None:
        """测试工具函数签名正确"""
        from backend.memory.core import CoreMemoryManager
        from inspect import signature

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        # 获取函数签名
        sig = signature(tool["func"])
        params = list(sig.parameters.keys())

        # 验证参数包含 file_key, content, mode
        assert "file_key" in params
        assert "content" in params
        assert "mode" in params

    def test_get_write_tool_supports_all_valid_keys(self, temp_dir: Path) -> None:
        """测试工具函数支持所有有效的 file_key"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool = manager.get_write_tool()

        valid_keys = ["soul", "identity", "user", "memory"]

        for key in valid_keys:
            result = tool["func"](
                file_key=key,
                content=f"Test content for {key}"
            )

            # 验证每次写入都成功
            assert isinstance(result, str)
            assert "成功" in result or "success" in result.lower()

    def test_get_write_tool_multiple_calls(self, temp_dir: Path) -> None:
        """测试多次调用 get_write_tool() 返回独立的工具实例"""
        from backend.memory.core import CoreMemoryManager

        manager = CoreMemoryManager(base_path=temp_dir)
        tool1 = manager.get_write_tool()
        tool2 = manager.get_write_tool()

        # 验证是独立的实例
        assert tool1 is not tool2
        assert tool1["name"] == tool2["name"]
        assert tool1["func"] is not tool2["func"]
