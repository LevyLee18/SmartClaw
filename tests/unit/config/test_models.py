"""测试 LLMConfig 模型"""
import pytest
from pydantic import ValidationError


class TestLLMConfig:
    """LLMConfig 测试类"""

    def test_valid_config(self):
        """测试有效配置"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-test-key-12345",
            max_tokens=4096,
            temperature=0.7
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-20250514"
        assert config.api_key == "sk-test-key-12345"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_valid_config_with_different_providers(self):
        """测试不同 provider 的有效配置"""
        from backend.config.models import LLMConfig

        # OpenAI provider
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            api_key="sk-openai-key",
            max_tokens=2000,
            temperature=0.5
        )
        assert config.provider == "openai"

        # Qwen provider
        config = LLMConfig(
            provider="qwen",
            model="qwen-max",
            api_key="sk-qwen-key",
            max_tokens=8000,
            temperature=0.3
        )
        assert config.provider == "qwen"

    def test_default_values(self):
        """测试默认值"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-test-key"
        )
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_max_tokens_boundary_min(self):
        """测试 max_tokens 最小边界"""
        from backend.config.models import LLMConfig

        # 刚好在范围内
        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-test-key",
            max_tokens=1,
            temperature=0.7
        )
        assert config.max_tokens == 1

    def test_max_tokens_below_range(self):
        """测试 max_tokens 低于范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                api_key="sk-test-key",
                max_tokens=0,
                temperature=0.7
            )
        assert "max_tokens" in str(exc_info.value)

    def test_max_tokens_boundary_max(self):
        """测试 max_tokens 最大边界"""
        from backend.config.models import LLMConfig

        # 刚好在范围内
        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-test-key",
            max_tokens=100000,
            temperature=0.7
        )
        assert config.max_tokens == 100000

    def test_max_tokens_above_range(self):
        """测试 max_tokens 超出范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                api_key="sk-test-key",
                max_tokens=100001,
                temperature=0.7
            )

    def test_temperature_boundary_min(self):
        """测试 temperature 最小边界"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-test-key",
            max_tokens=4096,
            temperature=0.0
        )
        assert config.temperature == 0.0

    def test_temperature_below_range(self):
        """测试 temperature 低于范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=-0.1
            )

    def test_temperature_boundary_max(self):
        """测试 temperature 最大边界"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-test-key",
            max_tokens=4096,
            temperature=2.0
        )
        assert config.temperature == 2.0

    def test_temperature_above_range(self):
        """测试 temperature 超出范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=2.1
            )

    def test_missing_required_field_provider(self):
        """测试缺少 provider 字段（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                model="claude-sonnet-4-20250514",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=0.7
            )
        assert "provider" in str(exc_info.value)

    def test_missing_required_field_model(self):
        """测试缺少 model 字段（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="anthropic",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=0.7
            )
        assert "model" in str(exc_info.value)

    def test_missing_required_field_api_key(self):
        """测试缺少 api_key 字段（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.7
            )
        assert "api_key" in str(exc_info.value)

    def test_invalid_provider(self):
        """测试无效的 provider（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="invalid_provider",
                model="claude-sonnet-4-20250514",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=0.7
            )
        assert "provider" in str(exc_info.value)

    def test_empty_api_key(self):
        """测试空 api_key（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                api_key="",
                max_tokens=4096,
                temperature=0.7
            )
        assert "api_key" in str(exc_info.value)

    def test_default_api_key_placeholder(self):
        """测试默认 api_key 占位符（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                api_key="your_api_key_here",
                max_tokens=4096,
                temperature=0.7
            )
        assert "api_key" in str(exc_info.value)

    def test_ollama_provider(self):
        """测试 ollama provider"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="ollama",
            model="llama3",
            api_key="not-needed",
            max_tokens=4096,
            temperature=0.7
        )
        assert config.provider == "ollama"

    def test_vllm_provider(self):
        """测试 vllm provider"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="vllm",
            model="llama-3-70b",
            api_key="not-needed",
            max_tokens=4096,
            temperature=0.7
        )
        assert config.provider == "vllm"
