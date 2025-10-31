#!/bin/bash
# Start the Crazy Trade Bot API Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Default port
PORT=${1:-8080}

echo "Starting Crazy Trade Bot API Server on port $PORT..."
python3 api_server.py --port $PORT

