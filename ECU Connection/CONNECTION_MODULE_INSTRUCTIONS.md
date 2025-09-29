# Kioti ECU Connection Module - Instructions

**GPL-3.0 with Commons Clause License**

## Overview
This module establishes and maintains a stable Bluetooth OBD2 connection to the Kioti NS4710 tractor ECU with automatic self-healing capabilities.

## Files
- `setup_connection.sh` - Setup script for dependencies and environment
- `ecu_connection.py` - Python module for ECU connection management
- `CONNECTION_MODULE_INSTRUCTIONS.md` - This file

## Prerequisites
- Linux operating system (tested on Ubuntu/Debian)
- ELM327 Bluetooth OBD2 adapter
- Kioti NS4710 tractor with OBD2 port access
- Root/sudo access for initial setup

## Setup Instructions

### 1. Initial Setup
Run the setup script to install dependencies and configure the environment:
```bash
./setup_connection.sh
```

This will:
- Install Python 3, Bluetooth utilities, and required system packages
- Create a Python virtual environment
- Install Python libraries (pyserial, pybluez, obd)
- Create `data/` and `logs/` directories
- Configure Bluetooth permissions

**IMPORTANT:** Log out and back in after setup for group permissions to take effect.

### 2. Pair Bluetooth Adapter
Before running the connection module, pair your ELM327 adapter:

```bash
bluetoothctl
scan on
# Wait for your adapter to appear (usually named "OBDII" or "ELM327")
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

### 3. Bind to Serial Port (if needed)
Some systems require binding the Bluetooth adapter to a serial port:

```bash
sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX
```

## Usage

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Run Connection Module
```bash
python3 ecu_connection.py
```

Or with specific port:
```bash
python3 ecu_connection.py --port /dev/rfcomm0
```

### Use as Python Module
```python
from ecu_connection import ECUConnection

# Create connection instance
ecu = ECUConnection()

# Connect to ECU
if ecu.connect():
    print("Connected successfully")

    # Get supported PIDs
    commands = ecu.get_supported_commands()

    # Query specific PID
    response = ecu.query_pid(obd.commands.RPM)

    # Start connection monitoring (blocks)
    ecu.maintain_connection()
```

## Features

### Self-Healing Connection
- Automatic health checks every 10 seconds
- Configurable reconnection attempts (default: 5)
- Exponential backoff between attempts
- Comprehensive logging of all connection events

### Safety Precautions
- Read-only queries to ECU (no write commands)
- Connection validation before each query
- Graceful error handling and disconnection
- Detailed logging for diagnostics

### Logging
All connection events are logged to timestamped files in `logs/`:
- Connection attempts and results
- Protocol and port information
- Reconnection events
- Error diagnostics

## Configuration

Edit `ecu_connection.py` to modify:
- `baudrate` (default: 38400)
- `reconnect_attempts` (default: 5)
- `reconnect_delay` (default: 3 seconds)
- `check_interval` (default: 10 seconds)

## Troubleshooting

### Connection Fails
1. Verify Bluetooth adapter is paired and connected
2. Ensure vehicle ignition is ON
3. Check adapter is bound to serial port: `ls -la /dev/rfcomm*`
4. Review logs in `logs/` directory

### Permission Errors
```bash
sudo usermod -a -G dialout $USER
sudo usermod -a -G bluetooth $USER
```
Then log out and back in.

### Adapter Not Found
```bash
# List available Bluetooth devices
hcitool scan

# Check Bluetooth service status
sudo systemctl status bluetooth
```

## Testing Checklist
- [ ] Setup script completes without errors
- [ ] Virtual environment activates successfully
- [ ] Bluetooth adapter pairs and connects
- [ ] Python script connects to ECU with ignition ON
- [ ] Connection health checks pass
- [ ] Automatic reconnection works after connection loss
- [ ] Log files created with detailed information

## Next Steps
This module provides the foundation for:
- PID discovery and querying (Module 2)
- Data collection during test scenarios (Module 3)
- Long-term data logging and analysis (Module 4)

## Support
Review log files in `logs/` directory for detailed diagnostic information.