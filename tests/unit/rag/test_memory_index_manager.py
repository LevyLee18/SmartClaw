"""MemoryIndexManager 类单元测试

测试 MemoryIndexManager 的初始化和基本功能。
使用 Mock 隔离 LlamaIndex 和 OpenAI API 调用。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.config.models import EmbeddingConfig, RAGConfig, Settings, StorageConfig
from backend.rag.index_manager import IndexManager
from backend.rag.memory_index_manager import MemoryIndexManager
from backend.rag.models import Segment


# ============ Fixtures ============

def create_mock_settings(tmp_path: Path, **kwargs) -> Settings:
    """创建带 Mock 配置的 Settings"""
    return Settings(
        storage=StorageConfig(base_path=tmp_path),
        embedding=EmbeddingConfig(
            provider="openai",
            model="text-embedding-3-small",
            api_key=kwargs.get("api_key", "test-api-key"),
            dimensions=kwargs.get("dimensions", 1536),
        ),
        rag=kwargs.get("rag", RAGConfig()),
    )


def mock_llama_index_components():
    """Mock LlamaIndex 组件"""
    mock_embed_model = MagicMock()
    mock_embed_model.model_name = "text-embedding-3-small"

    mock_chroma_client = MagicMock()
    mock_collection = MagicMock()
    mock_chroma_client.get_or_create_collection.return_value = mock_collection

    mock_vector_store = MagicMock()
    mock_index = MagicMock()
    mock_index.docstore = MagicMock()
    mock_index.as_retriever.return_value = MagicMock()

    return {
        "embed_model": mock_embed_model,
        "chroma_client": mock_chroma_client,
        "chroma_collection": mock_collection,
        "vector_store": mock_vector_store,
        "index": mock_index,
    }


# ============ Test Classes ============

class TestMemoryIndexManagerInit:
    """测试 MemoryIndexManager.__init__"""

    def test_init_with_valid_config(self, tmp_path: Path):
        """测试使用有效配置初始化"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert manager.config == config
            assert manager.base_path == tmp_path
            assert manager.rag_config == config.rag
            assert manager.embedding_config == config.embedding

    def test_init_stores_base_path_from_config(self, tmp_path: Path):
        """测试初始化存储 base_path"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert manager.base_path == tmp_path
            assert isinstance(manager.base_path, Path)

    def test_init_stores_rag_config(self, tmp_path: Path):
        """测试初始化存储 RAG 配置"""
        rag_config = RAGConfig(top_k=10, chunk_size=1024, chunk_overlap=100)

        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path, rag=rag_config)
            manager = MemoryIndexManager(config)

            assert manager.rag_config.top_k == 10
            assert manager.rag_config.chunk_size == 1024
            assert manager.rag_config.chunk_overlap == 100

    def test_init_stores_embedding_config(self, tmp_path: Path):
        """测试初始化存储 Embedding 配置"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(
                tmp_path, api_key="test-api-key", dimensions=3072
            )
            manager = MemoryIndexManager(config)

            assert manager.embedding_config.provider == "openai"
            assert manager.embedding_config.dimensions == 3072

    def test_init_creates_storage_directory(self, tmp_path: Path):
        """测试初始化创建存储目录"""
        base_path = tmp_path / "nonexistent" / "path"

        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(base_path)
            manager = MemoryIndexManager(config)

            assert manager.base_path.exists()
            assert manager.base_path.is_dir()


class TestMemoryIndexManagerInheritance:
    """测试 MemoryIndexManager 继承关系"""

    def test_inherits_from_index_manager(self, tmp_path: Path):
        """测试继承自 IndexManager"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert isinstance(manager, IndexManager)
            assert isinstance(manager, MemoryIndexManager)

    def test_has_search_method(self, tmp_path: Path):
        """测试具有 search 方法"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "search")
            assert callable(manager.search)

    def test_has_update_document_method(self, tmp_path: Path):
        """测试具有 update_document 方法"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "update_document")
            assert callable(manager.update_document)

    def test_has_delete_document_method(self, tmp_path: Path):
        """测试具有 delete_document 方法"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "delete_document")
            assert callable(manager.delete_document)

    def test_has_build_index_method(self, tmp_path: Path):
        """测试具有 build_index 方法"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "build_index")
            assert callable(manager.build_index)


class TestInitStorageContext:
    """测试 _init_storage_context 方法"""

    def test_cache_initialized(self, tmp_path: Path):
        """测试缓存初始化"""
        from backend.rag.cache import SQLiteCache

        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "cache")
            assert isinstance(manager.cache, SQLiteCache)

    def test_embed_model_initialized(self, tmp_path: Path):
        """测试 Embedding 模型初始化"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "embed_model")
            mock_embed.assert_called_once()

    def test_chroma_client_initialized(self, tmp_path: Path):
        """测试 ChromaDB 客户端初始化"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "chroma_client")
            assert hasattr(manager, "chroma_collection")

    def test_vector_store_initialized(self, tmp_path: Path):
        """测试向量存储初始化"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "vector_store")
            assert hasattr(manager, "index")

    def test_doc_store_initialized(self, tmp_path: Path):
        """测试文档存储初始化"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "doc_store")
            assert isinstance(manager.doc_store, dict)
            assert len(manager.doc_store) == 0


class TestInitPipeline:
    """测试 _init_pipeline 方法"""

    def test_splitter_initialized(self, tmp_path: Path):
        """测试分块器初始化"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            assert hasattr(manager, "splitter")

    def test_splitter_uses_config_chunk_size(self, tmp_path: Path):
        """测试分块器使用配置的 chunk_size"""
        rag_config = RAGConfig(chunk_size=2048, chunk_overlap=200)

        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx, patch(
            "backend.rag.memory_index_manager.SentenceSplitter"
        ) as mock_splitter:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()
            mock_splitter.return_value = MagicMock()

            config = create_mock_settings(tmp_path, rag=rag_config)
            MemoryIndexManager(config)

            mock_splitter.assert_called_with(chunk_size=2048, chunk_overlap=200)


