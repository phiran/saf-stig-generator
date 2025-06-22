"""
CLI Testing utilities for MCP tools.
"""

import subprocess
import sys
from pathlib import Path
from typing import List


class MCPToolCLITester:
    """Helper class for testing MCP tool CLI functionality."""

    def __init__(self, tool_path: Path):
        self.tool_path = tool_path

    def run_command(self, args: List[str], timeout: int = 10) -> dict:
        """Run a CLI command and return results."""
        cmd = [sys.executable, str(self.tool_path)] + args

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "success": False,
            }
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e), "success": False}

    def test_help(self) -> bool:
        """Test the --help flag."""
        result = self.run_command(["--help"])
        return result["success"] and "usage" in result["stdout"].lower()

    def test_version(self) -> bool:
        """Test the --version flag."""
        result = self.run_command(["--version"])
        return result["success"] and any(
            keyword in result["stdout"].lower()
            for keyword in ["version", "v1", "v2", "tool"]
        )

    def test_invalid_args(self) -> bool:
        """Test invalid arguments handling."""
        result = self.run_command(["--invalid-flag"])
        # Should fail with non-zero exit code
        return not result["success"]


def test_all_tools_cli():
    """Test CLI functionality for all MCP tools."""
    tools_dir = (
        Path(__file__).parent.parent / "agents" / "saf_stig_generator" / "services"
    )

    test_results = {}

    for tool_dir in tools_dir.iterdir():
        if tool_dir.is_dir() and (tool_dir / "tool.py").exists():
            tool_name = tool_dir.name
            tool_path = tool_dir / "tool.py"

            tester = MCPToolCLITester(tool_path)

            test_results[tool_name] = {
                "help": tester.test_help(),
                "version": tester.test_version(),
                "invalid_args": tester.test_invalid_args(),
            }

    return test_results


if __name__ == "__main__":
    import json

    results = test_all_tools_cli()
    print(json.dumps(results, indent=2))
