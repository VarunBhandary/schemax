#!/bin/bash

# Schemax Development Environment Setup Script
# This script sets up a complete development environment for Schemax

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Main setup function
main() {
    log_info "🚀 Setting up Schemax development environment..."
    
    # Check if we're in the right directory
    if [[ ! -f "pyproject.toml" ]] || [[ ! -d "schemax" ]]; then
        log_error "Please run this script from the Schemax root directory"
        exit 1
    fi
    
    # Check Python version
    log_info "Checking Python version..."
    if ! check_command python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Found Python $PYTHON_VERSION"
    
    # Verify Python version is 3.8+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python version is compatible"
    else
        log_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    # Check if virtual environment is active
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_warning "Virtual environment not detected. It's recommended to use a virtual environment."
        read -p "Do you want to create and activate a virtual environment? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Creating virtual environment..."
            python3 -m venv venv
            log_info "Activating virtual environment..."
            source venv/bin/activate
            log_success "Virtual environment created and activated"
        fi
    else
        log_success "Virtual environment detected: $VIRTUAL_ENV"
    fi
    
    # Upgrade pip
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    # Install package in development mode
    log_info "Installing package in development mode..."
    pip install -e ".[dev]"
    log_success "Package installed successfully"
    
    # Install pre-commit hooks
    log_info "Installing pre-commit hooks..."
    if check_command pre-commit; then
        pre-commit install --hook-type pre-commit
        pre-commit install --hook-type commit-msg
        log_success "Pre-commit hooks installed"
        
        # Install hooks in the repository
        log_info "Installing hook scripts..."
        pre-commit install --install-hooks
        log_success "Hook scripts installed"
    else
        log_error "pre-commit not found after installation"
        exit 1
    fi
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file from template..."
        if [[ -f "examples/env.example" ]]; then
            cp examples/env.example .env
            log_success ".env file created from template"
            log_warning "Please edit .env file with your Databricks credentials"
        else
            log_warning "env.example not found, creating basic .env file"
            cat > .env << 'EOF'
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=your-databricks-token
DATABRICKS_WAREHOUSE_ID=your-warehouse-id

# LLM Configuration
DATABRICKS_LLM_ENDPOINT=databricks-meta-llama-3-1-405b-instruct

# Optional: Schemax specific settings
SCHEMAX_LOG_LEVEL=INFO
SCHEMAX_OUTPUT_FORMAT=console
EOF
            log_success "Basic .env file created"
        fi
    else
        log_info ".env file already exists"
    fi
    
    # Create necessary directories
    log_info "Creating necessary directories..."
    mkdir -p reports
    mkdir -p docs/_build
    mkdir -p tests/fixtures
    log_success "Directories created"
    
    # Run initial checks
    log_info "Running initial code quality checks..."
    
    # Check if there are any Python files to lint
    if find schemax -name "*.py" | head -1 | grep -q .; then
        # Run a quick format check
        if black --check schemax/ >/dev/null 2>&1; then
            log_success "Code formatting looks good"
        else
            log_warning "Code needs formatting. Run 'make format' to fix."
        fi
        
        # Run a quick lint check
        if flake8 schemax/ >/dev/null 2>&1; then
            log_success "Basic linting passed"
        else
            log_warning "Linting issues found. Run 'make lint' for details."
        fi
    fi
    
    # Test CLI installation
    log_info "Testing CLI installation..."
    if schemax --version >/dev/null 2>&1; then
        log_success "CLI installed successfully"
        SCHEMAX_VERSION=$(schemax --version 2>&1 | head -1)
        log_info "Installed version: $SCHEMAX_VERSION"
    else
        log_warning "CLI test failed. Try running 'pip install -e .' again"
    fi
    
    # Run basic tests if they exist
    if [[ -d "tests" ]] && find tests -name "*.py" | head -1 | grep -q .; then
        log_info "Running basic tests..."
        if python3 -m pytest tests/ --maxfail=1 -q >/dev/null 2>&1; then
            log_success "Basic tests passed"
        else
            log_warning "Some tests failed. Run 'make test' for details."
        fi
    fi
    
    # Security check
    log_info "Running basic security scan..."
    if bandit -r schemax/ -q >/dev/null 2>&1; then
        log_success "No security issues found"
    else
        log_warning "Security issues detected. Run 'make security' for details."
    fi
    
    # Summary
    echo
    log_success "🎉 Development environment setup complete!"
    echo
    echo "Next steps:"
    echo "1. Edit .env file with your Databricks credentials"
    echo "2. Run 'make check-all' to verify everything works"
    echo "3. Run 'make help' to see available commands"
    echo "4. Check 'docs/DEVELOPMENT.md' for detailed development guide"
    echo
    echo "Available make targets:"
    echo "  make dev-install    - Install development dependencies"
    echo "  make format         - Format code with black and isort"
    echo "  make lint           - Run all linting checks"
    echo "  make test           - Run test suite"
    echo "  make test-cov       - Run tests with coverage"
    echo "  make security       - Run security scans"
    echo "  make check-all      - Run all checks"
    echo "  make pre-commit     - Run pre-commit hooks manually"
    echo
    
    # Check if Make is available
    if check_command make; then
        log_info "GNU Make is available. You can use 'make help' for more commands."
    else
        log_warning "GNU Make not found. You'll need to run commands manually."
        echo "Alternative commands:"
        echo "  python3 -m pytest              # Run tests"
        echo "  black schemax/ tests/           # Format code"
        echo "  flake8 schemax/ tests/          # Lint code"
        echo "  bandit -r schemax/              # Security scan"
    fi
    
    # Final environment check
    echo
    log_info "Environment Summary:"
    echo "  Python: $(python3 --version)"
    echo "  Pip: $(pip --version | cut -d' ' -f1-2)"
    echo "  Virtual Environment: ${VIRTUAL_ENV:-"Not active"}"
    echo "  Working Directory: $(pwd)"
    echo "  Git Branch: $(git branch --show-current 2>/dev/null || echo "Not a git repository")"
    
    log_success "Setup completed successfully! Happy coding! 🚀"
}

# Handle script interruption
trap 'log_error "Setup interrupted by user"; exit 1' INT

# Run main function
main "$@" 