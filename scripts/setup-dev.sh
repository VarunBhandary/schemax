#!/bin/bash

# Schemax Development Setup Script
# This script sets up a complete development environment

set -e

echo "🚀 Setting up Schemax development environment..."

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python 3.11+ is available
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo -e "${GREEN}✓ Python $python_version is compatible${NC}"
else
    echo -e "${RED}✗ Python $python_version is too old. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
python3 -m pip install --upgrade pip

# Install the package in development mode
echo -e "${BLUE}Installing package in development mode...${NC}"
pip install -e ".[dev]"

# Install pre-commit hooks
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
pre-commit install

# Run initial formatting
echo -e "${BLUE}Running initial code formatting...${NC}"
black schemax/ tests/
isort schemax/ tests/

# Run security scan
echo -e "${BLUE}Running initial security scan...${NC}"
bandit -r schemax/ || true

# Run tests
echo -e "${BLUE}Running tests...${NC}"
python -m pytest tests/ -v

echo ""
echo -e "${GREEN}🎉 Development environment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Create a virtual environment (recommended):"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo ""
echo "2. Make your first commit to test pre-commit hooks:"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""
echo "3. Use the Makefile for common tasks:"
echo "   make help          # Show all available commands"
echo "   make check-all     # Run all checks"
echo "   make test          # Run tests"
echo "   make security      # Run security scans"
echo ""
echo -e "${YELLOW}Note: Pre-commit hooks will run automatically on every commit${NC}"
echo -e "${YELLOW}to ensure code quality and consistency.${NC}"
