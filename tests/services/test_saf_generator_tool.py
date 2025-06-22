"""
Tests for SAF Generator Tool - comprehensive unit and integration tests.
"""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client

from agents.saf_stig_generator.services.saf_generator.tool import (
    generate_saf_stub,
)
from agents.saf_stig_generator.services.saf_generator.tool import (
    mcp as saf_generator_server,
)


class TestSafGeneratorTool:
    """Unit tests for SAF generator tool functionality."""

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.saf_generator.tool.subprocess.run")
    async def test_generate_saf_stub_success(self, mock_subprocess, mock_context):
        """Test successful SAF stub generation."""
        # Mock successful saf generate command
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Successfully generated profile stub"
        mock_subprocess.return_value.stderr = ""

        result_str = await generate_saf_stub(
            "/path/to/xccdf.xml", "/output/dir", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert "path" in result["data"]
        assert result["data"]["path"] == "/output/dir"
        mock_context.info.assert_any_call("Successfully generated SAF stub profile")

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.saf_generator.tool.subprocess.run")
    async def test_generate_saf_stub_command_failure(
        self, mock_subprocess, mock_context
    ):
        """Test handling of saf command failures."""
        # Mock failed saf command
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = "Error: Invalid XCCDF file"

        result_str = await generate_saf_stub(
            "/path/to/invalid.xml", "/output/dir", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Failed to generate SAF stub" in result["message"]
        assert "Error: Invalid XCCDF file" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.saf_generator.tool.subprocess.run")
    async def test_generate_saf_stub_file_not_found(
        self, mock_subprocess, mock_context
    ):
        """Test handling when XCCDF file doesn't exist."""
        # Mock FileNotFoundError when trying to access non-existent file
        mock_subprocess.side_effect = FileNotFoundError("No such file or directory")

        result_str = await generate_saf_stub(
            "/nonexistent/file.xml", "/output/dir", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "No such file or directory" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.saf_generator.tool.subprocess.run")
    async def test_generate_saf_stub_timeout(self, mock_subprocess, mock_context):
        """Test handling of command timeout."""
        import subprocess

        # Mock timeout error
        mock_subprocess.side_effect = subprocess.TimeoutExpired("saf", 30)

        result_str = await generate_saf_stub(
            "/path/to/large.xml", "/output/dir", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Command timed out" in result["message"]


class TestSafGeneratorToolIntegration:
    """Integration tests for SAF generator tool using FastMCP Client."""

    @pytest.fixture
    def mcp_server(self):
        """Provide the SAF generator MCP server for testing."""
        return saf_generator_server

    @pytest.mark.asyncio
    async def test_tool_via_mcp_client(self, mcp_server, temp_artifacts_dir):
        """Test the tool through MCP client interface."""
        with patch(
            "agents.saf_stig_generator.services.saf_generator.tool.subprocess.run"
        ) as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "Profile generated successfully"
            mock_subprocess.return_value.stderr = ""

            async with Client(mcp_server) as client:
                result_content, _ = await client.call_tool(
                    "generate_saf_stub",
                    {
                        "xccdf_path": "/test/path.xml",
                        "output_dir": str(temp_artifacts_dir),
                    },
                )
                result = json.loads(result_content.text)

                assert result["status"] == "success"
                assert "path" in result["data"]

    @pytest.mark.asyncio
    async def test_tool_resources(self, mcp_server):
        """Test tool resources are accessible."""
        async with Client(mcp_server) as client:
            # Test version resource
            version_result = await client.read_resource("saf-generator-tool://version")
            assert "SAF Generator Tool v" in version_result.text

            # Test info resource
            info_result = await client.read_resource("saf-generator-tool://info")
            info_data = json.loads(info_result.text)
            assert info_data["name"] == "SAF Generator Tool"
