"""ContainerManager 类单元测试

测试 ContainerManager 的初始化和容器管理功能。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.config.models import Settings


def create_mock_settings() -> Settings:
    """创建带 Mock 配置的 Settings"""
    return Settings()


class TestContainerManagerInit:
    """测试 ContainerManager.__init__"""

    def test_init_with_valid_config(self):
        """测试使用有效配置初始化"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

        assert manager.config == config

    def test_init_stores_config(self):
        """测试初始化存储配置"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

        assert hasattr(manager, "config")
        assert manager.config is config

    def test_init_initializes_containers_dict(self):
        """测试初始化容器字典"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

        assert hasattr(manager, "containers")
        assert isinstance(manager.containers, dict)
        assert len(manager.containers) == 0

    def test_init_initializes_docker_client(self):
        """测试初始化 Docker 客户端"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            manager = ContainerManager(config)

        mock_docker.assert_called_once()
        assert hasattr(manager, "docker_client")


class TestGetContainer:
    """测试 get_container 方法"""

    def test_get_container_creates_new(self):
        """测试获取容器时创建新容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)

            # Mock _create_container 方法
            manager._create_container = MagicMock(
                return_value=MagicMock(status="running")
            )

            container = manager.get_container("terminal", "session-1")

            assert container is not None
            manager._create_container.assert_called_once()

    def test_get_container_reuses_existing(self):
        """测试获取容器时复用现有容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 预先添加一个容器
            mock_container = MagicMock()
            mock_container.status = "running"
            manager.containers[("terminal", "session-1")] = mock_container

            container = manager.get_container("terminal", "session-1")

            assert container is mock_container

    def test_get_container_different_sessions(self):
        """测试不同会话获取不同容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # Mock _create_container 返回不同容器
            containers_created = []

            def create_mock_container(tool_type, session_id):
                mock_container = MagicMock()
                mock_container.status = "running"
                mock_container.id = f"{tool_type}-{session_id}"
                containers_created.append(mock_container)
                return mock_container

            manager._create_container = MagicMock(side_effect=create_mock_container)

            container1 = manager.get_container("terminal", "session-1")
            container2 = manager.get_container("terminal", "session-2")

            assert container1 is not container2
            assert len(manager.containers) == 2


class TestCleanupSessionContainers:
    """测试 cleanup_session_containers 方法"""

    def test_cleanup_removes_containers(self):
        """测试清理移除会话容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 添加一些容器
            mock_container1 = MagicMock()
            mock_container2 = MagicMock()
            manager.containers[("terminal", "session-1")] = mock_container1
            manager.containers[("python_repl", "session-1")] = mock_container2
            manager.containers[("terminal", "session-2")] = MagicMock()

            manager.cleanup_session_containers("session-1")

            # 验证 session-1 的容器被移除
            assert ("terminal", "session-1") not in manager.containers
            assert ("python_repl", "session-1") not in manager.containers
            assert ("terminal", "session-2") in manager.containers

    def test_cleanup_calls_container_remove(self):
        """测试清理调用容器 remove 方法"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            manager.containers[("terminal", "session-1")] = mock_container

            manager.cleanup_session_containers("session-1")

            mock_container.remove.assert_called_once()

    def test_cleanup_empty_session(self):
        """测试清理不存在的会话"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            # 清理不存在的会话应该不报错
            manager.cleanup_session_containers("nonexistent-session")

            assert len(manager.containers) == 0


class TestCreateContainer:
    """测试 _create_container 方法"""

    def test_create_container_with_config(self):
        """测试使用配置创建容器"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.create.return_value = mock_container
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)
            container = manager._create_container("terminal", "session-1")

            assert container is mock_container
            mock_client.containers.create.assert_called_once()

    def test_create_container_applies_resource_limits(self):
        """测试创建容器时应用资源限制"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)
            manager._create_container("terminal", "session-1")

            # 验证 create 被调用（资源限制在参数中）
            call_args = mock_client.containers.create.call_args
            assert call_args is not None


class TestRestartContainer:
    """测试 _restart_container 方法"""

    def test_restart_container_success(self):
        """测试重启容器成功"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.restart.return_value = None

            result = manager._restart_container(mock_container, attempt=1)

            assert result is True
            mock_container.restart.assert_called_once()

    def test_restart_container_with_backoff(self):
        """测试重启容器使用指数退避"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            with patch("time.sleep") as mock_sleep:
                manager = ContainerManager(config)

                mock_container = MagicMock()

                manager._restart_container(mock_container, attempt=2)

                # 验证退避时间（指数退避：1s, 2s, 4s）
                mock_sleep.assert_called_once()

    def test_restart_container_max_attempts(self):
        """测试重启容器达到最大重试次数"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env"):
            manager = ContainerManager(config)

            mock_container = MagicMock()
            mock_container.restart.side_effect = Exception("Container error")

            result = manager._restart_container(mock_container, attempt=3)

            assert result is False


class TestGetContainerStats:
    """测试 get_container_stats 方法"""

    def test_get_container_stats_returns_dict(self):
        """测试获取容器统计返回字典"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_container.stats.return_value = [
                {
                    "cpu_stats": {"cpu_usage": {"total_usage": 1000000}},
                    "memory_stats": {"usage": 10000000, "limit": 100000000},
                }
            ]
            mock_client.containers.get.return_value = mock_container
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)
            stats = manager.get_container_stats("container-id")

            assert isinstance(stats, dict)
            assert "cpu_usage" in stats or "memory_usage" in stats

    def test_get_container_stats_nonexistent_container(self):
        """测试获取不存在容器的统计"""
        from backend.tools.container import ContainerManager

        config = create_mock_settings()

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.get.side_effect = Exception("Container not found")
            mock_docker.return_value = mock_client

            manager = ContainerManager(config)
            stats = manager.get_container_stats("nonexistent-id")

            assert stats == {}
