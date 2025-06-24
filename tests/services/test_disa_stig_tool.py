"""
Tests for DISA STIG Tool - comprehensive unit and integration tests.
Uses FastMCP testing patterns with direct Client testing and respx for HTTP mocking.
CORRECT:
1. The `anyio.to_thread.run_sync` mocking is not complete in all test cases
2. The error expectations don't match the actual errors that occur
3. There's an issue with the zipfile handling mocking

For the DISA STIG tests, the main issue is that the test is expecting different error messages than what the code actually produces. Let me look at the code more carefully to see what error should actually occur for a 500 status code.

The main issue is that even with a 500 status code from the first request, the tool continues execution and tries to find an XCCDF file, which then fails with a different error message.
Fix the expectations in the tests to match what the code actually does, or fix the code to handle errors properly.

Check the error handling in the tool: The code calls `response.raise_for_status()` which should raise an exception for a 500 status code, but that exception is being caught by the outer exception handlers. Let me look at the exception handling: Perfect! I can see that there is a `requests.RequestException` handler that should catch the 500 status error and return the "Network error during download" message. The issue is that when requests.get gets a 500 status, it gets the response but `response.raise_for_status()` raises a `requests.HTTPError` which is a subclass of `requests.RequestException`.

The test should work correctly, but the issue might be that with my current fix, the tool is actually succeeding when it should be failing. Let me check what respx returns when a status code is set to 500.

The issue is that the test currently succeeds because the 500 status is being returned, but the execution continues. The error should be caught at the `response.raise_for_status()` line. Let me create a simple test to verify this behavior:
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
            ) as mock_run_sync,
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

            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

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

        with patch(
            "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
        ) as mock_run_sync:
            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

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
        with (
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.zipfile.ZipFile",
                side_effect=Exception("Extraction failed"),
            ),
            patch(
                "agents.saf_stig_generator.services.disa_stig.tool.anyio.to_thread.run_sync"
            ) as mock_run_sync,
        ):
            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

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
            ) as mock_run_sync,
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

            result_str = await fetch_disa_stig_with_cli_keyword.fn(
                "RHEL 9", mock_context
            )
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
            ) as mock_run_sync,
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

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
            ) as mock_run_sync,
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

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
            ) as mock_run_sync,
        ):
            mock_os_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R2_STIG_Manual-xccdf.xml"])
            ]

            # Mock anyio.to_thread.run_sync to call the lambda directly
            mock_run_sync.side_effect = lambda func: func()

            result_str = await fetch_disa_stig.fn("RHEL 9", mock_context)
            result = json.loads(result_str)

            # Should pick the latest version (V1R2)
            assert result["status"] == "success"
            assert "V1R2" in result["data"]["xccdf_path"]
