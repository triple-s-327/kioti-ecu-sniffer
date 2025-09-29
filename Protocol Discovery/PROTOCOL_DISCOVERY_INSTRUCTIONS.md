# Protocol Discovery Module Instructions

## Purpose
Automatically determines the communication protocol used by the Kioti NS4710 ECU and discovers all available Parameter IDs (PIDs) for data querying.

## Features
- Automatic protocol detection and identification
- Standard OBD-II PID scanning (Mode 01)
- Optional manufacturer-specific PID scanning (Modes 21, 22)
- JSON and human-readable output formats
- Comprehensive logging of all discovery operations

## Setup

```bash
cd "Protocol Discovery"
./setup_protocol_discovery.sh
```

## Usage

### Basic Usage
```bash
source venv/bin/activate
python3 protocol_discovery.py
```

The script will prompt you to choose between:
1. **Quick scan** - Standard PIDs only (~30 seconds)
2. **Full scan** - Includes manufacturer-specific PIDs (~5 minutes)

### Discovery Process

The module performs the following steps:

1. **Protocol Detection**
   - Identifies the ECU's communication protocol
   - Records protocol name, ID, and port information
   - Counts number of ECUs detected

2. **Standard PID Scanning**
   - Tests all standard OBD-II Mode 01 PIDs
   - Records which PIDs respond with valid data
   - Captures sample values and units for each PID

3. **Custom PID Scanning** (optional)
   - Tests manufacturer-specific diagnostic modes
   - Scans for Kioti-specific PIDs
   - Records raw responses for analysis

## Output Files

All results are saved to `../data/protocol_discovery/`:

### JSON Results File
`discovery_results_YYYYMMDD_HHMMSS.json`
- Complete discovery data in structured JSON format
- Protocol information
- List of responding PIDs with details
- Sample values and units

### Summary Text File
`discovery_summary_YYYYMMDD_HHMMSS.txt`
- Human-readable summary
- Protocol details
- Table of available PIDs with descriptions

### Log Files
`logs/protocol_discovery_YYYYMMDD_HHMMSS.log`
- Detailed execution log
- All queries and responses
- Error messages and debugging information

## Safety Notes

- This module only performs READ operations
- No data is written to the ECU
- Small delays are included between queries to prevent ECU overload
- All operations are logged for review

## Troubleshooting

**No PIDs responding:**
- Verify ECU Connection module is working
- Ensure vehicle ignition is ON
- Check that engine is running for certain PIDs (RPM, etc.)

**Connection lost during scan:**
- The ECU Connection module's self-healing will attempt reconnection
- Partial results are still logged
- Re-run the discovery after connection is restored

**Manufacturer PIDs not responding:**
- Kioti may use non-standard modes
- Try different mode values if needed
- Some PIDs may only respond under specific conditions

## Next Steps

After discovery is complete:
1. Review the JSON and summary files
2. Identify PIDs of interest for data collection
3. Proceed to Data Collection module for continuous monitoring