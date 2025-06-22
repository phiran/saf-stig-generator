# Naming Convention Guidelines

## Package Naming

- **Current**: `saf_gen` (unclear abbreviation)
- **Recommended**: `saf_stig_generator` (descriptive, follows Python conventions)

## Module Naming Standards

### Agents

- **Current**: `orchestrator_agent.py`, `coding_agent.py`, `qa_agent.py`
- **Recommended**: `orchestrator.py`, `coding.py`, `qa.py`
- **Rationale**: "Agent" is redundant when in an `agents/` directory

### Services (Tools)

- **Current**: `disa_stig_tool.py`, `mitre_baseline_tool.py`
- **Recommended**: `service.py` within descriptive directories
- **Structure**:

  ```
  services/
  ├── disa_stig/
  │   └── service.py
  ├── mitre_baseline/
  │   └── service.py
  └── memory/
      └── service.py
  ```

### Configuration

- **Current**: `saf_config.py`
- **Recommended**: `config.py` within `common/`
- **Rationale**: Follows standard Python configuration patterns

## Class Naming

Follow PascalCase for classes:

- `OrchestratorAgent` → `Orchestrator`
- `DisaStigTool` → `DisaStigService`
- `MitreBaselineTool` → `MitreBaselineService`

## Function Naming

Use descriptive, verb-based names:

- `fetch_disa_stig()` ✓ (good)
- `find_mitre_baseline()` ✓ (good)
- `run_inspec_tests()` ✓ (good)

## Constant Naming

Use UPPER_SNAKE_CASE:

- `VERSION` ✓
- `TOOL_DESCRIPTION` ✓
- `DEFAULT_TIMEOUT` ✓

## Directory Naming

- Use lowercase with underscores for Python packages
- Use kebab-case for top-level project directories
- Examples:
  - `saf_stig_generator/` (package)
  - `test_data/` (directory)
  - `docker-compose.yml` (file)
