"""测试 ConfigManager._validate_config() 方法"""
import os
from pathlib import Path
from unittest import mock

import pytest
import yaml


class TestConfigManagerValidateConfig:
    """ConfigManager._validate_config() 测试类"""

    def test_validate_invalid_provider_value(self, tmp_path: Path):
        """测试无效的 provider 值"""
        from backend.config.errors import ConfigError
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 无效的 provider
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "invalid_provider",  # 无效值
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with pytest.raises((ConfigError, ValueError)) as exc_info:
                ConfigManager()

        error_msg = str(exc_info.value)
        assert "provider" in error_msg.lower() or "literal" in error_msg.lower() or "invalid" in error_msg.lower()

    def test_validate_flush_ratio_out_of_range(self, tmp_path: Path):
        """测试 flush_ratio 超出有效范围（应 <= 1）"""
        from backend.config.errors import ConfigError
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # flush_ratio > 1
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "agent": {
                "session": {
                    "flush_ratio": 1.5,  # 无效值
                }
            },
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with pytest.raises((ConfigError, ValueError)) as exc_info:
                ConfigManager()

        error_msg = str(exc_info.value)
        assert "flush_ratio" in error_msg.lower() or "ratio" in error_msg.lower() or "range" in error_msg.lower() or "less than or equal" in error_msg.lower()

    def test_validate_valid_config_passes(self, tmp_path: Path):
        """测试有效配置通过验证"""
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 有效的完整配置
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "agent": {
                "session": {
                    "flush_ratio": 0.5,  # 有效值
                }
            },
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "test-key",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            # 不应抛出异常
            manager = ConfigManager()

        assert manager.get("storage.base_path") == str(tmp_path)

    def test_validate_empty_api_key(self, tmp_path: Path):
        """测试空 API Key 应该失败"""
        from backend.config.errors import ConfigError
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 空 API Key
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "",  # 空值
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with pytest.raises((ConfigError, ValueError)) as exc_info:
                ConfigManager()

        error_msg = str(exc_info.value)
        assert "api_key" in error_msg.lower() or "key" in error_msg.lower() or "empty" in error_msg.lower() or "required" in error_msg.lower()

    def test_validate_negative_max_tokens(self, tmp_path: Path):
        """测试负数 max_tokens 应该失败"""
        from backend.config.errors import ConfigError
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 负数 max_tokens
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "test-key",
                    "max_tokens": -100,  # 无效值
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with pytest.raises((ConfigError, ValueError)) as exc_info:
                ConfigManager()

        error_msg = str(exc_info.value)
        assert "max_tokens" in error_msg.lower() or "greater than" in error_msg.lower()

    def test_validate_temperature_out_of_range(self, tmp_path: Path):
        """测试 temperature 超出有效范围"""
        from backend.config.errors import ConfigError
        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # temperature > 2
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "test-key",
                    "temperature": 3.0,  # 无效值
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with pytest.raises((ConfigError, ValueError)) as exc_info:
                ConfigManager()

        error_msg = str(exc_info.value)
        assert "temperature" in error_msg.lower() or "less than or equal" in error_msg.lower()
