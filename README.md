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