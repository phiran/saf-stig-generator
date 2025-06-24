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
        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            # Mock the Docker client and a successful image pull
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(tags=["rhel9:latest"])
            mock_docker_client.images.pull.return_value = mock_image

            result_str = await fetch_docker_image("rhel9", mock_context)
            result = json.loads(result_str)

            # Verify the operation was successful
            assert result.get("status") == "success" or "data" in result
            mock_docker_client.images.pull.assert_called_with("rhel9", tag="latest")
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_with_tag(self, mock_context, mock_docker_client):
        """Test Docker image fetching with specific tag."""
        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(tags=["rhel9:8.5"])
            mock_docker_client.images.pull.return_value = mock_image

            result_str = await fetch_docker_image("rhel9:8.5", mock_context)
            result = json.loads(result_str)

            assert result.get("status") == "success" or "data" in result
            mock_docker_client.images.pull.assert_called_with("rhel9", tag="8.5")

    @pytest.mark.asyncio
    async def test_fetch_docker_image_not_found(self, mock_context, mock_docker_client):
        """Test handling when Docker image is not found."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.ImageNotFound(
                "Image not found"
            )

            result_str = await fetch_docker_image("nonexistent_image", mock_context)
            result = json.loads(result_str)

            assert "error" in result or result.get("status") == "failure"
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

            result_str = await fetch_docker_image("rhel9", mock_context)
            result = json.loads(result_str)

            assert "error" in result or result.get("status") == "failure"
            assert "daemon" in str(result).lower() or "docker" in str(result).lower()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_api_error(self, mock_context, mock_docker_client):
        """Test handling of Docker API errors."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.APIError(
                "API Error occurred"
            )

            result_str = await fetch_docker_image("rhel9", mock_context)
            result = json.loads(result_str)

            assert "error" in result or result.get("status") == "failure"
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_docker_image_invalid_name(self, mock_context):
        """Test handling of invalid Docker image names."""
        result_str = await fetch_docker_image("", mock_context)
        result = json.loads(result_str)

        assert "error" in result or result.get("status") == "failure"


class TestDockerToolIntegration:
    """Integration tests using FastMCP Client for end-to-end testing."""

    @pytest.mark.asyncio
    async def test_fetch_docker_image_integration_success(self, mock_docker_client):
        """Test successful Docker image fetch through MCP Client."""
        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(tags=["ubuntu:22.04"])
            mock_docker_client.images.pull.return_value = mock_image

            async with Client(docker_server) as client:
                result = await client.call_tool(
                    "fetch_docker_image", {"image_name": "ubuntu:22.04"}
                )

                response_data = json.loads(result[0].text)
                assert (
                    response_data.get("status") == "success"
                    or "data" in response_data
                    or "image" in response_data
                )

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
                    "fetch_docker_image", {"image_name": "ubuntu:22.04"}
                )

                response_data = json.loads(result[0].text)
                assert (
                    "error" in response_data or response_data.get("status") == "failure"
                )

    @pytest.mark.asyncio
    async def test_fetch_docker_image_integration_not_found(self, mock_docker_client):
        """Test Docker image not found through MCP Client."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.ImageNotFound(
                "Image not found"
            )

            async with Client(docker_server) as client:
                result = await client.call_tool(
                    "fetch_docker_image", {"image_name": "nonexistent:latest"}
                )

                response_data = json.loads(result[0].text)
                assert (
                    "error" in response_data or response_data.get("status") == "failure"
                )


class TestDockerToolEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_fetch_docker_image_complex_tag(
        self, mock_context, mock_docker_client
    ):
        """Test Docker image with complex registry and tag."""
        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_image = MagicMock(tags=["registry.redhat.io/rhel9/rhel:9.1"])
            mock_docker_client.images.pull.return_value = mock_image

            result_str = await fetch_docker_image(
                "registry.redhat.io/rhel9/rhel:9.1", mock_context
            )
            result = json.loads(result_str)

            assert result.get("status") == "success" or "data" in result

    @pytest.mark.asyncio
    async def test_fetch_docker_image_network_timeout(
        self, mock_context, mock_docker_client
    ):
        """Test handling of network timeout during image pull."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.APIError(
                "Network timeout"
            )

            result_str = await fetch_docker_image("large_image:latest", mock_context)
            result = json.loads(result_str)

            assert "error" in result or result.get("status") == "failure"

    @pytest.mark.asyncio
    async def test_fetch_docker_image_permission_denied(
        self, mock_context, mock_docker_client
    ):
        """Test handling of permission denied errors."""
        import docker

        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_from_env:
            mock_from_env.return_value = mock_docker_client
            mock_docker_client.ping.return_value = True
            mock_docker_client.images.pull.side_effect = docker.errors.APIError(
                "Permission denied"
            )

            result_str = await fetch_docker_image("private/image:latest", mock_context)
            result = json.loads(result_str)

            assert "error" in result or result.get("status") == "failure"
