# Kioti ECU Sniffer

A modular toolkit for interfacing with and analyzing Kioti NS4710 tractor ECU data via Bluetooth OBD2 communication.

## Project Goals

- Establish stable, self-healing Bluetooth OBD2 connection to tractor ECU
- Learn and document the Kioti NS4710 ECU communication protocol
- Actively query all available PIDs and record responses
- Collect comprehensive operational data across various operating conditions
- Provision data for future GUI development

## Modules

### ECU Connection

Stable Bluetooth OBD2 connection module with self-healing capabilities for reliable ECU communication.

**Features:**
- Automatic connection and reconnection logic
- Health monitoring and comprehensive logging
- Read-only safety precautions to protect ECU
- Support for ELM327 Bluetooth adapters

**Usage:**
```bash
cd "ECU Connection"
./setup_connection.sh
source venv/bin/activate
python3 ecu_connection.py
```

### Protocol Discovery

Automatically detects ECU communication protocol and discovers all available PIDs for querying.

**Features:**
- Automatic protocol detection and identification
- Standard OBD-II PID scanning (Mode 01)
- Optional manufacturer-specific PID scanning
- JSON and human-readable output formats
- Comprehensive logging of discovery operations

**Usage:**
```bash
cd "Protocol Discovery"
./setup_protocol_discovery.sh
source venv/bin/activate
python3 protocol_discovery.py
```

## Data Collection Plan

The project aims to collect ECU data during the following operational scenarios:

1. **Cold start with warm-up**: 5-minute period
2. **Idle operations**: 2-minute period after warm-up
3. **Varying engine RPM**: 2-minute period after warm-up
4. **Hydraulic operations**: 2-minute period after warm-up
5. **PTO operation**: 30-second period

All data is timestamped and logged for analysis.

## Requirements

- Linux system (tested on Ubuntu/Debian)
- Python 3.x
- Bluetooth-enabled system
- ELM327 Bluetooth OBD2 adapter
- Kioti NS4710 tractor

## Safety

This project implements read-only precautions to prevent accidental ECU modifications. All operations are designed for diagnostic and data collection purposes only.

## License

GPL-3.0 with Commons Clause

## Contributing

This is a research and development project. Contributions should maintain the modular architecture and safety-first approach to ECU communication.