#!/usr/bin/env python3
"""Entry points for the SAF STIG Generator project."""

import subprocess
import sys


def start_agent():
    """Start the ADK agent."""
    try:
        subprocess.run(["adk", "run", "-c", "run.yaml"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting agent: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'adk' command not found. Make sure ADK is installed.")
        sys.exit(1)


def start_disa_tool_sse():
    """Start DISA STIG tool with SSE."""
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "agents.services.disa_stig_tool.disa_stig_tool",
                "--sse",
                "127.0.0.1",
                "3001",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting DISA tool (SSE): {e}")
        sys.exit(1)


def start_disa_tool_http():
    """Start DISA STIG tool with HTTP."""
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "agents.services.disa_stig_tool.disa_stig_tool",
                "--http",
                "127.0.0.1",
                "3001",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting DISA tool (HTTP): {e}")
        sys.exit(1)


def start_mitre_tool():
    """Start MITRE baseline tool."""
    try:
        subprocess.run(
            [
                "uvicorn",
                "agents.services.mitre_baseline_tool.mitre_baseline_tool:starlette_app",
                "--reload",
                "--port",
                "3002",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting MITRE tool: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uvicorn' command not found. Make sure uvicorn is installed.")
        sys.exit(1)


def start_saf_tool():
    """Start SAF generator tool."""
    try:
        subprocess.run(
            [
                "uvicorn",
                "agents.services.saf_generator_tool.saf_generator_tool:starlette_app",
                "--reload",
                "--port",
                "3003",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting SAF tool: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uvicorn' command not found. Make sure uvicorn is installed.")
        sys.exit(1)


def start_docker_tool():
    """Start Docker tool."""
    try:
        subprocess.run(
            [
                "uvicorn",
                "agents.services.docker_tool.docker_tool:starlette_app",
                "--reload",
                "--port",
                "3004",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting Docker tool: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uvicorn' command not found. Make sure uvicorn is installed.")
        sys.exit(1)


def start_inspec_tool():
    """Start InSpec runner tool."""
    try:
        subprocess.run(
            [
                "uvicorn",
                "agents.services.inspec_runner_tool.inspec_runner_tool:starlette_app",
                "--reload",
                "--port",
                "3005",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error starting InSpec tool: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uvicorn' command not found. Make sure uvicorn is installed.")
        sys.exit(1)


def run_tests():
    """Run tests using pytest."""
    try:
        subprocess.run(["pytest"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'pytest' command not found. Make sure pytest is installed.")
        sys.exit(1)


if __name__ == "__main__":
    # This allows the script to be run directly
    import sys

    if len(sys.argv) > 1:
        func_name = sys.argv[1].replace("-", "_")
        if hasattr(sys.modules[__name__], func_name):
            getattr(sys.modules[__name__], func_name)()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Usage: python entry_points.py <command>")
        sys.exit(1)
