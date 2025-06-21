#!/usr/bin/env python3
"""
Test script for the improved DISA STIG tool with common configuration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_saf_config():
    """Test the standalone saf_config module."""
    print("Testing saf_config module...")

    try:
        from saf_config import get_download_dir, get_artifacts_dir, find_config_file

        print("✓ Successfully imported saf_config")
        print(f"✓ Artifacts dir: {get_artifacts_dir()}")
        print(f"✓ Download dir: {get_download_dir()}")

        config_file = find_config_file()
        if config_file:
            print(f"✓ Config file found: {config_file}")
        else:
            print("ℹ Config file not found (this is OK for testing)")

        return True

    except Exception as e:
        print(f"✗ Error testing saf_config: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_disa_tool_import():
    """Test importing the DISA STIG tool."""
    print("\nTesting DISA STIG tool import...")

    try:
        # Add the tool directory to path
        tool_dir = project_root / "agents" / "src" / "saf_gen" / "mcp"
        sys.path.insert(0, str(tool_dir))

        import disa_stig_tool

        print("✓ Successfully imported disa_stig_tool")
        print(f"✓ Tool version: {disa_stig_tool.VERSION}")

        # Test the download directory function
        download_dir = disa_stig_tool._get_artifacts_download_dir()
        print(f"✓ Download directory: {download_dir}")

        return True

    except Exception as e:
        print(f"✗ Error testing DISA tool: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Running SAF Generator Configuration Tests")
    print("=" * 50)

    success = True

    # Test saf_config module
    if not test_saf_config():
        success = False

    # Test DISA tool import
    if not test_disa_tool_import():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
