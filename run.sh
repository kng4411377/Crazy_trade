#!/bin/bash
# Quick start script for Crazy Trade Bot

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found"
    echo "Please create a config.yaml file first"
    exit 1
fi

# Run the bot
echo "🚀 Starting Crazy Trade Bot..."
python main.py "$@"

