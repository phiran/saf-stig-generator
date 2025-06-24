"""
Tests for DISA STIG Tool - comprehensive unit and integration tests.
Uses FastMCP testing patterns with direct Client testing and respx for HTTP mocking.
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


class TestDisaStigToolUnit:
    """Unit tests for DISA STIG tool core functions."""

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_success(
        self, mock_context, disa_downloads_page, mock_http_api
    ):
        """Test successful STIG download and extraction."""
        # Mock the DISA downloads page and the zip file download
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=disa_downloads_page
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        # Mock filesystem interactions
        with (
            patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile"),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.os.walk"
            ) as mock_os_walk,
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ),
        ):
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

            # Execute the test
            result_str = await fetch_disa_stig.fn("RHEL 9", mock_context)
            result = json.loads(result_str)

            # Assertions
            assert result["status"] == "success"
            assert "xccdf_path" in result["data"]
            assert result["data"]["xccdf_path"].endswith("_Manual-xccdf.xml")
            mock_context.info.assert_any_call("Searching for STIG matching: RHEL 9")

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_not_found(
        self, mock_context, empty_disa_page, mock_http_api
    ):
        """Test handling when STIG is not found."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=empty_disa_page
        )

        result_str = await fetch_disa_stig.fn("NonExistent STIG", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Could not find a STIG zip file" in result["message"]
        mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_network_error(self, mock_context, mock_http_api):
        """Test handling of network errors."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(500)

        result_str = await fetch_disa_stig.fn("RHEL 9", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Network error during download" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_extraction_error(
        self, mock_context, disa_downloads_page, mock_http_api
    ):
        """Test handling of zip extraction errors."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=disa_downloads_page
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        # Mock filesystem interactions to simulate extraction failure
        with patch(
            "agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile",
            side_effect=Exception("Extraction failed"),
        ):
            result_str = await fetch_disa_stig.fn("RHEL 9", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "Extraction failed" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_with_cli_keyword_success(
        self, mock_context, disa_downloads_page, mock_http_api
    ):
        """Test CLI keyword variant with successful execution."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=disa_downloads_page
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        with (
            patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile"),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.os.walk"
            ) as mock_os_walk,
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ),
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            result_str = await fetch_disa_stig_with_cli_keyword.fn("RHEL 9", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "success"
            assert "xccdf_path" in result["data"]


class TestDisaStigToolIntegration:
    """Integration tests using FastMCP Client for end-to-end testing."""

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_integration(
        self, disa_downloads_page, mock_http_api
    ):
        """Test the full MCP tool through the TestClient."""
        # Mock the external HTTP calls
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=disa_downloads_page
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        # Mock filesystem interactions
        with (
            patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile"),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.os.walk"
            ) as mock_os_walk,
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ),
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            async with Client(disa_stig_server) as client:
                result = await client.call_tool(
                    "fetch_disa_stig", {"product_keyword": "RHEL 9"}
                )

                response_data = json.loads(result[0].text)
                assert response_data["status"] == "success"
                assert response_data["data"]["xccdf_path"].endswith("_Manual-xccdf.xml")

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_with_cli_keyword_integration(
        self, disa_downloads_page, mock_http_api
    ):
        """Test CLI keyword variant through MCP Client."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=disa_downloads_page
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        with (
            patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile"),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.os.walk"
            ) as mock_os_walk,
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ),
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            async with Client(disa_stig_server) as client:
                result = await client.call_tool(
                    "fetch_disa_stig_with_cli_keyword", {"stig_keyword": "RHEL 9"}
                )

                response_data = json.loads(result[0].text)
                assert response_data["status"] == "success"
                assert "data" in response_data

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, empty_disa_page, mock_http_api):
        """Test error handling through MCP Client."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=empty_disa_page
        )

        async with Client(disa_stig_server) as client:
            result = await client.call_tool(
                "fetch_disa_stig", {"product_keyword": "NonExistent STIG"}
            )

            response_data = json.loads(result[0].text)
            assert response_data["status"] == "failure"
            assert "Could not find a STIG zip file" in response_data["message"]


class TestDisaStigToolEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_empty_keyword(self, mock_context):
        """Test handling of empty search keyword."""
        result_str = await fetch_disa_stig.fn("", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        # Should handle empty search gracefully

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_malformed_html(self, mock_context, mock_http_api):
        """Test handling of malformed HTML response."""
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html="<invalid>malformed</html>"
        )

        result_str = await fetch_disa_stig.fn("RHEL 9", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        # Should handle malformed HTML gracefully

    @pytest.mark.asyncio
    async def test_fetch_disa_stig_multiple_matches(self, mock_context, mock_http_api):
        """Test handling when multiple STIG files match the keyword."""
        multiple_matches_html = """
        <html>
            <body>
                <div>
                    <a href="/stigs/zip/U_RHEL_9_V1R1_STIG.zip">
                        Red Hat Enterprise Linux 9 STIG - Ver 1, Rel 1
                    </a>
                    <a href="/stigs/zip/U_RHEL_9_V1R2_STIG.zip">
                        Red Hat Enterprise Linux 9 STIG - Ver 1, Rel 2
                    </a>
                </div>
            </body>
        </html>
        """
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=multiple_matches_html
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R2_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        with (
            patch("agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile"),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.os.walk"
            ) as mock_os_walk,
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ),
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R2_STIG_Manual-xccdf.xml"])
            ]

            result_str = await fetch_disa_stig.fn("RHEL 9", mock_context)
            result = json.loads(result_str)

            # Should pick the latest version (V1R2)
            assert result["status"] == "success"
            assert "V1R2" in result["data"]["xccdf_path"]
