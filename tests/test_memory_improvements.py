#!/usr/bin/env python3
"""
Test script for the improved memory tool functionality.
This script demonstrates the new pretrain capabilities.
"""

import os
import tempfile

from agents.saf_stig_generator.services.memory.tool import manage_baseline_memory

# Sample InSpec control for testing
SAMPLE_CONTROL = """
control "V-000001" do
  title "The system must require authentication for all users."
  desc "This control ensures that all users must authenticate before accessing the system."
  impact 0.7
  tag "severity": "medium"
  tag "gtitle": "Authentication Required"
  tag "gid": "V-000001"
  tag "rid": "SV-000001r1_rule"
  tag "stig_id": "SAMPLE-00-000001"
  tag "fix_id": "F-000001r1_fix"
  tag "cci": ["CCI-000764"]
  tag "nist": ["IA-2", "Rev_4"]

  describe command('whoami') do
    its('stdout.strip') { should_not eq 'root' }
  end
end
"""


def test_memory_functionality():
    """Test the improved memory functionality."""
    print("Testing improved memory tool functionality...")

    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a controls subdirectory
        controls_dir = os.path.join(temp_dir, "controls")
        os.makedirs(controls_dir)

        # Write a sample control file
        control_file = os.path.join(controls_dir, "test_control.rb")
        with open(control_file, "w") as f:
            f.write(SAMPLE_CONTROL)

        print(f"Created test control in: {controls_dir}")

        # Test adding to memory
        print("\n1. Testing add functionality...")
        result = manage_baseline_memory(action="add", baseline_path=controls_dir)
        print(f"Add result: {result}")

        if result["status"] == "success":
            print(f"✅ Successfully added {result['message']}")
        else:
            print(f"❌ Failed to add: {result.get('message', 'Unknown error')}")

        # Test querying memory
        print("\n2. Testing query functionality...")
        query_result = manage_baseline_memory(
            action="query", query_text="authentication users system"
        )
        print(f"Query result: {query_result}")

        if query_result["status"] == "success":
            num_results = len(query_result.get("results", []))
            print(f"✅ Query successful, found {num_results} results")
            if num_results > 0:
                print("First result preview:")
                print(query_result["results"][0][:200] + "...")
        else:
            print(f"❌ Query failed: {query_result.get('message', 'Unknown error')}")

        # Test error handling
        print("\n3. Testing error handling...")
        error_result = manage_baseline_memory(action="invalid_action")
        print(f"Error handling result: {error_result}")

        if "error" in error_result["status"]:
            print("✅ Error handling works correctly")
        else:
            print("❌ Error handling not working as expected")


if __name__ == "__main__":
    test_memory_functionality()
