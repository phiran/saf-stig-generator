# Project Structure Recommendations

## Current Structure Issues

1. **Duplicated Agents**: Files exist in both `/agents/` and `/agents/src/saf_gen/agents/`
2. **Inconsistent Service Locations**: Services in `/agents/services/` should be in `/src/saf_stig_generator/services/`
3. **Non-Standard Package Structure**: Should follow Python packaging best practices

## Recommended Structure

```
saf-stig-generator/
├── src/
│   └── saf_stig_generator/           # Main package (renamed from saf_gen)
│       ├── __init__.py
│       ├── agents/                   # Centralized agents
│       │   ├── __init__.py
│       │   ├── orchestrator.py       # Renamed from orchestrator_agent.py
│       │   ├── coding.py            # Renamed from coding_agent.py
│       │   └── qa.py               # Renamed from qa_agent.py
│       ├── services/               # MCP tools/services
│       │   ├── __init__.py
│       │   ├── disa_stig/
│       │   │   ├── __init__.py
│       │   │   └── service.py      # Renamed from disa_stig_tool.py
│       │   ├── mitre_baseline/
│       │   │   ├── __init__.py
│       │   │   └── service.py
│       │   ├── memory/
│       │   ├── docker/
│       │   ├── inspec_runner/
│       │   └── saf_generator/
│       ├── common/
│       │   ├── __init__.py
│       │   ├── config.py           # Renamed from saf_config.py
│       │   ├── types.py            # Common type definitions
│       │   └── exceptions.py       # Custom exceptions
│       └── cli/                    # Command-line interfaces
│           ├── __init__.py
│           └── main.py
├── tests/
│   ├── __init__.py
│   ├── unit/                       # Unit tests
│   │   ├── test_agents/
│   │   ├── test_services/
│   │   └── test_common/
│   ├── integration/                # Integration tests
│   │   └── test_workflows/
│   └── fixtures/                   # Test data
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── artifacts/                     # Runtime artifacts
│   ├── downloads/
│   └── generated/
├── docker/                        # Docker files
│   ├── services/
│   └── docker-compose.yml
├── pyproject.toml
├── README.md
└── LICENSE
```

## Benefits of This Structure

1. **Clear separation of concerns**
2. **Standard Python packaging**
3. **Easier imports and testing**
4. **Better IDE support**
5. **Follows ADK and FastMCP best practices**
