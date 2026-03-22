"""测试配置数据模型"""
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


class TestContainerConfig:
    """ContainerConfig 测试类"""

    def test_valid_config(self):
        """测试有效配置"""
        from backend.config.models import ContainerConfig

        config = ContainerConfig(
            image="alpine:3.19",
            memory_limit="256m",
            cpu_limit="0.25",
            auto_restart=True
        )
        assert config.image == "alpine:3.19"
        assert config.memory_limit == "256m"
        assert config.cpu_limit == "0.25"
        assert config.auto_restart is True

    def test_valid_config_with_different_memory_formats(self):
        """测试不同内存格式"""
        from backend.config.models import ContainerConfig

        # 使用 m (兆字节)
        config = ContainerConfig(
            image="python:3.11-slim",
            memory_limit="512m",
            cpu_limit="0.5"
        )
        assert config.memory_limit == "512m"

        # 使用 g (吉字节)
        config = ContainerConfig(
            image="node:20",
            memory_limit="2g",
            cpu_limit="1.0"
        )
        assert config.memory_limit == "2g"

        # 纯数字 (字节)
        config = ContainerConfig(
            image="ubuntu:22.04",
            memory_limit="1073741824",
            cpu_limit="0.25"
        )
        assert config.memory_limit == "1073741824"

    def test_default_values(self):
        """测试默认值"""
        from backend.config.models import ContainerConfig

        config = ContainerConfig(
            image="alpine:3.19"
        )
        assert config.memory_limit == "256m"
        assert config.cpu_limit == "0.25"
        assert config.auto_restart is True

    def test_missing_required_field_image(self):
        """测试缺少 image 字段（异常场景）"""
        from backend.config.models import ContainerConfig

        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                memory_limit="256m",
                cpu_limit="0.25"
            )
        assert "image" in str(exc_info.value)

    def test_invalid_memory_format_with_space(self):
        """测试无效内存格式（带空格）"""
        from backend.config.models import ContainerConfig

        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                image="alpine:3.19",
                memory_limit="256 m",
                cpu_limit="0.25"
            )
        assert "memory_limit" in str(exc_info.value)

    def test_invalid_memory_format_with_gb(self):
        """测试无效内存格式（使用 gb 而非 g）"""
        from backend.config.models import ContainerConfig

        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                image="alpine:3.19",
                memory_limit="1gb",
                cpu_limit="0.25"
            )
        assert "memory_limit" in str(exc_info.value)

    def test_invalid_memory_format_negative(self):
        """测试无效内存格式（负数）"""
        from backend.config.models import ContainerConfig

        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                image="alpine:3.19",
                memory_limit="-256m",
                cpu_limit="0.25"
            )
        assert "memory_limit" in str(exc_info.value)

    def test_invalid_memory_format_with_decimal(self):
        """测试无效内存格式（小数）"""
        from backend.config.models import ContainerConfig

        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                image="alpine:3.19",
                memory_limit="1.5g",
                cpu_limit="0.25"
            )
        assert "memory_limit" in str(exc_info.value)

    def test_auto_restart_false(self):
        """测试 auto_restart 为 False"""
        from backend.config.models import ContainerConfig

        config = ContainerConfig(
            image="alpine:3.19",
            memory_limit="256m",
            cpu_limit="0.25",
            auto_restart=False
        )
        assert config.auto_restart is False

    def test_various_cpu_limits(self):
        """测试各种 CPU 限制值"""
        from backend.config.models import ContainerConfig

        # 小数
        config = ContainerConfig(image="alpine:3.19", cpu_limit="0.5")
        assert config.cpu_limit == "0.5"

        # 整数
        config = ContainerConfig(image="alpine:3.19", cpu_limit="1")
        assert config.cpu_limit == "1"

        # 多核
        config = ContainerConfig(image="alpine:3.19", cpu_limit="2.5")
        assert config.cpu_limit == "2.5"

    def test_empty_image(self):
        """测试空镜像名（异常场景）"""
        from backend.config.models import ContainerConfig

        with pytest.raises(ValidationError) as exc_info:
            ContainerConfig(
                image="",
                memory_limit="256m",
                cpu_limit="0.25"
            )
        assert "image" in str(exc_info.value)

    def test_image_without_tag(self):
        """测试无 tag 的镜像名"""
        from backend.config.models import ContainerConfig

        config = ContainerConfig(
            image="alpine",
            memory_limit="256m",
            cpu_limit="0.25"
        )
        assert config.image == "alpine"

    def test_image_with_digest(self):
        """测试带 digest 的镜像名"""
        from backend.config.models import ContainerConfig

        config = ContainerConfig(
            image="alpine@sha256:abc123",
            memory_limit="256m",
            cpu_limit="0.25"
        )
        assert config.image == "alpine@sha256:abc123"
