"""
Tests for Memory Tool - comprehensive unit and integration tests.
Uses FastMCP testing patterns with direct Client testing.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

# Import the tool components
from agents.saf_stig_generator.services.memory.tool import (
    add_to_memory,
    manage_baseline_memory,
    query_memory,
)
from agents.saf_stig_generator.services.memory.tool import (
    mcp as memory_server,
)


class TestMemoryToolUnit:
    """Unit tests for Memory tool core functions."""

    @pytest.mark.asyncio
    async def test_add_to_memory_success(self, mock_context):
        """Test adding baseline controls to memory."""
        with (
            patch(
                "agents.saf_stig_generator.services.memory.tool.legacy_collection"
            ) as mock_collection,
            patch(
                "agents.saf_stig_generator.services.memory.tool.Path"
            ) as mock_path_class,
        ):

            # Mock filesystem structure
            mock_baseline_path = MagicMock()
            mock_path_class.return_value = mock_baseline_path

            mock_controls_dir = MagicMock()
            mock_baseline_path.__truediv__.return_value = mock_controls_dir
            mock_controls_dir.is_dir.return_value = True

            # Mock control files
            mock_file = MagicMock()
            mock_file.read_text.return_value = """
            control 'V-230222' do
              title 'The RHEL 9 operating system must be a vendor-supported release.'
              desc 'An operating system release that is not supported by the vendor...'
              impact 1.0
            end
            """
            mock_controls_dir.glob.return_value = [mock_file]

            # Mock collection as available
            mock_collection.add = MagicMock()

            result_str = await add_to_memory("/fake/path", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "success"
            assert "controls_added" in result
            mock_context.info.assert_called()
            mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_memory_no_collection(self, mock_context):
        """Test handling when ChromaDB collection is not available."""
        with (
            patch(
                "agents.saf_stig_generator.services.memory.tool.legacy_collection", None
            ),
            patch(
                "agents.saf_stig_generator.services.memory.tool.examples_collection",
                None,
            ),
        ):

            result_str = await add_to_memory("/fake/path", mock_context)
            result = json.loads(result_str)

            assert result["status"] == "failure"
            assert "ChromaDB collection is not available" in result["message"]

    @pytest.mark.asyncio
    async def test_query_memory_success(self, mock_context):
        """Test querying memory for similar controls."""
        with patch(
            "agents.saf_stig_generator.services.memory.tool.legacy_collection"
        ) as mock_collection:
            # Mock the return value of the query
            mock_collection.query.return_value = {
                "ids": [["V-123"]],
                "metadatas": [
                    [{"code": "control 'V-123' do\n  title 'Test control'\nend"}]
                ],
            }

            result_str = await query_memory(
                "Check if OS is vendor supported", mock_context, 3
            )
            result = json.loads(result_str)

            assert result["status"] == "success"
            assert len(result["results"]) == 1
            assert "control 'V-123' do" in result["results"][0]["code"]
            mock_collection.query.assert_called_with(
                query_texts=["Check if OS is vendor supported"],
                n_results=3,
                include=["metadatas"],
            )

    def test_manage_baseline_memory_add_success(self):
        """Test manage_baseline_memory add functionality."""
        with (
            patch(
                "agents.saf_stig_generator.services.memory.tool.examples_collection"
            ) as mock_collection,
            patch(
                "agents.saf_stig_generator.services.memory.tool.os.path.isdir",
                return_value=True,
            ),
            patch(
                "agents.saf_stig_generator.services.memory.tool.os.walk"
            ) as mock_walk,
        ):

            # Mock walking through directory
            mock_walk.return_value = [
                ("/fake/path", [], ["control1.rb", "control2.rb"])
            ]

            # Mock control file parsing
            with patch(
                "agents.saf_stig_generator.services.memory.tool._parse_inspec_control"
            ) as mock_parse:
                mock_parse.side_effect = [
                    {
                        "id": "V-001",
                        "title": "Test Control 1",
                        "content": "control 'V-001' do\n  title 'Test Control 1'\nend",
                    },
                    {
                        "id": "V-002",
                        "title": "Test Control 2",
                        "content": "control 'V-002' do\n  title 'Test Control 2'\nend",
                    },
                ]

                mock_collection.add = MagicMock()

                result = manage_baseline_memory(
                    action="add", baseline_path="/fake/path"
                )

                assert result["status"] == "success"
                assert "Added 2 controls" in result["message"]
                mock_collection.add.assert_called_once()

    def test_manage_baseline_memory_query_success(self):
        """Test manage_baseline_memory query functionality."""
        with patch(
            "agents.saf_stig_generator.services.memory.tool.examples_collection"
        ) as mock_collection:
            mock_collection.query.return_value = {
                "documents": [["control content 1", "control content 2"]]
            }

            result = manage_baseline_memory(action="query", query_text="authentication")

            assert result["status"] == "success"
            assert len(result["results"]) == 2
            assert result["results"][0] == "control content 1"
            mock_collection.query.assert_called_with(
                query_texts=["authentication"], n_results=5
            )

    def test_manage_baseline_memory_invalid_action(self):
        """Test manage_baseline_memory with invalid action."""
        result = manage_baseline_memory(action="invalid")

        assert result["status"] == "error"
        assert "Invalid action" in result["message"]


class TestMemoryToolIntegration:
    """Integration tests using FastMCP Client for end-to-end testing."""

    @pytest.mark.asyncio
    async def test_add_to_memory_integration(self):
        """Test add_to_memory through MCP Client."""
        with (
            patch(
                "agents.saf_stig_generator.services.memory.tool.legacy_collection"
            ) as mock_collection,
            patch(
                "agents.saf_stig_generator.services.memory.tool.Path"
            ) as mock_path_class,
        ):

            # Setup mocks
            mock_baseline_path = MagicMock()
            mock_path_class.return_value = mock_baseline_path
            mock_controls_dir = MagicMock()
            mock_baseline_path.__truediv__.return_value = mock_controls_dir
            mock_controls_dir.is_dir.return_value = True

            mock_file = MagicMock()
            mock_file.read_text.return_value = """
            control 'V-230222' do
              title 'Test control'
              impact 1.0
            end
            """
            mock_controls_dir.glob.return_value = [mock_file]
            mock_collection.add = MagicMock()

            # Test through MCP Client
            async with Client(memory_server) as client:
                result = await client.call_tool(
                    "add_to_memory", {"baseline_path": "/fake/path"}
                )

                # Parse the JSON response
                response_data = json.loads(result[0].text)
                assert response_data["status"] == "success"
                assert "controls_added" in response_data

    @pytest.mark.asyncio
    async def test_query_memory_integration(self):
        """Test query_memory through MCP Client."""
        with patch(
            "agents.saf_stig_generator.services.memory.tool.legacy_collection"
        ) as mock_collection:
            mock_collection.query.return_value = {
                "ids": [["V-123"]],
                "metadatas": [[{"code": "control 'V-123' do\n  title 'Test'\nend"}]],
            }

            async with Client(memory_server) as client:
                result = await client.call_tool(
                    "query_memory",
                    {"control_description": "operating system support", "n_results": 3},
                )

                response_data = json.loads(result[0].text)
                assert response_data["status"] == "success"
                assert "results" in response_data

    @pytest.mark.asyncio
    async def test_manage_baseline_memory_mcp_integration(self):
        """Test manage_baseline_memory_mcp through MCP Client."""
        with patch(
            "agents.saf_stig_generator.services.memory.tool.examples_collection"
        ) as mock_collection:
            mock_collection.query.return_value = {
                "documents": [["sample control content"]]
            }

            async with Client(memory_server) as client:
                result = await client.call_tool(
                    "manage_baseline_memory_mcp",
                    {"action": "query", "query_text": "authentication"},
                )

                response_data = json.loads(result[0].text)
                assert response_data["status"] == "success"
                assert "results" in response_data
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
