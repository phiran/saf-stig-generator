# SAF STIG Generator: Comprehensive Organization & Naming Review

## Executive Summary

Your Google ADK and FastMCP project shows good architectural thinking but needs structural improvements to follow Python 3.x best practices. Here are the priority recommendations:

## 🚨 **Critical Issues (Fix First)**

### 1. **Package Structure Reorganization**

**Current Problem**: Duplicated agents, inconsistent import paths
**Impact**: Maintenance burden, testing difficulties, unclear dependencies

**Immediate Actions**:

1. Consolidate all code under `src/saf_stig_generator/`
2. Remove duplicated agent files
3. Standardize import paths
4. Update `pyproject.toml` for proper package discovery

### 2. **Import Path Standardization**

**Current Problem**: Complex sys.path manipulation in tests and imports
**Impact**: Fragile imports, IDE issues, testing problems

**Immediate Actions**:

1. Install package in editable mode: `pip install -e .`
2. Use relative imports within package
3. Remove all `sys.path.insert()` statements
4. Update test configuration

## 🔧 **Recommended Project Structure**

```
saf-stig-generator/
├── src/
│   └── saf_stig_generator/           # Renamed from saf_gen
│       ├── __init__.py
│       ├── agents/                   # Centralized agents
│       │   ├── __init__.py
│       │   ├── orchestrator.py       # Renamed from orchestrator_agent.py
│       │   ├── coding.py            # Renamed from coding_agent.py
│       │   └── qa.py               # Renamed from qa_agent.py
│       ├── services/               # MCP tools
│       │   ├── __init__.py
│       │   ├── disa_stig/
│       │   │   ├── __init__.py
│       │   │   └── service.py      # Renamed from disa_stig_tool.py
│       │   ├── mitre_baseline/
│       │   ├── memory/
│       │   ├── docker/
│       │   └── saf_generator/
│       ├── common/
│       │   ├── __init__.py
│       │   ├── config/             # Configuration management
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── development.py
│       │   │   ├── production.py
│       │   │   └── settings.py
│       │   ├── types.py
│       │   └── exceptions.py
│       └── cli/
├── tests/
│   ├── conftest.py               # Shared test configuration
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker/
│   ├── dockerfiles/
│   ├── compose/
│   └── scripts/
├── config/                       # Environment configurations
│   ├── development.env
│   ├── production.env
│   └── testing.env
├── docs/
├── artifacts/
└── scripts/
```

## 📋 **Implementation Roadmap**

### Phase 1: Core Restructuring (Priority 1)

- [ ] Create new `src/saf_stig_generator/` structure
- [ ] Move and rename agent files
- [ ] Update import statements
- [ ] Fix pyproject.toml package configuration
- [ ] Test basic imports work

### Phase 2: Service Organization (Priority 2)  

- [ ] Reorganize services into subdirectories
- [ ] Rename tool files to `service.py`
- [ ] Update MCP server initialization
- [ ] Fix service import paths
- [ ] Update Docker service references

### Phase 3: Configuration Management (Priority 3)

- [ ] Implement Pydantic-based configuration
- [ ] Create environment-specific configs
- [ ] Add configuration validation
- [ ] Update services to use new config
- [ ] Environment variable standardization

### Phase 4: Testing Infrastructure (Priority 4)

- [ ] Reorganize test structure
- [ ] Create shared test fixtures
- [ ] Implement test configuration
- [ ] Add integration test framework
- [ ] Update CI/CD pipelines

### Phase 5: Docker & Deployment (Priority 5)

- [ ] Reorganize Docker files
- [ ] Implement multi-stage builds
- [ ] Create environment-specific compose files
- [ ] Add deployment scripts
- [ ] Health check implementation

## 🔧 **Quick Wins (Implement Today)**

### 1. Update pyproject.toml

```toml
[project]
name = "saf-stig-generator"
packages = ["saf_stig_generator"]
package-dir = {"" = "src"}

[tool.setuptools]
package-dir = {"" = "src"}
packages = ["saf_stig_generator"]
```

### 2. Create src/saf_stig_generator/**init**.py

```python
"""SAF STIG Generator - Automated MITRE SAF baseline generation."""

__version__ = "0.1.0"
__author__ = "Your Name"

# Re-export main components
from .agents.orchestrator import Orchestrator
from .common.config.settings import settings

__all__ = ["Orchestrator", "settings"]
```

### 3. Install in Editable Mode

```bash
pip install -e .
```

### 4. Update a Test File Example

```python
# tests/unit/test_services/test_disa_stig.py
import pytest
from saf_stig_generator.services.disa_stig import DisaStigService

class TestDisaStigService:
    async def test_fetch_stig_success(self):
        service = DisaStigService()
        # Test implementation
```

## 🎯 **Best Practices to Follow**

### Naming Conventions

- **Packages**: `lowercase_with_underscores`
- **Modules**: `descriptive_names.py` (avoid redundant suffixes)
- **Classes**: `PascalCase`
- **Functions**: `snake_case_verbs`
- **Constants**: `UPPER_SNAKE_CASE`

### Import Conventions

```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
from fastmcp import FastMCP
from adk.agent import Agent

# Local imports (use relative within package)
from ..common.config import settings
from .base import BaseService
```

### Documentation Standards

- Use Google-style docstrings
- Include type hints for all functions
- Document complex configuration options
- Maintain README files for each major component

## 🚀 **Expected Benefits**

After implementing these changes:

1. **Cleaner Imports**: No more `sys.path` manipulation
2. **Better Testing**: Proper test isolation and fixtures
3. **Easier Development**: Standard Python packaging
4. **Improved Maintainability**: Clear separation of concerns
5. **Professional Structure**: Industry-standard organization
6. **Better IDE Support**: Autocomplete and navigation
7. **Deployment Ready**: Production-grade configuration

## 📞 **Next Steps**

1. **Start with Phase 1** - Focus on core restructuring first
2. **Test incrementally** - Ensure each phase works before moving on
3. **Update documentation** - Keep README and docs current
4. **Review dependencies** - Check for unused packages
5. **Set up CI/CD** - Automate testing and deployment

This restructuring will transform your project into a professional, maintainable Python package that follows industry best practices for Google ADK and FastMCP development.
