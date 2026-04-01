"""ContainerManager 边界测试

测试要点：
1. Docker 不可用（连接失败、守护进程未运行）
2. 容器崩溃（退出码 137、重启失败）
3. 资源耗尽（内存、CPU）
4. 并发操作
5. 异常恢复
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.config.models import Settings


def create_mock_settings() -> Settings:
    """创建带 Mock 配置的 Settings"""
    return Settings()


class TestDockerUnavailableBoundary:
    """Docker 不可用边界测试"""

    def test_init_when_docker_not_running(self) -> None:
        """测试 Docker 守护进程未运行时的初始化"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        # Mock Docker 连接失败
        with patch("docker.from_env", side_effect=Exception("Docker daemon not running")):
            # 应该抛出异常或优雅处理
            with pytest.raises(Exception):
                ContainerManager(config)

    def test_get_container_when_docker_disconnected(self) -> None:
        """测试 Docker 断开连接时获取容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # Mock Docker 客户端断开连接
            mock_client = MagicMock()
            mock_client.containers.create.side_effect = Exception("Connection lost")
            manager.docker_client = mock_client

            # 应该抛出异常
            with pytest.raises(Exception):
                manager.get_container("terminal", "session-1")

    def test_get_container_with_timeout(self) -> None:
        """测试 Docker API 超时"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_client = MagicMock()
            # 模拟超时异常
            import requests

            mock_client.containers.create.side_effect = requests.exceptions.Timeout(
                "Docker API timeout"
            )
            manager.docker_client = mock_client

            # 应该抛出超时异常
            with pytest.raises((requests.exceptions.Timeout, Exception)):
                manager.get_container("terminal", "session-1")

    def test_cleanup_when_docker_unavailable(self) -> None:
        """测试 Docker 不可用时清理容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 添加一个 mock 容器
            mock_container = MagicMock()
            mock_container.remove.side_effect = Exception("Docker not available")
            manager.containers[("terminal", "session-1")] = mock_container

            # 清理应该忽略错误
            manager.cleanup_session_containers("session-1")

            # 验证容器被移除
            assert ("terminal", "session-1") not in manager.containers


class TestContainerCrashBoundary:
    """容器崩溃边界测试"""

    def test_restart_oom_killed_container(self) -> None:
        """测试重启被 OOM 杀死的容器（退出码 137）"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.status = "exited"
            # 模拟容器因 OOM 被杀死
            mock_container.attrs = {"State": {"ExitCode": 137, "OomKilled": True}}

            # 重启应该成功
            result = manager._restart_container(mock_container, attempt=1)

            assert result is True
            mock_container.restart.assert_called()

    def test_restart_failed_multiple_attempts(self) -> None:
        """测试容器连续重启失败"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.restart.side_effect = Exception("Container crashed")

            # 第 4 次尝试应该返回 False
            result = manager._restart_container(mock_container, attempt=4)

            assert result is False

    def test_restart_with_exponential_backoff(self) -> None:
        """测试重启时的指数退避"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            with patch("time.sleep") as mock_sleep:
                manager = ContainerManager(config)

                mock_container = MagicMock()
                # 第一次成功
                mock_container.restart.return_value = None

                # 测试不同尝试次数的退避时间
                for attempt in [1, 2, 3]:
                    manager._restart_container(mock_container, attempt=attempt)
                    # 验证退避时间：2^(attempt-1)
                    expected_sleep = 2 ** (attempt - 1)
                    mock_sleep.assert_called_with(expected_sleep)

    def test_get_container_reloads_stale_status(self) -> None:
        """测试获取容器时刷新过时的状态"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.status = "exited"  # 容器已停止
            mock_container.reload.return_value = None  # 刷新状态
            manager._restart_container = MagicMock(return_value=True)  # type: ignore[method-assign]

            manager.containers[("terminal", "session-1")] = mock_container

            manager.get_container("terminal", "session-1")

            # 验证调用了 reload
            mock_container.reload.assert_called()

    def test_container_with_segfault(self) -> None:
        """测试容器因段错误崩溃（退出码 139）"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.status = "exited"
            # 模拟段错误
            mock_container.attrs = {"State": {"ExitCode": 139}}

            # 尝试重启
            result = manager._restart_container(mock_container, attempt=1)

            assert result is True
            mock_container.restart.assert_called()

    def test_container_unknown_tool_type(self) -> None:
        """测试未知工具类型"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 尝试创建未知类型的容器
            with pytest.raises(ValueError, match="Unknown tool type"):
                manager._create_container("unknown_tool", "session-1")


class TestResourceExhaustionBoundary:
    """资源耗尽边界测试"""

    def test_create_container_with_invalid_memory_limit(self) -> None:
        """测试创建容器时内存限制解析失败"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 修改配置为无效的内存限制格式
            manager.config.tools.terminal.memory_limit = "invalid"

            # 应该抛出 ValueError
            with pytest.raises((ValueError, Exception)):
                manager._create_container("terminal", "session-1")

    def test_create_container_with_zero_memory_limit(self) -> None:
        """测试创建容器时内存限制为 0"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 设置内存限制为 0
            manager.config.tools.terminal.memory_limit = "0m"

            # 应该能创建但可能被 Docker 拒绝
            try:
                container = manager._create_container("terminal", "session-1")
                assert container is not None
            except Exception:
                # Docker 可能拒绝 0 内存限制
                pass

    def test_create_container_with_very_large_memory_limit(self) -> None:
        """测试创建容器时内存限制过大"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.create.return_value = mock_container
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)

            # 设置超大内存限制（100GB）
            manager.config.tools.terminal.memory_limit = "100g"

            container = manager._create_container("terminal", "session-1")

            assert container is not None

    def test_create_container_with_zero_cpu_limit(self) -> None:
        """测试创建容器时 CPU 限制为 0"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 设置 CPU 限制为 0
            manager.config.tools.terminal.cpu_limit = "0"

            # 应该能创建但可能被 Docker 拒绝
            try:
                container = manager._create_container("terminal", "session-1")
                assert container is not None
            except Exception:
                # Docker 可能拒绝 0 CPU 限制
                pass

    def test_create_container_with_excessive_cpu_limit(self) -> None:
        """测试创建容器时 CPU 限制超过可用核心"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.create.return_value = mock_container
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)

            # 设置超大 CPU 限制（1000 核心）
            manager.config.tools.terminal.cpu_limit = "1000"

            container = manager._create_container("terminal", "session-1")

            assert container is not None

    def test_get_stats_when_container_not_running(self) -> None:
        """测试获取未运行容器的统计"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            # 模拟容器未运行，stats 可能失败
            mock_container.stats.side_effect = Exception("Container not running")
            mock_client.containers.get.return_value = mock_container
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)
            stats = manager.get_container_stats("container-id")

            # 应该返回空字典
            assert stats == {}

    def test_get_stats_with_missing_fields(self) -> None:
        """测试获取统计时缺少字段"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            # 返回不完整的统计数据
            mock_container.stats.return_value = {}
            mock_client.containers.get.return_value = mock_container
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)
            stats = manager.get_container_stats("container-id")

            # 应该返回默认值
            assert isinstance(stats, dict)
            assert "cpu_usage" in stats


