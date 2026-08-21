"""
Data models and enumeration definitions for WiFi AC Guardian.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class PhyMode(Enum):
    """Enumeration of wireless physical layer (PHY) modes."""
    EHT = "802.11be (Wi-Fi 7)"
    HE = "802.11ax (Wi-Fi 6/6E)"
    VHT = "802.11ac (Wi-Fi 5)"
    HT = "802.11n (Wi-Fi 4)"
    LEGACY = "802.11a/b/g (Legacy)"
    DISCONNECTED = "Disconnected"
    UNKNOWN = "Unknown"


class StatusState(Enum):
    """Enumeration of overall Guardian monitoring and tray status."""
    GOOD = "GOOD"             # Green: Wi-Fi 5+ active
    RETRYING = "RETRYING"     # Yellow: Wi-Fi 4 detected, retrying
    FAILED = "FAILED"         # Red: Failed after 10 attempts
    DISCONNECTED = "DISCONNECTED" # Red: No connection
    IDLE = "IDLE"             # Initial or paused state


import re

def extract_bitrate_mbps(bitrate_str: Optional[str]) -> Optional[float]:
    """Extracts numeric MBit/s bitrate from tx or rx bitrate string."""
    if not bitrate_str:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*MBit/s", bitrate_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


@dataclass
class LinkInfo:
    """Detailed information parsed from 'iw dev <interface> link' output."""
    connected: bool = False
    interface: str = ""
    bssid: Optional[str] = None
    ssid: Optional[str] = None
    freq_mhz: Optional[float] = None
    channel: Optional[int] = None
    signal_dbm: Optional[int] = None
    rx_bitrate: Optional[str] = None
    tx_bitrate: Optional[str] = None
    phy_mode: PhyMode = PhyMode.UNKNOWN
    raw_output: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_good(self) -> bool:
        """
        Returns True ONLY if:
        1. Connection is active.
        2. Bitrate is GREATER than 300.0 MBit/s (rates <= 300 MBit/s represent Wi-Fi 4 802.11n / HT and are NOT ACCEPTABLE).
        3. PHY mode is Wi-Fi 5 (VHT), Wi-Fi 6 (HE), or Wi-Fi 7 (EHT), or 5GHz/6GHz band.
        """
        if not self.connected:
            return False

        bitrate = extract_bitrate_mbps(self.tx_bitrate or self.rx_bitrate)

        # Rates <= 300.0 MBit/s (e.g. 270.0 MBit/s, 300.0 MBit/s, 144.4 MBit/s) indicate Wi-Fi 4 (802.11n) -> NOT GOOD
        if bitrate is not None and bitrate <= 300.0:
            return False

        # Wi-Fi 7 (EHT), Wi-Fi 6 (HE), or Wi-Fi 5 (VHT) with bitrate > 300 MBit/s
        if self.phy_mode in (PhyMode.VHT, PhyMode.HE, PhyMode.EHT):
            return True

        # 5 GHz / 6 GHz Band (freq >= 5000 MHz) with bitrate > 300 MBit/s
        if self.freq_mhz and self.freq_mhz >= 5000.0 and (bitrate is None or bitrate > 300.0):
            return True

        return False

    @property
    def phy_summary(self) -> str:
        """Returns concise human-readable description of PHY mode."""
        bitrate = extract_bitrate_mbps(self.tx_bitrate or self.rx_bitrate)
        if bitrate is not None and bitrate <= 300.0 and self.connected:
            return f"802.11n (Wi-Fi 4 - {bitrate:.1f} MBit/s)"
        return self.phy_mode.value


@dataclass
class GuardianConfig:
    """Configuration settings for the Wi-Fi monitoring service."""
    interface: Optional[str] = None  # None = auto-detect
    check_interval: float = 15.0     # Every 15 seconds for complete rate adaptation
    reconnect_delay: float = 15.0     # Wait 15 seconds before reconnecting
    max_attempts: int = 0             # Default 0 = Unlimited Continuous Retries
    log_file_path: str = "~/wifi_ac_guardian.log"
    enable_notifications: bool = False # Popups disabled (tray icon only)
    enable_tray: bool = True
    is_paused: bool = False


@dataclass
class GuardianState:
    """Current state tracker for the Guardian monitoring loop."""
    current_link: Optional[LinkInfo] = None
    status: StatusState = StatusState.IDLE
    attempts_count: int = 0
    last_check: Optional[datetime] = None
    last_reconnect: Optional[datetime] = None
    running: bool = False
