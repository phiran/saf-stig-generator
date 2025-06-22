# InSpec Runner Service - Official Chef InSpec Docker image with MCP server
FROM chef/inspec:latest

WORKDIR /app

# Accept Chef license
ENV CHEF_LICENSE=accept-silent

# Install Python for MCP server
USER root
RUN apk add --no-cache \
  python3 \
  py3-pip \
  py3-venv \
  curl \
  git \
  build-base \
  python3-dev

# Create app user and directories
RUN addgroup -g 1000 app && adduser -u 1000 -G app -s /bin/sh -D app

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=1

# Create virtual environment and set ownership
RUN python3 -m venv /app/venv && \
  mkdir -p /app/service /app/common /app/artifacts && \
  chown -R app:app /app

# Switch to app user
USER app

# Activate virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy Python source and dependencies
COPY --chown=app:app agents/saf_stig_generator/services/inspect_runner/ /app/service/
COPY --chown=app:app agents/saf_stig_generator/common/ /app/common/
COPY --chown=app:app pyproject.toml /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install fastmcp anyio uvicorn && \
  pip install -e .

# Create directories for artifacts
RUN mkdir -p /app/artifacts/generated

# Expose MCP server port
EXPOSE 3000

# Environment variables for InSpec
ENV INSPEC_PATH=/usr/bin/inspec

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Start the MCP server
CMD ["python3", "/app/service/service.py"]
