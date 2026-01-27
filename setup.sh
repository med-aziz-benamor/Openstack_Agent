#!/bin/bash
# Quick setup script for OpenStack Admin Assistant Portal

set -e

echo "🚀 OpenStack Admin Assistant Portal - Quick Setup"
echo "=================================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Build and start services
echo "📦 Building Docker images..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8088/api/health > /dev/null 2>&1; then
        echo "✅ Services are healthy!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Waiting for services... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  Services did not become healthy in time"
    echo "   Check logs with: docker compose logs"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ OpenStack Admin Assistant Portal is ready!"
echo "=================================================="
echo ""
echo "🌐 Web Interface:  http://localhost:8088"
echo "📚 API Docs:       http://localhost:8088/api/docs"
echo "🏥 Health Check:   http://localhost:8088/api/health"
echo ""
echo "Useful commands:"
echo "  make logs      - View logs"
echo "  make down      - Stop services"
echo "  make restart   - Restart services"
echo "  make test      - Run tests"
echo ""
echo "To create a sample bundle for testing:"
echo "  chmod +x scripts/create_sample_bundle.sh"
echo "  ./scripts/create_sample_bundle.sh"
echo ""
