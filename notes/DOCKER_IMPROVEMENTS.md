# Docker and Deployment Organization

## Current Issues

1. **Scattered Dockerfiles** - Docker files in different directories
2. **Inconsistent service naming** - Mixed naming conventions
3. **No multi-stage builds** - Inefficient container sizes
4. **Mixed concerns** - Build and runtime configs together

## Recommended Docker Structure

```
docker/
├── dockerfiles/
│   ├── base.Dockerfile          # Base image with common dependencies
│   ├── services.Dockerfile      # MCP services image
│   ├── agents.Dockerfile        # ADK agents image
│   └── development.Dockerfile   # Development environment
├── compose/
│   ├── docker-compose.yml       # Main composition
│   ├── docker-compose.dev.yml   # Development overrides
│   ├── docker-compose.prod.yml  # Production overrides
│   └── docker-compose.test.yml  # Testing environment
└── scripts/
    ├── build.sh                 # Build script
    ├── deploy.sh               # Deployment script
    └── health-check.sh         # Health check script
```

## Multi-Stage Dockerfiles

### Base Image

```dockerfile
# docker/dockerfiles/base.Dockerfile
FROM python:3.13-slim-bookworm as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install UV
RUN pip install uv

# Copy and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
```

### Services Image

```dockerfile
# docker/dockerfiles/services.Dockerfile
FROM base as services

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Install in development mode
RUN uv pip install -e .

# Create non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default service startup
CMD ["python", "-m", "saf_stig_generator.services"]
```

### Development Image

```dockerfile
# docker/dockerfiles/development.Dockerfile
FROM base as development

# Install development dependencies
RUN uv sync --locked

# Copy source code
COPY . .

# Install in editable mode
RUN uv pip install -e .

# Install development tools
RUN uv pip install pytest pytest-asyncio black isort ruff

USER app

CMD ["bash"]
```

## Improved Docker Compose

### Main Composition

```yaml
# docker/compose/docker-compose.yml
version: '3.8'

services:
  # Vector database for memory tool
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - PERSIST_DIRECTORY=/chroma/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  # DISA STIG service
  disa-stig-service:
    build:
      context: ../..
      dockerfile: docker/dockerfiles/services.Dockerfile
    ports:
      - "8001:8000"
    volumes:
      - artifacts_data:/app/artifacts
    environment:
      - SAF_ENVIRONMENT=production
      - SERVICE_NAME=disa-stig
      - SERVICE_PORT=8000
    command: ["python", "-m", "saf_stig_generator.services.disa_stig"]
    depends_on:
      chromadb:
        condition: service_healthy

  # MITRE baseline service
  mitre-baseline-service:
    build:
      context: ../..
      dockerfile: docker/dockerfiles/services.Dockerfile
    ports:
      - "8002:8000"
    volumes:
      - artifacts_data:/app/artifacts
    environment:
      - SAF_ENVIRONMENT=production
      - SERVICE_NAME=mitre-baseline
      - SERVICE_PORT=8000
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    command: ["python", "-m", "saf_stig_generator.services.mitre_baseline"]

  # Memory service
  memory-service:
    build:
      context: ../..
      dockerfile: docker/dockerfiles/services.Dockerfile
    ports:
      - "8003:8000"
    environment:
      - SAF_ENVIRONMENT=production
      - SERVICE_NAME=memory
      - SERVICE_PORT=8000
      - CHROMADB_URL=http://chromadb:8000
    command: ["python", "-m", "saf_stig_generator.services.memory"]
    depends_on:
      chromadb:
        condition: service_healthy

  # Orchestrator agent
  orchestrator:
    build:
      context: ../..
      dockerfile: docker/dockerfiles/agents.Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - artifacts_data:/app/artifacts
    environment:
      - SAF_ENVIRONMENT=production
      - DISA_STIG_SERVICE_URL=http://disa-stig-service:8000
      - MITRE_BASELINE_SERVICE_URL=http://mitre-baseline-service:8000
      - MEMORY_SERVICE_URL=http://memory-service:8000
    command: ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]
    depends_on:
      - disa-stig-service
      - mitre-baseline-service
      - memory-service

volumes:
  chromadb_data:
  artifacts_data:

networks:
  default:
    name: saf-stig-generator
```

### Development Overrides

```yaml
# docker/compose/docker-compose.dev.yml
version: '3.8'

services:
  disa-stig-service:
    build:
      dockerfile: docker/dockerfiles/development.Dockerfile
    volumes:
      - ../../src:/app/src:ro
      - ../../config:/app/config:ro
    environment:
      - SAF_ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    command: ["python", "-m", "saf_stig_generator.services.disa_stig", "--reload"]

  mitre-baseline-service:
    build:
      dockerfile: docker/dockerfiles/development.Dockerfile
    volumes:
      - ../../src:/app/src:ro
      - ../../config:/app/config:ro
    environment:
      - SAF_ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    command: ["python", "-m", "saf_stig_generator.services.mitre_baseline", "--reload"]

  orchestrator:
    build:
      dockerfile: docker/dockerfiles/development.Dockerfile
    volumes:
      - ../../src:/app/src:ro
      - ../../agents:/app/agents:ro
    environment:
      - SAF_ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
```

## Build and Deployment Scripts

### Build Script

```bash
#!/bin/bash
# docker/scripts/build.sh

set -e

echo "Building SAF STIG Generator Docker images..."

# Build base image
docker build -f docker/dockerfiles/base.Dockerfile -t saf-stig-generator:base .

# Build services image
docker build -f docker/dockerfiles/services.Dockerfile -t saf-stig-generator:services .

# Build agents image  
docker build -f docker/dockerfiles/agents.Dockerfile -t saf-stig-generator:agents .

echo "All images built successfully!"
```

### Deployment Script

```bash
#!/bin/bash
# docker/scripts/deploy.sh

set -e

ENVIRONMENT=${1:-development}

echo "Deploying SAF STIG Generator in $ENVIRONMENT mode..."

case $ENVIRONMENT in
  development)
    docker-compose -f docker/compose/docker-compose.yml -f docker/compose/docker-compose.dev.yml up -d
    ;;
  production)
    docker-compose -f docker/compose/docker-compose.yml -f docker/compose/docker-compose.prod.yml up -d
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Deployment complete!"
```

## Benefits

1. **Organized structure** - Clear separation of Docker concerns
2. **Multi-stage builds** - Smaller, more efficient images
3. **Environment-specific** - Easy dev/prod deployment
4. **Health checks** - Proper service monitoring
5. **Volume management** - Persistent data handling
6. **Security** - Non-root containers

## 🧪 **Testing the Setup**

1. **Build Images**: `./docker/build.sh`
2. **Start Development**: `./docker/deploy.sh development`
3. **Check Health**: `./docker/health-check.sh`
4. **Verify Services**:
   - ChromaDB: <http://localhost:8000>
   - DISA STIG: <http://localhost:8001>
   - MITRE Baseline: <http://localhost:8002>
   - Memory: <http://localhost:8003>
   - Orchestrator: <http://localhost:8080>

Your Docker setup is now properly aligned with your refactored codebase and follows best practices for multi-environment deployment!
