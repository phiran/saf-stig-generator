#!/usr/bin/env python3

"""Test script for the refactored MITRE baseline tool."""

import sys
import subprocess
import json
from pathlib import Path


def test_tool_help():
    """Test that the tool shows help correctly."""
    print("Testing tool help...")
    try:
        result = subprocess.run(
            [sys.executable, "agents/src/saf_gen/mcp/mitre_baseline_tool.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"Help exit code: {result.returncode}")
        if result.stdout:
            print("Help output received (showing first 300 chars):")
            print(
                result.stdout[:300] + "..."
                if len(result.stdout) > 300
                else result.stdout
            )
        return result.returncode == 0
    except Exception as e:
        print(f"Error testing help: {e}")
        return False


def test_tool_version():
    """Test that the tool shows version correctly."""
    print("\nTesting tool version...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "agents/src/saf_gen/mcp/mitre_baseline_tool.py",
                "--version",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"Version exit code: {result.returncode}")
        if result.stdout:
            print(f"Version output: {result.stdout.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error testing version: {e}")
        return False


def test_tool_import():
    """Test that the tool can be imported without errors."""
    print("\nTesting tool import...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, 'agents/src'); from saf_gen.mcp.mitre_baseline_tool import get_artifacts_directory, TOOL_VERSION; print(f'Import successful! Version: {TOOL_VERSION}')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"Import exit code: {result.returncode}")
        if result.stdout:
            print(f"Import output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Import stderr: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error testing import: {e}")
        return False


def main():
    """Run all tests."""
    print("=== MITRE Baseline Tool Test ===\n")

    # Change to project directory
    project_dir = Path(__file__).parent
    print(f"Working directory: {project_dir}")

    tests = [
        ("Help", test_tool_help),
        ("Version", test_tool_version),
        ("Import", test_tool_import),
    ]

    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()

    print(f"\n=== Test Results ===")
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
