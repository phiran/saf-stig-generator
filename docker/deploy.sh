#!/bin/bash
# docker/deploy.sh

set -e

ENVIRONMENT=${1:-development}
ACTION=${2:-up}

echo "Deploying SAF STIG Generator in $ENVIRONMENT mode..."

# Change to project root to ensure correct context
cd "$(dirname "$0")/.."

case $ENVIRONMENT in
  development)
    docker-compose -f docker/compose/docker-compose.yml -f docker/compose/docker-compose.dev.yml $ACTION -d
    ;;
  production)
    docker-compose -f docker/compose/docker-compose.yml -f docker/compose/docker-compose.prod.yml $ACTION -d
    ;;
  testing)
    docker-compose -f docker/compose/docker-compose.test.yml $ACTION --abort-on-container-exit
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Usage: $0 [development|production|testing] [up|down|restart]"
    exit 1
    ;;
esac

if [ "$ACTION" = "up" ]; then
    echo "Deployment complete!"
    echo "Services are starting up. Check status with: docker-compose ps"
else
    echo "Action '$ACTION' completed!"
fi