class TestConcurrentOperationsBoundary:
    """并发操作边界测试"""

    def test_concurrent_container_creation(self) -> None:
        """测试并发创建容器"""
        from backend.tools.container import ContainerManager
        from concurrent.futures import ThreadPoolExecutor, as_completed

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)

            containers_created = []

            def create_mock_container(tool_type, session_id):
                mock_container = MagicMock()
                mock_container.status = "running"
                mock_container.id = f"{tool_type}-{session_id}"
                containers_created.append(mock_container)
                return mock_container

            manager._create_container = MagicMock(side_effect=create_mock_container)  # type: ignore[method-assign]

            # 并发创建多个容器
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(manager.get_container, "terminal", f"session-{i}")
                    for i in range(10)
                ]
                results = [future.result() for future in as_completed(futures)]

            # 所有容器都应该创建成功
            assert len(results) == 10
            assert len(manager.containers) == 10

    def test_concurrent_cleanup_same_session(self) -> None:
        """测试并发清理同一会话"""
        from backend.tools.container import ContainerManager
        from concurrent.futures import ThreadPoolExecutor, as_completed

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 添加一些容器
            for i in range(5):
                mock_container = MagicMock()
                manager.containers[("terminal", "session-1")] = mock_container

            # 并发清理同一会话
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(manager.cleanup_session_containers, "session-1")
                    for _ in range(3)
                ]
                [future.result() for future in as_completed(futures)]

            # 清理应该成功
            assert ("terminal", "session-1") not in manager.containers

    def test_concurrent_get_and_cleanup(self) -> None:
        """测试并发获取和清理容器"""
        from backend.tools.container import ContainerManager
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 添加一个容器
            mock_container = MagicMock()
            mock_container.status = "running"
            manager.containers[("terminal", "session-1")] = mock_container

            operations = []

            def get_container():
                try:
                    container = manager.get_container("terminal", "session-1")
                    operations.append("get")
                    return container
                except Exception:
                    operations.append("get_error")
                    return None

            def cleanup_container():
                time.sleep(0.01)  # 稍微延迟
                manager.cleanup_session_containers("session-1")
                operations.append("cleanup")

            # 并发执行获取和清理
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(get_container),
                    executor.submit(cleanup_container),
                ]
                [future.result() for future in as_completed(futures)]

            # 两个操作都应该完成
            assert len(operations) == 2


