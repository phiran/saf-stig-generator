# tests/tools/test_disa_stig_tool.py

import json
from unittest.mock import AsyncMock, patch

import pytest

# You will need to install these testing libraries:
# pip install pytest pytest-asyncio respx
import respx
from fastmcp import Client

# Import the specific tool function and the MCP server instance
from agents.services.disa_stig_tool import (
    fetch_disa_stig,
)
from agents.services.disa_stig_tool import (
    mcp as disa_stig_server,
)

# A fake HTML response from the DISA website for our unit test
FAKE_STIG_PAGE_HTML = """
<html>
    <body>
        <a href="/stigs/zip/U_RHEL_9_V1R1_STIG.zip">Red Hat Enterprise Linux 9 STIG - Ver 1, Rel 1</a>
        <a href="/stigs/zip/U_Some_Other_File.zip">Some Other File</a>
    </body>
</html>
"""

# --- Unit Tests (Testing Core Logic) ---


@pytest.mark.asyncio
@patch("agents.services.disa_stig_tool.zipfile.ZipFile")
@patch("agents.services.disa_stig_tool.os.walk")
@patch("agents.services.disa_stig_tool.anyio.to_thread.run_sync")
async def test_fetch_disa_stig_logic_success(mock_run_sync, mock_os_walk, mock_zipfile):
    """
    Unit tests the core logic of `fetch_disa_stig` by mocking all I/O.
    """
    # 1. Arrange: Mock all external dependencies
    product_keyword = "RHEL 9"

    # Mock the context object that the tool expects
    mock_ctx = AsyncMock()

    # Mock the filesystem interactions
    # Simulate finding the extracted files
    mock_os_walk.return_value = [
        (
            "/fake/path",
            [],
            ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml", "U_RHEL_9_V1R1_STIG_Manual.xml"],
        )
    ]

    # Mock the network calls using respx
    async with respx.mock:
        # Mock the initial page request
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=FAKE_STIG_PAGE_HTML
        )
        # Mock the zip file download request
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        # 2. Act: Call the tool's function directly
        result_str = await fetch_disa_stig(product_keyword, mock_ctx)
        result = json.loads(result_str)

        # 3. Assert: Check that the result is correct
        assert result["status"] == "success"
        assert "xccdf_path" in result["data"]
        assert "manual_path" in result["data"]
        assert result["data"]["xccdf_path"].endswith("_Manual-xccdf.xml")

        # Assert that the correct logs were sent to the context
        mock_ctx.info.assert_any_call(f"Searching for STIG matching: {product_keyword}")
        mock_ctx.info.assert_any_call(
            "Found STIG download URL: https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip"
        )


@pytest.mark.asyncio
async def test_fetch_disa_stig_logic_not_found():
    """
    Unit tests the logic for when a STIG is not found on the page.
    """
    # 1. Arrange
    mock_ctx = AsyncMock()
    async with respx.mock:
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html="<html></html>"
        )

        # 2. Act
        result_str = await fetch_disa_stig("NonExistent STIG", mock_ctx)
        result = json.loads(result_str)

        # 3. Assert
        assert result["status"] == "failure"
        assert "Could not find a STIG zip file" in result["message"]
        mock_ctx.error.assert_called_once()


# --- Integration Tests (Testing the Full MCP Tool) ---


@pytest.fixture
def mcp_server():
    """
    A pytest fixture that provides the disa_stig_server instance for testing.
    This makes our MCP server available to any test that needs it.
    """
    return disa_stig_server


@pytest.mark.asyncio
async def test_disa_tool_in_memory_integration(mcp_server):
    """
    Tests the full MCP tool by connecting a client directly to the server
    instance in memory, as recommended by FastMCP docs.
    """
    # 1. Arrange: Mock the network layer with respx
    async with respx.mock:
        respx.get("https://public.cyber.mil/stigs/downloads/").respond(
            200, html=FAKE_STIG_PAGE_HTML
        )
        respx.get("https://public.cyber.mil/stigs/zip/U_RHEL_9_V1R1_STIG.zip").respond(
            200, content=b"fake_zip_content"
        )

        # Mock filesystem and zip extraction for the integration test
        with (
            patch("agents.services.disa_stig_tool.zipfile.ZipFile"),
            patch("agents.services.disa_stig_tool.os.walk") as mock_walk,
            patch("agents.services.disa_stig_tool.anyio.to_thread.run_sync"),
        ):

            mock_walk.return_value = [
                ("/fake/path", [], ["U_RHEL_9_V1R1_STIG_Manual-xccdf.xml"])
            ]

            # 2. Act: Connect a client directly to the server fixture
            async with Client(mcp_server) as client:
                # Call the tool by name, just as the OrchestratorAgent would
                result_content, _ = await client.call_tool(
                    "fetch_disa_stig", {"product_keyword": "RHEL 9"}
                )
                result = json.loads(result_content.text)

            # 3. Assert
            assert result["status"] == "success"
            assert result["data"]["xccdf_path"].endswith("_Manual-xccdf.xml")
