"""配置数据模型"""
import os
import re
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============ 基础配置模型 ============


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


# ============ Settings 嵌套配置块 ============


class StorageConfig(BaseModel):
    """存储配置"""

    base_path: Path = Field(
        default=Path("~/.smartclaw"), description="存储根目录"
    )


class EmbeddingConfig(BaseModel):
    """Embedding 配置"""

    provider: str = Field(default="openai", description="Embedding 提供商")
    model: str = Field(
        default="text-embedding-3-small", description="Embedding 模型"
    )
    api_key: Optional[str] = Field(default=None, description="API 密钥")
    dimensions: int = Field(default=1536, description="向量维度")


class SessionConfig(BaseModel):
    """会话配置"""

    token_threshold: int = Field(
        default=3000, ge=100, description="Token 阈值"
    )
    flush_ratio: float = Field(
        default=0.5, ge=0.1, le=1.0, description="冲刷比例"
    )
    max_session_messages: int = Field(
        default=100, ge=10, description="最大会话消息数"
    )


class SystemPromptConfig(BaseModel):
    """系统提示配置"""

    max_tokens: int = Field(
        default=30000, ge=1000, description="最大 Token 数"
    )
    near_memory_days: int = Field(
        default=2, ge=1, le=30, description="近端记忆天数"
    )


class AgentConfig(BaseModel):
    """Agent 配置"""

    session: SessionConfig = Field(
        default_factory=SessionConfig, description="会话配置"
    )
    system_prompt: SystemPromptConfig = Field(
        default_factory=SystemPromptConfig, description="系统提示配置"
    )


class NearMemoryConfig(BaseModel):
    """近端记忆配置"""

    days: int = Field(default=2, ge=1, le=30, description="近端记忆天数")
    pre_compress_threshold: int = Field(
        default=3000, ge=100, description="预压缩阈值"
    )
    flush_ratio: float = Field(
        default=0.5, ge=0.1, le=1.0, description="冲刷比例"
    )


class CoreMemoryConfig(BaseModel):
    """核心记忆配置"""

    max_tokens: int = Field(
        default=30000, ge=1000, description="最大 Token 数"
    )


class MemoryConfig(BaseModel):
    """记忆配置"""

    near_memory: NearMemoryConfig = Field(
        default_factory=NearMemoryConfig, description="近端记忆配置"
    )
    core_memory: CoreMemoryConfig = Field(
        default_factory=CoreMemoryConfig, description="核心记忆配置"
    )


class RAGConfig(BaseModel):
    """RAG 配置"""

    top_k: int = Field(default=5, ge=1, le=100, description="检索返回数量")
    chunk_size: int = Field(
        default=1024, ge=100, le=8192, description="分块大小"
    )
    chunk_overlap: int = Field(
        default=100, ge=0, le=500, description="分块重叠"
    )
    generate_queries: int = Field(
        default=3, ge=1, le=10, description="生成的查询数量"
    )


class TerminalToolConfig(BaseModel):
    """终端工具配置"""

    image: str = Field(default="alpine:3.19", description="Docker 镜像")
    memory_limit: str = Field(default="256m", description="内存限制")
    cpu_limit: str = Field(default="0.25", description="CPU 限制")


class PythonReplToolConfig(BaseModel):
    """Python REPL 工具配置"""

    image: str = Field(default="python:3.11-slim", description="Docker 镜像")
    memory_limit: str = Field(default="512m", description="内存限制")
    cpu_limit: str = Field(default="0.25", description="CPU 限制")


class ToolsConfig(BaseModel):
    """工具配置"""

    terminal: TerminalToolConfig = Field(
        default_factory=TerminalToolConfig, description="终端工具配置"
    )
    python_repl: PythonReplToolConfig = Field(
        default_factory=PythonReplToolConfig, description="Python REPL 配置"
    )


class SecurityConfig(BaseModel):
    """安全配置"""

    allowed_extensions: list[str] = Field(
        default=[
            ".md",
            ".txt",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".html",
            ".css",
            ".xml",
            ".csv",
            ".sh",
        ],
        description="允许的文件扩展名",
    )
    banned_commands: list[str] = Field(
        default=[
            "rm -rf",
            "sudo rm",
            "sudo",
            "mkfs",
            "dd",
            "reboot",
            "shutdown",
            "halt",
            "init 0",
            "init 6",
        ],
        description="直接禁止的命令",
    )
    confirm_commands: list[str] = Field(
        default=["rm", "mv", "cp", "chmod", "chown", "git push", "pip install"],
        description="需要确认的命令",
    )
    max_command_length: int = Field(
        default=10000, ge=1, description="最大命令长度"
    )


class LLMConfigWrapper(BaseModel):
    """LLM 配置包装器"""

    default: LLMConfig = Field(..., description="默认 LLM 配置")
    rag: Optional[LLMConfig] = Field(default=None, description="RAG LLM 配置")


def _get_default_llm_config() -> LLMConfigWrapper:
    """获取默认 LLM 配置（从环境变量）"""
    api_key = os.getenv("ANTHROPIC_API_KEY", "sk-placeholder-key-for-testing")
    return LLMConfigWrapper(
        default=LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key=api_key,
        )
    )


# ============ 主配置类 ============


class Settings(BaseModel):
    """SmartClaw 主配置类"""

    storage: StorageConfig = Field(
        default_factory=StorageConfig, description="存储配置"
    )
    llm: LLMConfigWrapper = Field(
        default_factory=_get_default_llm_config, description="LLM 配置"
    )
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig, description="Embedding 配置"
    )
    agent: AgentConfig = Field(
        default_factory=AgentConfig, description="Agent 配置"
    )
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig, description="记忆配置"
    )
    rag: RAGConfig = Field(default_factory=RAGConfig, description="RAG 配置")
    tools: ToolsConfig = Field(
        default_factory=ToolsConfig, description="工具配置"
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig, description="安全配置"
    )
