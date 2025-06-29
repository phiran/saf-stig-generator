# InSpec Runner Service - Based on official Chef InSpec Docker image
FROM chef/inspec:latest

WORKDIR /app

# Install Python for MCP server support
USER root
RUN apk add --no-cache \
  python3 \
  py3-pip \
  py3-venv \
  curl \
  git \
  build-base \
  python3-dev

# Accept Chef license
ENV CHEF_LICENSE=accept-silent

# Create app user and directories
RUN addgroup -g 1000 app && adduser -u 1000 -G app -s /bin/sh -D app
RUN mkdir -p /app/service /app/common /app/artifacts /app/venv && \
  chown -R app:app /app

# Switch to app user
USER app

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=1

# Create virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy Python source code and dependencies
COPY --chown=app:app agents/saf_stig_generator/services/inspect_runner/ /app/service/
COPY --chown=app:app agents/saf_stig_generator/common/ /app/common/
COPY --chown=app:app pyproject.toml uv.lock /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install fastmcp anyio uvicorn && \
  pip install -e .

# Create directories for artifacts
RUN mkdir -p /app/artifacts/generated

# Expose MCP server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Start the MCP server
CMD ["python3", "/app/service/service.py"]
