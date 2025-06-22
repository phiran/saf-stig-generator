# Testing Structure Improvements

## Current Issues

1. **Scattered test files** - Tests in multiple locations without clear organization
2. **Inconsistent test naming** - Some follow patterns, others don't
3. **Missing test utilities** - No shared fixtures or test helpers
4. **Import path complexity** - Tests struggling with imports

## Recommended Testing Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared pytest configuration
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── sample_stig.xml
│   ├── sample_baseline/
│   └── mock_responses.json
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_agents/
│   │   ├── __init__.py
│   │   ├── test_orchestrator.py
│   │   ├── test_coding.py
│   │   └── test_qa.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   ├── test_disa_stig.py
│   │   ├── test_mitre_baseline.py
│   │   ├── test_memory.py
│   │   ├── test_docker.py
│   │   └── test_inspec_runner.py
│   └── test_common/
│       ├── __init__.py
│       ├── test_config.py
│       └── test_types.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_workflows/
│   │   ├── __init__.py
│   │   ├── test_full_workflow.py
│   │   └── test_error_handling.py
│   └── test_mcp_services/
│       ├── __init__.py
│       └── test_service_communication.py
└── performance/               # Performance tests
    ├── __init__.py
    └── test_benchmarks.py
```

## Test Configuration (conftest.py)

```python
import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def temp_artifacts_dir():
    """Create temporary artifacts directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_context():
    """Mock MCP context for testing."""
    return AsyncMock()

@pytest.fixture
def sample_stig_data():
    """Load sample STIG data for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "sample_stig.xml") as f:
        return f.read()

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

## Naming Conventions

### Test File Naming

- `test_<module_name>.py` - Test the module
- Use descriptive test function names:

  ```python
  def test_fetch_disa_stig_success()
  def test_fetch_disa_stig_not_found()
  def test_orchestrator_handles_missing_baseline()
  ```

### Test Class Organization

```python
class TestDisaStigService:
    """Tests for DISA STIG service functionality."""
    
    async def test_fetch_stig_success(self, mock_context):
        """Test successful STIG fetching."""
        pass
    
    async def test_fetch_stig_network_error(self, mock_context):
        """Test handling of network errors."""
        pass

class TestDisaStigServiceIntegration:
    """Integration tests for DISA STIG service."""
    
    async def test_full_fetch_and_extract_workflow(self):
        """Test the complete fetch and extract process."""
        pass
```

## Test Data Management

### Fixtures Directory Structure

```
fixtures/
├── stigs/
│   ├── rhel_9_stig.xml
│   └── windows_2022_stig.xml
├── baselines/
│   ├── sample_baseline/
│   │   ├── controls/
│   │   └── inspec.yml
├── responses/
│   ├── disa_downloads_page.html
│   ├── github_search_results.json
│   └── docker_hub_results.json
└── configs/
    └── test_env.env
```

## Benefits

1. **Clear separation** between unit, integration, and performance tests
2. **Shared fixtures** reduce code duplication
3. **Consistent naming** makes tests easy to find and understand
4. **Proper async handling** for MCP services
5. **Isolated test environments** prevent interference
