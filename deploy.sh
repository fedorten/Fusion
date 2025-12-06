#!/bin/bash

# Deployment script for paerser2.ru
# Usage: ./deploy.sh [--no-cache]

set -e

echo "🚀 Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env file with required variables."
    exit 1
fi

# Load environment variables
source .env

# Set defaults
export DOMAIN=${DOMAIN:-paerser2.ru}
export DOCKER_IMAGE_BACKEND=${DOCKER_IMAGE_BACKEND:-messager-backend}
export DOCKER_IMAGE_FRONTEND=${DOCKER_IMAGE_FRONTEND:-messager-frontend}
export TAG=${TAG:-latest}
export ENVIRONMENT=${ENVIRONMENT:-production}

echo -e "${GREEN}✓ Environment variables loaded${NC}"
echo "  DOMAIN: $DOMAIN"
echo "  ENVIRONMENT: $ENVIRONMENT"

# Check if --no-cache flag is provided
NO_CACHE=""
if [[ "$1" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
    echo -e "${BLUE}ℹ️  Building without cache${NC}"
fi

# Build and deploy
echo -e "${YELLOW}📦 Building Docker images...${NC}"
docker compose -f docker-compose.prod.yml build $NO_CACHE

echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f docker-compose.prod.yml down

echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo "Your application should be available at:"
echo "  Frontend: http://$DOMAIN"
echo "  Backend API: http://$DOMAIN/api/v1"
echo "  API Docs: http://$DOMAIN/api/v1/docs"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To restart services:"
echo "  docker compose -f docker-compose.prod.yml restart"

