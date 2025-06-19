# Testing methods

## Manual

```sh
cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "
import sys
sys.path.append('agents/src')
try:
    import saf_gen.mcp.disa_stig_tool
    print('✅ Module imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "
import sys, asyncio
sys.path.append('agents/src')
from saf_gen.mcp.disa_stig_tool import mcp, VERSION
print(f'✅ DISA STIG Tool v{VERSION} loaded successfully')
print(f'✅ Tools: {[tool.name for tool in mcp._tool_manager.list_tools()]}')
print('✅ FastMCP server initialized correctly with SSE support')
"

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "
import sys
import argparse

# Test the argument parser setup
parser = argparse.ArgumentParser(description='Test')
parser.add_argument('--version', action='version', version='Test v1.0.0')
parser.add_argument('--help-test', action='store_true')

# Test with version
try:
    args = parser.parse_args(['--version'])
    print('Should not reach here')
except SystemExit as e:
    print(f'✅ Version flag works, exit code: {e.code}')

# Test with help
try:
    args = parser.parse_args(['-h'])
    print('Should not reach here')  
except SystemExit as e:
    print(f'✅ Help flag works, exit code: {e.code}')
"

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "
import sys
sys.path.append('.')
try:
    from saf_config import get_download_dir, find_config_file
    print('✓ Successfully imported saf_config')
    print('✓ Download dir:', get_download_dir())
    print('✓ Config file:', find_config_file())
except Exception as e:
    print('✗ Error:', e)
"

cd /Users/hp/MyCode/ML/saf-stig-generator && python agents/src/saf_gen/mcp/disa_stig_tool.py --help 2>&1 || echo "Exit code: $?"

cd /Users/hp/MyCode/ML/saf-stig-generator && timeout 3 python agents/src/saf_gen/mcp/disa_stig_tool.py --version 2>&1 || echo "Exit code: $?"

cd /Users/hp/MyCode/ML/saf-stig-generator && python test_tool.py

cd /Users/hp/MyCode/ML/saf-stig-generator && python test_mitre_baseline.py

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "import sys; sys.path.append('agents/src'); from saf_gen.mcp.mitre_baseline_tool import TOOL_VERSION; print(f'Import successful! Version: {TOOL_VERSION}')"

# MITRE Baseline Tool
cd /Users/hp/MyCode/ML/saf-stig-generator && python agents/src/saf_gen/mcp/mitre_baseline_tool.py --query "MITRE STIG baseline"
cd /Users/hp/MyCode/ML/saf-stig-generator && python agents/src/saf_gen/mcp/mitre_baseline_tool.py --stdio  # Use STDIO instead of SSE

# Docker Tool  
cd /Users/hp/MyCode/ML/saf-stig-generator && python agents/src/saf_gen/mcp/docker_tool.py --keyword "RHEL 9"
cd /Users/hp/MyCode/ML/saf-stig-generator && python agents/src/saf_gen/mcp/docker_tool.py --http --host 0.0.0.0 --port 8001

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "import fastmcp; print(f'FastMCP: {fastmcp.__version__ if hasattr(fastmcp, \"__version__\") else \"unknown\"}')"

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "import uvicorn; print(f'uvicorn: {uvicorn.__version__}')"

cd /Users/hp/MyCode/ML/saf-stig-generator && pip list | grep -E "(uvicorn|websockets|fastmcp)"

cd /Users/hp/MyCode/ML/saf-stig-generator && uv pip list
```
