#!/bin/bash

# Schemax Installation Script

set -e

echo "🚀 Installing Schemax - Databricks Schema Management CLI"

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -lt 3 ] || [ "$major_version" -eq 3 -a "$minor_version" -lt 11 ]; then
    echo "❌ Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install package in development mode
echo "📥 Installing Schemax..."
pip install -e .

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy examples/env.example to .env and configure your settings"
echo "2. Run: source venv/bin/activate"
echo "3. Test with: schemax validate --schema-file examples/simple_schema.yaml"
echo ""
echo "📚 For more information, see README.md"
