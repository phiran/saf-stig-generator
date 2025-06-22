"""
Tests for Memory Tool - comprehensive unit and integration tests.
"""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client

from agents.saf_stig_generator.services.memory.tool import (
    add_to_memory,
    query_memory,
)
from agents.saf_stig_generator.services.memory.tool import (
    mcp as memory_server,
)


class TestMemoryTool:
    """Unit tests for Memory tool functionality."""

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.memory.tool.collection")
    @patch("agents.saf_stig_generator.services.memory.tool.Path")
    async def test_add_to_memory_success(
        self, mock_path, mock_collection, mock_context
    ):
        """Test adding baseline controls to memory."""
        # Mock file system
        mock_baseline_path = mock_path.return_value
        mock_controls_dir = mock_baseline_path / "controls"
        mock_controls_dir.is_dir.return_value = True
        mock_controls_dir.glob.return_value = [mock_path("control1.rb")]

        # Mock file content
        control_content = """
        control 'V-230222' do
          title 'The RHEL 9 operating system must be a vendor-supported release.'
          desc 'An operating system release...'
          impact 1.0
        end
        """
        mock_path("control1.rb").read_text.return_value = control_content

        result_str = await add_to_memory("/fake/path", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert result["controls_added"] >= 0
        mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.memory.tool.collection")
    async def test_query_memory_success(self, mock_collection, mock_context):
        """Test querying memory for similar controls."""
        # Setup mock ChromaDB collection response
        mock_collection.query.return_value = {
            "ids": [["V-123"]],
            "metadatas": [[{"code": "control 'V-123' do..."}]],
        }

        result_str = await query_memory(
            "Check if OS is vendor supported", mock_context, 3
        )
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert len(result["results"]) == 1
        mock_collection.query.assert_called_with(
            query_texts=["Check if OS is vendor supported"],
            n_results=3,
            include=["metadatas"],
        )

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.memory.tool.collection", None)
    async def test_add_to_memory_no_collection(self, mock_context):
        """Test adding to memory when ChromaDB collection is unavailable."""
        result_str = await add_to_memory("/fake/path", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "ChromaDB collection is not available" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.memory.tool.collection")
    @patch("agents.saf_stig_generator.services.memory.tool.Path")
    async def test_add_to_memory_no_rb_files(
        self, mock_path, mock_collection, mock_context
    ):
        """Test adding to memory when no .rb files are found."""
        mock_baseline_path = mock_path.return_value
        mock_controls_dir = mock_baseline_path / "controls"
        mock_controls_dir.is_dir.return_value = True
        mock_controls_dir.glob.return_value = []  # No .rb files

        result_str = await add_to_memory("/fake/path", mock_context)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "No .rb files found" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.memory.tool.collection")
    async def test_query_memory_no_collection(self, mock_context):
        """Test querying memory when ChromaDB collection is unavailable."""
        with patch("agents.saf_stig_generator.services.memory.tool.collection", None):
            result_str = await query_memory("test query", mock_context, 3)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "ChromaDB collection is not available" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.memory.tool.collection")
    async def test_query_memory_exception(self, mock_collection, mock_context):
        """Test handling ChromaDB query exceptions."""
        mock_collection.query.side_effect = Exception("ChromaDB query failed")

        result_str = await query_memory("test query", mock_context, 3)
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "ChromaDB query failed" in result["message"]


class TestMemoryToolIntegration:
    """Integration tests for Memory tool using FastMCP Client."""

    @pytest.fixture
    def mcp_server(self):
        """Provide the Memory MCP server for testing."""
        return memory_server

    @pytest.mark.asyncio
    async def test_tool_via_mcp_client(self, mcp_server):
        """Test the tool through MCP client interface."""
        with patch(
            "agents.saf_stig_generator.services.memory.tool.collection"
        ) as mock_collection:
            mock_collection.query.return_value = {
                "ids": [["test-id"]],
                "metadatas": [[{"code": "sample control"}]],
            }

            async with Client(mcp_server) as client:
                result_content, _ = await client.call_tool(
                    "query_memory", {"control_description": "test control"}
                )
                result = json.loads(result_content.text)

                assert result["status"] == "success"
                assert "results" in result

    @pytest.mark.asyncio
    async def test_tool_resources(self, mcp_server):
        """Test tool resources are accessible."""
        async with Client(mcp_server) as client:
            # Test version resource
            version_result = await client.read_resource("memory-tool://version")
            assert "Memory Tool v" in version_result.text

            # Test info resource
            info_result = await client.read_resource("memory-tool://info")
            info_data = json.loads(info_result.text)
            assert info_data["name"] == "Memory Tool"
