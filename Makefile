# Schemax Development Makefile

.PHONY: help install dev-install clean lint format test security check-all build release
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
PROJECT_NAME := schemax
SRC_DIR := schemax
TEST_DIR := tests

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Schemax Development Commands$(RESET)"
	@echo "$(BLUE)=============================$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install the package
	$(PIP) install -e .

dev-install: ## Install the package with development dependencies
	$(PIP) install -e ".[dev]"
	pre-commit install

# Cleaning targets
clean: ## Clean up build artifacts and cache files
	@echo "$(YELLOW)Cleaning up...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

# Code formatting and linting
format: ## Format code with black and isort
	@echo "$(YELLOW)Formatting code...$(RESET)"
	black $(SRC_DIR)/ $(TEST_DIR)/
	isort $(SRC_DIR)/ $(TEST_DIR)/
	@echo "$(GREEN)Code formatting complete!$(RESET)"

lint: ## Run all linting checks
	@echo "$(YELLOW)Running linting checks...$(RESET)"
	black --check $(SRC_DIR)/ $(TEST_DIR)/
	isort --check-only $(SRC_DIR)/ $(TEST_DIR)/
	flake8 $(SRC_DIR)/ $(TEST_DIR)/
	pylint $(SRC_DIR)/
	mypy $(SRC_DIR)/
	@echo "$(GREEN)Linting complete!$(RESET)"

# Testing targets
test: ## Run test suite
	@echo "$(YELLOW)Running tests...$(RESET)"
	pytest $(TEST_DIR)/ -v

test-cov: ## Run test suite with coverage
	@echo "$(YELLOW)Running tests with coverage...$(RESET)"
	pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-integration: ## Run integration tests only
	@echo "$(YELLOW)Running integration tests...$(RESET)"
	pytest $(TEST_DIR)/ -v -m integration

# Security checks
security: ## Run security scans
	@echo "$(YELLOW)Running security scans...$(RESET)"
	bandit -r $(SRC_DIR)/ -f txt
	safety check
	@echo "$(GREEN)Security scans complete!$(RESET)"

security-comprehensive: ## Run comprehensive security scans (alternative to GitHub Advanced Security)
	@echo "$(YELLOW)Running comprehensive security scans...$(RESET)"
	./scripts/security-scan.sh
	@echo "$(GREEN)Comprehensive security scans complete!$(RESET)"

security-report: ## Generate detailed security reports
	@echo "$(YELLOW)Generating security reports...$(RESET)"
	mkdir -p reports
	bandit -r $(SRC_DIR)/ -f json -o reports/bandit-report.json
	bandit -r $(SRC_DIR)/ -f html -o reports/bandit-report.html
	safety check --json --output reports/safety-report.json || true
	pip install pip-audit
	pip-audit --format json --output reports/pip-audit-report.json || true
	@echo "$(GREEN)Security reports generated in reports/ directory$(RESET)"

# Pre-commit hooks
pre-commit: ## Run pre-commit hooks on all files
	@echo "$(YELLOW)Running pre-commit hooks...$(RESET)"
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	@echo "$(YELLOW)Updating pre-commit hooks...$(RESET)"
	pre-commit autoupdate

# Comprehensive checks
check-all: lint test security ## Run all checks (linting, testing, security)
	@echo "$(GREEN)All checks passed!$(RESET)"

# Documentation
docs: ## Build documentation
	@echo "$(YELLOW)Building documentation...$(RESET)"
	cd docs && make html
	@echo "$(GREEN)Documentation built in docs/_build/html/$(RESET)"

docs-serve: ## Serve documentation locally
	@echo "$(YELLOW)Serving documentation on http://localhost:8000$(RESET)"
	cd docs/_build/html && $(PYTHON) -m http.server 8000

