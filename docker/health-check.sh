#!/bin/bash
# docker/health-check.sh

set -e

echo "SAF STIG Generator Health Check"
echo "================================"

# Check if containers are running
echo "Checking container status..."
docker-compose -f docker/compose/docker-compose.yml ps

echo ""
echo "Checking service health..."

# Check ChromaDB
echo -n "ChromaDB: "
if curl -f -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check DISA STIG Service
echo -n "DISA STIG Service: "
if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check MITRE Baseline Service
echo -n "MITRE Baseline Service: "
if curl -f -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Memory Service
echo -n "Memory Service: "
if curl -f -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Orchestrator
echo -n "Orchestrator: "
if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

echo ""
echo "Health check complete!"
