#!/usr/bin/env python3
"""
Kioti NS4710 ECU Data Capture Module
Captures ECU data during operational scenarios with automated timing
GPL-3.0 with Commons Clause License
"""

import sys
import csv
import json
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Add parent directory to path for ECU Connection module import
sys.path.append(str(Path(__file__).parent.parent / "ECU Connection"))
from ecu_connection import ECUConnection

import obd


class Scenario(Enum):
    """Operational scenarios for data capture"""
    COLD_START = ("cold_start", 300)  # 5 minutes
    IDLE = ("idle", 120)  # 2 minutes
    VARYING_RPM = ("varying_rpm", 120)  # 2 minutes
    HYDRAULICS = ("hydraulics", 120)  # 2 minutes
    PTO = ("pto", 30)  # 30 seconds

    def __init__(self, filename: str, duration: int):
        self.filename = filename
        self.duration = duration


class DataCapture:
    """Manages scenario-based ECU data capture with automated timing"""

    def __init__(self, ecu_connection: ECUConnection, data_dir: str = "data",
                 sampling_rate: float = 1.0):
        """
        Initialize data capture module

        Args:
            ecu_connection: Active ECU connection instance
            data_dir: Base directory for data storage
            sampling_rate: Samples per second (default: 1.0 Hz)
        """
        self.ecu = ecu_connection
        self.sampling_rate = sampling_rate
        self.sampling_interval = 1.0 / sampling_rate

        # Directory structure
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.logs_dir = self.data_dir / "logs"

        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Session variables
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.sessions_dir / self.session_timestamp
        self.session_dir.mkdir(exist_ok=True)

        # Monitoring PIDs
        self.monitored_pids = []
        self.pid_commands = {}

        # Capture control
        self.is_capturing = False
        self.emergency_stop = False

        # Statistics
        self.stats = {
            "total_samples": 0,
            "failed_samples": 0,
            "reconnections": 0
        }

        self._setup_logging()
        self._setup_signal_handlers()

    def _setup_logging(self):
        """Configure logging with timestamped log file"""
        log_file = self.logs_dir / f"data_capture_{self.session_timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Data capture log file: {log_file}")
        self.logger.info(f"Session directory: {self.session_dir}")

    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            self.logger.warning("\nEmergency stop triggered!")
            self.emergency_stop = True
            self.is_capturing = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def configure_pids(self, pid_list: Optional[List[str]] = None):
        """
        Configure which PIDs to monitor during capture

        Args:
            pid_list: List of PID command names. If None, auto-detect supported PIDs
        """
        self.logger.info("Configuring PIDs for monitoring...")

        if pid_list:
            # Use specified PIDs
            for pid_name in pid_list:
                try:
                    cmd = obd.commands[pid_name]
                    self.monitored_pids.append(pid_name)
                    self.pid_commands[pid_name] = cmd
                    self.logger.info(f"  Added PID: {pid_name}")
                except KeyError:
                    self.logger.warning(f"  Unknown PID: {pid_name}")
        else:
            # Auto-detect supported PIDs
            supported = self.ecu.get_supported_commands()

            # Filter for most relevant PIDs
            priority_pids = [
                'RPM', 'SPEED', 'THROTTLE_POS', 'ENGINE_LOAD',
                'COOLANT_TEMP', 'INTAKE_TEMP', 'MAF', 'FUEL_LEVEL',
                'FUEL_PRESSURE', 'TIMING_ADVANCE', 'INTAKE_PRESSURE',
                'FUEL_RATE', 'ABSOLUTE_LOAD', 'THROTTLE_ACTUATOR',
                'CONTROL_MODULE_VOLTAGE', 'AMBIANT_AIR_TEMP'
            ]

            for cmd in supported:
                if cmd.name in priority_pids:
                    self.monitored_pids.append(cmd.name)
                    self.pid_commands[cmd.name] = cmd
                    self.logger.info(f"  Added PID: {cmd.name}")

        self.logger.info(f"Total PIDs configured: {len(self.monitored_pids)}")

        if not self.monitored_pids:
            self.logger.warning("No PIDs configured for monitoring!")

    def _create_csv_file(self, scenario: Scenario) -> Tuple[Path, object, object]:
        """
        Create CSV file for scenario data

        Args:
            scenario: Scenario enum

        Returns:
            Tuple of (file_path, csv_writer, file_handle)
        """
        csv_file = self.session_dir / f"{scenario.filename}.csv"

        file_handle = open(csv_file, 'w', newline='')
        writer = csv.writer(file_handle)

        # Write header
        header = ['timestamp', 'elapsed_time'] + self.monitored_pids
        writer.writerow(header)

        self.logger.info(f"Created CSV file: {csv_file}")

        return csv_file, writer, file_handle

    def _capture_sample(self) -> Dict:
        """
        Capture a single data sample from all monitored PIDs

        Returns:
            dict: Sample data with timestamp
        """
        sample = {
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        for pid_name in self.monitored_pids:
            try:
                cmd = self.pid_commands[pid_name]
                response = self.ecu.query_pid(cmd)

                if response and not response.is_null():
                    # Extract value, handling different response types
                    if hasattr(response.value, 'magnitude'):
                        # Pint quantity
                        value = float(response.value.magnitude)
                    else:
                        value = str(response.value)

                    sample['data'][pid_name] = value
                else:
                    sample['data'][pid_name] = None

            except Exception as e:
                self.logger.debug(f"Error reading {pid_name}: {e}")
                sample['data'][pid_name] = None
                self.stats['failed_samples'] += 1

        self.stats['total_samples'] += 1
        return sample

    def _check_and_maintain_connection(self) -> bool:
        """
        Check connection health and reconnect if needed

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.ecu.check_connection():
            self.logger.warning("Connection lost during capture - attempting reconnection...")
            self.stats['reconnections'] += 1

            if self.ecu.reconnect():
                self.logger.info("Reconnection successful - resuming capture")
                return True
            else:
                self.logger.error("Reconnection failed - stopping capture")
                return False

        return True

    def capture_scenario(self, scenario: Scenario, prompt: bool = True) -> bool:
        """
        Capture data for a specific operational scenario

        Args:
            scenario: Scenario enum
            prompt: Whether to prompt user before starting

        Returns:
            bool: True if capture completed successfully
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"SCENARIO: {scenario.name.replace('_', ' ').title()}")
        self.logger.info(f"Duration: {scenario.duration} seconds")
        self.logger.info("=" * 60)

        if prompt:
            try:
                print(f"\nPrepare for {scenario.name.replace('_', ' ')} scenario.")
                print(f"Duration: {scenario.duration} seconds ({scenario.duration // 60}:{scenario.duration % 60:02d})")
                input("Press ENTER when ready to start (Ctrl+C for emergency stop)... ")
            except KeyboardInterrupt:
                self.logger.warning("Scenario cancelled by user")
                return False

        # Create CSV file
        csv_file, writer, file_handle = self._create_csv_file(scenario)

        # Start capture
        self.is_capturing = True
        start_time = time.time()
        sample_count = 0

        self.logger.info(f"Starting capture at {self.sampling_rate} Hz...")

        try:
            while self.is_capturing and not self.emergency_stop:
                elapsed = time.time() - start_time

                # Check if scenario duration is complete
                if elapsed >= scenario.duration:
                    self.logger.info(f"Scenario duration complete ({scenario.duration}s)")
                    break

                # Check connection health
                if not self._check_and_maintain_connection():
                    self.logger.error("Cannot continue without connection")
                    return False

                # Capture sample
                sample = self._capture_sample()

                # Write to CSV
                row = [
                    sample['timestamp'],
                    f"{elapsed:.3f}"
                ]
                row.extend([sample['data'].get(pid, '') for pid in self.monitored_pids])
                writer.writerow(row)

                sample_count += 1

                # Progress indication (every 10 samples)
                if sample_count % 10 == 0:
                    progress = (elapsed / scenario.duration) * 100
                    remaining = scenario.duration - elapsed
                    print(f"  Progress: {progress:.1f}% | Samples: {sample_count} | "
                          f"Remaining: {int(remaining)}s", end='\r')

                # Sleep until next sample
                next_sample_time = start_time + (sample_count * self.sampling_interval)
                sleep_time = next_sample_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            self.logger.error(f"Error during capture: {e}")
            return False

        finally:
            file_handle.close()
            self.is_capturing = False
            print()  # New line after progress indicator

        self.logger.info(f"Captured {sample_count} samples")
        self.logger.info(f"Data saved to: {csv_file}")

        return True

    def run_full_session(self):
        """
        Run complete data capture session with all scenarios
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("STARTING FULL DATA CAPTURE SESSION")
        self.logger.info("=" * 60)
        self.logger.info(f"Session ID: {self.session_timestamp}")
        self.logger.info(f"Sampling rate: {self.sampling_rate} Hz")
        self.logger.info(f"Monitored PIDs: {len(self.monitored_pids)}")
        self.logger.info("=" * 60 + "\n")

        scenarios = [
            Scenario.COLD_START,
            Scenario.IDLE,
            Scenario.VARYING_RPM,
            Scenario.HYDRAULICS,
            Scenario.PTO
        ]

        completed_scenarios = []

        for scenario in scenarios:
            if self.emergency_stop:
                self.logger.warning("Session stopped by emergency stop")
                break

            success = self.capture_scenario(scenario)

            if success:
                completed_scenarios.append(scenario.name)
            else:
                self.logger.error(f"Failed to complete {scenario.name}")

                # Ask user if they want to continue
                try:
                    choice = input("\nContinue with remaining scenarios? (y/n): ").strip().lower()
                    if choice != 'y':
                        break
                except KeyboardInterrupt:
                    break

        # Save session metadata
        self._save_session_metadata(completed_scenarios)

        # Display statistics
        self._display_session_summary(completed_scenarios)

    def _save_session_metadata(self, completed_scenarios: List[str]):
        """Save session metadata to JSON file"""
        metadata_file = self.session_dir / "session_metadata.json"

        metadata = {
            "session_id": self.session_timestamp,
            "start_time": self.session_timestamp,
            "end_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "sampling_rate_hz": self.sampling_rate,
            "monitored_pids": self.monitored_pids,
            "completed_scenarios": completed_scenarios,
            "statistics": self.stats,
            "ecu_info": {
                "protocol": self.ecu.connection.protocol_name() if self.ecu.is_connected else "Unknown",
                "port": self.ecu.connection.port_name() if self.ecu.is_connected else "Unknown"
            }
        }

        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            self.logger.info(f"Session metadata saved to: {metadata_file}")

        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")

    def _display_session_summary(self, completed_scenarios: List[str]):
        """Display session summary statistics"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("SESSION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Session ID: {self.session_timestamp}")
        self.logger.info(f"Completed scenarios: {len(completed_scenarios)}/{len(Scenario)}")

        for scenario in completed_scenarios:
            self.logger.info(f"  ✓ {scenario.replace('_', ' ').title()}")

        self.logger.info(f"\nTotal samples collected: {self.stats['total_samples']}")
        self.logger.info(f"Failed sample reads: {self.stats['failed_samples']}")
        self.logger.info(f"Connection reconnections: {self.stats['reconnections']}")

        if self.stats['total_samples'] > 0:
            success_rate = ((self.stats['total_samples'] - self.stats['failed_samples'])
                           / self.stats['total_samples'] * 100)
            self.logger.info(f"Sample success rate: {success_rate:.1f}%")

        self.logger.info(f"\nData saved to: {self.session_dir}")
        self.logger.info("=" * 60 + "\n")


