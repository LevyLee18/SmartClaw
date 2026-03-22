"""测试 ConfigManager 类"""
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestConfigManagerLoad:
    """ConfigManager.load() 测试类"""

    def test_load_from_existing_file(self, tmp_path: Path):
        """测试从现有文件加载配置"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建临时配置文件
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "api_key": "sk-test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        # Mock 配置路径
        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager = ConfigManager()
            config = manager.get_config()

        assert config["storage"]["base_path"] == str(tmp_path)
        assert config["llm"]["default"]["provider"] == "anthropic"

    def test_load_missing_file_returns_default(self, tmp_path: Path):
        """测试缺失文件时返回默认配置"""
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 指向不存在的文件
        non_existent = tmp_path / "non_existent.yaml"

        with mock.patch.object(
            Path, "expanduser", return_value=non_existent
        ):
            manager = ConfigManager()
            config = manager.get_config()

        # 应该返回默认配置
        assert config is not None
        assert isinstance(config, dict)
        # 默认配置应包含基本结构
        assert "storage" in config or "llm" in config

    def test_singleton_pattern(self, tmp_path: Path):
        """测试单例模式"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建临时配置文件
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "test-model",
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager1 = ConfigManager()
            manager2 = ConfigManager()

        assert manager1 is manager2

    def test_load_with_nested_config(self, tmp_path: Path):
        """测试加载嵌套配置"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建深度嵌套的配置
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "api_key": "sk-test-key",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                },
                "rag": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-openai-key",
                },
            },
            "agent": {
                "session": {
                    "token_threshold": 3000,
                    "flush_ratio": 0.5,
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager = ConfigManager()
            config = manager.get_config()

        # 验证嵌套访问
        assert config["llm"]["default"]["max_tokens"] == 4096
        assert config["agent"]["session"]["token_threshold"] == 3000

    def test_load_empty_yaml_file(self, tmp_path: Path):
        """测试加载空 YAML 文件"""
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建空配置文件
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager = ConfigManager()
            config = manager.get_config()

        # 空 YAML 返回 None，应使用默认配置
        assert config is not None
        assert isinstance(config, dict)

    def test_load_malformed_yaml_raises_error(self, tmp_path: Path):
        """测试加载格式错误的 YAML 抛出错误"""
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建格式错误的配置文件
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            with pytest.raises(Exception):  # YAML 解析错误
                ConfigManager()


class TestConfigManagerGet:
    """ConfigManager.get() 测试类"""

    def test_get_with_dot_notation(self, tmp_path: Path):
        """测试点分路径访问"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "test-model",
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager = ConfigManager()

        assert manager.get("llm.default.provider") == "anthropic"
        assert manager.get("llm.default.model") == "test-model"
        assert manager.get("storage.base_path") == str(tmp_path)

    def test_get_non_existent_key_returns_default(self, tmp_path: Path):
        """测试不存在的键返回默认值"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "test-model",
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager = ConfigManager()

        assert manager.get("non.existent.key") is None
        assert manager.get("non.existent.key", "default_value") == "default_value"

    def test_get_top_level_key(self, tmp_path: Path):
        """测试获取顶级键"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "test-model",
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(
            Path, "expanduser", return_value=config_file
        ):
            manager = ConfigManager()

        storage = manager.get("storage")
        assert storage == {"base_path": str(tmp_path)}
