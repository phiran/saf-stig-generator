# SAF CLI Service - Official MITRE SAF Docker image with MCP server
FROM mitre/saf:latest

WORKDIR /app

# Install Python for MCP server
USER root
RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=1

# Create virtual environment and set ownership
RUN python3 -m venv /app/venv && \
  chown -R app:app /app

# Switch to app user
USER app

# Activate virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy Python source and dependencies
COPY --chown=app:app agents/saf_stig_generator/services/saf_generator/ /app/service/
COPY --chown=app:app agents/saf_stig_generator/common/ /app/common/
COPY --chown=app:app pyproject.toml /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install fastmcp anyio uvicorn && \
  pip install -e .

# Create directories for artifacts and shared volume mounts
RUN mkdir -p /app/artifacts/generated /share

# Expose MCP server port
EXPOSE 3000

# Environment variables for SAF CLI
ENV SAF_CLI_PATH=/usr/local/bin/saf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Start the MCP server
CMD ["python3", "/app/service/service.py"]
