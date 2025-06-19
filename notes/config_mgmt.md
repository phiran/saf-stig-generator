# Summary of configuration processing chagnges

Cleaner architecture with reusable configuration management that can be shared across all Python files in the SAF Generator project.

### 1. ✅ Common Configuration Module (saf_config.py)

I've created a standalone configuration module at the project root that provides:

- **Automatic environment loading** from development.env
- **Smart path detection** that searches up the directory tree
- **Common directory utilities** (artifacts, downloads, generated)
- **Reusable across all Python files** in the project

**Usage:**

```python
from saf_config import get_download_dir, get_artifacts_dir, ensure_dir

# Automatically loads environment on import
download_dir = get_download_dir()  # Gets artifacts/downloads
artifacts_dir = get_artifacts_dir()  # Gets artifacts directory
ensure_dir(some_path)  # Creates directory if needed
```

### 2. ✅ CLI Keyword Support for SSE/HTTP

Added a `--keyword` argument that allows passing product keywords via command line:

- **New tool**: `fetch_disa_stig_with_cli_keyword` - uses the CLI-provided keyword
- **Global keyword storage** - `CLI_PRODUCT_KEYWORD` variable
- **Works with all transports** (SSE, HTTP, STDIO)

**Usage:**

```bash
python disa_stig_tool.py --keyword "RHEL 9"  # Uses SSE by default
python disa_stig_tool.py --keyword "Ubuntu 22" --host 0.0.0.0 --port 8001
```

### 3. ✅ SSE as Default Transport

Changed the default transport from STDIO to SSE:

- **SSE is now default** - no flag needed
- **STDIO is optional** - use `--stdio` flag
- **HTTP is optional** - use `--http` flag
- **Better help documentation** with examples

**Usage Examples:**

```bash
# Default - runs with SSE transport
python disa_stig_tool.py

# With keyword and custom host/port  
python disa_stig_tool.py --keyword "RHEL 9" --host 0.0.0.0 --port 8001

# Use STDIO transport instead
python disa_stig_tool.py --stdio

# Use HTTP transport
python disa_stig_tool.py --http --host 127.0.0.1 --port 8000
```

### Key Features Added

1. **Centralized Configuration**: The saf_config.py module can be imported by any Python file in the `saf_gen` directory
2. **Automatic Environment Loading**: Environment variables are loaded automatically when importing the config module  
3. **Smart Path Resolution**: Handles both absolute and relative paths from the `ARTIFACTS_DIR` environment variable
4. **Two MCP Tools Available**:
   - `fetch_disa_stig(product_keyword)` - for dynamic keyword input
   - `fetch_disa_stig_with_cli_keyword()` - uses CLI-provided keyword
5. **Better CLI Interface**: More intuitive with SSE as default and clear examples

### Files Created/Modified

1. **saf_config.py** - Standalone configuration module (new)
2. **config.py** - Common configuration utilities (new)
3. ****init**.py** - Common module exports (new)
4. **disa_stig_tool.py** - Updated to use common config and new CLI options (modified)
