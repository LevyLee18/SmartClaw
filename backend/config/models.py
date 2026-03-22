"""配置数据模型"""
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
