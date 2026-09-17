"""
Data models and enumeration definitions for WiFi AC Guardian (Windows Edition).
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import os

from wifi_ac_guardian_win.logger import DEFAULT_LOG_FILE_PATH


class PhyMode(Enum):
    """Enumeration of wireless physical layer (PHY) modes on Windows."""
    EHT = "802.11be (Wi-Fi 7)"
    HE = "802.11ax (Wi-Fi 6/6E)"
    VHT = "802.11ac (Wi-Fi 5)"
    HT = "802.11n (Wi-Fi 4)"
    LEGACY = "802.11a/b/g (Legacy)"
    DISCONNECTED = "Disconnected"
    UNKNOWN = "Unknown"


APPROVED_PHY_MODES = frozenset({PhyMode.VHT, PhyMode.HE, PhyMode.EHT})


class StatusState(Enum):
    """Enumeration of overall Guardian monitoring and tray status."""
    GOOD = "GOOD"                           # Green: Primary Wi-Fi 5+ active (> 300 Mbps)
    RETRYING = "RECONNECTING"              # Yellow: Restoring Wi-Fi adapter / radio reset
    FAILED = "DOWNGRADED"                  # Red: Primary connected but degraded
    DISCONNECTED = "DISCONNECTED"          # Red: No Wi-Fi connection
    STANDBY = "STANDBY"                    # Blue: Backup Network Active (e.g. Metalgear)
    IDLE = "IDLE"                          # Blue: Paused or Initializing


class RadioState(Enum):
    """Availability of the Windows Wi-Fi radio/interface reported by the OS."""
    ACTIVE = "active"                      # Connected Wi-Fi link is active
    DISCONNECTED = "disconnected"          # Adapter exists but has no Wi-Fi link
    RADIO_OFF = "radio_off"                # Wi-Fi radio is unavailable (including Airplane Mode)
    ADAPTER_DISABLED = "adapter_disabled"  # User or policy disabled the Wi-Fi adapter
    NO_ADAPTER = "no_adapter"              # Windows reports no usable Wi-Fi adapter
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BssidCandidate:
    """One BSSID observed during a Windows WLAN network inventory."""

    ssid: str
    bssid: str
    channel: Optional[int] = None
    signal_pct: Optional[int] = None
    radio_type: str = ""
    phy_mode: PhyMode = PhyMode.UNKNOWN

    @property
    def band(self) -> str:
        if self.channel is None:
            return "unknown"
        if 1 <= self.channel <= 14:
            return "2.4GHz"
        if self.channel >= 181:
            return "6GHz"
        return "5GHz"


@dataclass
class LinkInfo:
    """Detailed information parsed from 'netsh wlan show interfaces' output on Windows."""
    connected: bool = False
    interface: str = ""
    adapter: Optional[str] = None
    bssid: Optional[str] = None
    ssid: Optional[str] = None
    freq_mhz: Optional[float] = None
    channel: Optional[int] = None
    signal_pct: Optional[int] = None
    rx_bitrate: Optional[str] = None
    tx_bitrate: Optional[str] = None
    phy_mode: PhyMode = PhyMode.UNKNOWN
    radio_type: str = ""
    radio_state: RadioState = RadioState.UNKNOWN
    raw_output: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def max_bitrate_mbps(self) -> float:
        """Returns the highest numerical bitrate (Tx or Rx) parsed from link info."""
        rates = [rate for rate in (self.tx_bitrate_mbps, self.rx_bitrate_mbps) if rate > 0]
        return max(rates) if rates else 0.0

    @staticmethod
    def _parse_bitrate(value: Optional[str]) -> float:
        if not value:
            return 0.0
        match = re.search(r"(\d+(?:\.\d+)?)", value)
        if not match:
            return 0.0
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0

    @property
    def tx_bitrate_mbps(self) -> float:
        """Return the numeric transmit bitrate reported by Windows, if present."""
        return self._parse_bitrate(self.tx_bitrate)

    @property
    def rx_bitrate_mbps(self) -> float:
        """Return the numeric receive bitrate reported by Windows, if present."""
        return self._parse_bitrate(self.rx_bitrate)

    def has_approved_phy(self) -> bool:
        """True when Windows reports a connected Wi-Fi 5, 6, or 7 link."""
        return self.connected and self.phy_mode in APPROVED_PHY_MODES

    def is_good(self, min_bitrate_threshold: float = 300.0) -> bool:
        """
        Returns True if:
        1. Connected
        2. PHY mode is Wi-Fi 5 (VHT), Wi-Fi 6 (HE), or Wi-Fi 7 (EHT)
        3. Every available directional bitrate is strictly greater than the
           configured threshold. When Windows reports only one direction, that
           single measured bitrate is used.
        """
        if not self.has_approved_phy():
            return False
        tx_rate = self.tx_bitrate_mbps
        rx_rate = self.rx_bitrate_mbps
        if tx_rate > 0 and rx_rate > 0:
            bitrate_ok = tx_rate > min_bitrate_threshold and rx_rate > min_bitrate_threshold
        else:
            bitrate_ok = self.max_bitrate_mbps > min_bitrate_threshold
        return bitrate_ok

    @property
    def has_available_adapter(self) -> bool:
        """True only when Windows reports a Wi-Fi adapter/radio that can be used."""
        return self.radio_state in {RadioState.ACTIVE, RadioState.DISCONNECTED}

    @property
    def phy_summary(self) -> str:
        """Returns concise human-readable description of PHY mode."""
        labels = {
            PhyMode.VHT: "Wi-Fi 5 (802.11ac)",
            PhyMode.HE: "Wi-Fi 6/6E (802.11ax)",
            PhyMode.EHT: "Wi-Fi 7 (802.11be)",
            PhyMode.HT: "Wi-Fi 4 (802.11n)",
        }
        return labels.get(self.phy_mode, self.phy_mode.value)


@dataclass
class GuardianConfig:
    """Configuration settings for the Wi-Fi monitoring service on Windows."""
    interface: Optional[str] = None       # None = dynamically select the active Windows Wi-Fi interface
    target_ssid: str = ""                 # Empty = adopt the currently connected SSID for this session
    auto_switch_primary: bool = True      # Automatically switch back to primary when back online
    auto_start: bool = True               # Start WiFi AC Guardian when Windows starts
    check_interval: float = 3.0           # Dynamic internal poll interval
    reconnect_delay: float = 3.0          # Default radio OFF hold for bounded native auto-association cycles
    max_attempts: int = 0                 # 0 = unlimited recovery attempts
    min_bitrate_threshold: float = 300.0  # Minimum required link speed in Mbps
    vht_grace_period: float = 5.0         # Seconds to observe a fresh 802.11n association before recovering
    recovery_cooldown: float = 8.0        # Rest period between recovery cycles after a failed attempt
    post_connect_verify: float = 6.0      # Hold time after apparent success before confirming recovery
    post_scan_settle: float = 2.0         # Pause after an active scan before evaluating results
    log_file_path: str = DEFAULT_LOG_FILE_PATH
    enable_notifications: bool = False    # False by default
    enable_tray: bool = True
    start_minimized: bool = False         # Start the UI hidden in the system tray
    is_paused: bool = False
    animations_enabled: bool = False      # UI micro-animations (presentation-only); OFF until validated
    sound_alerts: bool = False            # Play Windows alert sound on reconnection events
    preferred_bssids: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass
class GuardianState:
    """Current state tracker for the Guardian monitoring loop."""
    current_link: Optional[LinkInfo] = None
    status: StatusState = StatusState.IDLE
    primary_available: bool = False        # Primary target SSID detected in range while on backup
    attempts_count: int = 0
    last_check: Optional[datetime] = None
    last_reconnect: Optional[datetime] = None
    next_check: Optional[datetime] = None
    running: bool = False
    recovery_active: bool = False
    recovery_status: str = ""
