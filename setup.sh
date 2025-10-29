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

# Check config
if [ ! -f "config.yaml" ]; then
    echo "⚠️  Warning: config.yaml not found"
    echo "   Please review and customize config.yaml before running"
else
    echo "✅ Configuration file found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "   source venv/bin/activate"
echo ""
echo "To start the bot, run:"
echo "   python main.py"
echo ""
echo "⚠️  IMPORTANT:"
echo "   1. Start IB Gateway on port 5000"
echo "   2. Enable API connections in Gateway settings"
echo "   3. Test in paper trading mode first"
echo ""

