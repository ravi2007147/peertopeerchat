#!/bin/bash
# Run script for Peer-to-Peer Chat Application

echo "🚀 Starting Peer-to-Peer Chat Application..."

# Check if virtual environment exists
if [ ! -d "../myenv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source ../myenv/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please ensure you're in the correct directory."
    exit 1
fi

# Run the application
echo "✅ Starting application..."
python main.py

echo "👋 Application closed."