# docker/dockerfiles/base.Dockerfile
FROM python:3.13-slim-bookworm as base

# Install system dependencies including Docker for some services
RUN apt-get update && apt-get install -y \
  git \
  curl \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  UV_LINK_MODE=copy

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --locked --no-dev

# Create common directories
RUN mkdir -p /app/artifacts /app/config && \
  chown -R app:app /app/artifacts /app/config