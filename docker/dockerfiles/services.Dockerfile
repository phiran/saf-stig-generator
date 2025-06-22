# docker/dockerfiles/services.Dockerfile
FROM base as services

# Copy source code (services are in agents/saf_stig_generator/services/)
COPY agents/ ./agents/
COPY config/ ./config/

# Install the package in development mode
RUN uv pip install -e .

# Switch to non-root user
USER app

# Health check for services
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default service startup - this will be overridden by docker-compose
CMD ["python", "-m", "saf_stig_generator.services"]