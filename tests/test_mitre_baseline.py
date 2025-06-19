#!/usr/bin/env python3

"""
Simple test for the MITRE Baseline Tool.
"""

import sys
import subprocess


def run_command(cmd, timeout=10):
    """Run a command and return its output."""
    print(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT: {result.stdout[:500]}" if result.stdout else "STDOUT: [empty]")
        print(f"STDERR: {result.stderr[:500]}" if result.stderr else "STDERR: [empty]")
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return None


def main():
    """Run tests for the MITRE baseline tool."""
    print("=== Testing MITRE Baseline Tool ===\n")

    # Test 1: Help output
    print("\n=== Test 1: Help Output ===")
    run_command(
        [sys.executable, "agents/src/saf_gen/mcp/mitre_baseline_tool.py", "--help"]
    )

    # Test 2: Version output
    print("\n=== Test 2: Version Output ===")
    run_command(
        [sys.executable, "agents/src/saf_gen/mcp/mitre_baseline_tool.py", "--version"]
    )

    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    main()
