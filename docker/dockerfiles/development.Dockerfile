# docker/dockerfiles/development.Dockerfile
FROM base as development

# Install development dependencies
RUN uv sync --locked

# Copy all source code for development
COPY . .

# Install in editable mode for development
RUN uv pip install -e .

# Install development tools
RUN uv pip install pytest pytest-asyncio black isort ruff mypy

# Switch to non-root user for development
USER app

# Default to bash for interactive development
CMD ["bash"]