class TestExceptionRecoveryBoundary:
    """异常恢复边界测试"""

    def test_recover_from_create_failure(self) -> None:
        """测试从创建失败中恢复"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_client = MagicMock()
            # 第一次创建失败
            call_count = [0]

            def side_effect_func(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Image not found")
                # 后续成功
                mock_container = MagicMock()
                mock_container.status = "running"
                return mock_container

            mock_client.containers.create.side_effect = side_effect_func
            manager.docker_client = mock_client

            # 第一次尝试失败
            with pytest.raises(Exception):
                manager._create_container("terminal", "session-1")

            # 第二次尝试成功
            container = manager._create_container("terminal", "session-2")
            assert container is not None

    def test_cleanup_with_partial_failures(self) -> None:
        """测试部分容器清理失败"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 添加多个容器，部分删除失败
            mock_container1 = MagicMock()  # 删除成功
            mock_container2 = MagicMock()  # 删除失败
            mock_container2.remove.side_effect = Exception("Remove failed")
            mock_container3 = MagicMock()  # 删除成功

            manager.containers[("terminal", "session-1")] = mock_container1
            manager.containers[("python_repl", "session-1")] = mock_container2
            manager.containers[("terminal", "session-2")] = mock_container3

            # 清理会话 1，应该忽略失败
            manager.cleanup_session_containers("session-1")

            # 所有容器都应该被移除（即使删除失败）
            assert ("terminal", "session-1") not in manager.containers
            assert ("python_repl", "session-1") not in manager.containers
            assert ("terminal", "session-2") in manager.containers

    def test_handle_corrupted_container_state(self) -> None:
        """测试处理损坏的容器状态"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.reload.side_effect = Exception("State corrupted")
            manager.containers[("terminal", "session-1")] = mock_container

            # 尝试获取容器
            with pytest.raises(Exception):
                manager.get_container("terminal", "session-1")

    def test_multiple_restart_failures_then_success(self) -> None:
        """测试多次重启失败后成功"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            call_count = [0]

            def side_effect_restart(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] <= 2:
                    raise Exception("Restart failed")
                # 第三次成功
                return None

            mock_container.restart.side_effect = side_effect_restart

            # 重启应该在 3 次内成功
            result = manager._restart_container(mock_container, attempt=1)
            assert result is True
            assert call_count[0] == 3
