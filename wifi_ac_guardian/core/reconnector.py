"""
NetworkManager reconnection handler for Wi-Fi AC Guardian.
Handles disconnecting, waiting, reconnecting, and waiting for state stabilization.
"""

import time
import subprocess
from typing import Optional
from wifi_ac_guardian.core.models import LinkInfo, GuardianConfig
from wifi_ac_guardian.core.detector import WifiDetector
from wifi_ac_guardian.logger import get_logger

logger = get_logger()


class WifiReconnector:
    """Manages NetworkManager Wi-Fi disconnection and reconnection routines."""

    def __init__(self, config: Optional[GuardianConfig] = None):
        self.config = config or GuardianConfig()
        self.detector = WifiDetector(interface=self.config.interface)

    def trigger_reconnect(self, interface: str, ssid: Optional[str] = None) -> LinkInfo:
        """
        Executes disconnect, delay, reconnect sequence via NetworkManager (nmcli),
        then waits until interface re-connects and returns the updated LinkInfo.

        Steps:
        1. Log warning.
        2. Disconnect Wi-Fi via 'nmcli dev disconnect <interface>'.
        3. Wait reconnect_delay seconds (default 2s).
        4. Reconnect via NetworkManager.
        5. Poll until connected or timeout.

        Args:
            interface: Wireless interface name (e.g. wlp3s0).
            ssid: Target SSID string if known.

        Returns:
            LinkInfo after reconnection attempt.
        """
        logger.warning(
            f"Triggering Wi-Fi reconnection on interface '{interface}' "
            f"(Target SSID: '{ssid or 'Auto'}')..."
        )

        # 1. Disconnect interface
        self._disconnect_interface(interface, ssid)

        # 2. Wait 2 seconds (or configured reconnect_delay)
        delay = max(0.5, self.config.reconnect_delay)
        logger.info(f"Waiting {delay:.1f} seconds before reconnecting...")
        time.sleep(delay)

        # 3. Connect via NetworkManager
        self._connect_interface(interface, ssid)

        # 4. Wait until connected and verify PHY mode
        updated_link = self._wait_for_connection(interface, timeout_seconds=15)
        return updated_link

    def _disconnect_interface(self, interface: str, ssid: Optional[str] = None) -> bool:
        """Disconnects the wireless interface using nmcli."""
        logger.info(f"Disconnecting Wi-Fi interface {interface} via nmcli...")
        try:
            res = subprocess.run(
                ["nmcli", "device", "disconnect", interface],
                capture_output=True,
                text=True,
                timeout=10
            )
            if res.returncode == 0:
                logger.info(f"Successfully disconnected interface {interface}.")
                return True
            else:
                logger.warning(f"nmcli disconnect returned non-zero code ({res.returncode}): {res.stderr}")
        except Exception as e:
            logger.error(f"Error disconnecting interface {interface}: {e}")

        # Fallback: try connection down if SSID is present
        if ssid:
            try:
                subprocess.run(
                    ["nmcli", "connection", "down", "id", ssid],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Error disconnecting connection id '{ssid}': {e}")

        return False

    def _connect_interface(self, interface: str, ssid: Optional[str] = None) -> bool:
        """Reconnects Wi-Fi using NetworkManager."""
        logger.info(f"Initiating Wi-Fi connection on {interface}...")

        # If specific SSID is known, attempt connection up
        if ssid:
            cmd = ["nmcli", "connection", "up", "id", ssid]
            logger.info(f"Running command: {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if res.returncode == 0:
                    logger.info(f"nmcli connection up succeeded for SSID '{ssid}'.")
                    return True
                else:
                    logger.warning(f"nmcli connection up failed ({res.returncode}): {res.stderr}")
            except Exception as e:
                logger.error(f"Error bringing connection '{ssid}' up: {e}")

        # Fallback / General interface connect
        cmd = ["nmcli", "device", "connect", interface]
        logger.info(f"Running fallback command: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                logger.info(f"nmcli device connect succeeded for {interface}.")
                return True
            else:
                logger.warning(f"nmcli device connect output: {res.stdout or res.stderr}")
        except Exception as e:
            logger.error(f"Error connecting device {interface}: {e}")

        return False

    def _wait_for_connection(self, interface: str, timeout_seconds: float = 15.0) -> LinkInfo:
        """
        Polls 'iw dev <interface> link' until connection is established or timeout.

        Args:
            interface: Wireless interface name.
            timeout_seconds: Maximum poll duration in seconds.

        Returns:
            Latest parsed LinkInfo.
        """
        start_time = time.time()
        poll_interval = 1.0

        link_info = self.detector.get_link_info()

        while time.time() - start_time < timeout_seconds:
            if link_info.connected:
                logger.info(
                    f"Connection re-established on interface '{interface}'! "
                    f"SSID: '{link_info.ssid}' | PHY Mode: {link_info.phy_summary}"
                )
                return link_info

            time.sleep(poll_interval)
            link_info = self.detector.get_link_info()

        logger.warning(f"Timed out waiting for Wi-Fi connection state stabilization on {interface}.")
        return link_info
