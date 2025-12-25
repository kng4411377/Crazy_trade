#!/bin/bash
# Setup script for Crazy Trade Bot

set -e

echo "🚀 Setting up Crazy Trade Bot..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

echo "📌 Detected Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Setup config files
if [ ! -f "config.yaml" ]; then
    if [ -f "config.yaml.example" ]; then
        echo "📝 Creating config.yaml from template..."
        cp config.yaml.example config.yaml
        echo "   ✅ config.yaml created - please customize it for your needs"
    else
        echo "⚠️  Warning: config.yaml and config.yaml.example not found"
    fi
else
    echo "✅ config.yaml already exists"
fi

if [ ! -f "momentum_config.yaml" ]; then
    if [ -f "momentum_config.yaml.example" ]; then
        echo "📝 Creating momentum_config.yaml from template..."
        cp momentum_config.yaml.example momentum_config.yaml
        echo "   ✅ momentum_config.yaml created (momentum layer disabled by default)"
    else
        echo "⚠️  Warning: momentum_config.yaml.example not found"
    fi
else
    echo "✅ momentum_config.yaml already exists"
fi

if [ ! -f "secrets.yaml" ]; then
    if [ -f "secrets.yaml.example" ]; then
        echo "📝 Creating secrets.yaml from template..."
        cp secrets.yaml.example secrets.yaml
        echo "   ⚠️  REQUIRED: Add your Alpaca API keys to secrets.yaml"
    else
        echo "⚠️  Warning: secrets.yaml and secrets.yaml.example not found"
    fi
else
    echo "✅ secrets.yaml already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "   source venv/bin/activate"
echo ""
echo "To start the bot, run:"
echo "   ./run.sh"
echo ""
echo "⚠️  IMPORTANT:"
echo "   1. Get Alpaca API keys from https://app.alpaca.markets/"
echo "   2. Update config.yaml with your API keys"
echo "   3. Test in paper trading mode first"
echo ""

