# Schemax - Databricks Schema Management CLI

A CLI tool for declarative Databricks schema management that uses LLM-powered change script generation.

## Overview

Schemax allows you to:
- Define Databricks catalogs, schemas, and tables in YAML
- Compare desired state against target environments
- Generate change scripts using Databricks LLM endpoints
- Run in CI/CD pipelines for automated schema management

## Features

- **Declarative Schema Definition**: Define your Databricks objects in YAML
- **LLM-Powered Change Generation**: Uses Databricks LLM endpoints with DSPy for intelligent change script generation  
- **Target Environment Inspection**: Automatically compares desired vs actual state
- **CI/CD Ready**: Designed for pipeline automation
- **Rich CLI Interface**: Beautiful terminal output with progress indicators

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file or set environment variables:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
DATABRICKS_LLM_ENDPOINT=databricks-meta-llama-3-1-405b-instruct
```

## Usage

### Generate Change Script

```bash
schemax generate --schema-file schema.yaml --target-catalog my_catalog --target-schema my_schema
```

### Apply Changes

```bash
schemax apply --schema-file schema.yaml --target-catalog my_catalog --target-schema my_schema
```

### Validate Schema

```bash
schemax validate --schema-file schema.yaml
```

## Schema Definition Format

```yaml
catalog:
  name: my_catalog
  comment: "Production data catalog"
  
schemas:
  - name: bronze
    comment: "Raw data layer"
    tables:
      - name: user_events
        type: EXTERNAL
        location: "s3://my-bucket/user-events/"
        columns:
          - name: user_id
            type: STRING
            nullable: false
          - name: event_time
            type: TIMESTAMP
            nullable: false
          - name: event_data
            type: STRING
            nullable: true
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
python -m pytest

# Format code
black schemax/
```

## CI/CD Pipeline

This project includes a comprehensive GitHub Actions workflow that runs:

- **Security Scanning**: Bandit, Safety, and pip-audit for code and dependency security
- **Code Quality**: Black formatting, isort, flake8, pylint, and mypy type checking
- **Testing**: Unit tests with coverage reporting
- **Build & Package**: Package building and validation
- **Dependency Review**: Automated dependency vulnerability scanning

### Dependency Review Setup

The dependency review step requires GitHub Advanced Security features. If you encounter the error:

```
Dependency review is not supported on this repository
```

**Option 1: Enable GitHub Advanced Security (Recommended)**
1. Go to your repository Settings
2. Navigate to Security & analysis
3. Enable "Dependency graph"
4. For private repositories, ensure you have a GitHub Advanced Security license

**Option 2: Use Alternative Security Scanning**
The workflow already includes comprehensive security scanning via:
- `safety` - Checks for known vulnerabilities in dependencies
- `pip-audit` - Additional dependency vulnerability scanning
- `bandit` - Static security analysis of Python code
- `semgrep` - Advanced static analysis

These tools provide similar functionality to the dependency review action without requiring GitHub Advanced Security.

**Local Security Scanning**
You can also run comprehensive security scans locally:

```bash
# Run the security scanning script
./scripts/security-scan.sh
```

This script runs all security tools and generates detailed reports in the `security-reports/` directory. 