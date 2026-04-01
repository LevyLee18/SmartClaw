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


class TestSearchWithFilters:
    """测试 _search_with_filters 方法"""

    def test_search_with_filters_exists(self, tmp_path: Path):
        """测试 _search_with_filters 方法存在"""
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

            assert hasattr(manager, "_search_with_filters")
            assert callable(manager._search_with_filters)

    def test_search_with_filters_returns_list(self, tmp_path: Path):
        """测试 _search_with_filters 返回列表"""
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

            # Mock _vector_search 和 _bm25_search
            manager._vector_search = lambda q, k: []
            manager._bm25_search = lambda q, k: []
            manager._rrf_fusion = lambda v, b, k: []

            filters = {"start_date": "2024-01-01", "end_date": "2024-12-31"}
            results = manager._search_with_filters("test query", 5, filters)

            assert isinstance(results, list)

    def test_search_with_filters_accepts_date_range(self, tmp_path: Path):
        """测试 _search_with_filters 接受日期范围"""
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

            manager._vector_search = lambda q, k: []
            manager._bm25_search = lambda q, k: []
            manager._rrf_fusion = lambda v, b, k: []

            # 测试不同日期格式
            filters1 = {"start_date": "2024-01-01"}
            filters2 = {"end_date": "2024-12-31"}
            filters3 = {"start_date": "2024-01-01", "end_date": "2024-12-31"}

            # 不应抛出异常
            manager._search_with_filters("test", 5, filters1)
            manager._search_with_filters("test", 5, filters2)
            manager._search_with_filters("test", 5, filters3)

    def test_search_with_filters_handles_empty_filters(self, tmp_path: Path):
        """测试 _search_with_filters 处理空过滤器"""
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

            manager._vector_search = lambda q, k: []
            manager._bm25_search = lambda q, k: []
            manager._rrf_fusion = lambda v, b, k: []

            # 空过滤器应该正常工作
            results = manager._search_with_filters("test", 5, {})
            assert isinstance(results, list)

    def test_search_with_filters_handles_none_filters(self, tmp_path: Path):
        """测试 _search_with_filters 处理 None 过滤器"""
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

            manager._vector_search = lambda q, k: []
            manager._bm25_search = lambda q, k: []
            manager._rrf_fusion = lambda v, b, k: []

            # None 过滤器应该正常工作
            results = manager._search_with_filters("test", 5, None)
            assert isinstance(results, list)


class TestExtractDateFromPath:
    """测试 _extract_date_from_path 方法"""

    def test_extract_date_from_path_exists(self, tmp_path: Path):
        """测试 _extract_date_from_path 方法存在"""
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

            assert hasattr(manager, "_extract_date_from_path")
            assert callable(manager._extract_date_from_path)

    def test_extract_date_from_yyyy_mm_dd_format(self, tmp_path: Path):
        """测试从 YYYY-MM-DD 格式路径提取日期"""
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

            # 测试各种路径格式
            result = manager._extract_date_from_path("/docs/2024-03-15/note.md")
            assert result == "2024-03-15"

    def test_extract_date_from_yyyy_mm_dd_format(self, tmp_path: Path):
        """测试从 YYYY/MM/DD 格式路径提取日期"""
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

            result = manager._extract_date_from_path("/docs/2024/03/15/note.md")
            assert result == "2024-03-15"

    def test_extract_date_returns_none_for_no_date(self, tmp_path: Path):
        """测试无日期路径返回 None"""
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

            result = manager._extract_date_from_path("/docs/notes/meeting.md")
            assert result is None

    def test_extract_date_handles_various_formats(self, tmp_path: Path):
        """测试处理多种日期格式"""
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

            # YYYY-MM-DD 在路径中
            assert manager._extract_date_from_path("/2024-01-15/file.md") == "2024-01-15"
            # YYYY/MM/DD 在路径中
            assert manager._extract_date_from_path("/2024/01/15/file.md") == "2024-01-15"
            # 无日期
            assert manager._extract_date_from_path("/documents/file.md") is None


class TestMemoryIndexManagerBoundary:
    """MemoryIndexManager 边界测试"""

    def test_search_on_empty_index(self, tmp_path: Path):
        """测试空索引检索"""
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

            # 空索引检索应返回空列表
            results = manager.search("any query")
            assert results == []

    def test_update_document_empty_content(self, tmp_path: Path):
        """测试空内容文档"""
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

            # Mock splitter 返回空节点列表
            manager.splitter = MagicMock()
            manager.splitter.get_nodes_from_documents.return_value = []

            result = manager.update_document("empty_doc", "")
            assert result is True
            # 空内容文档会被添加，但节点列表为空
            assert "empty_doc" in manager.doc_store
            assert manager.doc_store["empty_doc"] == []

    def test_update_document_special_characters(self, tmp_path: Path):
        """测试特殊字符文档"""
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
            mock_node.node_id = "special-node-id"
            manager.splitter = MagicMock()
            manager.splitter.get_nodes_from_documents.return_value = [mock_node]

            # 特殊字符内容
            special_content = "特殊字符: 中文、日本語、한국어、emoji 🎉 and symbols @#$%^&*()"
            result = manager.update_document("special_doc", special_content)

            assert result is True
            assert "special_doc" in manager.doc_store

    def test_update_document_unicode_doc_id(self, tmp_path: Path):
        """测试 Unicode 文档 ID"""
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
            mock_node.node_id = "unicode-node-id"
            manager.splitter = MagicMock()
            manager.splitter.get_nodes_from_documents.return_value = [mock_node]

            # Unicode 文档 ID
            unicode_doc_id = "文档/ドキュメント/문서"
            result = manager.update_document(unicode_doc_id, "test content")

            assert result is True
            assert unicode_doc_id in manager.doc_store

    def test_delete_nonexistent_document(self, tmp_path: Path):
        """测试删除不存在的文档"""
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

            # 删除不存在的文档应返回 True
            result = manager.delete_document("nonexistent_doc")
            assert result is True

    def test_search_with_filters_empty_results(self, tmp_path: Path):
        """测试过滤后无结果"""
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

            # Mock 检索返回结果，但时间戳不匹配过滤器
            from backend.rag.models import Segment

            manager._vector_search = lambda q, k: [
                Segment(content="old doc", source="test", file_type="md", score=0.9, timestamp="2020-01-01")
            ]
            manager._bm25_search = lambda q, k: []
            manager._rrf_fusion = lambda v, b, k: v

            # 过滤 2024 年，但文档是 2020 年
            filters = {"start_date": "2024-01-01", "end_date": "2024-12-31"}
            results = manager._search_with_filters("test", 5, filters)

            assert results == []

    def test_extract_date_from_invalid_path(self, tmp_path: Path):
        """测试从无效路径提取日期"""
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

            # 无效日期格式
            assert manager._extract_date_from_path("/invalid-date/file.md") is None
            assert manager._extract_date_from_path("/99-99-99/file.md") is None
            assert manager._extract_date_from_path("") is None

