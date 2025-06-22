# Import Path Issues and Solutions

## Current Import Problems

### 1. Inconsistent Import Paths

```python
# Current problematic imports in tests
from agents.services.disa_stig_tool import fetch_disa_stig, mcp as disa_stig_server

# Path manipulation needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from saf_config import ensure_dir, get_config_value, get_download_dir
```

### 2. Circular Dependencies

- Services importing from root-level `saf_config.py`
- Agents importing from services
- Tests struggling with import paths

## Recommended Solutions

### 1. Standardize Package Structure

```python
# After restructuring, clean imports:
from saf_stig_generator.services.disa_stig import DisaStigService
from saf_stig_generator.common.config import get_download_dir
from saf_stig_generator.agents.orchestrator import Orchestrator
```

### 2. Use Relative Imports Within Package

```python
# Within services/disa_stig/service.py
from ...common.config import get_download_dir
from ...common.types import ServiceResult

# Within agents/orchestrator.py
from ..services.disa_stig import DisaStigService
from ..common.config import get_artifacts_dir
```

### 3. Update pyproject.toml

```toml
[project]
name = "saf-stig-generator"
# Add package discovery
packages = ["saf_stig_generator"]
package-dir = {"" = "src"}

[tool.setuptools]
package-dir = {"" = "src"}
packages = ["saf_stig_generator"]
```

### 4. Test Configuration

```python
# tests/conftest.py
import pytest
import sys
from pathlib import Path

# Add src to path for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
```

### 5. Development Setup

```python
# For development, install in editable mode
# pip install -e .
# This makes imports work consistently
```

## Benefits

1. **No more sys.path manipulation**
2. **Consistent imports across files**
3. **Better IDE support and autocomplete**
4. **Easier testing and debugging**
5. **Standard Python packaging practices**
