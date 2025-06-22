"""
Tests for InSpec Runner Tool - comprehensive unit and integration tests.
"""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client

from agents.saf_stig_generator.services.inspect_runner.tool import (
    mcp as inspec_runner_server,
)
from agents.saf_stig_generator.services.inspect_runner.tool import (
    run_inspec_tests,
)


class TestInspecRunnerTool:
    """Unit tests for InSpec runner tool functionality."""

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.inspect_runner.tool.subprocess.run")
    async def test_run_inspec_tests_success(self, mock_subprocess, mock_context):
        """Test successful InSpec test execution."""
        # Mock successful InSpec run
        mock_results = {
            "version": "5.22.29",
            "profiles": [{"status": "loaded"}],
            "statistics": {
                "duration": 0.1,
                "total": 10,
                "passed": {"total": 8},
                "failed": {"total": 2},
            },
        }
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = json.dumps(mock_results)
        mock_subprocess.return_value.stderr = ""

        result_str = await run_inspec_tests(
            "/path/to/baseline", "my-container", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert "results" in result["data"]
        assert result["data"]["results"]["statistics"]["total"] == 10
        assert result["data"]["results"]["statistics"]["passed"]["total"] == 8

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.inspect_runner.tool.subprocess.run")
    async def test_run_inspec_tests_command_error(self, mock_subprocess, mock_context):
        """Test handling when InSpec command fails."""
        # Mock failed InSpec command
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = "InSpec command not found"

        result_str = await run_inspec_tests(
            "/path/to/baseline", "my-container", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "InSpec execution failed" in result["message"]
        assert "InSpec command not found" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.inspect_runner.tool.subprocess.run")
    async def test_run_inspec_tests_invalid_json(self, mock_subprocess, mock_context):
        """Test handling of invalid JSON output from InSpec."""
        # Mock InSpec run with invalid JSON output
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Invalid JSON output"
        mock_subprocess.return_value.stderr = ""

        result_str = await run_inspec_tests(
            "/path/to/baseline", "my-container", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Failed to parse InSpec JSON output" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.inspect_runner.tool.subprocess.run")
    async def test_run_inspec_tests_timeout(self, mock_subprocess, mock_context):
        """Test handling of InSpec command timeout."""
        import subprocess

        # Mock timeout error
        mock_subprocess.side_effect = subprocess.TimeoutExpired("inspec", 300)

        result_str = await run_inspec_tests(
            "/path/to/baseline", "my-container", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "InSpec command timed out" in result["message"]

    @pytest.mark.asyncio
    @patch("agents.saf_stig_generator.services.inspect_runner.tool.subprocess.run")
    async def test_run_inspec_tests_file_not_found(self, mock_subprocess, mock_context):
        """Test handling when baseline path doesn't exist."""
        # Mock FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError("Baseline path not found")

        result_str = await run_inspec_tests(
            "/nonexistent/baseline", "my-container", mock_context
        )
        result = json.loads(result_str)

        assert result["status"] == "failure"
        assert "Baseline path not found" in result["message"]


class TestInspecRunnerToolIntegration:
    """Integration tests for InSpec runner tool using FastMCP Client."""

    @pytest.fixture
    def mcp_server(self):
        """Provide the InSpec runner MCP server for testing."""
        return inspec_runner_server

    @pytest.mark.asyncio
    async def test_tool_via_mcp_client(self, mcp_server):
        """Test the tool through MCP client interface."""
        with patch(
            "agents.saf_stig_generator.services.inspect_runner.tool.subprocess.run"
        ) as mock_subprocess:
            mock_results = {
                "statistics": {
                    "total": 5,
                    "passed": {"total": 4},
                    "failed": {"total": 1},
                }
            }
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = json.dumps(mock_results)
            mock_subprocess.return_value.stderr = ""

            async with Client(mcp_server) as client:
                result_content, _ = await client.call_tool(
                    "run_inspec_tests",
                    {
                        "baseline_path": "/test/baseline",
                        "target": "docker://test-container",
                    },
                )
                result = json.loads(result_content.text)

                assert result["status"] == "success"
                assert "results" in result["data"]

    @pytest.mark.asyncio
    async def test_tool_resources(self, mcp_server):
        """Test tool resources are accessible."""
        async with Client(mcp_server) as client:
            # Test version resource
            version_result = await client.read_resource("inspec-runner-tool://version")
            assert "InSpec Runner Tool v" in version_result.text

            # Test info resource
            info_result = await client.read_resource("inspec-runner-tool://info")
            info_data = json.loads(info_result.text)
            assert info_data["name"] == "InSpec Runner Tool"