# Build and release
build: clean ## Build the package
	@echo "$(YELLOW)Building package...$(RESET)"
	$(PYTHON) -m build
	twine check dist/*
	@echo "$(GREEN)Package built successfully!$(RESET)"

release-test: build ## Upload to Test PyPI
	@echo "$(YELLOW)Uploading to Test PyPI...$(RESET)"
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

release: build ## Upload to PyPI
	@echo "$(YELLOW)Uploading to PyPI...$(RESET)"
	twine upload dist/*

# Development helpers
install-hooks: ## Install git hooks
	pre-commit install --hook-type pre-commit
	pre-commit install --hook-type commit-msg

requirements: ## Generate requirements.txt
	@echo "$(YELLOW)Generating requirements.txt...$(RESET)"
	pip-compile --output-file=requirements.txt pyproject.toml
	@echo "$(GREEN)requirements.txt generated!$(RESET)"

dev-setup: dev-install install-hooks ## Complete development setup
	@echo "$(GREEN)Development environment setup complete!$(RESET)"
	@echo "$(BLUE)You can now run:$(RESET)"
	@echo "  make lint     - Run linting checks"
	@echo "  make test     - Run tests"
	@echo "  make security - Run basic security scans"
	@echo "  make security-comprehensive - Run comprehensive security scans (alternative to GitHub Advanced Security)"
	@echo "  make check-all - Run all checks"

# Environment info
env-info: ## Show environment information
	@echo "$(BLUE)Environment Information$(RESET)"
	@echo "$(BLUE)======================$(RESET)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Pip version: $$($(PIP) --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Git status: $$(git status --porcelain 2>/dev/null | wc -l) modified files"

# CLI testing
cli-test: ## Test CLI commands
	@echo "$(YELLOW)Testing CLI commands...$(RESET)"
	$(PROJECT_NAME) --help
	$(PROJECT_NAME) --version
	@echo "$(GREEN)CLI tests complete!$(RESET)"

# Docker targets (if Dockerfile exists)
docker-build: ## Build Docker image
	@if [ -f Dockerfile ]; then \
		echo "$(YELLOW)Building Docker image...$(RESET)"; \
		docker build -t $(PROJECT_NAME):latest .; \
		echo "$(GREEN)Docker image built!$(RESET)"; \
	else \
		echo "$(RED)Dockerfile not found$(RESET)"; \
	fi

docker-run: ## Run Docker container
	@if [ -f Dockerfile ]; then \
		echo "$(YELLOW)Running Docker container...$(RESET)"; \
		docker run --rm -it $(PROJECT_NAME):latest; \
	else \
		echo "$(RED)Dockerfile not found$(RESET)"; \
	fi

# Benchmarking
benchmark: ## Run performance benchmarks
	@echo "$(YELLOW)Running benchmarks...$(RESET)"
	pytest $(TEST_DIR)/ -v -m benchmark --benchmark-only
	@echo "$(GREEN)Benchmarks complete!$(RESET)"

# Database/Schema testing
schema-test: ## Test schema validation with sample files
	@echo "$(YELLOW)Testing schema validation...$(RESET)"
	$(PROJECT_NAME) validate --schema-file examples/simple_schema.yaml
	$(PROJECT_NAME) validate --schema-file examples/sample_schema.yaml
	@if [ -f examples/advanced_schema.yaml ]; then \
		$(PROJECT_NAME) validate --schema-file examples/advanced_schema.yaml; \
	fi
	@echo "$(GREEN)Schema validation tests complete!$(RESET)"

# Version management
version: ## Show current version
	@$(PYTHON) -c "import $(SRC_DIR); print($(SRC_DIR).__version__)"

bump-patch: ## Bump patch version
	@echo "$(YELLOW)Bumping patch version...$(RESET)"
	bump2version patch

bump-minor: ## Bump minor version
	@echo "$(YELLOW)Bumping minor version...$(RESET)"
	bump2version minor

bump-major: ## Bump major version
	@echo "$(YELLOW)Bumping major version...$(RESET)"
	bump2version major 