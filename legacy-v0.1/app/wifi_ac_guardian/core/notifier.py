"""
Desktop notifications manager using notify-send and GNotification / libnotify.
Supports quiet mode to prevent annoying notification popup spam.
"""

import subprocess
import shutil
from typing import Optional
from wifi_ac_guardian.core.models import StatusState, LinkInfo
from wifi_ac_guardian.logger import get_logger

logger = get_logger()


class DesktopNotifier:
    """Sends native Ubuntu desktop notifications for Wi-Fi status changes."""

    def __init__(self, enabled: bool = False, quiet_mode: bool = True):
        self.enabled = enabled
        self.quiet_mode = quiet_mode  # Suppresses repetitive retry popups
        self.last_status: Optional[StatusState] = None
        self._notify_send_path = shutil.which("notify-send")

    def notify_status(
        self,
        status: StatusState,
        link: Optional[LinkInfo] = None,
        attempts: int = 0,
        max_attempts: int = 10,
        force: bool = False
    ) -> None:
        """
        Sends desktop notification if enabled and status changed.

        Args:
            status: Target StatusState (GOOD, RETRYING, FAILED, DISCONNECTED).
            link: Current LinkInfo object if available.
            attempts: Current retry attempt count.
            max_attempts: Maximum retry count.
            force: Force notification even if status hasn't changed.
        """
        if not self.enabled:
            return

        # Quiet mode: Do NOT send annoying popups during RETRYING attempts
        if self.quiet_mode and status == StatusState.RETRYING and not force:
            return

        # Avoid redundant desktop popups if state hasn't changed
        if not force and status == self.last_status:
            return

        self.last_status = status

        if status == StatusState.GOOD:
            title = "Wi-Fi AC Guardian"
            phy_name = link.phy_summary if link else "Wi-Fi 5 (802.11ac)"
            ssid = link.ssid if (link and link.ssid) else "Connected"
            bitrate = f" ({link.tx_bitrate})" if (link and link.tx_bitrate) else ""
            body = f"Connected using {phy_name}\nSSID: {ssid}{bitrate}"
            icon = "network-wireless"
            urgency = "normal"

        elif status == StatusState.RETRYING:
            title = "Wi-Fi AC Guardian - Wi-Fi 4 Detected"
            body = f"Detected Wi-Fi 4 (802.11n).\nRetrying connection... (Attempt {attempts}/{max_attempts})"
            icon = "dialog-warning"
            urgency = "normal"

        elif status == StatusState.FAILED:
            title = "Wi-Fi AC Guardian - Reconnection Failed"
            body = f"Unable to obtain Wi-Fi 5 after {max_attempts} attempts."
            icon = "dialog-error"
            urgency = "critical"

        elif status == StatusState.DISCONNECTED:
            title = "Wi-Fi AC Guardian - Disconnected"
            body = "Wi-Fi interface is currently disconnected."
            icon = "network-wireless-disconnected"
            urgency = "normal"

        else:
            return

        self.send_notification(title, body, icon=icon, urgency=urgency)

    def send_notification(
        self,
        title: str,
        body: str,
        icon: str = "dialog-information",
        urgency: str = "normal"
    ) -> bool:
        """Executes notify-send command."""
        if not self.enabled or not self._notify_send_path:
            return False

        cmd = [
            self._notify_send_path,
            "-u", urgency,
            "-i", icon,
            "-a", "WiFi AC Guardian",
            title,
            body
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            logger.debug(f"Desktop notification sent: '{title}' - '{body}'")
            return True
        except Exception as e:
            logger.error(f"Failed to execute notify-send: {e}")
            return False
