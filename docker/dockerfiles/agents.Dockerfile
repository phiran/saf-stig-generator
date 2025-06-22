# docker/dockerfiles/agents.Dockerfile
FROM base as agents

# Copy source code (agents are in agents/ directory)
COPY agents/ ./agents/
COPY config/ ./config/

# Install the package in development mode to make agents importable
RUN uv pip install -e .

# Create artifacts directory
RUN mkdir -p /app/artifacts && chown app:app /app/artifacts

# Switch to non-root user
USER app

# Health check for agents
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Default ADK web interface startup
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]