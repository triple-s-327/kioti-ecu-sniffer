#!/bin/bash
# Setup script for Kioti ECU Connection Module
# GPL-3.0 with Commons Clause License

set -e

echo "=== Kioti ECU Connection Module Setup ==="
echo

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is designed for Linux systems"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    bluez \
    bluetooth \
    libbluetooth-dev \
    rfkill

# Enable Bluetooth
echo "Enabling Bluetooth..."
sudo rfkill unblock bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment and install Python packages
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install \
    pyserial \
    pybluez \
    obd

# Create necessary directories
echo "Creating project directories..."
mkdir -p ../data
mkdir -p logs

# Set permissions for Bluetooth access
echo "Configuring Bluetooth permissions..."
sudo usermod -a -G dialout $USER
sudo usermod -a -G bluetooth $USER

echo
echo "=== Setup Complete ==="
echo "NOTE: You may need to log out and back in for group permissions to take effect"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo