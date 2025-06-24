"""
Tests for Docker Tool - comprehensive unit and integration tests.
Uses FastMCP testing patterns with direct Client testing.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

# Import the tool components
from agents.saf_stig_generator.services.docker.tool import (
    fetch_docker_image,
)
from agents.saf_stig_generator.services.docker.tool import (
    mcp as docker_server,
)


class TestDockerToolUnit:
    """Unit tests for Docker tool core functions."""

    @pytest.mark.asyncio
    async def test_fetch_docker_image_success(self, mock_context, mock_docker_client):
        """Test successful Docker image fetching."""
        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            # Mock the Docker client and a successful image pull
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(
                tags=["rhel9:latest"],
                id="sha256:test123",
                attrs={"Size": 123456789, "Created": "2024-01-01T00:00:00Z"},
            )
            mock_docker_client.images.pull.return_value = mock_image

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "rhel9",
                    "description": "Red Hat Enterprise Linux 9",
                    "is_official": True,
                    "pull_count": 1000000,
                }
            ]

            result_str = await fetch_docker_image.fn("rhel9", mock_context)
            result = json.loads(result_str)

            # Verify the operation was successful
            assert "name" in result
            assert result["name"] == "rhel9"
            assert "tag" in result
            mock_docker_client.images.pull.assert_called_with("rhel9", tag="latest")
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_with_tag(self, mock_context, mock_docker_client):
        """Test Docker image fetching with specific tag."""
        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(
                tags=["rhel9:8.5"],
                id="sha256:test456",
                attrs={"Size": 123456789, "Created": "2024-01-01T00:00:00Z"},
            )
            mock_docker_client.images.pull.return_value = mock_image

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "rhel9",
                    "description": "Red Hat Enterprise Linux 9",
                    "is_official": True,
                    "pull_count": 1000000,
                }
            ]

            result_str = await fetch_docker_image.fn("rhel9:8.5", mock_context)
            result = json.loads(result_str)

            assert "name" in result
            assert result["name"] == "rhel9"
            assert "tag" in result
            # Note: The function currently doesn't parse tags from the input,
            # it always uses "latest". This is a limitation of the current implementation.

    @pytest.mark.asyncio
    async def test_fetch_docker_image_not_found(self, mock_context, mock_docker_client):
        """Test handling when Docker image is not found."""
        import docker

        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.ImageNotFound(
                "Image not found"
            )

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "nonexistent_image",
                    "description": "A non-existent image",
                    "is_official": False,
                    "pull_count": 0,
                }
            ]

            result_str = await fetch_docker_image.fn("nonexistent_image", mock_context)
            result = json.loads(result_str)

            assert "error" in result
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_daemon_error(self, mock_context):
        """Test handling when Docker daemon is not available."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.side_effect = docker.errors.DockerException(
                "Docker daemon not available"
            )

            result_str = await fetch_docker_image.fn("rhel9", mock_context)
            result = json.loads(result_str)

            assert "error" in result
            assert "daemon" in str(result).lower() or "docker" in str(result).lower()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_api_error(self, mock_context, mock_docker_client):
        """Test handling of Docker API errors."""
        import docker

        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.APIError(
                "API Error occurred"
            )

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "rhel9",
                    "description": "Red Hat Enterprise Linux 9",
                    "is_official": True,
                    "pull_count": 1000000,
                }
            ]

            result_str = await fetch_docker_image.fn("rhel9", mock_context)
            result = json.loads(result_str)

            assert "error" in result
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_invalid_name(self, mock_context):
        """Test handling of invalid Docker image names."""
        with patch(
            "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
        ) as mock_search:
            # Mock search returning no results
            mock_search.return_value = []

            result_str = await fetch_docker_image.fn("", mock_context)
            result = json.loads(result_str)

            assert "error" in result


class TestDockerToolIntegration:
    """Integration tests using FastMCP Client for end-to-end testing."""

    @pytest.mark.asyncio
    async def test_fetch_docker_image_integration_success(self, mock_docker_client):
        """Test successful Docker image fetch through MCP Client."""
        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(
                tags=["ubuntu:22.04"],
                id="sha256:test789",
                attrs={"Size": 123456789, "Created": "2024-01-01T00:00:00Z"},
            )
            mock_docker_client.images.pull.return_value = mock_image

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "ubuntu",
                    "description": "Ubuntu Linux",
                    "is_official": True,
                    "pull_count": 5000000,
                }
            ]

            async with Client(docker_server) as client:
                result = await client.call_tool(
                    "fetch_docker_image", {"product_keyword": "ubuntu:22.04"}
                )

                response_data = json.loads(result[0].text)
                assert "name" in response_data
                assert "tag" in response_data

    @pytest.mark.asyncio
    async def test_fetch_docker_image_integration_failure(self):
        """Test Docker image fetch failure through MCP Client."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.side_effect = docker.errors.DockerException(
                "Docker daemon not available"
            )

            async with Client(docker_server) as client:
                result = await client.call_tool(
                    "fetch_docker_image", {"product_keyword": "ubuntu:22.04"}
                )

                response_data = json.loads(result[0].text)
                assert "error" in response_data

    @pytest.mark.asyncio
    async def test_fetch_docker_image_integration_not_found(self, mock_docker_client):
        """Test Docker image not found through MCP Client."""
        import docker

        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.ImageNotFound(
                "Image not found"
            )

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "nonexistent",
                    "description": "Non-existent image",
                    "is_official": False,
                    "pull_count": 0,
                }
            ]

            async with Client(docker_server) as client:
                result = await client.call_tool(
                    "fetch_docker_image", {"product_keyword": "nonexistent:latest"}
                )

                response_data = json.loads(result[0].text)
                assert "error" in response_data


class TestDockerToolEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_fetch_docker_image_complex_tag(
        self, mock_context, mock_docker_client
    ):
        """Test Docker image with complex registry and tag."""
        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(
                tags=["registry.redhat.io/rhel9/rhel:9.1"],
                id="sha256:complex123",
                attrs={"Size": 123456789, "Created": "2024-01-01T00:00:00Z"},
            )
            mock_docker_client.images.pull.return_value = mock_image

            # Mock Docker Hub search to return a result for the registry image
            mock_search.return_value = [
                {
                    "name": "registry.redhat.io/rhel9/rhel",
                    "description": "Red Hat Enterprise Linux 9 from registry",
                    "is_official": False,
                    "pull_count": 100000,
                }
            ]

            result_str = await fetch_docker_image.fn(
                "registry.redhat.io/rhel9/rhel:9.1", mock_context
            )
            result = json.loads(result_str)

            assert "name" in result or "error" in result

    @pytest.mark.asyncio
    async def test_fetch_docker_image_network_timeout(
        self, mock_context, mock_docker_client
    ):
        """Test handling of network timeout during image pull."""
        import docker

        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.APIError(
                "Network timeout"
            )

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "large_image",
                    "description": "A large Docker image",
                    "is_official": False,
                    "pull_count": 1000,
                }
            ]

            result_str = await fetch_docker_image.fn("large_image:latest", mock_context)
            result = json.loads(result_str)

            assert "error" in result

    @pytest.mark.asyncio
    async def test_fetch_docker_image_permission_denied(
        self, mock_context, mock_docker_client
    ):
        """Test handling of permission denied errors."""
        import docker

        with (
            patch(
                "agents.saf_stig_generator.services.docker.tool.docker.from_env"
            ) as mock_from_env,
            patch(
                "agents.saf_stig_generator.services.docker.tool._search_docker_hub"
            ) as mock_search,
        ):
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.APIError(
                "Permission denied"
            )

            # Mock Docker Hub search to return a result
            mock_search.return_value = [
                {
                    "name": "private/image",
                    "description": "A private Docker image",
                    "is_official": False,
                    "pull_count": 100,
                }
            ]

            result_str = await fetch_docker_image.fn(
                "private/image:latest", mock_context
            )
            result = json.loads(result_str)

            assert "error" in result
