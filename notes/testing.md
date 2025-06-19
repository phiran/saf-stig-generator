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
import os
from pathlib import Path
script_path = Path('./agents/src/saf_gen/mcp/disa_stig_tool.py').resolve()
config_dir = script_path.parent.parent.parent.parent / 'config'
env_file = config_dir / 'development.env'
print(f'Script path: {script_path}')
print(f'Config dir: {config_dir}')
print(f'Env file: {env_file}')
print(f'Env file exists: {env_file.exists()}')
"

cd /Users/hp/MyCode/ML/saf-stig-generator && python agents/src/saf_gen/mcp/disa_stig_tool.py --help 2>&1 || echo "Exit code: $?"

cd /Users/hp/MyCode/ML/saf-stig-generator && timeout 3 python agents/src/saf_gen/mcp/disa_stig_tool.py --version 2>&1 || echo "Exit code: $?"

cd /Users/hp/MyCode/ML/saf-stig-generator && python test_tool.py

cd /Users/hp/MyCode/ML/saf-stig-generator && python test_mitre_baseline.py

cd /Users/hp/MyCode/ML/saf-stig-generator && python -c "import sys; sys.path.append('agents/src'); from saf_gen.mcp.mitre_baseline_tool import TOOL_VERSION; print(f'Import successful! Version: {TOOL_VERSION}')"

```
