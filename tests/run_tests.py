#!/usr/bin/env python3
"""
Comprehensive test runner for SAF STIG Generator MCP tools.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests for the MCP tools."""
    test_dir = Path(__file__).parent
    project_root = test_dir.parent

    print("🧪 Running SAF STIG Generator MCP Tools Tests")
    print("=" * 50)

    # Change to project root
    import os

    os.chdir(project_root)

    # Add project root to Python path
    sys.path.insert(0, str(project_root))

    # Test commands to run
    test_commands = [
        # Unit tests for all services
        ["python", "-m", "pytest", "tests/services/", "-v", "--tb=short"],
        # Integration tests (if they exist)
        # ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
        # Run with coverage if available
        # ["python", "-m", "pytest", "tests/", "--cov=agents", "--cov-report=term-missing"],
    ]

    for i, cmd in enumerate(test_commands, 1):
        print(f"\n📋 Running test command {i}/{len(test_commands)}:")
        print(f"   {' '.join(cmd)}")
        print("-" * 30)

        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            if result.returncode != 0:
                print(f"❌ Test command {i} failed with exit code {result.returncode}")
                return False
            else:
                print(f"✅ Test command {i} passed")
        except FileNotFoundError as e:
            print(f"❌ Command not found: {e}")
            print("   Make sure pytest is installed: pip install pytest pytest-asyncio")
            return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False

    print("\n🎉 All tests completed successfully!")
    return True


def check_dependencies():
    """Check if required test dependencies are available."""
    print("🔍 Checking test dependencies...")

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "fastmcp",
        # Note: respx and other packages might not be installed yet
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install " + " ".join(missing_packages))
        return False

    print("   🎯 All required dependencies found")
    return True


def main():
    """Main test runner entry point."""
    print("SAF STIG Generator - MCP Tools Test Suite")
    print("=========================================")

    # Check dependencies first
    if not check_dependencies():
        print("\n⚠️  Some dependencies are missing. Install them and try again.")
        sys.exit(1)

    # Run the tests
    if run_tests():
        print("\n✨ Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test suite failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
