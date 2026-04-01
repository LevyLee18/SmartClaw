"""TerminalExecutor 实现

在 Docker 容器中安全执行终端命令。
"""

from typing import Any, Optional

from backend.config.models import Settings
from backend.tools.container import ContainerManager
from backend.tools.security import SecurityChecker


class TerminalExecutor:
    """终端命令执行器

    在 Docker 容器中安全执行 shell 命令。

    Attributes:
        config: SmartClaw 配置对象
        security_checker: 安全检查器
        container_manager: 容器管理器
        session_id: 会话 ID
    """

    def __init__(
        self,
        config: Settings,
        security_checker: SecurityChecker,
        container_manager: ContainerManager,
        session_id: str,
    ) -> None:
        """初始化终端命令执行器

        Args:
            config: SmartClaw 配置对象
            security_checker: 安全检查器
            container_manager: 容器管理器
            session_id: 会话 ID
        """
        self.config = config
        self.security_checker = security_checker
        self.container_manager = container_manager
        self.session_id = session_id

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT: int = 30

    def execute(
        self,
        command: str,
        confirmed: bool = False,
        timeout: Optional[int] = None,
    ) -> str:
        """执行终端命令

        Args:
            command: 要执行的命令
            confirmed: 是否已确认需确认的命令
            timeout: 超时时间（秒），None 使用默认值

        Returns:
            命令执行输出或错误信息
        """
        # 1. 安全检查
        allowed, status = self.security_checker.check_command_safety(command)

        if not allowed:
            return f"Security Error: Command is banned and cannot be executed"

        if status == "confirm" and not confirmed:
            return f"Command requires confirmation: {command}. Use confirmed=True to proceed."

        # 2. 获取容器
        try:
            container = self.container_manager.get_container(
                "terminal", self.session_id
            )
        except Exception as e:
            return f"Container Error: Failed to get container - {e}"

        # 3. 执行命令
        try:
            # 使用配置的超时或自定义超时
            exec_timeout = timeout or self.DEFAULT_TIMEOUT

            exit_code, output = container.exec_run(
                f"sh -c {repr(command)}",
                workdir="/workspace",
                timeout=exec_timeout,
            )

            # 4. 处理结果
            if exit_code == 0:
                return output.decode("utf-8", errors="replace")
            else:
                return f"Error (exit code {exit_code}): {output.decode('utf-8', errors='replace')}"

        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                return f"Timeout Error: Command execution timed out after {exec_timeout} seconds"
            return f"Execution Error: {e}"

    def get_tool_adapter(self) -> dict[str, Any]:
        """获取 LangChain 工具适配器

        返回一个符合 LangChain 工具规范的字典，包含：
        - name: 工具名称
        - description: 工具描述
        - func: 可调用的工具函数

        Returns:
            工具配置字典
        """

        def terminal(command: str, confirmed: bool = False) -> str:
            """命令行操作工具（Docker 沙箱）

            在隔离的 Docker 容器中执行 shell 命令。

            Args:
                command: 要执行的 shell 命令
                confirmed: 是否已确认需确认的命令（如 reboot）

            Returns:
                命令执行输出或错误信息

            安全限制：
            - 危险命令被拦截（如 rm -rf, dd, mkfs）
            - 需确认的命令需要 explicit 确认
            - 命令执行有超时限制
            """
            return self.execute(command, confirmed=confirmed)

        return {
            "name": "terminal",
            "description": (
                "命令行操作工具（Docker 沙箱）。"
                "在隔离的 Docker 容器中执行 shell 命令。"
                "危险命令会被拦截，需确认的命令需要 explicit 确认。"
            ),
            "func": terminal,
        }
