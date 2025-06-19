import subprocess
import sys

# Test help command
print("Testing --help...")
result = subprocess.run(
    [sys.executable, "agents/src/saf_gen/mcp/disa_stig_tool.py", "--help"],
    capture_output=True,
    text=True,
    timeout=5,
)

print(f"Exit code: {result.returncode}")
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
