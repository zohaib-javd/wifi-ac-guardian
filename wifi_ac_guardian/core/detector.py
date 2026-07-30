"""
Wireless interface detector and iw link parser.
Parses output of 'iw dev <interface> link' to extract physical mode, bitrate, frequency,
channel, signal, and connection state.
"""

import re
import shutil
import subprocess
from typing import Optional, List, Tuple
from wifi_ac_guardian.core.models import LinkInfo, PhyMode
from wifi_ac_guardian.logger import get_logger

logger = get_logger()


def get_iw_binary_path() -> str:
    """Finds absolute binary path for 'iw' executable."""
    return shutil.which("iw") or "/usr/sbin/iw"


def calculate_channel(freq_mhz: float) -> Optional[int]:
    """
    Calculates Wi-Fi channel number from frequency in MHz.
    Supports 2.4 GHz, 5 GHz, and 6 GHz bands.

    Args:
        freq_mhz: Frequency in MHz (e.g. 5805.0 or 2412.0)

    Returns:
        Channel number as integer, or None if invalid.
    """
    if freq_mhz <= 0:
        return None

    freq_int = int(round(freq_mhz))

    # 2.4 GHz Band (2412 - 2484 MHz)
    if 2412 <= freq_int <= 2472:
        return (freq_int - 2412) // 5 + 1
    elif freq_int == 2484:
        return 14

    # 5 GHz Band (5160 - 5885 MHz)
    elif 5000 <= freq_int <= 5885:
        return (freq_int - 5000) // 5

    # 6 GHz Band (5955 - 7115 MHz)
    elif 5955 <= freq_int <= 7115:
        return (freq_int - 5950) // 5

    return None


def detect_wireless_interface(override_interface: Optional[str] = None) -> str:
    """
    Auto-detects active or primary wireless interface name on Ubuntu.

    Args:
        override_interface: User-provided interface name override.

    Returns:
        Interface name string (e.g. 'wlp3s0' or 'wlan0').

    Raises:
        RuntimeError: If no wireless interface could be found.
    """
    if override_interface:
        logger.info(f"Using explicitly specified wireless interface: {override_interface}")
        return override_interface

    # 1. Try 'iw dev' command
    iw_bin = get_iw_binary_path()
    try:
        res = subprocess.run(
            [iw_bin, "dev"],
            capture_output=True,
            text=True,
            check=True
        )
        interfaces: List[str] = []
        for line in res.stdout.splitlines():
            line_str = line.strip()
            if line_str.startswith("Interface "):
                iface = line_str.split()[1]
                interfaces.append(iface)

        if interfaces:
            logger.info(f"Auto-detected wireless interface via 'iw dev': {interfaces[0]}")
            return interfaces[0]
    except Exception as e:
        logger.debug(f"Could not auto-detect interface via 'iw dev': {e}")

    # 2. Try 'nmcli' command
    try:
        res = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE", "dev"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in res.stdout.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 2 and parts[1] == "wifi":
                iface = parts[0]
                logger.info(f"Auto-detected wireless interface via 'nmcli': {iface}")
                return iface
    except Exception as e:
        logger.debug(f"Could not auto-detect interface via 'nmcli': {e}")

    raise RuntimeError("No wireless interface auto-detected on this system.")


