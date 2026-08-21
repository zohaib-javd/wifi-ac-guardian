"""
Windows WLAN reconnection handler for Wi-Fi AC Guardian using netsh wlan.
"""

import time
import subprocess
from typing import Optional
from wifi_ac_guardian_win.core.models import LinkInfo, GuardianConfig
from wifi_ac_guardian_win.core.detector_win import WifiDetectorWin
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()


class WifiReconnectorWin:
    """Manages Wi-Fi adapter device reset (OFF -> ON) and netsh wlan reconnection routines on Windows 11."""

    def __init__(self, config: Optional[GuardianConfig] = None):
        self.config = config or GuardianConfig()
        self.detector = WifiDetectorWin(interface=self.config.interface)

    def trigger_reconnect(self, interface: str = "Wi-Fi", ssid: Optional[str] = None) -> LinkInfo:
        """
        Executes Hardware Wi-Fi Adapter Device Reset (OFF -> Wait 15s -> ON -> Wait 15s -> Connect -> Wait).
        """
        target_iface = interface or self.config.interface or "Wi-Fi"
        logger.warning(
            f"Triggering Hardware Wi-Fi Adapter Device Reset on interface '{target_iface}' "
            f"(Target SSID: '{ssid or 'Auto'}')..."
        )

        # 1. Disable Wi-Fi Adapter (OFF - Wi-Fi Airplane mode toggle)
        self._disable_adapter(target_iface)

        # 2. Wait reconnect_delay seconds (default 15.0s) while radio powers off
        delay = max(1.0, self.config.reconnect_delay)
        logger.info(f"Waiting {delay:.1f} seconds while Wi-Fi adapter radio powers off...")
        time.sleep(delay)

        # 3. Enable Wi-Fi Adapter (ON)
        self._enable_adapter(target_iface)

        # 4. Wait 15.0s for adapter radio & driver initialization
        logger.info(f"Waiting {delay:.1f} seconds for Wi-Fi interface radio stabilization...")
        time.sleep(delay)

        # 5. Connect via netsh wlan connect
        self._connect_interface(target_iface, ssid)

        # 6. Wait up to 15.0 seconds for link state stabilization
        updated_link = self._wait_for_connection(target_iface, timeout_seconds=15.0)
        return updated_link

    def _disable_adapter(self, interface: str) -> bool:
        """
        Disables the physical Wi-Fi adapter / radio (Wi-Fi only Airplane mode toggle).
        Uses WinRT Radio API (User-mode supported) with fallback to PowerShell Disable-NetAdapter and netsh.
        """
        logger.info(f"Disabling Wi-Fi adapter/radio '{interface}' (Hardware Radio Toggle OFF)...")

        # Method 1: WinRT Radio API (User mode & Admin compatible)
        if self._toggle_winrt_radio("Off"):
            logger.info(f"Successfully toggled Wi-Fi radio OFF via WinRT Radio API.")
            return True

        # Method 2: PowerShell Disable-NetAdapter
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        ps_cmd = ["powershell", "-NoProfile", "-Command", f"Disable-NetAdapter -Name '{interface}' -Confirm:$false"]
        try:
            res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            if res.returncode == 0:
                logger.info(f"Successfully disabled adapter '{interface}' via PowerShell Disable-NetAdapter.")
                return True
            else:
                logger.warning(f"Disable-NetAdapter output: {res.stdout or res.stderr}")
        except Exception as e:
            logger.warning(f"PowerShell Disable-NetAdapter failed: {e}")

        # Method 3: PowerShell Start-Process elevated Disable-NetAdapter
        ps_elevated = [
            "powershell", "-NoProfile", "-Command",
            f"Start-Process powershell -ArgumentList \"-NoProfile -Command Disable-NetAdapter -Name '{interface}' -Confirm:`$false\" -Verb RunAs -WindowStyle Hidden"
        ]
        try:
            subprocess.run(ps_elevated, capture_output=True, text=True, timeout=15, creationflags=flags)
            logger.info(f"Issued elevated Disable-NetAdapter for interface '{interface}'.")
            return True
        except Exception as e:
            logger.warning(f"Elevated Disable-NetAdapter failed: {e}")

        # Method 4: netsh interface set interface
        netsh_cmd = ["netsh", "interface", "set", "interface", f"name={interface}", "admin=disabled"]
        try:
            res = subprocess.run(netsh_cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            if res.returncode == 0:
                logger.info(f"Successfully disabled adapter '{interface}' via netsh.")
                return True
        except Exception as e:
            logger.error(f"netsh disable interface failed: {e}")

        # Secondary fallback: netsh wlan disconnect
        return self._disconnect_interface(interface)

    def _enable_adapter(self, interface: str) -> bool:
        """
        Enables the physical Wi-Fi adapter / radio (Hardware Radio Toggle ON).
        """
        logger.info(f"Enabling Wi-Fi adapter/radio '{interface}' (Hardware Radio Toggle ON)...")

        # Method 1: WinRT Radio API
        if self._toggle_winrt_radio("On"):
            logger.info(f"Successfully toggled Wi-Fi radio ON via WinRT Radio API.")
            return True

        # Method 2: PowerShell Enable-NetAdapter
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        ps_cmd = ["powershell", "-NoProfile", "-Command", f"Enable-NetAdapter -Name '{interface}' -Confirm:$false"]
        try:
            res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            if res.returncode == 0:
                logger.info(f"Successfully enabled adapter '{interface}' via PowerShell Enable-NetAdapter.")
                return True
            else:
                logger.warning(f"Enable-NetAdapter output: {res.stdout or res.stderr}")
        except Exception as e:
            logger.warning(f"PowerShell Enable-NetAdapter failed: {e}")

        # Method 3: PowerShell Start-Process elevated Enable-NetAdapter
        ps_elevated = [
            "powershell", "-NoProfile", "-Command",
            f"Start-Process powershell -ArgumentList \"-NoProfile -Command Enable-NetAdapter -Name '{interface}' -Confirm:`$false\" -Verb RunAs -WindowStyle Hidden"
        ]
        try:
            subprocess.run(ps_elevated, capture_output=True, text=True, timeout=15, creationflags=flags)
            logger.info(f"Issued elevated Enable-NetAdapter for interface '{interface}'.")
            return True
        except Exception as e:
            logger.warning(f"Elevated Enable-NetAdapter failed: {e}")

        # Method 4: netsh interface set interface
        netsh_cmd = ["netsh", "interface", "set", "interface", f"name={interface}", "admin=enabled"]
        try:
            res = subprocess.run(netsh_cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            if res.returncode == 0:
                logger.info(f"Successfully enabled adapter '{interface}' via netsh.")
                return True
        except Exception as e:
            logger.error(f"netsh enable interface failed: {e}")

        return False

    def _toggle_winrt_radio(self, state_str: str) -> bool:
        """Toggles Windows Wi-Fi radio state (Off / On) using WinRT Radio API via PowerShell."""
        ps_script = f"""
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        $asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }}[0]
        Function Await($WinRtTask, $ResultType) {{
            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
            $netTask = $asTask.Invoke($null, @($WinRtTask))
            $netTask.Wait()
            return $netTask.Result
        }}
        [Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
        $asyncOp = [Windows.Devices.Radios.Radio]::GetRadiosAsync()
        $radios = Await $asyncOp ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
        $wifi = $radios | Where-Object {{ $_.Kind -eq 'WiFi' -or $_.Name -like '*Wi-Fi*' }} | Select-Object -First 1
        if ($wifi) {{
            $targetState = [Windows.Devices.Radios.RadioState]::{state_str}
            $op = $wifi.SetStateAsync($targetState)
            $res = Await $op ([Windows.Devices.Radios.RadioAccessStatus])
            if ($res -eq [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {{
                Write-Host "SUCCESS"
            }}
        }}
        """
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=flags
            )
            return "SUCCESS" in res.stdout
        except Exception as e:
            logger.debug(f"WinRT radio toggle failed: {e}")
            return False

    def _disconnect_interface(self, interface: str) -> bool:
        """Disconnects Wi-Fi using netsh wlan disconnect."""
        logger.info(f"Disconnecting Wi-Fi interface {interface} via netsh...")
        try:
            cmd = ["netsh", "wlan", "disconnect", f"interface={interface}"]
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=flags)
            if res.returncode == 0:
                logger.info(f"Successfully disconnected interface {interface}.")
                return True
            else:
                logger.warning(f"netsh disconnect returned output: {res.stdout or res.stderr}")
        except Exception as e:
            logger.error(f"Error disconnecting interface {interface}: {e}")
        return False

    def _connect_interface(self, interface: str, ssid: Optional[str] = None) -> bool:
        """Reconnects Wi-Fi using netsh wlan connect."""
        logger.info(f"Initiating Wi-Fi connection on {interface}...")

        target_ssid = ssid or self.config.target_ssid
        if target_ssid:
            cmd = ["netsh", "wlan", "connect", f"name={target_ssid}", f"interface={interface}"]
        else:
            cmd = ["netsh", "wlan", "connect"]

        logger.info(f"Running command: {' '.join(cmd)}")
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, creationflags=flags)
            if res.returncode == 0:
                logger.info(f"netsh connect succeeded for SSID '{target_ssid or 'Auto'}'.")
                return True
            else:
                logger.warning(f"netsh connect output: {res.stdout or res.stderr}")
        except Exception as e:
            logger.error(f"Error connecting device {interface}: {e}")

        return False

    def _wait_for_connection(self, interface: str, timeout_seconds: float = 15.0) -> LinkInfo:
        """Polls netsh wlan show interfaces until connection is established or timeout."""
        start_time = time.time()
        poll_interval = 1.0

        link_info = self.detector.get_link_info()

        while time.time() - start_time < timeout_seconds:
            if link_info.connected:
                logger.info(
                    f"Connection re-established on Windows interface '{interface}'! "
                    f"SSID: '{link_info.ssid}' | PHY Mode: {link_info.phy_summary} | Bitrate: {link_info.tx_bitrate or link_info.rx_bitrate or 'N/A'}"
                )
                return link_info

            time.sleep(poll_interval)
            link_info = self.detector.get_link_info()

        logger.warning(f"Timed out waiting for Wi-Fi connection state stabilization on {interface}.")
        return link_info
