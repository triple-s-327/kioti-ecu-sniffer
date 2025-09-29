#!/usr/bin/env python3
"""
Kioti NS4710 ECU Connection Module
Establishes and maintains stable Bluetooth OBD2 connection with self-healing capabilities
GPL-3.0 with Commons Clause License
"""

import obd
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys


class ECUConnection:
    """Manages connection to Kioti NS4710 ECU via ELM327 Bluetooth adapter"""

    def __init__(self, port: Optional[str] = None, baudrate: int = 38400,
                 log_dir: str = "logs", reconnect_attempts: int = 5,
                 reconnect_delay: int = 3):
        """
        Initialize ECU connection manager

        Args:
            port: Bluetooth serial port (e.g., /dev/rfcomm0). Auto-detect if None
            baudrate: Communication baud rate (default 38400 for ELM327)
            log_dir: Directory for log files
            reconnect_attempts: Number of reconnection attempts
            reconnect_delay: Delay in seconds between reconnection attempts
        """
        self.port = port
        self.baudrate = baudrate
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.connection: Optional[obd.OBD] = None
        self.is_connected = False

        # Setup logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging with timestamped log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"ecu_connection_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log file created: {log_file}")

    def connect(self) -> bool:
        """
        Establish connection to ECU

        Returns:
            bool: True if connection successful, False otherwise
        """
        self.logger.info("Attempting to connect to ECU...")

        try:
            if self.port:
                self.logger.info(f"Connecting to port: {self.port}")
                self.connection = obd.OBD(portstr=self.port, baudrate=self.baudrate, fast=False)
            else:
                self.logger.info("Auto-detecting OBD2 adapter...")
                self.connection = obd.OBD(fast=False)

            if self.connection.is_connected():
                self.is_connected = True
                self.logger.info("✓ Successfully connected to ECU")
                self.logger.info(f"Port: {self.connection.port_name()}")
                self.logger.info(f"Protocol: {self.connection.protocol_name()}")
                self.logger.info(f"Available PIDs: {len(self.connection.supported_commands)}")
                return True
            else:
                self.logger.error("✗ Failed to establish connection")
                self.is_connected = False
                return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Safely disconnect from ECU"""
        if self.connection and self.is_connected:
            try:
                self.connection.close()
                self.is_connected = False
                self.logger.info("Disconnected from ECU")
            except Exception as e:
                self.logger.error(f"Error during disconnection: {e}")

    def reconnect(self) -> bool:
        """
        Attempt to reconnect to ECU with retry logic

        Returns:
            bool: True if reconnection successful, False otherwise
        """
        self.logger.warning("Attempting to reconnect...")
        self.disconnect()

        for attempt in range(1, self.reconnect_attempts + 1):
            self.logger.info(f"Reconnection attempt {attempt}/{self.reconnect_attempts}")

            if self.connect():
                return True

            if attempt < self.reconnect_attempts:
                self.logger.info(f"Waiting {self.reconnect_delay}s before next attempt...")
                time.sleep(self.reconnect_delay)

        self.logger.error("All reconnection attempts failed")
        return False

    def check_connection(self) -> bool:
        """
        Verify connection health

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.connection or not self.is_connected:
            return False

        try:
            # Attempt to query a basic PID to verify connection
            response = self.connection.query(obd.commands.STATUS)
            if response.is_null():
                self.logger.warning("Connection check failed - received null response")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return False

    def maintain_connection(self, check_interval: int = 10):
        """
        Monitor and maintain connection with automatic reconnection

        Args:
            check_interval: Seconds between connection health checks
        """
        self.logger.info("Starting connection maintenance loop...")

        while True:
            if not self.check_connection():
                self.logger.warning("Connection lost - initiating self-healing")
                if not self.reconnect():
                    self.logger.error("Self-healing failed - manual intervention required")
                    break

            time.sleep(check_interval)

    def get_supported_commands(self) -> list:
        """
        Get list of PIDs supported by the ECU

        Returns:
            list: Supported OBD commands
        """
        if not self.connection or not self.is_connected:
            self.logger.error("No active connection")
            return []

        return self.connection.supported_commands

    def query_pid(self, command):
        """
        Query a specific PID

        Args:
            command: OBD command object

        Returns:
            OBD response object or None
        """
        if not self.connection or not self.is_connected:
            self.logger.error("No active connection")
            return None

        try:
            response = self.connection.query(command)
            return response
        except Exception as e:
            self.logger.error(f"Error querying PID {command}: {e}")
            return None


def main():
    """Test the ECU connection module"""
    print("=== Kioti ECU Connection Module ===\n")

    # Initialize connection
    ecu = ECUConnection()

    # Attempt to connect
    if not ecu.connect():
        print("\nFailed to connect. Please check:")
        print("1. Bluetooth adapter is paired and connected")
        print("2. Vehicle ignition is ON")
        print("3. ELM327 adapter is functioning")
        sys.exit(1)

    # Display supported commands
    print(f"\nSupported PIDs: {len(ecu.get_supported_commands())}")

    # Test query
    print("\nTesting RPM query...")
    response = ecu.query_pid(obd.commands.RPM)
    if response and not response.is_null():
        print(f"RPM: {response.value}")
    else:
        print("RPM query returned no data (engine may be off)")

    # Keep connection alive
    print("\nConnection established. Press Ctrl+C to exit...")
    try:
        ecu.maintain_connection()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        ecu.disconnect()
        print("Connection closed.")


if __name__ == "__main__":
    main()