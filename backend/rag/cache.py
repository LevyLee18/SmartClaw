"""SQLiteCache 缓存类

用于缓存节点转换结果，避免重复计算。
"""

import base64
import hashlib
import json
import sqlite3
from typing import Any


class SQLiteCache:
    """SQLite 缓存类

    使用 SQLite 数据库缓存转换结果。

    Attributes:
        cache_path: 缓存数据库文件路径
    """

    def __init__(self, cache_path: str) -> None:
        """初始化缓存

        创建数据库文件、缓存表和索引。

        Args:
            cache_path: 缓存数据库文件路径
        """
        self.cache_path = cache_path

        # 创建数据库连接并初始化表
        conn = sqlite3.connect(cache_path)
        cursor = conn.cursor()

        # 创建缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建访问时间索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_accessed_at
            ON cache(accessed_at)
        """)

        conn.commit()
        conn.close()

    def get(self, key: str) -> Any:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在返回 None
        """
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
        result = cursor.fetchone()

        if result is not None:
            # 更新访问时间
            cursor.execute(
                "UPDATE cache SET accessed_at = CURRENT_TIMESTAMP WHERE key = ?",
                (key,),
            )
            conn.commit()
            conn.close()
            data = json.loads(result[0])
            # 处理 bytes 类型的反序列化
            if isinstance(data, dict) and "__bytes__" in data:
                return base64.b64decode(data["__bytes__"])
            return data

        conn.close()
        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值（将被 JSON 序列化）
        """
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        # 处理 bytes 类型的序列化
        if isinstance(value, bytes):
            value = {"__bytes__": base64.b64encode(value).decode("utf-8")}

        # 使用 INSERT OR REPLACE 实现插入或更新
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
            (key, json.dumps(value, ensure_ascii=False)),
        )

        conn.commit()
        conn.close()

    def _generate_cache_key(self, content: str) -> str:
        """生成缓存键

        使用 SHA256 算法生成内容哈希作为缓存键。

        Args:
            content: 原始内容

        Returns:
            SHA256 十六进制字符串
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
