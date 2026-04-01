"""测试 SQLiteCache 类

测试要点：
1. __init__(cache_path) - 初始化 SQLite 连接
2. get(key) / set(key, value) - 缓存读写
3. _generate_cache_key() - SHA256 键生成
"""

from pathlib import Path

import pytest


class TestSQLiteCacheInit:
    """SQLiteCache.__init__() 测试"""

    def test_init_creates_database_file(self, temp_dir: Path) -> None:
        """测试初始化创建数据库文件"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        assert cache_path.exists()

    def test_init_sets_cache_path(self, temp_dir: Path) -> None:
        """测试初始化设置 cache_path"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        assert cache.cache_path == str(cache_path)

    def test_init_creates_cache_table(self, temp_dir: Path) -> None:
        """测试初始化创建缓存表"""
        import sqlite3

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        SQLiteCache(str(cache_path))

        # 检查表是否存在
        conn = sqlite3.connect(str(cache_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cache'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_init_creates_index(self, temp_dir: Path) -> None:
        """测试初始化创建索引"""
        import sqlite3

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        SQLiteCache(str(cache_path))

        # 检查索引是否存在
        conn = sqlite3.connect(str(cache_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_accessed_at'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None


class TestSQLiteCacheGetSet:
    """SQLiteCache.get() / set() 测试"""

    def test_set_stores_value(self, temp_dir: Path) -> None:
        """测试 set 存储值"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        cache.set("test-key", "test-value")

        # 验证值已存储
        result = cache.get("test-key")
        assert result == "test-value"

    def test_get_returns_none_for_nonexistent_key(self, temp_dir: Path) -> None:
        """测试 get 不存在的 key 返回 None"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        result = cache.get("nonexistent-key")

        assert result is None

    def test_set_overwrites_existing_value(self, temp_dir: Path) -> None:
        """测试 set 覆盖已存在的值"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        cache.set("test-key", "first-value")
        cache.set("test-key", "second-value")

        result = cache.get("test-key")
        assert result == "second-value"

    def test_set_stores_complex_object(self, temp_dir: Path) -> None:
        """测试 set 存储复杂对象"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        complex_value = {
            "text": "Hello",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"source": "test.md"},
        }
        cache.set("complex-key", complex_value)

        result = cache.get("complex-key")
        assert result == complex_value

    def test_set_stores_list(self, temp_dir: Path) -> None:
        """测试 set 存储列表"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        list_value = ["item1", "item2", "item3"]
        cache.set("list-key", list_value)

        result = cache.get("list-key")
        assert result == list_value

    def test_set_stores_bytes(self, temp_dir: Path) -> None:
        """测试 set 存储字节"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        bytes_value = b"\x00\x01\x02\x03"
        cache.set("bytes-key", bytes_value)

        result = cache.get("bytes-key")
        assert result == bytes_value


class TestSQLiteCacheGenerateCacheKey:
    """SQLiteCache._generate_cache_key() 测试"""

    def test_generate_cache_key_returns_string(self, temp_dir: Path) -> None:
        """测试生成缓存键返回字符串"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        key = cache._generate_cache_key("test content")

        assert isinstance(key, str)

    def test_generate_cache_key_is_deterministic(self, temp_dir: Path) -> None:
        """测试相同输入生成相同键"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        key1 = cache._generate_cache_key("test content")
        key2 = cache._generate_cache_key("test content")

        assert key1 == key2

    def test_generate_cache_key_different_for_different_input(
        self, temp_dir: Path
    ) -> None:
        """测试不同输入生成不同键"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        key1 = cache._generate_cache_key("content 1")
        key2 = cache._generate_cache_key("content 2")

        assert key1 != key2

    def test_generate_cache_key_format(self, temp_dir: Path) -> None:
        """测试缓存键格式为 SHA256 十六进制"""
        import hashlib

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        key = cache._generate_cache_key("test content")

        # SHA256 生成 64 字符的十六进制字符串
        assert len(key) == 64
        # 验证是有效的十六进制字符串
        try:
            int(key, 16)
        except ValueError:
            pytest.fail("Cache key is not a valid hexadecimal string")


class TestSQLiteCacheBoundary:
    """SQLiteCache 边界测试"""

    def test_set_empty_string(self, temp_dir: Path) -> None:
        """测试存储空字符串"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        cache.set("empty-key", "")
        result = cache.get("empty-key")

        assert result == ""

    def test_set_none_value(self, temp_dir: Path) -> None:
        """测试存储 None 值"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        cache.set("none-key", None)
        result = cache.get("none-key")

        assert result is None

    def test_set_unicode_content(self, temp_dir: Path) -> None:
        """测试存储 Unicode 内容"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        unicode_value = "中文测试 🎉 日本語"
        cache.set("unicode-key", unicode_value)

        result = cache.get("unicode-key")
        assert result == unicode_value

    def test_set_large_value(self, temp_dir: Path) -> None:
        """测试存储大值"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        large_value = "x" * 100000  # 100KB
        cache.set("large-key", large_value)

        result = cache.get("large-key")
        assert result == large_value

    def test_multiple_keys(self, temp_dir: Path) -> None:
        """测试多个键值对"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 存储多个键值对
        for i in range(10):
            cache.set(f"key-{i}", f"value-{i}")

        # 验证所有值
        for i in range(10):
            result = cache.get(f"key-{i}")
            assert result == f"value-{i}"


class TestSQLiteCacheConcurrent:
    """SQLiteCache 并发访问测试"""

    def test_concurrent_reads(self, temp_dir: Path) -> None:
        """测试并发读取"""
        import threading

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 预先存储数据
        cache.set("concurrent-key", "concurrent-value")

        errors: list[Exception] = []
        results: list[str | None] = []

        def read_cache() -> None:
            try:
                result = cache.get("concurrent-key")
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建多个读取线程
        threads = [threading.Thread(target=read_cache) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证无错误且结果正确
        assert len(errors) == 0
        assert len(results) == 10
        assert all(r == "concurrent-value" for r in results)

    def test_concurrent_writes(self, temp_dir: Path) -> None:
        """测试并发写入"""
        import threading

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        errors: list[Exception] = []

        def write_cache(i: int) -> None:
            try:
                cache.set(f"write-key-{i}", f"write-value-{i}")
            except Exception as e:
                errors.append(e)

        # 创建多个写入线程
        threads = [threading.Thread(target=write_cache, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证无错误且数据完整
        assert len(errors) == 0
        for i in range(10):
            result = cache.get(f"write-key-{i}")
            assert result == f"write-value-{i}"

    def test_concurrent_read_write(self, temp_dir: Path) -> None:
        """测试并发读写"""
        import threading

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 预先存储数据
        for i in range(5):
            cache.set(f"rw-key-{i}", f"rw-value-{i}")

        errors: list[Exception] = []

        def read_cache(i: int) -> None:
            try:
                cache.get(f"rw-key-{i % 5}")
            except Exception as e:
                errors.append(e)

        def write_cache(i: int) -> None:
            try:
                cache.set(f"rw-key-{i % 5}", f"rw-value-{i}")
            except Exception as e:
                errors.append(e)

        # 创建读写线程
        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=read_cache, args=(i,)))
            threads.append(threading.Thread(target=write_cache, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证无错误
        assert len(errors) == 0


class TestSQLiteCacheLargeData:
    """SQLiteCache 大数据测试"""

    def test_very_large_value(self, temp_dir: Path) -> None:
        """测试存储非常大的值（10MB）"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 10MB 数据
        large_value = "x" * (10 * 1024 * 1024)
        cache.set("very-large-key", large_value)

        result = cache.get("very-large-key")
        assert result == large_value

    def test_many_keys(self, temp_dir: Path) -> None:
        """测试存储大量键"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 存储 1000 个键值对
        for i in range(1000):
            cache.set(f"many-key-{i}", f"many-value-{i}")

        # 验证所有值
        for i in range(1000):
            result = cache.get(f"many-key-{i}")
            assert result == f"many-value-{i}"

    def test_large_json_object(self, temp_dir: Path) -> None:
        """测试存储大型 JSON 对象"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 创建大型嵌套对象
        large_object = {
            "items": [{"id": i, "data": "x" * 1000} for i in range(100)],
            "metadata": {"count": 100, "size": 1000},
        }
        cache.set("large-json-key", large_object)

        result = cache.get("large-json-key")
        assert result == large_object


class TestSQLiteCacheCorruptedDatabase:
    """SQLiteCache 损坏数据库测试"""

    def test_corrupted_database_file(self, temp_dir: Path) -> None:
        """测试损坏的数据库文件抛出 DatabaseError"""
        import sqlite3

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"

        # 创建损坏的文件
        with open(cache_path, "w") as f:
            f.write("This is not a valid SQLite database")

        # 尝试初始化应该抛出 DatabaseError
        with pytest.raises(sqlite3.DatabaseError):
            SQLiteCache(str(cache_path))

    def test_empty_database_file(self, temp_dir: Path) -> None:
        """测试空数据库文件"""
        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"

        # 创建空文件
        cache_path.touch()

        # 尝试初始化应该能恢复
        cache = SQLiteCache(str(cache_path))
        cache.set("empty-recovery-key", "empty-recovery-value")

        result = cache.get("empty-recovery-key")
        assert result == "empty-recovery-value"

    def test_missing_database_file_on_get(self, temp_dir: Path) -> None:
        """测试 get 时数据库文件被删除"""
        import os

        from backend.rag.cache import SQLiteCache

        cache_path = temp_dir / "cache.db"
        cache = SQLiteCache(str(cache_path))

        # 存储数据
        cache.set("delete-test-key", "delete-test-value")

        # 删除数据库文件
        os.remove(cache_path)

        # 重新创建 cache 实例（会重建数据库）
        cache = SQLiteCache(str(cache_path))

        # 数据应该不存在
        result = cache.get("delete-test-key")
        assert result is None
