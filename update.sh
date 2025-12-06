#!/bin/bash

# Quick update script - updates code and redeploys
# Usage: ./update.sh

set -e

echo "🔄 Starting update..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Ask user if they want to pull from git
if [ -d ".git" ]; then
    read -p "Pull latest changes from Git? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📥 Pulling latest changes from Git...${NC}"
        git pull
    fi
fi

# Run deploy script
echo -e "${YELLOW}🚀 Redeploying...${NC}"
./deploy.sh

echo -e "${GREEN}✅ Update completed!${NC}"

