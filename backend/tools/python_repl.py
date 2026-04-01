"""PythonExecutor 实现

在 Docker 容器中安全执行 Python 代码。
"""

from typing import Any, Optional

from backend.config.models import Settings
from backend.tools.container import ContainerManager
from backend.tools.security import SecurityChecker


class PythonExecutor:
    """Python 代码执行器

    在 Docker 容器中安全执行 Python 代码。

    Attributes:
        config: SmartClaw 配置对象
        security_checker: 安全检查器
        container_manager: 容器管理器
        session_id: 会话 ID
    """

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT: int = 30

    def __init__(
        self,
        config: Settings,
        security_checker: SecurityChecker,
        container_manager: ContainerManager,
        session_id: str,
    ) -> None:
        """初始化 Python 代码执行器

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

    def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> str:
        """执行 Python 代码

        Args:
            code: 要执行的 Python 代码
            timeout: 超时时间（秒），None 使用默认值

        Returns:
            代码执行输出或错误信息
        """
        # 1. 安全检查
        allowed, status = self.security_checker.check_python_code(code)

        if not allowed:
            return "Security Error: Code contains dangerous modules and cannot be executed"

        # 2. 获取容器
        try:
            container = self.container_manager.get_container(
                "python_repl", self.session_id
            )
        except Exception as e:
            return f"Container Error: Failed to get container - {e}"

        # 3. 执行代码
        try:
            # 使用配置的超时或自定义超时
            exec_timeout = timeout or self.DEFAULT_TIMEOUT

            # 使用 Python 执行代码
            python_code = f"import sys\n{code}\n"
            exit_code, output = container.exec_run(
                f'python3 -c {repr(python_code)}',
                workdir="/workspace",
                timeout=exec_timeout,
            )

            # 4. 处理结果
            if exit_code == 0:
                result = output.decode("utf-8", errors="replace")
                # 移除末尾的换行符（如果有）
                return result.rstrip("\n")
            else:
                return f"Error (exit code {exit_code}): {output.decode('utf-8', errors='replace')}"

        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                return f"Timeout Error: Code execution timed out after {exec_timeout} seconds"
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

        def python_repl(code: str) -> str:
            """Python 代码执行工具（Docker 沙箱）

            在隔离的 Docker 容器中执行 Python 代码。

            Args:
                code: 要执行的 Python 代码

            Returns:
                代码执行结果或错误信息

            安全限制：
            - 危险模块被拦截（如 subprocess, os.system）
            - 代码执行有超时限制
            - 容器资源限制（内存、CPU）
            """
            return self.execute(code)

        return {
            "name": "python_repl",
            "description": (
                "Python 代码执行工具（Docker 沙箱）。"
                "在隔离的 Docker 容器中执行 Python 代码。"
                "危险模块会被拦截，代码执行有超时限制。"
            ),
            "func": python_repl,
        }
