#!/bin/bash
# Setup script for Kioti ECU Protocol Discovery Module
# GPL-3.0 with Commons Clause License

echo "================================"
echo "Protocol Discovery Setup"
echo "================================"
echo ""

# Check if running from correct directory
if [ ! -f "protocol_discovery.py" ]; then
    echo "Error: Please run this script from the 'Protocol Discovery' directory"
    exit 1
fi

# Check if ECU Connection module exists
if [ ! -f "../ECU Connection/ecu_connection.py" ]; then
    echo "Error: ECU Connection module not found"
    echo "Please ensure the ECU Connection module is set up first"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install obd > /dev/null 2>&1
echo "✓ Dependencies installed"

# Create data directory at project root level
echo ""
echo "Setting up data directories..."
mkdir -p ../data/protocol_discovery
mkdir -p logs
echo "✓ Directories created"

# Make Python script executable
chmod +x protocol_discovery.py

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To use the Protocol Discovery module:"
echo ""
echo "  1. Ensure your Bluetooth OBD2 adapter is paired"
echo "  2. Turn on vehicle ignition"
echo "  3. Run: source venv/bin/activate"
echo "  4. Run: python3 protocol_discovery.py"
echo ""
echo "Results will be saved to: ../data/protocol_discovery/"
echo "Logs will be saved to: logs/"
echo ""