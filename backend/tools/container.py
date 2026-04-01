"""ContainerManager 实现

管理 Docker 容器的生命周期。
"""

import time
from typing import Any, Union

import docker

from backend.config.models import PythonReplToolConfig, Settings, TerminalToolConfig


class ContainerManager:
    """容器管理器

    负责创建、管理和清理 Docker 容器。

    Attributes:
        config: SmartClaw 配置对象
        docker_client: Docker 客户端
        containers: 容器字典 {(tool_type, session_id): container}
    """

    def __init__(self, config: Settings) -> None:
        """初始化容器管理器

        Args:
            config: SmartClaw 配置对象
        """
        self.config = config
        self.docker_client = docker.from_env()
        self.containers: dict[tuple[str, str], Any] = {}

    def get_container(self, tool_type: str, session_id: str) -> Any:
        """获取或创建容器

        如果容器不存在，则创建新容器。
        如果容器存在但未运行，则尝试重启。

        Args:
            tool_type: 工具类型（terminal, python_repl）
            session_id: 会话 ID

        Returns:
            Docker 容器对象
        """
        key = (tool_type, session_id)

        if key not in self.containers:
            # 创建新容器
            container = self._create_container(tool_type, session_id)
            self.containers[key] = container
            return container

        # 检查容器状态
        container = self.containers[key]
        container.reload()  # 刷新容器状态

        if container.status != "running":
            # 尝试重启容器
            self._restart_container(container, attempt=1)

        return container

    def cleanup_session_containers(self, session_id: str) -> None:
        """清理会话的所有容器

        Args:
            session_id: 会话 ID
        """
        # 找到该会话的所有容器
        keys_to_remove = [
            key for key in self.containers if key[1] == session_id
        ]

        for key in keys_to_remove:
            container = self.containers[key]
            try:
                container.remove(force=True)
            except Exception:
                pass  # 忽略删除错误
            del self.containers[key]

    def _get_tool_config(
        self, tool_type: str
    ) -> Union[TerminalToolConfig, PythonReplToolConfig]:
        """获取工具配置

        Args:
            tool_type: 工具类型

        Returns:
            工具配置对象

        Raises:
            ValueError: 未知工具类型
        """
        if tool_type == "terminal":
            return self.config.tools.terminal
        elif tool_type == "python_repl":
            return self.config.tools.python_repl
        else:
            raise ValueError(f"Unknown tool type: {tool_type}")

    def _create_container(self, tool_type: str, session_id: str) -> Any:
        """创建新容器

        Args:
            tool_type: 工具类型
            session_id: 会话 ID

        Returns:
            Docker 容器对象
        """
        tool_config = self._get_tool_config(tool_type)

        # 解析内存限制
        memory_limit = tool_config.memory_limit
        if memory_limit.endswith("m"):
            mem_mb = int(memory_limit[:-1])
        elif memory_limit.endswith("g"):
            mem_mb = int(memory_limit[:-1]) * 1024
        else:
            mem_mb = int(memory_limit)

        # 解析 CPU 限制（Docker 使用 100000 = 1 CPU）
        cpu_limit = float(tool_config.cpu_limit)
        cpu_quota = int(cpu_limit * 100000)

        # 创建容器
        container = self.docker_client.containers.create(
            image=tool_config.image,
            detach=True,
            labels={
                "tool_type": tool_type,
                "session_id": session_id,
                "app": "smartclaw",
            },
            mem_limit=mem_mb * 1024 * 1024,  # 转换为字节
            cpu_quota=cpu_quota,
        )

        # 启动容器
        container.start()

        return container

    def _restart_container(self, container: Any, attempt: int) -> bool:
        """重启容器

        使用指数退避策略重启容器。

        Args:
            container: Docker 容器对象
            attempt: 当前尝试次数

        Returns:
            是否重启成功
        """
        max_attempts = 3

        if attempt > max_attempts:
            return False

        # 指数退避：1s, 2s, 4s
        backoff_time = 2 ** (attempt - 1)
        time.sleep(backoff_time)

        try:
            container.restart()
            return True
        except Exception:
            # 递归重试
            return self._restart_container(container, attempt + 1)

    def get_container_stats(self, container_id: str) -> dict[str, Any]:
        """获取容器资源使用统计

        Args:
            container_id: 容器 ID

        Returns:
            资源使用统计字典
        """
        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)

            # 解析统计信息
            cpu_usage = 0.0
            memory_usage = 0
            memory_limit = 0

            if "cpu_stats" in stats and "precpu_stats" in stats:
                cpu_delta = stats["cpu_stats"]["cpu_usage"].get(
                    "total_usage", 0
                ) - stats["precpu_stats"]["cpu_usage"].get("total_usage", 0)
                system_delta = stats["cpu_stats"].get(
                    "system_cpu_usage", 0
                ) - stats["precpu_stats"].get("system_cpu_usage", 0)
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * 100

            if "memory_stats" in stats:
                memory_usage = stats["memory_stats"].get("usage", 0)
                memory_limit = stats["memory_stats"].get("limit", 0)

            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
            }
        except Exception:
            return {}
