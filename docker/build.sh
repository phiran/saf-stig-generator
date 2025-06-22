#!/bin/bash
# docker/build.sh

set -e

echo "Building SAF STIG Generator Docker images..."

# Change to project root
cd "$(dirname "$0")/.."

# Build base image
docker build -f docker/dockerfiles/base.Dockerfile -t saf-stig-generator:base .

# Build services image
docker build -f docker/dockerfiles/services.Dockerfile -t saf-stig-generator:services .

# Build agents image  
docker build -f docker/dockerfiles/agents.Dockerfile -t saf-stig-generator:agents .

# Build development image
docker build -f docker/dockerfiles/development.Dockerfile -t saf-stig-generator:development .

echo "All images built successfully!"