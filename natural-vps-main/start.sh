#!/bin/bash
# Natural VPS Startup Script for Linux/Mac

cd "$(dirname "$0")"

echo "Checking if port 5000 is available..."
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 5000 is already in use. Choose a different port."
    read -p "Enter port (default 5000): " PORT
    PORT=${PORT:-5000}
    export PORT
else
    PORT=5000
fi

echo ""
echo "Starting Natural VPS on port $PORT..."
echo ""

python3 run.py
