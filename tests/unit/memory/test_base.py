"""测试 MemoryManager 抽象基类

测试要点：
1. 类是抽象类，不能直接实例化
2. 抽象方法 load() 和 exists() 必须由子类实现
3. write() 方法有默认实现
"""

from abc import ABC
from pathlib import Path

import pytest


class TestMemoryManagerAbstractClass:
    """MemoryManager 抽象类测试"""

    def test_is_abstract_class(self) -> None:
        """测试 MemoryManager 是抽象类"""
        from backend.memory.base import MemoryManager

        assert issubclass(MemoryManager, ABC)

    def test_cannot_be_instantiated_directly(self) -> None:
        """测试 MemoryManager 不能直接实例化"""
        from backend.memory.base import MemoryManager

        with pytest.raises(TypeError):
            MemoryManager(base_path=Path("/tmp/test"))  # type: ignore[abstract]

    def test_has_abstract_load_method(self) -> None:
        """测试 load() 是抽象方法"""
        from backend.memory.base import MemoryManager

        # 检查 load 方法是抽象方法
        assert hasattr(MemoryManager.load, "__isabstractmethod__")
        assert MemoryManager.load.__isabstractmethod__ is True

    def test_has_abstract_exists_method(self) -> None:
        """测试 exists() 是抽象方法"""
        from backend.memory.base import MemoryManager

        # 检查 exists 方法是抽象方法
        assert hasattr(MemoryManager.exists, "__isabstractmethod__")
        assert MemoryManager.exists.__isabstractmethod__ is True

    def test_write_has_default_implementation(self) -> None:
        """测试 write() 有默认实现（不是抽象方法）"""
        from backend.memory.base import MemoryManager

        # write 方法不应该是抽象方法
        assert not getattr(MemoryManager.write, "__isabstractmethod__", False)


class TestMemoryManagerConcreteImplementation:
    """测试具体的 MemoryManager 实现"""

    def test_concrete_class_can_be_instantiated(self, temp_dir: Path) -> None:
        """测试实现了所有抽象方法的子类可以被实例化"""
        from backend.memory.base import MemoryManager

        class ConcreteMemoryManager(MemoryManager):
            """具体实现类"""

            def load(self) -> str:
                return "test content"

            def exists(self) -> bool:
                return True

        manager = ConcreteMemoryManager(base_path=temp_dir)
        assert manager.base_path == temp_dir

    def test_concrete_class_load_returns_string(self, temp_dir: Path) -> None:
        """测试具体实现类的 load() 返回字符串"""
        from backend.memory.base import MemoryManager

        class ConcreteMemoryManager(MemoryManager):
            def load(self) -> str:
                return "loaded content"

            def exists(self) -> bool:
                return True

        manager = ConcreteMemoryManager(base_path=temp_dir)
        content = manager.load()

        assert isinstance(content, str)
        assert content == "loaded content"

    def test_concrete_class_exists_returns_bool(self, temp_dir: Path) -> None:
        """测试具体实现类的 exists() 返回布尔值"""
        from backend.memory.base import MemoryManager

        class ConcreteMemoryManager(MemoryManager):
            def load(self) -> str:
                return ""

            def exists(self) -> bool:
                return False

        manager = ConcreteMemoryManager(base_path=temp_dir)
        result = manager.exists()

        assert isinstance(result, bool)
        assert result is False

    def test_write_default_implementation(self, temp_dir: Path) -> None:
        """测试 write() 默认实现"""
        from backend.memory.base import MemoryManager

        class ConcreteMemoryManager(MemoryManager):
            def load(self) -> str:
                return ""

            def exists(self) -> bool:
                return True

        manager = ConcreteMemoryManager(base_path=temp_dir)

        # 默认实现应该不执行任何操作
        manager.write()

    def test_base_path_attribute(self, temp_dir: Path) -> None:
        """测试 base_path 属性正确设置"""
        from backend.memory.base import MemoryManager

        class ConcreteMemoryManager(MemoryManager):
            def load(self) -> str:
                return ""

            def exists(self) -> bool:
                return True

        manager = ConcreteMemoryManager(base_path=temp_dir)

        assert manager.base_path == temp_dir
        assert isinstance(manager.base_path, Path)


class TestMemoryManagerSubclassWithoutAbstractMethods:
    """测试未实现所有抽象方法的子类"""

    def test_subclass_without_load_cannot_be_instantiated(
        self, temp_dir: Path
    ) -> None:
        """测试未实现 load() 的子类不能被实例化"""
        from backend.memory.base import MemoryManager

        class IncompleteMemoryManager(MemoryManager):
            """缺少 load() 实现"""

            def exists(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteMemoryManager(base_path=temp_dir)  # type: ignore[abstract]

    def test_subclass_without_exists_cannot_be_instantiated(
        self, temp_dir: Path
    ) -> None:
        """测试未实现 exists() 的子类不能被实例化"""
        from backend.memory.base import MemoryManager

        class IncompleteMemoryManager(MemoryManager):
            """缺少 exists() 实现"""

            def load(self) -> str:
                return ""

        with pytest.raises(TypeError):
            IncompleteMemoryManager(base_path=temp_dir)  # type: ignore[abstract]