class WifiLinkParser:
    """Parses output from 'iw dev <interface> link' command."""

    @staticmethod
    def parse_link_output(raw_output: str, interface: str = "") -> LinkInfo:
        """
        Parses raw text output from 'iw dev <interface> link'.

        Sample inputs handled:
        - "Not connected."
        - "Connected to 08:5c:1b:17:7d:80 (on wlp3s0)..."

        Args:
            raw_output: Output from iw dev <interface> link.
            interface: Name of interface.

        Returns:
            LinkInfo dataclass populated with parsed attributes.
        """
        info = LinkInfo(interface=interface, raw_output=raw_output)

        if not raw_output or "Not connected." in raw_output:
            info.connected = False
            info.phy_mode = PhyMode.DISCONNECTED
            return info

        # Parse Connection line & BSSID
        conn_match = re.search(r"Connected to ([0-9a-fA-F:]{17})", raw_output)
        if conn_match:
            info.connected = True
            info.bssid = conn_match.group(1).upper()

        # Parse SSID
        ssid_match = re.search(r"\bSSID:\s*(.+)", raw_output)
        if ssid_match:
            info.ssid = ssid_match.group(1).strip()

        # Parse Frequency (MHz)
        freq_match = re.search(r"\bfreq:\s*([0-9]+(?:\.[0-9]+)?)", raw_output)
        if freq_match:
            try:
                info.freq_mhz = float(freq_match.group(1))
                info.channel = calculate_channel(info.freq_mhz)
            except ValueError:
                pass

        # Parse Signal Level (dBm)
        signal_match = re.search(r"\bsignal:\s*(-?[0-9]+)\s*dBm", raw_output)
        if signal_match:
            try:
                info.signal_dbm = int(signal_match.group(1))
            except ValueError:
                pass

        # Parse RX Bitrate line
        rx_match = re.search(r"\brx bitrate:\s*(.+)", raw_output)
        if rx_match:
            info.rx_bitrate = rx_match.group(1).strip()

        # Parse TX Bitrate line
        tx_match = re.search(r"\btx bitrate:\s*(.+)", raw_output)
        if tx_match:
            info.tx_bitrate = tx_match.group(1).strip()

        # Determine PHY Mode
        info.phy_mode = WifiLinkParser._determine_phy_mode(raw_output, info.tx_bitrate, info.rx_bitrate)

        return info

    @staticmethod
    def _determine_phy_mode(
        full_text: str,
        tx_bitrate: Optional[str] = None,
        rx_bitrate: Optional[str] = None
    ) -> PhyMode:
        """
        Determines the physical protocol (EHT, HE, VHT, HT, Legacy) based on iw link output.

        Indicators:
        - Wi-Fi 7 (EHT): "EHT-MCS", "EHT", "802.11be"
        - Wi-Fi 6/6E (HE): "HE-MCS", "HE-NSS", "HE", "802.11ax"
        - Wi-Fi 5 (VHT): "VHT-MCS", "VHT-NSS", "VHT", "802.11ac"
        - Wi-Fi 4 (HT): "HT-MCS", "MCS", "802.11n"
        - Legacy: Standard rate (e.g. 54.0 MBit/s) without MCS or VHT/HE/EHT flags.
        """
        combined = f"{full_text} {tx_bitrate or ''} {rx_bitrate or ''}"

        # 1. Wi-Fi 7 (EHT / 802.11be)
        if re.search(r"\b(EHT|EHT-MCS|802\.11be)\b", combined, re.IGNORECASE):
            return PhyMode.EHT

        # 2. Wi-Fi 6 / 6E (HE / 802.11ax)
        if re.search(r"\b(HE|HE-MCS|HE-NSS|802\.11ax)\b", combined, re.IGNORECASE):
            return PhyMode.HE

        # 3. Wi-Fi 5 (VHT / 802.11ac)
        if re.search(r"\b(VHT|VHT-MCS|VHT-NSS|802\.11ac)\b", combined, re.IGNORECASE):
            return PhyMode.VHT

        # 4. Wi-Fi 4 (HT / 802.11n)
        if re.search(r"\b(HT|HT-MCS|MCS|802\.11n)\b", combined, re.IGNORECASE):
            return PhyMode.HT

        # 5. Legacy 802.11a/b/g
        if re.search(r"[0-9]+\.?[0-9]*\s*MBit/s", combined, re.IGNORECASE):
            return PhyMode.LEGACY

        return PhyMode.UNKNOWN


class WifiDetector:
    """High-level interface for querying current wireless link status using 'iw'."""

    def __init__(self, interface: Optional[str] = None):
        self.interface = interface

    def get_interface(self) -> str:
        """Ensure interface is detected and returned."""
        if not self.interface:
            self.interface = detect_wireless_interface()
        return self.interface

    def get_link_info(self) -> LinkInfo:
        """
        Executes 'iw dev <interface> link' and returns parsed LinkInfo object.

        Returns:
            LinkInfo populated with current Wi-Fi parameters.
        """
        iface = self.get_interface()
        iw_bin = get_iw_binary_path()
        cmd = [iw_bin, "dev", iface, "link"]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            raw_output = res.stdout.strip()
            return WifiLinkParser.parse_link_output(raw_output, interface=iface)
        except Exception as e:
            logger.error(f"Error running '{' '.join(cmd)}': {e}")
            return LinkInfo(
                connected=False,
                interface=iface,
                phy_mode=PhyMode.UNKNOWN,
                raw_output=f"Error executing command: {e}"
            )
