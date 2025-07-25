#!/bin/bash

# Security scanning script for Schemax
# This script provides comprehensive security scanning including dependency review
# as an alternative to GitHub Advanced Security dependency review

set -e

echo "🔒 Running comprehensive security scan for Schemax..."

# Install security tools if not already installed
echo "📦 Installing security tools..."
pip install --quiet bandit[toml] safety pip-audit semgrep

# Create reports directory
mkdir -p security-reports

echo "🔍 Running Bandit security scan..."
bandit -r schemax/ -f json -o security-reports/bandit-report.json
bandit -r schemax/ -f txt -o security-reports/bandit-report.txt

echo "📋 Running Safety dependency scan..."
safety check --json --output security-reports/safety-report.json
safety check --full-report > security-reports/safety-report.txt

echo "🔍 Running pip-audit dependency scan..."
pip-audit --format json --output security-reports/pip-audit-report.json
pip-audit --format text > security-reports/pip-audit-report.txt

echo "🔍 Running Semgrep static analysis..."
semgrep scan --config auto --json --output security-reports/semgrep-report.json
semgrep scan --config auto --output security-reports/semgrep-report.txt

echo "📊 Generating security summary..."
{
    echo "Security Scan Summary"
    echo "===================="
    echo ""
    echo "Bandit Issues:"
    if [ -f security-reports/bandit-report.txt ]; then
        cat security-reports/bandit-report.txt | grep -E "(Issue:|Total issues)" || echo "No issues found"
    fi
    echo ""
    echo "Safety Issues:"
    if [ -f security-reports/safety-report.txt ]; then
        cat security-reports/safety-report.txt | grep -E "(VULNERABILITY|Total vulnerabilities)" || echo "No vulnerabilities found"
    fi
    echo ""
    echo "pip-audit Issues:"
    if [ -f security-reports/pip-audit-report.txt ]; then
        cat security-reports/pip-audit-report.txt | grep -E "(VULNERABILITY|Found)" || echo "No vulnerabilities found"
    fi
    echo ""
    echo "Semgrep Issues:"
    if [ -f security-reports/semgrep-report.txt ]; then
        cat security-reports/semgrep-report.txt | grep -E "(WARNING|ERROR)" || echo "No issues found"
    fi
} > security-reports/security-summary.txt

echo "✅ Security scan completed!"
echo "📁 Reports saved to security-reports/"
echo "📋 Summary: security-reports/security-summary.txt"

# Display summary
echo ""
echo "=== Security Summary ==="
cat security-reports/security-summary.txt
