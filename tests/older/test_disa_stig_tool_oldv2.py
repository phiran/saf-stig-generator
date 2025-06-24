"""
Tests for DISA STIG Tool - comprehensive unit and integration tests.
"""

import json
from unittest.mock import patch

import pytest
import respx
from fastmcp import Client

# Import the tool components
from agents.saf_stig_generator.services.disa_stig.tool import (
    fetch_disa_stig,
    fetch_disa_stig_with_cli_keyword,
)
from agents.saf_stig_generator.services.disa_stig.tool import (
    mcp as disa_stig_server,
)


class TestDisaStigTool:
    """Unit tests for DISA STIG tool functionality."""

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile")
    @patch("agents.saf_stig_generator.services.disa_stig.tool.os.walk")
    @patch("agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync")
    async def test_fetch_disa_stig_success(
        self,
        mock_run_sync,
        mock_os_walk,
        mock_zipfile,
        mock_context,
        disa_downloads_page,
    ):
        """Test successful STIG download and extraction."""
        # Mock filesystem interactions
        mock_os_walk.return_value = [
            (
                "/fake/path",
                [],
                [
                    "U_RHEL_9_V1R1_STIG_Manual-xccdf.xml",
                    "U_RHEL_9_V1R1_STIG_Manual.xml",
                ],
            )
        ]

        # Mock network calls
        async with respx.mock:
            respx.get("https://public.cyber.mil/stigs/downloads/").respond(
                200, html=disa_downloads_page
            )
            respx.get(
                "https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip"
            ).respond(200, content=b"fake_zip_content")

            # Execute the test
            result_str = await fetch_disa_stig("RHEL 9", mock_context)
            result = json.loads(result_str)

            # Assertions
            assert result["status"] == "success"
            assert "xccdf_path" in result["data"]
            assert "manual_path" in result["data"]
            assert result["data"]["xccdf_path"].endswith("_Manual-xccdf.xml")

            # Verify logging
            mock_context.info.assert_any_call("Searching for STIG matching: RHEL 9")

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_not_found(self, mock_context, empty_disa_page):
        """Test handling when STIG is not found."""
        async with respx.mock:
            respx.get("https://public.cyber.mil/stigs/downloads/").respond(
                200, html=empty_disa_page
            )

            result_str = await fetch_disa_stig("NonExistent STIG", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "Could not find a STIG zip file" in result["message"]
            mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_network_error(self, mock_context):
        """Test handling of network errors."""
        async with respx.mock:
            respx.get("https://public.cyber.mil/stigs/downloads/").respond(500)

            result_str = await fetch_disa_stig("RHEL 9", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "Network error during download" in result["message"]

    @pytest.mark.asyncio
    @patch(
        "agents.saf_stig_generator.services.disa_stig.tool.CLI_PRODUCT_KEYWORD",
        "RHEL 9",
    )
    async def test_fetch_with_cli_keyword_success(self, mock_context):
        """Test CLI keyword functionality."""
        with patch(
            "agents.saf_stig_generator.services.disa_stig.tool.fetch_disa_stig"
        ) as mock_fetch:
            mock_fetch.return_value = '{"status": "success"}'

            result = await fetch_disa_stig_with_cli_keyword(mock_context)

            mock_fetch.assert_called_once_with("RHEL 9", mock_context)

    @pytest.mark.asyncio
    @patch(
        "agents.saf_stig_generator.services.disa_stig.tool.CLI_PRODUCT_KEYWORD", None
    )
    async def test_fetch_with_cli_keyword_no_keyword(self, mock_context):
        """Test CLI keyword functionality when no keyword provided."""
        result_str = await fetch_disa_stig_with_cli_keyword(mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "No product keyword was provided via CLI" in result["message"]


class TestDisaStigToolIntegration:
    """Integration tests for DISA STIG tool using FastMCP Client."""

    @pytest.fixture
    def mcp_server(self):
        """Provide the DISA STIG MCP server for testing."""
        return disa_stig_server

    @pytest.mark.asyncio
    async def test_tool_via_mcp_client(
        self, mcp_server, disa_downloads_page, temp_artifacts_dir
    ):
        """Test the tool through MCP client interface."""
        # Mock filesystem and network operations
        with (
            patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile"),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.os.walk"
            ) as mock_walk,
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ),
        ):
            mock_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            async with respx.mock:
                respx.get("https://public.cyber.mil/stigs/downloads/").respond(
                    200, html=disa_downloads_page
                )
                respx.get(
                    "https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip"
                ).respond(200, content=b"fake_zip_content")

                async with Client(mcp_server) as client:
                    result_content, _ = await client.call_tool(
                        "fetch_disa_stig", {"product_keyword": "RHEL 9"}
                    )
                    result = json.loads(result_content.text)

                    assert result["status"] == "success"
                    assert result["data"]["xccdf_path"].endswith("_Manual-xccdf.xml")

    @pytest.mark.asyncio
    async def test_tool_resources(self, mcp_server):
        """Test tool resources are accessible."""
        async with Client(mcp_server) as client:
            # Test version resource
            version_result = await client.read_resource("disa-stig-tool://version")
            assert "DISA STIG Tool v" in version_result.text

            # Test info resource
            info_result = await client.read_resource("disa-stig-tool://info")
            info_data = json.loads(info_result.text)
            assert info_data["name"] == "DISA STIG Tool"
            assert "version" in info_data


class TestDisaStigToolCLI:
    """Test CLI functionality of the DISA STIG tool."""

    def test_cli_help_displays_correctly(self):
        """Test that CLI help information is formatted correctly."""
        # This would test the help text formatting
        pass

    @patch("agents.saf_stig_generator.services.disa_stig.tool.mcp.run")
    def test_cli_stdio_transport(self, mock_run):
        """Test CLI with stdio transport."""
        # Mock CLI arguments
        import sys
        from unittest.mock import patch

        with patch.object(sys, "argv", ["tool.py", "--stdio"]):
            # This would test CLI parsing and transport selection
            pass

    @patch("agents.saf_stig_generator.services.disa_stig.tool.mcp.run")
    def test_cli_with_keyword(self, mock_run):
        """Test CLI with product keyword."""
        # Mock CLI arguments
        import sys
        from unittest.mock import patch

        with patch.object(sys, "argv", ["tool.py", "--keyword", "RHEL 9"]):
            # This would test keyword setting
            pass
