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
        Returns True if the PHY mode is Wi-Fi 5 (VHT), Wi-Fi 6 (HE), or Wi-Fi 7 (EHT).
        Per requirements, Wi-Fi 5 and higher are considered GOOD.
        """
        return self.connected and self.phy_mode in (PhyMode.VHT, PhyMode.HE, PhyMode.EHT)

    @property
    def phy_summary(self) -> str:
        """Returns concise human-readable description of PHY mode."""
        return self.phy_mode.value


@dataclass
class GuardianConfig:
    """Configuration settings for the Wi-Fi monitoring service."""
    interface: Optional[str] = None  # None = auto-detect
    check_interval: float = 10.0      # Every 10 seconds per requirements
    reconnect_delay: float = 2.0      # Wait 2 seconds before reconnecting
    max_attempts: int = 10            # Max retry count (10 attempts)
    log_file_path: str = "~/wifi_ac_guardian.log"
    enable_notifications: bool = False # Off by default to prevent popup spam
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
