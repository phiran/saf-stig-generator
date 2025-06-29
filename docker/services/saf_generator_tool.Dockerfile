# SAF Generator Service - Based on official MITRE SAF CLI Docker image
FROM mitre/saf:latest

WORKDIR /app

# Install Python for MCP server support
USER root
RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create app user and set ownership
RUN groupadd -r app && useradd -r -g app app
RUN chown -R app:app /app

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
COPY --chown=app:app agents/saf_stig_generator/services/saf_generator/ /app/service/
COPY --chown=app:app agents/saf_stig_generator/common/ /app/common/
COPY --chown=app:app pyproject.toml uv.lock /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install fastmcp anyio uvicorn && \
  pip install -e .

# Create directories for artifacts and bind mount points
RUN mkdir -p /app/artifacts/generated /share

# Expose MCP server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Start the MCP server
CMD ["python3", "/app/service/service.py"]
