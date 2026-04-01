"""测试 RAG 模块数据模型

测试要点：
1. Document 类 - 验证 doc_id, content, metadata 字段
2. Node 类 - 验证 node_id, content, metadata, relationships 字段
3. Segment 类 - 验证 content, source, file_type, timestamp, score 字段
"""


class TestDocument:
    """Document 数据类测试"""

    def test_document_has_doc_id(self) -> None:
        """测试 Document 包含 doc_id 字段"""
        from backend.rag.models import Document

        doc = Document(doc_id="test-doc-123", content="Test content")

        assert doc.doc_id == "test-doc-123"

    def test_document_has_content(self) -> None:
        """测试 Document 包含 content 字段"""
        from backend.rag.models import Document

        doc = Document(doc_id="test-doc-123", content="Test content")

        assert doc.content == "Test content"

    def test_document_has_metadata(self) -> None:
        """测试 Document 包含 metadata 字段"""
        from backend.rag.models import Document

        doc = Document(
            doc_id="test-doc-123",
            content="Test content",
            metadata={"source": "test.md", "type": "markdown"},
        )

        assert doc.metadata == {"source": "test.md", "type": "markdown"}

    def test_document_metadata_default_is_empty_dict(self) -> None:
        """测试 Document metadata 默认为空字典"""
        from backend.rag.models import Document

        doc = Document(doc_id="test-doc-123", content="Test content")

        assert doc.metadata == {}

    def test_document_with_empty_content(self) -> None:
        """测试 Document 可以有空内容"""
        from backend.rag.models import Document

        doc = Document(doc_id="test-doc-123", content="")

        assert doc.content == ""

    def test_document_with_special_characters_in_content(self) -> None:
        """测试 Document 内容包含特殊字符"""
        from backend.rag.models import Document

        special_content = "# 标题\n\n- 列表项\n\n```python\nprint('hello')\n```\n\nEmoji: 🎉"
        doc = Document(doc_id="test-doc-123", content=special_content)

        assert "标题" in doc.content
        assert "🎉" in doc.content

    def test_document_with_large_content(self) -> None:
        """测试 Document 可以有大内容"""
        from backend.rag.models import Document

        large_content = "x" * 100000  # 100KB 内容
        doc = Document(doc_id="test-doc-123", content=large_content)

        assert len(doc.content) == 100000


class TestNode:
    """Node 数据类测试"""

    def test_node_has_node_id(self) -> None:
        """测试 Node 包含 node_id 字段"""
        from backend.rag.models import Node

        node = Node(node_id="node-123", content="Test content")

        assert node.node_id == "node-123"

    def test_node_has_content(self) -> None:
        """测试 Node 包含 content 字段"""
        from backend.rag.models import Node

        node = Node(node_id="node-123", content="Test content")

        assert node.content == "Test content"

    def test_node_has_metadata(self) -> None:
        """测试 Node 包含 metadata 字段"""
        from backend.rag.models import Node

        node = Node(
            node_id="node-123",
            content="Test content",
            metadata={"heading": "Introduction", "level": 1},
        )

        assert node.metadata == {"heading": "Introduction", "level": 1}

    def test_node_has_relationships(self) -> None:
        """测试 Node 包含 relationships 字段"""
        from backend.rag.models import Node

        node = Node(
            node_id="node-123",
            content="Test content",
            relationships={"parent": "node-456", "children": ["node-789"]},
        )

        assert node.relationships == {"parent": "node-456", "children": ["node-789"]}

    def test_node_metadata_default_is_empty_dict(self) -> None:
        """测试 Node metadata 默认为空字典"""
        from backend.rag.models import Node

        node = Node(node_id="node-123", content="Test content")

        assert node.metadata == {}

    def test_node_relationships_default_is_empty_dict(self) -> None:
        """测试 Node relationships 默认为空字典"""
        from backend.rag.models import Node

        node = Node(node_id="node-123", content="Test content")

        assert node.relationships == {}


class TestSegment:
    """Segment 数据类测试"""

    def test_segment_has_content(self) -> None:
        """测试 Segment 包含 content 字段"""
        from backend.rag.models import Segment

        segment = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            score=0.95,
        )

        assert segment.content == "Test content"

    def test_segment_has_source(self) -> None:
        """测试 Segment 包含 source 字段"""
        from backend.rag.models import Segment

        segment = Segment(
            content="Test content",
            source="/path/to/test.md",
            file_type="long_term",
            score=0.95,
        )

        assert segment.source == "/path/to/test.md"

    def test_segment_has_file_type(self) -> None:
        """测试 Segment 包含 file_type 字段"""
        from backend.rag.models import Segment

        segment = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            score=0.95,
        )

        assert segment.file_type == "long_term"

    def test_segment_has_timestamp(self) -> None:
        """测试 Segment 包含 timestamp 字段"""
        from backend.rag.models import Segment

        segment = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            timestamp="2026-03-25T10:30:00",
            score=0.95,
        )

        assert segment.timestamp == "2026-03-25T10:30:00"

    def test_segment_has_score(self) -> None:
        """测试 Segment 包含 score 字段"""
        from backend.rag.models import Segment

        segment = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            score=0.95,
        )

        assert segment.score == 0.95

    def test_segment_timestamp_default_is_none(self) -> None:
        """测试 Segment timestamp 默认为 None"""
        from backend.rag.models import Segment

        segment = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            score=0.95,
        )

        assert segment.timestamp is None

    def test_segment_with_different_file_types(self) -> None:
        """测试 Segment 支持不同文件类型"""
        from backend.rag.models import Segment

        for file_type in ["long_term", "near", "core"]:
            segment = Segment(
                content="Test content",
                source="test.md",
                file_type=file_type,
                score=0.95,
            )
            assert segment.file_type == file_type

    def test_segment_with_score_range(self) -> None:
        """测试 Segment score 在有效范围内"""
        from backend.rag.models import Segment

        # 最小值
        segment_min = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            score=0.0,
        )
        assert segment_min.score == 0.0

        # 最大值
        segment_max = Segment(
            content="Test content",
            source="test.md",
            file_type="long_term",
            score=1.0,
        )
        assert segment_max.score == 1.0
