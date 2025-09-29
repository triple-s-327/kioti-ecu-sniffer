#!/usr/bin/env python3
"""
Kioti NS4710 ECU Protocol Discovery Module
Determines ECU communication protocol and discovers available PIDs
GPL-3.0 with Commons Clause License
"""

import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for ECU Connection module import
sys.path.append(str(Path(__file__).parent.parent / "ECU Connection"))
from ecu_connection import ECUConnection

import obd


class ProtocolDiscovery:
    """Discovers ECU protocol and scans for available PIDs"""

    def __init__(self, ecu_connection: ECUConnection, data_dir: str = "../data"):
        """
        Initialize protocol discovery module

        Args:
            ecu_connection: Active ECU connection instance
            data_dir: Directory for storing discovery results
        """
        self.ecu = ecu_connection
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Create subdirectories
        self.protocol_dir = self.data_dir / "protocol_discovery"
        self.protocol_dir.mkdir(exist_ok=True)

        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        self._setup_logging()

        self.protocol_info = {}
        self.discovered_pids = []
        self.pid_responses = {}

    def _setup_logging(self):
        """Configure logging with timestamped log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"protocol_discovery_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Protocol discovery log file: {log_file}")

    def detect_protocol(self) -> Dict:
        """
        Detect and analyze ECU communication protocol

        Returns:
            dict: Protocol information including name, ID, and characteristics
        """
        self.logger.info("=== Starting Protocol Detection ===")

        if not self.ecu.is_connected:
            self.logger.error("ECU not connected")
            return {}

        try:
            connection = self.ecu.connection

            self.protocol_info = {
                "timestamp": datetime.now().isoformat(),
                "protocol_name": connection.protocol_name(),
                "protocol_id": connection.protocol_id(),
                "port": connection.port_name(),
                "ecus": len(connection.ecus) if hasattr(connection, 'ecus') else 1,
                "supported_commands_count": len(connection.supported_commands)
            }

            self.logger.info(f"Protocol Name: {self.protocol_info['protocol_name']}")
            self.logger.info(f"Protocol ID: {self.protocol_info['protocol_id']}")
            self.logger.info(f"Port: {self.protocol_info['port']}")
            self.logger.info(f"ECUs detected: {self.protocol_info['ecus']}")
            self.logger.info(f"Supported commands: {self.protocol_info['supported_commands_count']}")

            return self.protocol_info

        except Exception as e:
            self.logger.error(f"Protocol detection error: {e}")
            return {}

    def scan_standard_pids(self) -> List[str]:
        """
        Scan for standard OBD-II PIDs (Mode 01)

        Returns:
            list: Available standard PIDs
        """
        self.logger.info("=== Scanning Standard OBD-II PIDs (Mode 01) ===")

        if not self.ecu.is_connected:
            self.logger.error("ECU not connected")
            return []

        available_pids = []

        try:
            supported_commands = self.ecu.get_supported_commands()

            for cmd in supported_commands:
                self.logger.info(f"Testing PID: {cmd.name} ({cmd.command})")

                response = self.ecu.query_pid(cmd)

                if response and not response.is_null():
                    pid_info = {
                        "name": cmd.name,
                        "command": cmd.command,
                        "desc": cmd.desc,
                        "mode": str(cmd.mode) if hasattr(cmd, 'mode') else "01",
                        "pid": str(cmd.pid) if hasattr(cmd, 'pid') else "Unknown",
                        "value": str(response.value),
                        "unit": str(response.unit) if hasattr(response, 'unit') else ""
                    }

                    available_pids.append(pid_info["command"])
                    self.pid_responses[pid_info["command"]] = pid_info

                    self.logger.info(f"  ✓ {cmd.name}: {response.value} {response.unit if hasattr(response, 'unit') else ''}")
                else:
                    self.logger.debug(f"  ✗ {cmd.name}: No response")

                # Small delay to avoid overwhelming the ECU
                time.sleep(0.1)

            self.discovered_pids = available_pids
            self.logger.info(f"\nTotal PIDs responding: {len(available_pids)}")

            return available_pids

        except Exception as e:
            self.logger.error(f"PID scanning error: {e}")
            return []

    def scan_custom_pids(self, mode: str = "01", pid_range: Tuple[int, int] = (0x00, 0xFF)) -> Dict:
        """
        Scan custom PID range (for manufacturer-specific PIDs)

        Args:
            mode: OBD mode (hex string, e.g., "01", "22")
            pid_range: Tuple of (start_pid, end_pid) in hex

        Returns:
            dict: Custom PIDs that responded
        """
        self.logger.info(f"=== Scanning Custom PIDs (Mode {mode}) ===")
        self.logger.info(f"Range: 0x{pid_range[0]:02X} to 0x{pid_range[1]:02X}")

        if not self.ecu.is_connected:
            self.logger.error("ECU not connected")
            return {}

        custom_pids = {}

        try:
            connection = self.ecu.connection

            for pid in range(pid_range[0], pid_range[1] + 1):
                pid_hex = f"{mode}{pid:02X}"

                try:
                    # Send raw command
                    response = connection.query(obd.OBDCommand("CUSTOM",
                                                               f"Custom PID {pid_hex}",
                                                               pid_hex,
                                                               0,
                                                               lambda messages: messages))

                    if response and not response.is_null() and response.value:
                        custom_pids[pid_hex] = {
                            "pid": pid_hex,
                            "raw_response": str(response.value),
                            "messages": [str(msg) for msg in response.messages] if hasattr(response, 'messages') else []
                        }
                        self.logger.info(f"  ✓ PID {pid_hex}: {response.value}")

                except Exception as e:
                    self.logger.debug(f"  ✗ PID {pid_hex}: {e}")

                # Delay to prevent ECU overload
                time.sleep(0.15)

            self.logger.info(f"\nCustom PIDs responding: {len(custom_pids)}")
            return custom_pids

        except Exception as e:
            self.logger.error(f"Custom PID scanning error: {e}")
            return {}

    def test_manufacturer_modes(self) -> Dict:
        """
        Test for manufacturer-specific diagnostic modes
        Common modes: 0x21, 0x22 (manufacturer-specific)

        Returns:
            dict: Modes that responded
        """
        self.logger.info("=== Testing Manufacturer-Specific Modes ===")

        manufacturer_modes = {}
        test_modes = ["21", "22"]

        for mode in test_modes:
            self.logger.info(f"Testing Mode {mode}...")

            # Test first few PIDs in each mode
            mode_pids = self.scan_custom_pids(mode=mode, pid_range=(0x00, 0x0F))

            if mode_pids:
                manufacturer_modes[mode] = mode_pids
                self.logger.info(f"  Mode {mode} has {len(mode_pids)} responding PIDs")

        return manufacturer_modes

    def save_discovery_results(self):
        """Save all discovery results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.protocol_dir / f"discovery_results_{timestamp}.json"

        results = {
            "discovery_timestamp": timestamp,
            "protocol_info": self.protocol_info,
            "standard_pids": {
                "count": len(self.discovered_pids),
                "pids": self.discovered_pids,
                "details": self.pid_responses
            }
        }

        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            self.logger.info(f"\n✓ Results saved to: {output_file}")

            # Also create a human-readable summary
            summary_file = self.protocol_dir / f"discovery_summary_{timestamp}.txt"
            self._save_summary(summary_file, results)

            return output_file

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            return None

    def _save_summary(self, filename: Path, results: Dict):
        """Save human-readable summary of discovery results"""
        try:
            with open(filename, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("KIOTI NS4710 ECU PROTOCOL DISCOVERY SUMMARY\n")
                f.write("=" * 60 + "\n\n")

                f.write("PROTOCOL INFORMATION\n")
                f.write("-" * 60 + "\n")
                for key, value in results["protocol_info"].items():
                    f.write(f"{key:.<30} {value}\n")

                f.write("\n\nSTANDARD PIDs (Mode 01)\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total responding PIDs: {results['standard_pids']['count']}\n\n")

                for pid, details in results["standard_pids"]["details"].items():
                    f.write(f"{details['name']:.<40} {details['command']}\n")
                    f.write(f"  Description: {details['desc']}\n")
                    f.write(f"  Last Value: {details['value']} {details['unit']}\n\n")

            self.logger.info(f"✓ Summary saved to: {filename}")

        except Exception as e:
            self.logger.error(f"Error saving summary: {e}")

    def run_full_discovery(self, include_custom: bool = False):
        """
        Run complete protocol discovery process

        Args:
            include_custom: Whether to scan for custom/manufacturer PIDs (slower)
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("STARTING FULL PROTOCOL DISCOVERY")
        self.logger.info("=" * 60 + "\n")

        # Step 1: Detect protocol
        self.detect_protocol()

        # Step 2: Scan standard PIDs
        self.scan_standard_pids()

        # Step 3: Optional custom PID scanning
        if include_custom:
            self.logger.info("\n" + "=" * 60)
            self.test_manufacturer_modes()

        # Step 4: Save results
        self.logger.info("\n" + "=" * 60)
        self.save_discovery_results()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("PROTOCOL DISCOVERY COMPLETE")
        self.logger.info("=" * 60 + "\n")


def main():
    """Main execution for protocol discovery"""
    print("=== Kioti NS4710 Protocol Discovery ===\n")

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

    # Initialize protocol discovery
    discovery = ProtocolDiscovery(ecu)

    # Ask user about custom PID scanning
    print("\nOptions:")
    print("  1. Quick scan (standard PIDs only) - ~30 seconds")
    print("  2. Full scan (includes manufacturer PIDs) - ~5 minutes")

    try:
        choice = input("\nSelect option (1 or 2): ").strip()
        include_custom = (choice == "2")
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        ecu.disconnect()
        sys.exit(0)

    # Run discovery
    print("\nStarting discovery process...\n")
    try:
        discovery.run_full_discovery(include_custom=include_custom)

        print("\n✓ Discovery complete!")
        print(f"Results saved to: {discovery.protocol_dir}")

    except KeyboardInterrupt:
        print("\n\nDiscovery interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during discovery: {e}")
    finally:
        print("\nDisconnecting from ECU...")
        ecu.disconnect()
        print("Done.")


if __name__ == "__main__":
    main()