def main():
    """Main execution for data capture"""
    print("=== Kioti NS4710 ECU Data Capture ===\n")

    # Initialize ECU connection
    print("Initializing ECU connection...")
    ecu = ECUConnection()

    if not ecu.connect():
        print("\n✗ Failed to connect to ECU")
        print("\nPlease ensure:")
        print("  1. Bluetooth adapter is paired and connected")
        print("  2. Vehicle ignition is ON")
        print("  3. ELM327 adapter is functioning")
        sys.exit(1)

    print("✓ ECU connected\n")

    # Initialize data capture
    capture = DataCapture(ecu, sampling_rate=1.0)

    # Configure PIDs (auto-detect)
    print("Detecting supported PIDs...")
    capture.configure_pids()

    if not capture.monitored_pids:
        print("\n✗ No PIDs available for monitoring")
        ecu.disconnect()
        sys.exit(1)

    print(f"✓ Configured {len(capture.monitored_pids)} PIDs for monitoring\n")

    # Display session info
    print("=" * 60)
    print("DATA CAPTURE SESSION")
    print("=" * 60)
    print(f"Session ID: {capture.session_timestamp}")
    print(f"Sampling rate: {capture.sampling_rate} Hz")
    print(f"\nScenarios:")
    print(f"  1. Cold Start + Warm-up: 5 minutes")
    print(f"  2. Idle Operation: 2 minutes")
    print(f"  3. Varying RPM: 2 minutes")
    print(f"  4. Hydraulics Operation: 2 minutes")
    print(f"  5. PTO Operation: 30 seconds")
    print(f"\nTotal duration: ~11.5 minutes")
    print("=" * 60)

    # Confirm start
    try:
        input("\nPress ENTER to begin data capture session (Ctrl+C to cancel)... ")
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        ecu.disconnect()
        sys.exit(0)

    # Run full session
    try:
        capture.run_full_session()

        print("\n✓ Data capture session complete!")

    except Exception as e:
        print(f"\n✗ Error during session: {e}")
    finally:
        print("\nDisconnecting from ECU...")
        ecu.disconnect()
        print("Done.")


if __name__ == "__main__":
    main()