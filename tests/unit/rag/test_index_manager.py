"""测试 IndexManager 抽象基类

测试要点：
1. 验证类为抽象类，不能直接实例化
2. 验证抽象方法定义
3. 验证子类必须实现所有抽象方法
"""

from pathlib import Path
from typing import Any

import pytest


class TestIndexManagerIsAbstract:
    """IndexManager 抽象类验证测试"""

    def test_cannot_instantiate_directly(self, temp_dir: Path) -> None:
        """测试不能直接实例化抽象类"""
        from backend.rag.index_manager import IndexManager

        with pytest.raises(TypeError):
            IndexManager(base_path=temp_dir)  # type: ignore[abstract]

    def test_has_search_abstract_method(self) -> None:
        """测试定义了 search 抽象方法"""
        from backend.rag.index_manager import IndexManager

        assert hasattr(IndexManager, "search")
        method = getattr(IndexManager, "search")
        assert getattr(method, "__isabstractmethod__", False)

    def test_has_update_document_abstract_method(self) -> None:
        """测试定义了 update_document 抽象方法"""
        from backend.rag.index_manager import IndexManager

        assert hasattr(IndexManager, "update_document")
        method = getattr(IndexManager, "update_document")
        assert getattr(method, "__isabstractmethod__", False)

    def test_has_delete_document_abstract_method(self) -> None:
        """测试定义了 delete_document 抽象方法"""
        from backend.rag.index_manager import IndexManager

        assert hasattr(IndexManager, "delete_document")
        method = getattr(IndexManager, "delete_document")
        assert getattr(method, "__isabstractmethod__", False)

    def test_has_build_index_abstract_method(self) -> None:
        """测试定义了 build_index 抽象方法"""
        from backend.rag.index_manager import IndexManager

        assert hasattr(IndexManager, "build_index")
        method = getattr(IndexManager, "build_index")
        assert getattr(method, "__isabstractmethod__", False)


class TestIndexManagerSubclass:
    """IndexManager 子类测试"""

    def test_subclass_must_implement_all_abstract_methods(
        self, temp_dir: Path
    ) -> None:
        """测试子类必须实现所有抽象方法"""

        from backend.rag.index_manager import IndexManager

        # 不完整的实现应该无法实例化
        class IncompleteIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5):
                pass

        with pytest.raises(TypeError):
            IncompleteIndexManager(base_path=temp_dir)  # type: ignore[abstract]

    def test_complete_subclass_can_be_instantiated(self, temp_dir: Path) -> None:
        """测试完整实现的子类可以实例化"""

        from backend.rag.index_manager import IndexManager
        from backend.rag.models import Segment

        class CompleteIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5) -> list[Segment]:
                return []

            def update_document(
                self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
            ) -> bool:
                return True

            def delete_document(self, doc_id: str) -> bool:
                return True

            def build_index(self, force: bool = False) -> bool:
                return True

        # 应该可以实例化
        manager = CompleteIndexManager(base_path=temp_dir)
        assert manager is not None


class TestIndexManagerInterface:
    """IndexManager 接口测试"""

    def test_search_returns_list_of_segments(self, temp_dir: Path) -> None:
        """测试 search 返回 Segment 列表"""

        from backend.rag.index_manager import IndexManager
        from backend.rag.models import Segment

        class MockIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5) -> list[Segment]:
                return [
                    Segment(
                        content="Test content",
                        source="test.md",
                        file_type="long_term",
                        score=0.95,
                    )
                ]

            def update_document(
                self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
            ) -> bool:
                return True

            def delete_document(self, doc_id: str) -> bool:
                return True

            def build_index(self, force: bool = False) -> bool:
                return True

        manager = MockIndexManager(base_path=temp_dir)
        results = manager.search("test query")

        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], Segment)

    def test_update_document_returns_bool(self, temp_dir: Path) -> None:
        """测试 update_document 返回布尔值"""

        from backend.rag.index_manager import IndexManager

        class MockIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5):
                return []

            def update_document(
                self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
            ) -> bool:
                return doc_id == "valid-id"

            def delete_document(self, doc_id: str) -> bool:
                return True

            def build_index(self, force: bool = False) -> bool:
                return True

        manager = MockIndexManager(base_path=temp_dir)

        assert manager.update_document("valid-id", "content") is True
        assert manager.update_document("invalid-id", "content") is False

    def test_delete_document_returns_bool(self, temp_dir: Path) -> None:
        """测试 delete_document 返回布尔值"""

        from backend.rag.index_manager import IndexManager

        class MockIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5):
                return []

            def update_document(
                self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
            ) -> bool:
                return True

            def delete_document(self, doc_id: str) -> bool:
                return doc_id == "existing-id"

            def build_index(self, force: bool = False) -> bool:
                return True

        manager = MockIndexManager(base_path=temp_dir)

        assert manager.delete_document("existing-id") is True
        assert manager.delete_document("non-existing-id") is False

    def test_build_index_returns_bool(self, temp_dir: Path) -> None:
        """测试 build_index 返回布尔值"""

        from backend.rag.index_manager import IndexManager

        class MockIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5):
                return []

            def update_document(
                self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
            ) -> bool:
                return True

            def delete_document(self, doc_id: str) -> bool:
                return True

            def build_index(self, force: bool = False) -> bool:
                return True

        manager = MockIndexManager(base_path=temp_dir)

        assert manager.build_index() is True
        assert manager.build_index(force=True) is True

    def test_index_manager_has_base_path_attribute(self, temp_dir: Path) -> None:
        """测试 IndexManager 有 base_path 属性"""

        from backend.rag.index_manager import IndexManager

        class MockIndexManager(IndexManager):
            def search(self, query: str, top_k: int = 5):
                return []

            def update_document(
                self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
            ) -> bool:
                return True

            def delete_document(self, doc_id: str) -> bool:
                return True

            def build_index(self, force: bool = False) -> bool:
                return True

        manager = MockIndexManager(base_path=temp_dir)

        assert manager.base_path == temp_dir
