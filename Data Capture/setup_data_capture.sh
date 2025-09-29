#!/bin/bash
# Setup script for Kioti ECU Data Capture Module
# GPL-3.0 with Commons Clause License

set -e

echo "=== Kioti ECU Data Capture Module Setup ==="
echo

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is designed for Linux systems"
    exit 1
fi

# Check if ECU Connection module is set up
if [ ! -d "../ECU Connection/venv" ]; then
    echo "Error: ECU Connection module not found or not set up"
    echo "Please run setup for ECU Connection module first"
    exit 1
fi

# Use existing virtual environment from ECU Connection module
VENV_PATH="../ECU Connection/venv"

echo "Using shared virtual environment from ECU Connection module..."
echo "Virtual environment path: $VENV_PATH"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install any additional dependencies (if needed in future)
echo "Verifying Python dependencies..."
pip install --quiet --upgrade \
    pyserial \
    pybluez \
    obd

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/sessions
mkdir -p data/logs

echo
echo "=== Setup Complete ==="
echo "Data Capture module is ready to use"
echo
echo "To run data capture:"
echo "  1. Activate virtual environment: source $VENV_PATH/bin/activate"
echo "  2. Run: python3 data_capture.py"
echo