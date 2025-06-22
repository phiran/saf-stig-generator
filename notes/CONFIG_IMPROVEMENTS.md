# Configuration Management Improvements

## Current Issues

1. **Scattered configuration files** - Config logic in multiple places
2. **Unclear environment handling** - Manual .env loading in multiple files  
3. **Hardcoded paths** - Some paths not configurable
4. **No validation** - Configuration values not validated
5. **Mixed concerns** - Config mixed with business logic

## Recommended Configuration Structure

```
src/saf_stig_generator/common/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── base.py              # Base configuration
│   ├── development.py       # Development settings
│   ├── production.py        # Production settings
│   ├── testing.py          # Test settings
│   └── settings.py         # Settings loader
├── exceptions.py
└── types.py
```

## Configuration Classes

### Base Configuration

```python
# src/saf_stig_generator/common/config/base.py
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, validator

class BaseConfig(BaseSettings):
    """Base configuration with common settings."""
    
    # Project paths
    project_root: Path = Path(__file__).parent.parent.parent.parent
    artifacts_dir: Path = project_root / "artifacts"
    downloads_dir: Path = artifacts_dir / "downloads"
    generated_dir: Path = artifacts_dir / "generated"
    
    # Service settings
    log_level: str = "INFO"
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # External service URLs
    disa_stig_base_url: str = "https://public.cyber.mil/stigs/downloads/"
    github_api_base_url: str = "https://api.github.com"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("artifacts_dir", pre=True)
    def ensure_artifacts_dir_exists(cls, v):
        """Ensure artifacts directory exists."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
```

### Environment-Specific Configurations

```python
# src/saf_stig_generator/common/config/development.py
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    debug: bool = True
    log_level: str = "DEBUG"
    
    # Use local paths for development
    artifacts_dir: Path = BaseConfig.project_root / "artifacts"
    
    class Config:
        env_file = "config/development.env"

# src/saf_stig_generator/common/config/production.py
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    debug: bool = False
    log_level: str = "WARNING"
    
    # Could use cloud storage paths
    artifacts_dir: Path = Path("/app/artifacts")
    
    class Config:
        env_file = "config/production.env"

# src/saf_stig_generator/common/config/testing.py
from .base import BaseConfig
import tempfile

class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    debug: bool = True
    log_level: str = "DEBUG"
    
    # Use temporary directories for testing
    artifacts_dir: Path = Path(tempfile.mkdtemp())
    
    class Config:
        env_file = "config/testing.env"
```

### Settings Loader

```python
# src/saf_stig_generator/common/config/settings.py
import os
from typing import Type
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

# Configuration mapping
CONFIG_MAPPING = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

def get_config() -> BaseConfig:
    """Get configuration based on environment."""
    env = os.getenv("SAF_ENVIRONMENT", "development").lower()
    config_class = CONFIG_MAPPING.get(env, DevelopmentConfig)
    return config_class()

# Global configuration instance
settings = get_config()
```

### Usage in Services

```python
# src/saf_stig_generator/services/disa_stig/service.py
from ...common.config import settings

class DisaStigService:
    def __init__(self):
        self.base_url = settings.disa_stig_base_url
        self.downloads_dir = settings.downloads_dir
        self.timeout = settings.timeout_seconds
    
    async def fetch_stig(self, product_keyword: str):
        # Use configured values
        pass
```

## Environment Files

### Development Environment

```bash
# config/development.env
SAF_ENVIRONMENT=development
LOG_LEVEL=DEBUG
ARTIFACTS_DIR=./artifacts
GITHUB_TOKEN=your_dev_token_here
DOCKER_REGISTRY=localhost:5000
```

### Production Environment  

```bash
# config/production.env
SAF_ENVIRONMENT=production
LOG_LEVEL=WARNING
ARTIFACTS_DIR=/app/artifacts
GITHUB_TOKEN=${GITHUB_TOKEN}
DOCKER_REGISTRY=gcr.io/your-project
```

## Benefits

1. **Type safety** with Pydantic validation
2. **Environment separation** - Clear dev/prod/test configs
3. **Validation** - Config values validated at startup
4. **Documentation** - Self-documenting configuration
5. **Testing** - Easy to override for tests
6. **Deployment** - Environment-specific settings
