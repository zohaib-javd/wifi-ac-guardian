"""
Windows wireless interface detector and netsh wlan link parser.
Parses output of 'netsh wlan show interfaces' to extract physical mode, bitrate, frequency,
channel, signal percentage, and connection state on Windows 11.
"""

import re
import subprocess
from typing import Optional, List
from wifi_ac_guardian_win.core.models import LinkInfo, PhyMode
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()


def parse_netsh_output(raw_output: str, interface_fallback: str = "Wi-Fi") -> LinkInfo:
    """
    Parses output of 'netsh wlan show interfaces' command on Windows 11.

    Args:
        raw_output: Command stdout string.
        interface_fallback: Default interface name if unparsed.

    Returns:
        LinkInfo dataclass populated with parsed parameters.
    """
    info = LinkInfo(interface=interface_fallback, raw_output=raw_output)

    if not raw_output or "disconnected" in raw_output.lower() and "connected" not in raw_output.lower():
        info.connected = False
        info.phy_mode = PhyMode.DISCONNECTED
        return info

    lines = raw_output.splitlines()
    key_val = {}

    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()
            key_val[key] = val

    # Interface name
    if "name" in key_val:
        info.interface = key_val["name"]

    # State check
    state_str = key_val.get("state", "").lower()
    if "connected" in state_str:
        info.connected = True
    else:
        info.connected = False
        info.phy_mode = PhyMode.DISCONNECTED
        return info

    # BSSID & SSID
    info.bssid = key_val.get("bssid")
    info.ssid = key_val.get("ssid")

    # Radio Type (PHY Mode)
    radio_type = key_val.get("radio type", "")
    info.radio_type = radio_type

    # Channel & Band
    chan_str = key_val.get("channel")
    if chan_str:
        try:
            info.channel = int(chan_str)
        except ValueError:
            pass

    band_str = key_val.get("band", "")
    if "5" in band_str and info.channel:
        info.freq_mhz = 5000.0 + (info.channel * 5)
    elif "6" in band_str and info.channel:
        info.freq_mhz = 5950.0 + (info.channel * 5)
    elif "2.4" in band_str and info.channel:
        info.freq_mhz = 2407.0 + (info.channel * 5)

    # Signal Percentage
    sig_str = key_val.get("signal", "").replace("%", "").strip()
    if sig_str:
        try:
            info.signal_pct = int(sig_str)
        except ValueError:
            pass

    # Transmit & Receive Rate
    info.tx_bitrate = key_val.get("transmit rate (mbps)")
    if info.tx_bitrate and "Mbps" not in info.tx_bitrate:
        info.tx_bitrate = f"{info.tx_bitrate} Mbps"

    info.rx_bitrate = key_val.get("receive rate (mbps)")
    if info.rx_bitrate and "Mbps" not in info.rx_bitrate:
        info.rx_bitrate = f"{info.rx_bitrate} Mbps"

    # Determine PhyMode from Radio Type / full output
    info.phy_mode = determine_win_phy_mode(radio_type, raw_output)

    return info


def determine_win_phy_mode(radio_type: str, full_output: str) -> PhyMode:
    """
    Maps Windows Radio Type string (802.11ac, 802.11ax, 802.11be, 802.11n) to PhyMode enum.
    """
    rt = (radio_type or "").lower()

    if "802.11be" in rt or "eht" in rt:
        return PhyMode.EHT

    if "802.11ax" in rt or "he" in rt:
        return PhyMode.HE

    if "802.11ac" in rt or "vht" in rt:
        return PhyMode.VHT

    if "802.11n" in rt or "ht" in rt:
        return PhyMode.HT

    if any(leg in rt for leg in ["802.11a", "802.11b", "802.11g"]):
        return PhyMode.LEGACY

    combined = full_output.lower()
    if "802.11be" in combined:
        return PhyMode.EHT
    if "802.11ax" in combined:
        return PhyMode.HE
    if "802.11ac" in combined:
        return PhyMode.VHT
    if "802.11n" in combined:
        return PhyMode.HT

    return PhyMode.UNKNOWN


class WifiDetectorWin:
    """High-level interface for querying current wireless link status using netsh wlan."""

    def __init__(self, interface: Optional[str] = None):
        self.interface = interface or "Wi-Fi"

    def get_link_info(self) -> LinkInfo:
        """
        Executes 'netsh wlan show interfaces' and returns parsed LinkInfo object.
        """
        cmd = ["netsh", "wlan", "show", "interfaces"]
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=flags
            )
            return parse_netsh_output(res.stdout.strip(), interface_fallback=self.interface)
        except Exception as e:
            logger.error(f"Error running 'netsh wlan show interfaces': {e}")
            return LinkInfo(
                connected=False,
                interface=self.interface,
                phy_mode=PhyMode.UNKNOWN,
                raw_output=f"Error executing command: {e}"
            )
    def get_available_ssids(self) -> List[str]:
        """
        Executes 'netsh wlan show networks' and returns a sorted list of unique nearby SSIDs.
        """
        cmd = ["netsh", "wlan", "show", "networks"]
        ssids = []
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=flags
            )
            for line in res.stdout.splitlines():
                if "SSID" in line and ":" in line:
                    parts = line.split(":", 1)
                    val = parts[1].strip()
                    if val and val not in ssids:
                        ssids.append(val)
        except Exception as e:
            logger.error(f"Error scanning nearby networks: {e}")
        return ssids
