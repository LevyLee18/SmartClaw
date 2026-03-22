"""配置数据模型"""
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """LLM 配置模型"""

    provider: Literal["anthropic", "openai", "qwen", "ollama", "vllm"] = Field(
        ..., description="LLM 提供商"
    )
    model: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API 密钥")
    max_tokens: int = Field(
        default=4096, ge=1, le=100000, description="最大 token 数"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="温度参数"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """验证 API 密钥不能为空或使用默认占位符"""
        if not v or v.strip() == "":
            raise ValueError("API key must be configured")
        if v == "your_api_key_here":
            raise ValueError("API key must be configured")
        return v


class ContainerConfig(BaseModel):
    """容器配置模型"""

    image: str = Field(..., description="Docker 镜像名称")
    memory_limit: str = Field(default="256m", description="内存限制")
    cpu_limit: str = Field(default="0.25", description="CPU 限制")
    auto_restart: bool = Field(default=True, description="是否自动重启")

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """验证镜像名称不能为空"""
        if not v or v.strip() == "":
            raise ValueError("Image name must be configured")
        return v

    @field_validator("memory_limit")
    @classmethod
    def validate_memory_limit(cls, v: str) -> str:
        """验证内存限制格式（支持纯数字、数字+m、数字+g）"""
        if not re.match(r"^\d+[mg]?$", v):
            raise ValueError(
                f"Invalid memory format: {v}. "
                "Expected format: number, number+m, or number+g"
            )
        return v
