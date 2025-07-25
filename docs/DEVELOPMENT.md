# Schemax Development Guide

This guide covers development setup, coding standards, linting, security practices, and contribution workflows for Schemax.

## 🚀 Quick Development Setup

```bash
# Clone the repository
git clone https://github.com/VarunBhandary/schemax.git
cd schemax

# Complete development setup (installs dependencies and git hooks)
make dev-setup

# Or manually:
pip install -e ".[dev]"
pre-commit install
```

## 🛠️ Development Tools & Standards

### Code Quality Tools

We use a comprehensive set of tools to maintain high code quality:

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Black** | Code formatting | `pyproject.toml` |
| **isort** | Import sorting | `pyproject.toml` |
| **flake8** | Linting | `pyproject.toml` |
| **pylint** | Advanced linting | `pyproject.toml` |
| **mypy** | Type checking | `pyproject.toml` |
| **pre-commit** | Git hooks | `.pre-commit-config.yaml` |

### Security Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Bandit** | Security vulnerability scanning | `pyproject.toml` |
| **Safety** | Dependency vulnerability check | N/A |
| **Semgrep** | Advanced security patterns | Pre-commit hook |

## 🔧 Development Workflow

### 1. Setting Up Your Environment

```bash
# Activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make dev-install

# Verify setup
make env-info
```

### 2. Pre-Development Checks

Before starting development, ensure all tools are working:

```bash
# Run all checks
make check-all

# Individual checks
make lint      # Code quality
make test      # Run tests
make security  # Security scans
```

### 3. Development Loop

1. **Write Code**: Implement your changes
2. **Format Code**: `make format` (or let pre-commit handle it)
3. **Run Tests**: `make test` or `make test-cov`
4. **Security Check**: `make security`
5. **Commit**: Git hooks will run automatically

### 4. Pre-Commit Hooks

Pre-commit hooks run automatically on `git commit`:

- **Code Formatting**: Black, isort
- **Linting**: flake8, pylint, mypy
- **Security**: Bandit, safety
- **General**: trailing whitespace, file sizes, YAML validation
- **Documentation**: Markdown linting

To run hooks manually:
```bash
make pre-commit           # Run on all files
pre-commit run --all-files # Alternative command
```

## 📋 Code Standards

### Python Code Style

- **Line Length**: 88 characters (Black default)
- **Import Style**: Sorted by isort with Black profile
- **Type Hints**: Required for all public functions and methods
- **Docstrings**: Google style docstrings for all public APIs
- **Naming**: 
  - snake_case for functions and variables
  - PascalCase for classes
  - UPPER_CASE for constants

### Example Code Structure

```python
"""Module docstring explaining the purpose."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from schemax.exceptions import SchemaxError


class ExampleClass:
    """Class docstring explaining the purpose.
    
    Args:
        name: The name of the example.
        config: Optional configuration dictionary.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.config = config or {}
    
    def process_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Process data and return list of processed items.
        
        Args:
            data: List of data dictionaries to process.
            
        Returns:
            List of processed item names.
            
        Raises:
            SchemaxError: If data processing fails.
        """
        try:
            return [item["name"] for item in data if "name" in item]
        except Exception as e:
            raise SchemaxError(f"Data processing failed: {e}") from e
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_parser.py
│   └── test_client.py
├── integration/          # Integration tests
│   ├── test_databricks.py
│   └── test_llm.py
└── fixtures/            # Test data
    ├── schemas/
    └── responses/
```

### Test Categories

- **Unit Tests**: Fast, isolated tests for individual functions/classes
- **Integration Tests**: Test interactions between components
- **Security Tests**: Test security-related functionality

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Integration tests only
make test-integration

# Specific test file
pytest tests/unit/test_models.py -v

# Specific test function
pytest tests/unit/test_models.py::test_schema_validation -v
```

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_basic_functionality():
    """Unit test example."""
    pass

@pytest.mark.integration
def test_databricks_connection():
    """Integration test example."""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Slow test example."""
    pass
```

## 🔒 Security Practices

### Security Scanning

Regular security scans are mandatory:

```bash
# Run all security checks
make security

# Generate detailed reports
make security-report
```

### Security Guidelines

1. **No Hardcoded Secrets**: Use environment variables
2. **Input Validation**: Validate all external inputs
3. **Error Handling**: Don't expose sensitive information in errors
4. **Dependencies**: Keep dependencies updated
5. **Logging**: Be careful not to log sensitive data

### Handling Security Issues

1. **Never commit sensitive data**
2. **Use `.env` files for local development**
3. **Report security vulnerabilities privately**
4. **Follow responsible disclosure practices**

## 🚨 Troubleshooting Common Issues

### Pre-commit Hook Failures

```bash
# Hook failed due to formatting
make format
git add .
git commit -m "Your message"

# Update hooks
make pre-commit-update
```

### Linting Errors

```bash
# Auto-fix formatting issues
make format

# Check specific linting issues
flake8 schemax/
pylint schemax/
mypy schemax/
```

### Test Failures

```bash
# Run tests with verbose output
pytest -v --tb=short

# Run specific failing test
pytest tests/path/to/test.py::test_name -v

# Run with debugger
pytest --pdb tests/path/to/test.py::test_name
```

### Security Scan Failures

```bash
# Review security issues
bandit -r schemax/ -v

# Check dependency vulnerabilities
safety check --json
```

## 📦 Building and Releasing

### Building the Package

```bash
# Clean build
make build

# Test the built package
pip install dist/schemax-*.whl
schemax --help
```

### Release Process

1. **Update Version**: `make bump-patch` (or `bump-minor`, `bump-major`)
2. **Update Changelog**: Document changes
3. **Run Full Checks**: `make check-all`
4. **Create PR**: Submit for review
5. **Tag Release**: Create Git tag after merge
6. **CI/CD**: Automated build and publish

### Manual Release

```bash
# Test release
make release-test

# Production release
make release
```

## 🔍 Debugging Tips

### Development Debugging

```python
# Use rich for better debug output
from rich import print
print({"debug": "data"})

# Use pdb for debugging
import pdb; pdb.set_trace()
```

### Logging Configuration

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use rich logging
from rich.logging import RichHandler
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler()]
)
```

## 🤝 Contributing

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes following the coding standards
4. **Test** your changes: `make check-all`
5. **Commit** your changes: `git commit -m 'Add amazing feature'`
6. **Push** to the branch: `git push origin feature/amazing-feature`
7. **Open** a Pull Request

### Commit Message Format

We use conventional commits:

```
feat: add new schema validation feature
fix: resolve issue with table parsing
docs: update development guide
test: add unit tests for parser
refactor: improve error handling
chore: update dependencies
```

### Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Security scans pass
- [ ] Documentation updated
- [ ] Changelog updated (if needed)
- [ ] No sensitive data committed

## 📚 Additional Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [pylint Documentation](https://pylint.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [pre-commit Documentation](https://pre-commit.com/)
- [pytest Documentation](https://docs.pytest.org/)

## 🆘 Getting Help

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Security**: Report privately via GitHub Security Advisory
- **Development**: Check this guide and existing code examples

---

**Happy coding! 🚀** 