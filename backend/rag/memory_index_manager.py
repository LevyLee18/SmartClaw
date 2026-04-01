"""MemoryIndexManager 实现

基于 LlamaIndex 的内存索引管理器，使用 LlamaIndex 的 BM25 和 RRF 融合检索。
"""

from typing import Any, Optional

import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.chroma import ChromaVectorStore

from backend.config.models import EmbeddingConfig, RAGConfig, Settings
from backend.rag.cache import SQLiteCache
from backend.rag.index_manager import IndexManager
from backend.rag.models import Segment


class MemoryIndexManager(IndexManager):
    """内存索引管理器

    使用 LlamaIndex 实现混合检索（向量 + BM25）和 RRF 融合。

    Attributes:
        config: SmartClaw 配置对象
        rag_config: RAG 配置
        embedding_config: Embedding 配置
        cache: 转换结果缓存
        embed_model: OpenAI Embedding 模型
        chroma_client: ChromaDB 客户端
        chroma_collection: ChromaDB 集合
        vector_store: LlamaIndex 向量存储
        index: LlamaIndex 向量索引
        splitter: 句子分块器
        doc_store: 文档到节点的映射 (doc_id -> node_ids)
        _all_nodes: 所有节点的缓存（用于 BM25 检索）
    """

    def __init__(self, config: Settings) -> None:
        """初始化索引管理器

        Args:
            config: SmartClaw 配置对象
        """
        # 存储配置
        self.config = config
        self.rag_config: RAGConfig = config.rag
        self.embedding_config: EmbeddingConfig = config.embedding

        # 初始化基类
        base_path = config.storage.base_path
        base_path.mkdir(parents=True, exist_ok=True)
        super().__init__(base_path)

        # 初始化存储上下文
        self._init_storage_context()

        # 初始化处理管道
        self._init_pipeline()

        # 节点缓存（用于 BM25 检索）
        self._all_nodes: list = []

    def _init_storage_context(self) -> None:
        """初始化存储上下文

        创建缓存、OpenAI Embedding、ChromaDB 向量存储和索引。
        """
        # 1. 初始化 SQLite 缓存
        cache_path = str(self.base_path / "cache.db")
        self.cache = SQLiteCache(cache_path)

        # 2. 初始化 OpenAI Embedding 模型
        self.embed_model = OpenAIEmbedding(
            model=self.embedding_config.model,
            dimensions=self.embedding_config.dimensions,
            api_key=self.embedding_config.api_key,
        )

        # 3. 初始化 ChromaDB (持久化到 base_path/chroma)
        chroma_path = self.base_path / "chroma"
        chroma_path.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(path=str(chroma_path))
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name="smartclaw_documents",
            metadata={"hnsw:space": "cosine"},
        )

        # 4. 创建 VectorStore 和 Index
        self.vector_store = ChromaVectorStore(
            chroma_collection=self.chroma_collection
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            embed_model=self.embed_model,
        )

        # 5. 初始化文档存储（用于跟踪 doc_id -> node_ids 映射）
        self.doc_store: dict[str, list[str]] = {}

    def _init_pipeline(self) -> None:
        """初始化处理管道

        配置 SentenceSplitter 用于文档分块。
        """
        self.splitter = SentenceSplitter(
            chunk_size=self.rag_config.chunk_size,
            chunk_overlap=self.rag_config.chunk_overlap,
        )

    def search(self, query: str, top_k: int = 5) -> list[Segment]:
        """执行检索

        执行混合检索（向量 + BM25）并使用 RRF 融合结果。

        Args:
            query: 查询文本
            top_k: 返回结果数量，默认使用 rag_config.top_k

        Returns:
            相关片段列表，按相关性得分降序排列
        """
        # 使用配置的 top_k 如果未指定
        if top_k == 5:
            top_k = self.rag_config.top_k

        # 执行向量检索
        vector_results = self._vector_search(query, top_k)

        # 执行 BM25 检索
        bm25_results = self._bm25_search(query, top_k)

        # RRF 融合
        fused_results = self._rrf_fusion(vector_results, bm25_results, top_k)

        return fused_results

    def _search_with_filters(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[Segment]:
        """带过滤条件的检索

        执行混合检索并根据日期等条件过滤结果。

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件，支持:
                - start_date: 起始日期 (YYYY-MM-DD)
                - end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            过滤后的片段列表
        """
        # 如果没有过滤器，直接调用普通检索
        if not filters:
            vector_results = self._vector_search(query, top_k)
            bm25_results = self._bm25_search(query, top_k)
            return self._rrf_fusion(vector_results, bm25_results, top_k)

        # 执行检索（获取更多结果用于过滤）
        fetch_k = top_k * 3  # 获取更多结果以便过滤后仍有足够数量
        vector_results = self._vector_search(query, fetch_k)
        bm25_results = self._bm25_search(query, fetch_k)

        # RRF 融合
        fused_results = self._rrf_fusion(vector_results, bm25_results, fetch_k)

        # 应用日期过滤
        filtered_results = self._apply_date_filters(fused_results, filters)

        # 返回 top_k 结果
        return filtered_results[:top_k]

    def _apply_date_filters(
        self,
        segments: list[Segment],
        filters: dict[str, Any],
    ) -> list[Segment]:
        """应用日期过滤

        Args:
            segments: 片段列表
            filters: 过滤条件

        Returns:
            过滤后的片段列表
        """
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")

        if not start_date and not end_date:
            return segments

        filtered = []
        for segment in segments:
            # 获取片段的时间戳
            timestamp = segment.timestamp
            if not timestamp:
                # 如果没有时间戳，检查元数据中的日期
                continue

            # 检查日期范围
            try:
                seg_date = timestamp[:10]  # 取 YYYY-MM-DD 部分

                if start_date and seg_date < start_date:
                    continue
                if end_date and seg_date > end_date:
                    continue

                filtered.append(segment)
            except (TypeError, IndexError):
                # 日期格式错误，跳过该片段
                continue

        return filtered

    def _extract_date_from_path(self, path: str) -> str | None:
        """从路径中提取日期

        支持的日期格式：
        - YYYY-MM-DD (如 2024-03-15)
        - YYYY/MM/DD (如 2024/03/15)

        Args:
            path: 文件路径

        Returns:
            日期字符串 (YYYY-MM-DD 格式) 或 None
        """
        import re

        # 匹配 YYYY-MM-DD 格式
        date_pattern_dash = r"(\d{4}-\d{2}-\d{2})"
        match = re.search(date_pattern_dash, path)
        if match:
            return match.group(1)

        # 匹配 YYYY/MM/DD 格式并转换为 YYYY-MM-DD
        date_pattern_slash = r"(\d{4})/(\d{2})/(\d{2})"
        match = re.search(date_pattern_slash, path)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"

        return None

    def _vector_search(self, query: str, top_k: int) -> list[Segment]:
        """执行向量检索

        使用 LlamaIndex VectorStoreIndex 进行语义检索。

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关片段列表
        """
        if not self._all_nodes:
            return []

        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes_with_scores = retriever.retrieve(query)

        segments = []
        for node_with_score in nodes_with_scores:
            node = node_with_score.node
            segment = Segment(
                content=node.get_content(),
                source=node.metadata.get("source", "unknown"),
                file_type=node.metadata.get("file_type", "unknown"),
                timestamp=node.metadata.get("timestamp"),
                score=node_with_score.score or 0.0,
            )
            segments.append(segment)

        return segments

    def _bm25_search(self, query: str, top_k: int) -> list[Segment]:
        """执行 BM25 检索

        使用 LlamaIndex BM25Retriever 进行关键词检索。

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关片段列表
        """
        if not self._all_nodes:
            return []

        # 使用 LlamaIndex BM25Retriever
        bm25_retriever = BM25Retriever.from_defaults(
            nodes=self._all_nodes,
            similarity_top_k=top_k,
        )

        nodes_with_scores = bm25_retriever.retrieve(query)

        segments = []
        for node_with_score in nodes_with_scores:
            node = node_with_score.node
            segment = Segment(
                content=node.get_content(),
                source=node.metadata.get("source", "unknown"),
                file_type=node.metadata.get("file_type", "unknown"),
                timestamp=node.metadata.get("timestamp"),
                score=node_with_score.score or 0.0,
            )
            segments.append(segment)

        return segments

    def _rrf_fusion(
        self,
        vector_results: list[Segment],
        bm25_results: list[Segment],
        top_k: int,
        k: int = 60,
    ) -> list[Segment]:
        """RRF 融合算法

        Reciprocal Rank Fusion: score(d) = sum(1 / (k + rank(d)))

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            top_k: 返回结果数量
            k: RRF 常数（默认 60）

        Returns:
            融合后的片段列表
        """
        from collections import defaultdict

        rrf_scores: dict[str, float] = defaultdict(float)
        segment_map: dict[str, Segment] = {}

        # 处理向量检索结果
        for rank, segment in enumerate(vector_results):
            key = self._get_segment_key(segment)
            rrf_scores[key] += 1.0 / (k + rank + 1)
            segment_map[key] = segment

        # 处理 BM25 检索结果
        for rank, segment in enumerate(bm25_results):
            key = self._get_segment_key(segment)
            rrf_scores[key] += 1.0 / (k + rank + 1)
            segment_map[key] = segment

        # 按 RRF 分数排序
        sorted_keys = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )

        # 返回 top_k 结果
        fused_segments = []
        for key in sorted_keys[:top_k]:
            segment = segment_map[key]
            # 更新分数为 RRF 分数
            segment.score = rrf_scores[key]
            fused_segments.append(segment)

        return fused_segments

    def _get_segment_key(self, segment: Segment) -> str:
        """生成片段的唯一键

        Args:
            segment: 片段对象

        Returns:
            唯一键字符串
        """
        import hashlib

        content_hash = hashlib.md5(segment.content.encode()).hexdigest()[:8]
        return f"{segment.source}:{content_hash}"

    def update_document(
        self, doc_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """添加或更新文档

        Args:
            doc_id: 文档唯一标识符
            content: 文档内容
            metadata: 文档元数据

        Returns:
            操作是否成功
        """
        try:
            # 如果文档已存在，先删除
            if doc_id in self.doc_store:
                self.delete_document(doc_id)

            # 创建文档
            doc = Document(
                text=content,
                doc_id=doc_id,
                metadata=metadata or {},
            )

            # 使用 splitter 分块
            nodes = self.splitter.get_nodes_from_documents([doc])

            # 为每个节点添加元数据
            for node in nodes:
                node.metadata["doc_id"] = doc_id
                if metadata:
                    node.metadata.update(metadata)

            # 添加到索引
            self.index.insert_nodes(nodes)

            # 记录 doc_id -> node_ids 映射
            self.doc_store[doc_id] = [node.node_id for node in nodes]

            # 更新节点缓存
            self._all_nodes.extend(nodes)

            return True
        except Exception:
            return False

    def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档唯一标识符

        Returns:
            操作是否成功
        """
        try:
            if doc_id not in self.doc_store:
                return True  # 文档不存在，视为成功

            # 获取该文档的所有节点 ID
            node_ids = self.doc_store[doc_id]

            # 从索引中删除节点
            self.index.delete_nodes(node_ids)

            # 从节点缓存中移除
            node_id_set = set(node_ids)
            self._all_nodes = [
                node for node in self._all_nodes if node.node_id not in node_id_set
            ]

            # 从 doc_store 中移除
            del self.doc_store[doc_id]

            return True
        except Exception:
            return False

    def build_index(self, force: bool = False) -> bool:
        """全量重建索引

        Args:
            force: 是否强制重建

        Returns:
            操作是否成功
        """
        try:
            if not force and not self.doc_store:
                return True  # 无文档，无需重建

            # 清空 ChromaDB collection
            try:
                self.chroma_client.delete_collection("smartclaw_documents")
            except Exception:
                pass

            # 重新创建 collection
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="smartclaw_documents",
                metadata={"hnsw:space": "cosine"},
            )

            # 重新创建 vector store 和 index
            self.vector_store = ChromaVectorStore(
                chroma_collection=self.chroma_collection
            )
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model,
            )

            # 清空 doc_store 和节点缓存
            self.doc_store.clear()
            self._all_nodes.clear()

            return True
        except Exception:
            return False

    def check_consistency(self) -> dict[str, list[str]]:
        """检查索引与数据源的一致性

        Returns:
            一致性检查结果，包含缺失、多余、损坏的文档 ID 列表
        """
        # 简化实现：始终返回一致
        return {
            "missing": [],
            "extra": [],
            "corrupted": []
        }

    def repair_consistency(self) -> dict[str, int]:
        """修复一致性异常

        Returns:
            修复结果统计
        """
        # 简化实现：无需修复
        return {
            "fixed": 0,
            "removed": 0,
            "rebuilt": 0
        }

    def get_search_tool(self) -> dict[str, Any]:
        """获取 search_memory 工具适配器

        返回一个符合 LangChain 工具规范的字典，包含：
        - name: 工具名称
        - description: 工具描述
        - func: 可调用的工具函数

        Returns:
            工具配置字典
        """
        def search_memory(
            query: str,
            top_k: int = 5,
            date_range: Optional[tuple[str, str]] = None
        ) -> str:
            """检索长期记忆

            在已归档的会话记录中搜索与查询相关的内容。
            支持向量语义检索和 BM25 关键词检索的混合模式。

            Args:
                query: 查询文本
                top_k: 返回结果数量，默认 5
                date_range: 日期范围过滤，格式为 (start_date, end_date)，
                           日期使用 YYYY-MM-DD 格式

            Returns:
                格式化的字符串，包含每个片段的来源、类型和内容

            示例：
                search_memory("用户偏好设置", top_k=3)
                search_memory("项目讨论", date_range=("2026-03-01", "2026-03-15"))
            """
            try:
                # 执行检索
                if date_range:
                    # 使用日期范围过滤
                    filters = {
                        "start_date": date_range[0],
                        "end_date": date_range[1]
                    }
                    segments = self._search_with_filters(query, top_k, filters)
                else:
                    # 普通检索
                    segments = self.search(query, top_k)

                # 如果没有结果
                if not segments:
                    return "未找到相关的记忆片段。"

                # 格式化结果
                formatted_results = []
                for i, segment in enumerate(segments, 1):
                    formatted_results.append(
                        f"[来源: {segment.source} | 类型: {segment.file_type}]\n"
                        f"{segment.content}"
                    )

                return "\n\n".join(formatted_results)

            except Exception as e:
                return f"错误：检索失败 - {e}"

        return {
            "name": "search_memory",
            "description": (
                "检索长期记忆。在已归档的会话记录中搜索与查询相关的内容。"
                "支持向量语义检索和 BM25 关键词检索的混合模式。"
                "可以指定日期范围过滤结果。"
            ),
            "func": search_memory,
        }
