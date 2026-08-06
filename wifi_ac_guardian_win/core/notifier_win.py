"""
Windows Toast Notifications Manager using PowerShell / Win10Toast.
"""

import subprocess
from typing import Optional
from wifi_ac_guardian_win.core.models import StatusState, LinkInfo
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()


class WindowsNotifier:
    """Sends native Windows 11 Toast notifications."""

    def __init__(self, enabled: bool = False, quiet_mode: bool = True):
        self.enabled = enabled
        self.quiet_mode = quiet_mode
        self.last_status: Optional[StatusState] = None

    def notify_status(
        self,
        status: StatusState,
        link: Optional[LinkInfo] = None,
        attempts: int = 0,
        max_attempts: int = 10,
        force: bool = False
    ) -> None:
        if not self.enabled:
            return

        if self.quiet_mode and status == StatusState.RETRYING and not force:
            return

        if not force and status == self.last_status:
            return

        self.last_status = status

        # Source notification text from the shared status descriptor (feature 001, T023)
        from wifi_ac_guardian_win.status_presentation import get_presentation
        desc = get_presentation(status)

        if status == StatusState.GOOD:
            title = "WiFi AC Guardian"
            phy_name = link.phy_summary if link else "Wi-Fi 5 (802.11ac)"
            ssid = link.ssid if (link and link.ssid) else "Connected"
            body = f"Connected using {phy_name} - SSID: {ssid}"

        elif status == StatusState.RETRYING:
            title = f"WiFi AC Guardian - {desc.headline}"
            body = f"{desc.supporting} (Attempt {attempts}/{max_attempts})"

        elif status == StatusState.FAILED:
            title = f"WiFi AC Guardian - {desc.headline}"
            body = f"Unable to obtain Wi-Fi 5 after {max_attempts} attempts."

        else:
            return

        self.send_toast(title, body)

    def send_toast(self, title: str, body: str) -> bool:
        """Sends native Windows Toast via PowerShell script."""
        if not self.enabled:
            return False

        ps_script = f"""
        [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = '{title}'
        $notification.BalloonTipText = '{body}'
        $notification.Visible = $true
        $notification.ShowBalloonTip(5000)
        """

        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=flags
            )
            return True
        except Exception as e:
            logger.debug(f"Failed to send Windows Toast: {e}")
            return False