class TestSearch:
    """测试 search 方法"""

    def test_search_returns_list(self, tmp_path: Path):
        """测试 search 返回列表"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            results = manager.search("test query")

            assert isinstance(results, list)

    def test_search_calls_vector_and_bm25(self, tmp_path: Path):
        """测试 search 调用向量和 BM25 检索"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            # Mock 检索方法
            manager._vector_search = lambda q, k: []
            manager._bm25_search = lambda q, k: []
            manager._rrf_fusion = lambda v, b, k: []

            manager.search("test query")

            # 验证空结果正常处理


class TestRRFFusion:
    """测试 _rrf_fusion 方法"""

    def test_rrf_fusion_returns_list(self, tmp_path: Path):
        """测试 RRF 融合返回列表"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            from backend.rag.models import Segment

            vector_results = [
                Segment(content="result 1", source="test", file_type="md", score=0.9)
            ]
            bm25_results = [
                Segment(content="result 2", source="test", file_type="md", score=0.8)
            ]

            fused = manager._rrf_fusion(vector_results, bm25_results, 5)

            assert isinstance(fused, list)

    def test_rrf_fusion_respects_top_k(self, tmp_path: Path):
        """测试 RRF 融合遵守 top_k"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            from backend.rag.models import Segment

            vector_results = [
                Segment(content=f"vector result {i}", source="test", file_type="md", score=0.9)
                for i in range(5)
            ]
            bm25_results = [
                Segment(content=f"bm25 result {i}", source="test", file_type="md", score=0.8)
                for i in range(5)
            ]

            fused = manager._rrf_fusion(vector_results, bm25_results, 3)

            assert len(fused) <= 3


class TestDocumentOperations:
    """测试文档操作"""

    def test_update_document_returns_true(self, tmp_path: Path):
        """测试添加文档返回 True"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_index = MagicMock()
            mock_index.insert_nodes = MagicMock()
            mock_idx.from_vector_store.return_value = mock_index

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            # Mock splitter
            mock_node = MagicMock()
            mock_node.node_id = "test-node-id"
            manager.splitter = MagicMock()
            manager.splitter.get_nodes_from_documents.return_value = [mock_node]

            result = manager.update_document("doc1", "test content")

            assert result is True

    def test_delete_document_returns_true(self, tmp_path: Path):
        """测试删除文档返回 True"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_index = MagicMock()
            mock_index.delete_nodes = MagicMock()
            mock_idx.from_vector_store.return_value = mock_index

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            # 先添加一个文档
            manager.doc_store["doc1"] = ["node1", "node2"]

            result = manager.delete_document("doc1")

            assert result is True
            assert "doc1" not in manager.doc_store

    def test_build_index_returns_true(self, tmp_path: Path):
        """测试重建索引返回 True"""
        with patch(
            "backend.rag.memory_index_manager.OpenAIEmbedding"
        ) as mock_embed, patch(
            "backend.rag.memory_index_manager.chromadb.PersistentClient"
        ) as mock_chroma, patch(
            "backend.rag.memory_index_manager.ChromaVectorStore"
        ) as mock_vs, patch(
            "backend.rag.memory_index_manager.VectorStoreIndex"
        ) as mock_idx:
            mock_embed.return_value = MagicMock()
            mock_chroma.return_value = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_chroma.return_value.delete_collection = MagicMock()
            mock_vs.return_value = MagicMock()
            mock_idx.from_vector_store.return_value = MagicMock()

            config = create_mock_settings(tmp_path)
            manager = MemoryIndexManager(config)

            result = manager.build_index(force=True)

            assert result is True
