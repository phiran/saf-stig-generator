"""
Tests for MITRE Baseline Tool - comprehensive unit and integration tests.
"""

import json
from unittest.mock import patch

import pytest
import respx
from fastmcp import Client

from agents.saf_stig_generator.services.mitre_baseline.tool import (
    find_mitre_baseline,
    search_github_for_baseline,
)
from agents.saf_stig_generator.services.mitre_baseline.tool import (
    mcp as mitre_baseline_server,
)


class TestMitreBaselineTool:
    """Unit tests for MITRE baseline tool functionality."""

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.mitre_baseline.tool.subprocess.run")
    async def test_find_mitre_baseline_success(self, mock_subprocess, mock_context):
        """Test successful baseline cloning."""
        # Mock successful git clone
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Cloning into repository..."
        mock_subprocess.return_value.stderr = ""

        result_str = await find_mitre_baseline(
            "Red Hat Enterprise Linux 9", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert "path" in result["data"]
        assert "redhat-enterprise-linux-9-stig-baseline" in result["data"]["path"]
        mock_context.info.assert_any_call("Successfully cloned baseline repository")

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.mitre_baseline.tool.subprocess.run")
    async def test_find_mitre_baseline_clone_failure(
        self, mock_subprocess, mock_context
    ):
        """Test handling of git clone failures."""
        # Mock failed git clone
        mock_subprocess.return_value.returncode = 128
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = "Repository not found"

        result_str = await find_mitre_baseline("NonExistent Product", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "could not be found or cloned" in result["message"]

    @pytest.mark.asyncio
    async def test_search_github_for_baseline_success(
        self, mock_context, mock_github_api_response
    ):
        """Test successful GitHub API search."""
        async with respx.mock:
            respx.get("https://api.github.com/search/repositories").respond(
                200, json=mock_github_api_response
            )

            result_str = await search_github_for_baseline("RHEL 9", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "success"
            assert len(result["data"]["repositories"]) == 1
            assert (
                "redhat-enterprise-linux-9-stig-baseline"
                in result["data"]["repositories"][0]["name"]
            )

    @pytest.mark.asyncio
    async def test_search_github_for_baseline_no_results(self, mock_context):
        """Test GitHub search with no results."""
        async with respx.mock:
            respx.get("https://api.github.com/search/repositories").respond(
                200, json={"items": []}
            )

            result_str = await search_github_for_baseline(
                "Unknown Product", mock_context
            )
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "No MITRE baselines found" in result["message"]

    @pytest.mark.asyncio
    async def test_search_github_api_error(self, mock_context):
        """Test GitHub API error handling."""
        async with respx.mock:
            respx.get("https://api.github.com/search/repositories").respond(403)

            result_str = await search_github_for_baseline("RHEL 9", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "GitHub API error" in result["message"]


class TestMitreBaselineToolIntegration:
    """Integration tests for MITRE baseline tool using FastMCP Client."""

    @pytest.fixture
    def mcp_server(self):
        """Provide the MITRE baseline MCP server for testing."""
        return mitre_baseline_server

    @pytest.mark.asyncio
    async def test_tool_via_mcp_client(self, mcp_server, temp_artifacts_dir):
        """Test the tool through MCP client interface."""
        with patch(
            "agents.saf_stig_generator.services.mitre_baseline.tool.subprocess.run"
        ) as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "Cloning..."
            mock_subprocess.return_value.stderr = ""

            async with Client(mcp_server) as client:
                result_content, _ = await client.call_tool(
                    "find_mitre_baseline", {"product_name": "RHEL 9"}
                )
                result = json.loads(result_content.text)

                assert result["status"] == "success"
                assert "path" in result["data"]

    @pytest.mark.asyncio
    async def test_tool_resources(self, mcp_server):
        """Test tool resources are accessible."""
        async with Client(mcp_server) as client:
            # Test version resource
            version_result = await client.read_resource("mitre-baseline-tool://version")
            assert "MITRE Baseline Tool v" in version_result.text

            # Test info resource
            info_result = await client.read_resource("mitre-baseline-tool://info")
            info_data = json.loads(info_result.text)
            assert info_data["name"] == "MITRE Baseline Tool"
