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


class TestConfigManagerExpandEnvVars:
    """ConfigManager._expand_env_vars() 测试类"""

    def test_expand_simple_env_var(self, tmp_path: Path):
        """测试展开简单的环境变量 ${VAR}"""
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
                    "api_key": "${ANTHROPIC_API_KEY}",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key-12345"}):
                manager = ConfigManager()
                config = manager.get_config()

        assert config["llm"]["default"]["api_key"] == "sk-test-key-12345"

    def test_expand_env_var_in_path(self, tmp_path: Path):
        """测试展开路径中的环境变量"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": "${SMARTCLAW_HOME}/data"},
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
            with mock.patch.dict(os.environ, {"SMARTCLAW_HOME": "/home/user/smartclaw"}):
                manager = ConfigManager()
                config = manager.get_config()

        assert config["storage"]["base_path"] == "/home/user/smartclaw/data"

    def test_expand_undefined_env_var_returns_empty(self, tmp_path: Path):
        """测试未定义的环境变量返回空字符串"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "custom": {"value": "${UNDEFINED_VAR}"},  # 使用非验证字段
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "test-key",  # 使用有效值避免验证错误
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        # 确保环境变量不存在
        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with mock.patch.dict(os.environ, {}, clear=True):
                manager = ConfigManager()
                config = manager.get_config()

        assert config["custom"]["value"] == ""

    def test_expand_nested_config_ref(self, tmp_path: Path):
        """测试展开嵌套配置引用 ${storage.base_path}"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "memory": {"base_path": "${storage.base_path}"},
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
            manager = ConfigManager()
            config = manager.get_config()

        assert config["memory"]["base_path"] == str(tmp_path)

    def test_expand_nested_config_ref_deep(self, tmp_path: Path):
        """测试展开深层嵌套配置引用"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "rag": {"index_path": "${storage.base_path}/store/memory"},
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
            manager = ConfigManager()
            config = manager.get_config()

        assert config["rag"]["index_path"] == f"{tmp_path}/store/memory"

    def test_expand_in_nested_dict(self, tmp_path: Path):
        """测试在嵌套字典中展开环境变量"""
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
                    "api_key": "${ANTHROPIC_API_KEY}",
                },
                "rag": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",  # 添加必需字段
                    "api_key": "${OPENAI_API_KEY}",
                },
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with mock.patch.dict(
                os.environ,
                {
                    "ANTHROPIC_API_KEY": "sk-anthropic-key",
                    "OPENAI_API_KEY": "sk-openai-key",
                },
            ):
                manager = ConfigManager()
                config = manager.get_config()

        assert config["llm"]["default"]["api_key"] == "sk-anthropic-key"
        assert config["llm"]["rag"]["api_key"] == "sk-openai-key"

    def test_expand_in_list(self, tmp_path: Path):
        """测试在列表中展开环境变量"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "tools": {
                "allowed_extensions": ["md", "txt", "${SPECIAL_EXT}"],
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
            with mock.patch.dict(os.environ, {"SPECIAL_EXT": "py"}):
                manager = ConfigManager()
                config = manager.get_config()

        assert "py" in config["tools"]["allowed_extensions"]

    def test_no_expansion_for_plain_string(self, tmp_path: Path):
        """测试普通字符串不进行展开"""
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
                    "model": "claude-sonnet-4-20250514",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            manager = ConfigManager()
            config = manager.get_config()

        assert config["llm"]["default"]["model"] == "claude-sonnet-4-20250514"

    def test_expand_mixed_env_and_config_ref(self, tmp_path: Path):
        """测试混合使用环境变量和配置引用"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        config_content = {
            "storage": {"base_path": "${SMARTCLAW_HOME}"},
            "logs": {"path": "${storage.base_path}/logs"},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "api_key": "${ANTHROPIC_API_KEY}",
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            with mock.patch.dict(
                os.environ,
                {
                    "SMARTCLAW_HOME": "/home/user/smartclaw",
                    "ANTHROPIC_API_KEY": "sk-test-key",
                },
            ):
                manager = ConfigManager()
                config = manager.get_config()

        assert config["storage"]["base_path"] == "/home/user/smartclaw"
        assert config["logs"]["path"] == "/home/user/smartclaw/logs"
        assert config["llm"]["default"]["api_key"] == "sk-test-key"


class TestConfigManagerBoundary:
    """ConfigManager 边界测试类"""

    def test_empty_config_file(self, tmp_path: Path):
        """测试空配置文件"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建空配置文件
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump({}, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            manager = ConfigManager()
            config = manager.get_config()

        # 空配置应使用默认配置
        assert config is not None
        assert isinstance(config, dict)

    def test_very_large_config(self, tmp_path: Path):
        """测试超大配置"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建包含大量配置项的配置
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "llm": {
                "default": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "api_key": "test-key",
                }
            },
            "large_list": list(range(1000)),  # 1000 个元素的列表
            "deep_nested": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": {
                                    "value": "deep_value"
                                }
                            }
                        }
                    }
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        with mock.patch.object(Path, "expanduser", return_value=config_file):
            manager = ConfigManager()
            config = manager.get_config()

        # 验证深度嵌套值
        assert config["deep_nested"]["level1"]["level2"]["level3"]["level4"]["level5"]["value"] == "deep_value"
        assert len(config["large_list"]) == 1000

    def test_circular_config_reference(self, tmp_path: Path):
        """测试循环引用"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建循环引用配置
        config_content = {
            "storage": {"base_path": "${logs.path}"},  # 引用 logs.path
            "logs": {"path": "${storage.base_path}/logs"},  # 引用 storage.base_path
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
            manager = ConfigManager()
            config = manager.get_config()

        # 循环引用：storage.base_path 引用 logs.path，logs.path 引用 storage.base_path
        # 实际行为：logs.path 先展开，遇到 storage.base_path 循环引用返回空，得到 "/logs"
        # 然后 storage.base_path 得到 logs.path 的值 "/logs"
        assert config["storage"]["base_path"] == "/logs"
        assert config["logs"]["path"] == "/logs"

    def test_special_characters_in_config(self, tmp_path: Path):
        """测试配置中的特殊字符"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建包含特殊字符的配置
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "special": {
                "emoji": "🚀 SmartClaw",
                "chinese": "中文测试",
                "special_chars": "a@b#c$1!2&3*4%5",
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
            manager = ConfigManager()
            config = manager.get_config()

        assert config["special"]["emoji"] == "🚀 SmartClaw"
        assert config["special"]["chinese"] == "中文测试"
        assert "!" in config["special"]["special_chars"]

    def test_empty_string_values(self, tmp_path: Path):
        """测试空字符串值"""
        import yaml

        from backend.config.manager import ConfigManager

        # 重置单例
        ConfigManager._instance = None
        ConfigManager._config = None

        # 创建包含空字符串值的配置
        config_content = {
            "storage": {"base_path": str(tmp_path)},
            "empty_values": {
                "empty_string": "",
                "none_value": None,
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
            manager = ConfigManager()
            config = manager.get_config()

        assert config["empty_values"]["empty_string"] == ""
        assert config["empty_values"]["none_value"] is None
