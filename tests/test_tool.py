#!/usr/bin/env python3
"""Test script for the DISA STIG Tool"""

import os
import subprocess
import sys

# Change to the project directory
os.chdir("/Users/hp/MyCode/ML/saf-stig-generator")


def test_help():
    """Test --help flag"""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "agents/services/disa_stig_tool/disa_stig_tool.py",
                "--help",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        print("=== HELP TEST ===")
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        print("=" * 50)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Help test timed out")
        return False
    except Exception as e:
        print(f"❌ Help test error: {e}")
        return False


def test_version():
    """Test --version flag"""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "agents/services/disa_stig_tool/disa_stig_tool.py",
                "--version",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        print("=== VERSION TEST ===")
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        print("=" * 50)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Version test timed out")
        return False
    except Exception as e:
        print(f"❌ Version test error: {e}")
        return False


def test_import():
    """Test if the module can be imported"""
    try:
        sys.path.insert(
            0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        )
        import agents.services.disa_stig_tool.disa_stig_tool as tool

        print("✅ Module imports successfully")
        print(f"✅ Version: {tool.VERSION}")
        print(
            f"✅ Tools available: {[t.name for t in tool.mcp._tool_manager.list_tools()]}"
        )
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


if __name__ == "__main__":
    print("Testing DISA STIG Tool...")

    tests = [
        ("Import Test", test_import),
        ("Help Test", test_help),
        ("Version Test", test_version),
    ]

    passed = 0
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")

    print("\n=== SUMMARY ===")
    print(f"Passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
