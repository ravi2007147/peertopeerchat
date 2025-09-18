#!/bin/bash
# Setup script for Peer-to-Peer Chat Application

echo "Setting up Peer-to-Peer Chat Application..."

# Check if virtual environment exists
if [ ! -d "../myenv" ]; then
    echo "Creating virtual environment at ../myenv"
    python3 -m venv ../myenv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ../myenv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing required packages..."
pip install -r requirements.txt

# Run database migration if needed
echo "Checking database migration..."
if [ -f "migrate_db.py" ]; then
    python migrate_db.py
fi

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Activate virtual environment: source ../myenv/bin/activate"
echo "2. Run the application: python index.py"
echo ""
echo "Or use the run script: ./run.sh"
