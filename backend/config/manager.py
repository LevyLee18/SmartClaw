"""配置管理器模块"""
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import ValidationError

from backend.config.models import Settings


class ConfigManager:
    """配置管理器（单例模式）

    负责：
    - 从 config.yaml 加载配置
    - 展开环境变量引用
    - 验证配置有效性
    - 提供点分路径访问
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[dict] = None
    _config_path: Path = Path("~/.smartclaw/config.yaml")

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
        return cls._instance

    def __init__(self) -> None:
        """初始化配置管理器"""
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        config_path = self._config_path.expanduser()
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            # 如果配置为空或缺少必需字段，使用默认配置
            if not config:
                config = self._get_default_config()
            else:
                config = self._apply_defaults(config)
            self._validate_config(config)
            self._config = config
        else:
            # 文件不存在，使用默认配置
            self._config = self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "storage": {"base_path": str(Path("~/.smartclaw"))},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", "sk-placeholder-key"),
                }
            },
        }

    def _apply_defaults(self, config: dict) -> dict:
        """应用默认值到配置中缺失的部分"""
        default = self._get_default_config()
        result = {}

        # 复制所有默认值
        for key, default_value in default.items():
            if key in config:
                if isinstance(default_value, dict) and isinstance(config[key], dict):
                    result[key] = self._merge_dicts(config[key], default_value)
                else:
                    result[key] = config[key]
            else:
                result[key] = default_value

        # 复制配置中额外的键
        for key, value in config.items():
            if key not in result:
                result[key] = value

        return result

    def _merge_dicts(self, config: dict, default: dict) -> dict:
        """合并两个字典，config 中的值优先"""
        result = default.copy()
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(value, result[key])
            else:
                result[key] = value
        return result

    def _validate_config(self, config: dict) -> None:
        """验证配置有效性"""
        try:
            Settings(**config)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点分路径如 llm.default.model）"""
        if not self._config:
            return default
        keys = key.split(".")
        value: Any = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_config(self) -> dict:
        """获取完整配置"""
        return self._config.copy() if self._config else {}
