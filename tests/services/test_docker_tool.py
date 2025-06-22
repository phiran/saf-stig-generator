"""
Tests for Docker Tool - comprehensive unit and integration tests.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

from agents.saf_stig_generator.services.docker.tool import (
    fetch_docker_image,
    search_docker_images,
)
from agents.saf_stig_generator.services.docker.tool import (
    mcp as docker_server,
)


class TestDockerTool:
    """Unit tests for Docker tool functionality."""

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.docker.tool.docker.from_env")
    async def test_fetch_docker_image_success(self, mock_docker_env, mock_context):
        """Test successful Docker image fetching."""
        # Mock Docker client
        mock_client = MagicMock()
        mock_docker_env.return_value = mock_client

        # Mock successful image pull
        mock_image = MagicMock()
        mock_image.tags = ["rhel9:latest"]
        mock_client.images.pull.return_value = mock_image

        result_str = await fetch_docker_image("rhel9", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert "image_name" in result["data"]
        assert result["data"]["image_name"] == "rhel9:latest"
        mock_client.images.pull.assert_called_with("rhel9")

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.docker.tool.docker.from_env")
    async def test_fetch_docker_image_not_found(self, mock_docker_env, mock_context):
        """Test handling when Docker image is not found."""
        import docker

        # Mock Docker client
        mock_client = MagicMock()
        mock_docker_env.return_value = mock_client

        # Mock image not found error
        mock_client.images.pull.side_effect = docker.errors.ImageNotFound(
            "Image not found"
        )

        result_str = await fetch_docker_image("nonexistent_image", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Image not found" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.docker.tool.docker.from_env")
    async def test_fetch_docker_image_api_error(self, mock_docker_env, mock_context):
        """Test handling of Docker API errors."""
        import docker

        # Mock Docker client
        mock_client = MagicMock()
        mock_docker_env.return_value = mock_client

        # Mock API error
        mock_client.images.pull.side_effect = docker.errors.APIError("API Error")

        result_str = await fetch_docker_image("test_image", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Docker API error" in result["message"]

    @pytest.mark.asyncio
    async def test_search_docker_images_success(self, mock_context):
        """Test successful Docker Hub search."""
        # Mock the Docker Hub API response
        mock_response_data = {
            "results": [
                {
                    "name": "rhel9",
                    "description": "Red Hat Enterprise Linux 9 base image",
                    "star_count": 100,
                    "is_official": True,
                },
                {
                    "name": "centos/rhel9",
                    "description": "CentOS-based RHEL 9 image",
                    "star_count": 50,
                    "is_official": False,
                },
            ]
        }

        import respx

        async with respx.mock:
            respx.get("https://hub.docker.com/v2/search/repositories/").respond(
                200, json=mock_response_data
            )

            result_str = await search_docker_images("rhel9", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "success"
            assert len(result["data"]["images"]) == 2
            assert result["data"]["images"][0]["name"] == "rhel9"

    @pytest.mark.asyncio
    async def test_search_docker_images_no_results(self, mock_context):
        """Test Docker Hub search with no results."""
        import respx

        async with respx.mock:
            respx.get("https://hub.docker.com/v2/search/repositories/").respond(
                200, json={"results": []}
            )

            result_str = await search_docker_images("nonexistent", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "No Docker images found" in result["message"]


class TestDockerToolIntegration:
    """Integration tests for Docker tool using FastMCP Client."""

    @pytest.fixture
    def mcp_server(self):
        """Provide the Docker MCP server for testing."""
        return docker_server

    @pytest.mark.asyncio
    async def test_tool_via_mcp_client(self, mcp_server):
        """Test the tool through MCP client interface."""
        with patch(
            "agents.saf_stig_generator.services.docker.tool.docker.from_env"
        ) as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            mock_image = MagicMock()
            mock_image.tags = ["test:latest"]
            mock_client.images.pull.return_value = mock_image

            async with Client(mcp_server) as client:
                result_content, _ = await client.call_tool(
                    "fetch_docker_image", {"image_name": "test"}
                )
                result = json.loads(result_content.text)

                assert result["status"] == "success"
                assert "image_name" in result["data"]

    @pytest.mark.asyncio
    async def test_tool_resources(self, mcp_server):
        """Test tool resources are accessible."""
        async with Client(mcp_server) as client:
            # Test version resource
            version_result = await client.read_resource("docker-tool://version")
            assert "Docker Tool v" in version_result.text

            # Test info resource
            info_result = await client.read_resource("docker-tool://info")
            info_data = json.loads(info_result.text)
            assert info_data["name"] == "Docker Tool"
