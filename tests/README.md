# MCP Tools Testing Documentation

## Overview

This directory contains comprehensive tests for all MCP (Model Context Protocol) tools in the SAF STIG Generator project.

## Test Structure

```
tests/
├── conftest.py                 # Shared pytest configuration and fixtures
├── requirements.txt            # Test dependencies
├── run_tests.py               # Comprehensive test runner
├── cli_test_helper.py         # CLI testing utilities
└── services/                  # Service-specific tests
    ├── test_disa_stig_tool.py
    ├── test_mitre_baseline_tool.py
    ├── test_saf_generator_tool.py
    ├── test_docker_tool.py
    ├── test_inspect_runner_tool.py
    └── test_memory_tool.py
```

## Test Categories

### Unit Tests

- **Purpose**: Test individual functions and methods in isolation
- **Pattern**: Mock all external dependencies (network, filesystem, Docker, etc.)
- **Coverage**: Core business logic, error handling, input validation

### Integration Tests

- **Purpose**: Test MCP tools through the FastMCP Client interface
- **Pattern**: Use in-memory testing as recommended by FastMCP
- **Coverage**: Tool registration, parameter handling, response formatting

### CLI Tests

- **Purpose**: Test command-line interface functionality
- **Pattern**: Subprocess execution with controlled inputs
- **Coverage**: Help text, version info, argument parsing, transport modes

## Key Testing Patterns

### FastMCP In-Memory Testing

Following the [FastMCP testing recommendations](https://gofastmcp.com/patterns/testing):

```python
@pytest.mark.asyncio
async def test_tool_via_mcp_client(self, mcp_server):
    """Test the tool through MCP client interface."""
    async with Client(mcp_server) as client:
        result_content, _ = await client.call_tool(
            "tool_name", {"param": "value"}
        )
        result = json.loads(result_content.text)
        assert result["status"] == "success"
```

### Mocking External Dependencies

```python
@patch("agents.saf_stig_generator.services.tool.external_dependency")
async def test_with_mocks(self, mock_dependency, mock_context):
    """Test with all external dependencies mocked."""
    mock_dependency.return_value = expected_result
    result = await tool_function("input", mock_context)
    assert json.loads(result)["status"] == "success"
```

### Error Handling Tests

```python
async def test_error_conditions(self, mock_context):
    """Test various error conditions."""
    # Test network errors, file not found, invalid inputs, etc.
    result = await tool_function("invalid_input", mock_context)
    result_data = json.loads(result)
    assert result_data["status"] == "failure"
    assert "error message" in result_data["message"]
```

## Tool-Specific Test Coverage

### DISA STIG Tool (`test_disa_stig_tool.py`)

- ✅ Successful STIG download and extraction
- ✅ Network error handling
- ✅ STIG not found scenarios
- ✅ CLI keyword functionality
- ✅ MCP client integration
- ✅ Resource endpoints (version, info)

### MITRE Baseline Tool (`test_mitre_baseline_tool.py`)

- ✅ Successful baseline cloning
- ✅ Git clone failures
- ✅ GitHub API search
- ✅ No results handling
- ✅ API error handling

### SAF Generator Tool (`test_saf_generator_tool.py`)

- ✅ Successful SAF stub generation
- ✅ Command failures
- ✅ File not found errors
- ✅ Timeout handling
- ✅ Resource endpoints

### Docker Tool (`test_docker_tool.py`)

- ✅ Image fetching success
- ✅ Docker daemon errors
- ✅ Image not found handling
- ✅ Connection errors

### InSpec Runner Tool (`test_inspect_runner_tool.py`)

- ✅ Successful test execution
- ✅ Command errors
- ✅ Invalid JSON output
- ✅ Timeout handling
- ✅ File path errors

### Memory Tool (`test_memory_tool.py`)

- ✅ Adding controls to memory
- ✅ Querying memory
- ✅ ChromaDB connection issues
- ✅ No results scenarios
- ✅ Exception handling

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
# Using the test runner
python tests/run_tests.py

# Or directly with pytest
pytest tests/services/ -v
```

### Run Specific Tool Tests

```bash
pytest tests/services/test_disa_stig_tool.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=agents --cov-report=term-missing
```

## Fixtures and Test Data

### Global Fixtures (`conftest.py`)

- `mock_context`: Mock MCP context for logging
- `temp_artifacts_dir`: Temporary directory for file operations
- `sample_stig_data`: Sample XCCDF content
- `sample_inspec_control`: Sample InSpec control
- `disa_downloads_page`: Mock DISA website HTML
- `mock_github_api_response`: Mock GitHub API responses

### Using Fixtures

```python
async def test_with_fixtures(self, mock_context, temp_artifacts_dir, sample_stig_data):
    """Test using shared fixtures."""
    # mock_context, temp_artifacts_dir, and sample_stig_data are automatically provided
```

## Best Practices

### Test Isolation

- Each test should be independent
- Use fresh mocks for each test
- Clean up any state changes

### Async Testing

- Use `@pytest.mark.asyncio` for async tests
- Properly await async functions
- Handle async context managers correctly

### Mocking Guidelines

- Mock at the boundary (external dependencies)
- Use specific patches for each test
- Verify mock calls when relevant

### Error Testing

- Test all expected error conditions
- Verify error messages are helpful
- Check proper error propagation

## Tool Improvements Made

### Added Resource Endpoints

All tools now have standardized resource endpoints:

- `{tool-name}://version` - Returns tool version
- `{tool-name}://info` - Returns tool metadata and configuration

### Fixed Function Signatures

- Corrected parameter ordering in memory tool
- Standardized async function patterns
- Fixed import issues in test files

### Enhanced Error Handling

- Better error messages
- Proper exception propagation
- Consistent JSON response formats

### CLI Testing Framework

- Helper classes for CLI testing
- Standardized CLI argument testing
- Transport mode validation

## Continuous Integration

These tests are designed to run in CI/CD environments:

- No external dependencies required (all mocked)
- Fast execution (in-memory testing)
- Clear pass/fail indicators
- Detailed error reporting

For GitHub Actions or similar CI systems, use:

```yaml
- name: Run MCP Tool Tests
  run: |
    pip install -r tests/requirements.txt
    python tests/run_tests.py
```
