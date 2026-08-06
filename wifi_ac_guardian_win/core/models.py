"""
Data models and enumeration definitions for WiFi AC Guardian (Windows Edition).
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import os


class PhyMode(Enum):
    """Enumeration of wireless physical layer (PHY) modes on Windows."""
    EHT = "802.11be (Wi-Fi 7)"
    HE = "802.11ax (Wi-Fi 6/6E)"
    VHT = "802.11ac (Wi-Fi 5)"
    HT = "802.11n (Wi-Fi 4)"
    LEGACY = "802.11a/b/g (Legacy)"
    DISCONNECTED = "Disconnected"
    UNKNOWN = "Unknown"


class StatusState(Enum):
    """Enumeration of overall Guardian monitoring and tray status."""
    GOOD = "GOOD"                           # Green: Primary Wi-Fi 5+ active (> 300 Mbps)
    RETRYING = "RECONNECTING"              # Yellow: Restoring Wi-Fi adapter / radio reset
    FAILED = "DOWNGRADED"                  # Red: Primary connected but degraded
    DISCONNECTED = "DISCONNECTED"          # Red: No Wi-Fi connection
    STANDBY = "STANDBY"                    # Blue: Backup Network Active (e.g. Metalgear)
    IDLE = "IDLE"                          # Blue: Paused or Initializing


@dataclass
class LinkInfo:
    """Detailed information parsed from 'netsh wlan show interfaces' output on Windows."""
    connected: bool = False
    interface: str = "Wi-Fi"
    bssid: Optional[str] = None
    ssid: Optional[str] = None
    freq_mhz: Optional[float] = None
    channel: Optional[int] = None
    signal_pct: Optional[int] = None
    rx_bitrate: Optional[str] = None
    tx_bitrate: Optional[str] = None
    phy_mode: PhyMode = PhyMode.UNKNOWN
    radio_type: str = ""
    raw_output: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def max_bitrate_mbps(self) -> float:
        """Returns the highest numerical bitrate (Tx or Rx) parsed from link info."""
        rates = []
        for rate_str in (self.tx_bitrate, self.rx_bitrate):
            if rate_str:
                match = re.search(r"(\d+(?:\.\d+)?)", rate_str)
                if match:
                    try:
                        rates.append(float(match.group(1)))
                    except ValueError:
                        pass
        return max(rates) if rates else 0.0

    @property
    def is_good(self) -> bool:
        """
        Returns True if:
        1. Connected
        2. PHY mode is Wi-Fi 5 (VHT), Wi-Fi 6 (HE), or Wi-Fi 7 (EHT)
        3. Transmit/Receive Bitrate is strictly GREATER than 300.0 Mbps (> 300.0 Mbps)
        """
        if not self.connected:
            return False
        phy_ok = self.phy_mode in (PhyMode.VHT, PhyMode.HE, PhyMode.EHT)
        bitrate_ok = self.max_bitrate_mbps > 300.0
        return phy_ok and bitrate_ok

    @property
    def phy_summary(self) -> str:
        """Returns concise human-readable description of PHY mode."""
        return self.phy_mode.value


@dataclass
class GuardianConfig:
    """Configuration settings for the Wi-Fi monitoring service on Windows."""
    interface: Optional[str] = None       # None = auto-detect or 'Wi-Fi'
    target_ssid: str = "lab5g"            # Default primary protected network (e.g. lab5g)
    auto_switch_primary: bool = True      # Automatically switch back to primary when back online
    auto_start: bool = True               # Start WiFi AC Guardian when Windows starts
    check_interval: float = 10.0          # Dynamic internal poll interval
    reconnect_delay: float = 15.0         # Hardware adapter radio stabilization delay
    max_attempts: int = 99                # Connection retry attempts limit (99)
    log_file_path: str = os.path.join(os.path.expanduser("~"), "wifi_ac_guardian_win.log")
    enable_notifications: bool = False    # False by default
    enable_tray: bool = True
    start_minimized: bool = False         # Start the UI hidden in the system tray
    is_paused: bool = False
    animations_enabled: bool = False      # UI micro-animations (presentation-only); OFF until validated


@dataclass
class GuardianState:
    """Current state tracker for the Guardian monitoring loop."""
    current_link: Optional[LinkInfo] = None
    status: StatusState = StatusState.IDLE
    primary_available: bool = False        # Primary target SSID detected in range while on backup
    attempts_count: int = 0
    last_check: Optional[datetime] = None
    last_reconnect: Optional[datetime] = None
    running: bool = False
