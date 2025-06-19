#!/usr/bin/env python3
"""Simple verification of DISA STIG Tool argument parsing"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n🧪 Testing: {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run the command with a timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/Users/hp/MyCode/ML/saf-stig-generator",
            check=False,
        )

        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    # Test cases
    tests = [
        (
            [sys.executable, "agents/src/saf_gen/mcp/disa_stig_tool.py", "--help"],
            "Help flag",
        ),
        (
            [sys.executable, "agents/src/saf_gen/mcp/disa_stig_tool.py", "--version"],
            "Version flag",
        ),
        (
            [
                sys.executable,
                "-c",
                "import sys; sys.path.append('agents/src'); import saf_gen.mcp.disa_stig_tool; print('Import successful')",
            ],
            "Module import",
        ),
    ]

    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
        print("✅ PASSED" if success else "❌ FAILED")

    print(f"\n{'='*50}")
    print("SUMMARY:")
    for desc, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {desc}: {status}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
