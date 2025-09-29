# Kioti ECU Data Capture Module

## Overview
The Data Capture module records ECU operational data during specific scenarios with automated timing and self-healing connection management. Data is captured during cold start, idle, varying RPM, hydraulics operation, and PTO operation.

## Features
- **Scenario-based recording** with automated timing control
- **Cold start with 5-minute warm-up** period monitoring
- **2-minute idle operation** data collection
- **2-minute varying RPM** operation tracking
- **2-minute hydraulics operation** monitoring
- **30-second PTO operation** recording
- Automatic PID detection and configuration
- Configurable sampling rate (default: 1 Hz)
- CSV output for easy data analysis
- JSON metadata for session information
- Connection health monitoring with automatic reconnection
- Emergency stop capability (Ctrl+C)
- Real-time progress indicators
- Session statistics and summaries

## Prerequisites
- ECU Connection module must be set up and working
- Bluetooth OBD2 adapter paired and connected
- Vehicle/tractor must be accessible for operation

## Setup

### 1. Run Setup Script
```bash
cd "Data Capture"
./setup_data_capture.sh
```

The setup script will:
- Verify ECU Connection module is installed
- Use shared virtual environment
- Create data directories
- Verify all dependencies

### 2. Activate Virtual Environment
```bash
source "../ECU Connection/venv/bin/activate"
```

## Usage

### Basic Usage
Run a complete data capture session with all scenarios:

```bash
python3 data_capture.py
```

The script will:
1. Connect to ECU and detect supported PIDs
2. Display session information
3. Prompt you before each scenario begins
4. Capture data at 1 Hz (configurable)
5. Save CSV files for each scenario
6. Generate session metadata and statistics

### Data Capture Session Flow

1. **Cold Start + Warm-up (5 minutes)**
   - Start engine and begin capture immediately
   - Records initial cold start behavior
   - Continues through 5-minute warm-up period
   - Monitors temperature stabilization

2. **Idle Operation (2 minutes)**
   - Engine at idle speed after warm-up
   - Records steady-state idle behavior
   - Wait for prompt before starting

3. **Varying RPM Operation (2 minutes)**
   - Manually vary engine RPM during capture
   - Records response to throttle changes
   - Useful for analyzing engine dynamics

4. **Hydraulics Operation (2 minutes)**
   - Operate hydraulic systems during capture
   - Records system load and performance
   - May include loader, backhoe, or other hydraulics

5. **PTO Operation (30 seconds)**
   - Engage PTO during capture
   - Records PTO load characteristics
   - Brief duration to minimize equipment wear

### Emergency Stop
Press `Ctrl+C` at any time to safely stop data capture. The session will save all collected data up to that point.

## Output Structure

Each session creates a timestamped directory with organized data files:

```
data/
├── sessions/
│   └── YYYYMMDD_HHMMSS/           # Session timestamp
│       ├── session_metadata.json   # Session configuration and stats
│       ├── cold_start.csv          # Cold start data
│       ├── idle.csv                # Idle operation data
│       ├── varying_rpm.csv         # Varying RPM data
│       ├── hydraulics.csv          # Hydraulics operation data
│       └── pto.csv                 # PTO operation data
└── logs/
    └── data_capture_YYYYMMDD_HHMMSS.log
```

### CSV File Format
Each CSV file contains:
- `timestamp`: ISO format timestamp for each sample
- `elapsed_time`: Seconds since scenario start
- PID columns: One column per monitored PID with values

Example:
```csv
timestamp,elapsed_time,RPM,SPEED,COOLANT_TEMP,THROTTLE_POS
2025-09-29T10:30:00.123,0.000,850,0,45.5,12.3
2025-09-29T10:30:01.125,1.002,855,0,45.7,12.5
...
```

### Session Metadata (JSON)
Contains:
- Session ID and timestamps
- Sampling rate
- List of monitored PIDs
- Completed scenarios
- Statistics (total samples, failures, reconnections)
- ECU information (protocol, port)

## Advanced Usage

### Custom Sampling Rate
Edit `data_capture.py` to change sampling rate:

```python
# In main() function, modify this line:
capture = DataCapture(ecu, sampling_rate=2.0)  # 2 Hz instead of 1 Hz
```

**Note:** Higher sampling rates increase data volume and may stress the ECU. Test carefully.

### Custom PID Selection
To monitor specific PIDs instead of auto-detection:

```python
# In main() function, after creating capture object:
custom_pids = ['RPM', 'SPEED', 'COOLANT_TEMP', 'THROTTLE_POS']
capture.configure_pids(custom_pids)
```

### Individual Scenario Capture
To capture a single scenario programmatically:

```python
from data_capture import DataCapture, Scenario
from ecu_connection import ECUConnection

ecu = ECUConnection()
ecu.connect()

capture = DataCapture(ecu)
capture.configure_pids()

# Capture just idle scenario
capture.capture_scenario(Scenario.IDLE, prompt=True)

ecu.disconnect()
```

## Data Analysis Tips

### Loading Data in Python
```python
import pandas as pd

# Load a scenario
df = pd.read_csv('data/sessions/YYYYMMDD_HHMMSS/cold_start.csv')

# Plot RPM over time
import matplotlib.pyplot as plt
plt.plot(df['elapsed_time'], df['RPM'])
plt.xlabel('Time (s)')
plt.ylabel('RPM')
plt.title('Engine RPM During Cold Start')
plt.show()
```

### Analyzing Multiple Sessions
```python
from pathlib import Path
import json

# Find all sessions
sessions = Path('data/sessions').glob('*/session_metadata.json')

for session_file in sessions:
    with open(session_file) as f:
        metadata = json.load(f)
        print(f"Session: {metadata['session_id']}")
        print(f"Scenarios: {metadata['completed_scenarios']}")
        print(f"Samples: {metadata['statistics']['total_samples']}")
```

## Troubleshooting

### Connection Issues
If connection is lost during capture:
- Module will automatically attempt to reconnect
- Capture pauses during reconnection
- If reconnection succeeds, capture resumes
- If reconnection fails, session ends gracefully

### No PIDs Detected
If no PIDs are available:
- Verify ECU connection is working
- Check that engine is running (for some PIDs)
- Try running Protocol Discovery module first
- Some PIDs may only respond under specific conditions

### Sample Collection Errors
If many samples fail:
- Check connection stability
- Reduce sampling rate
- Verify specific PIDs are supported
- Check ECU Connection module logs

### Permission Errors
If you get permission errors accessing directories:
- Ensure you have write permissions in the module directory
- Check that data/ subdirectories exist
- Re-run setup script if needed

## Safety Notes

⚠️ **CRITICAL SAFETY REMINDERS:**
- This module performs READ-ONLY operations
- No ECU parameters are modified
- Safe to use during normal operation
- Emergency stop (Ctrl+C) works at any time
- Connection issues trigger automatic safety stops

⚠️ **OPERATIONAL SAFETY:**
- Ensure safe operating environment before starting
- Have another person assist with operation phases
- Follow all manufacturer safety guidelines
- Do not operate equipment in unsafe conditions

## Integration with Other Modules

### ECU Connection
- Shares virtual environment and dependencies
- Uses ECUConnection class for all communication
- Inherits connection stability features

### Protocol Discovery
- Can use Protocol Discovery results to select PIDs
- Load discovered PIDs from JSON output
- Focus on manufacturer-specific PIDs if found

## License
GPL-3.0 with Commons Clause License

---

For more information about the Kioti ECU Sniffer project, see the main README.md file.