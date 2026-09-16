"""Windows recovery handler for native WLAN auto-association and PHY verification."""

import subprocess
import time
from datetime import datetime
from typing import Optional

from wifi_ac_guardian_win.core.detector_win import WifiDetectorWin
from wifi_ac_guardian_win.core.models import APPROVED_PHY_MODES, BssidCandidate, GuardianConfig, LinkInfo
from wifi_ac_guardian_win.core.radio_control_win import cycle_preferred_radio_state
from wifi_ac_guardian_win.logger import get_logger


logger = get_logger()


class WifiReconnectorWin:
    """Recover the selected Wi-Fi profile through a clean radio reassociation."""

    _COMMAND_TIMEOUT_SECONDS = 20
    _STATE_TIMEOUT_SECONDS = 15.0
    _NATIVE_ASSOCIATION_TIMEOUT_SECONDS = 20.0
    _MICRO_CYCLE_LIMIT = 3

    def __init__(self, config: Optional[GuardianConfig] = None):
        self.config = config or GuardianConfig()
        self.detector = WifiDetectorWin(interface=self.config.interface)
        # Recovery-sequence telemetry for the dashboard's Recovery Details row.
        # `recovery_start_time` is set once, on the first attempt of a
        # sequence, and `recovery_attempt_count` increments on every
        # trigger_reconnect() call. Both are left populated after a
        # successful reconnection (a historical readout of "how it went")
        # until Guardian calls reset_recovery_tracking() at the start of the
        # next fresh degraded-link sequence.
        self.recovery_start_time: Optional[datetime] = None
        self.recovery_attempt_count: int = 0

    def reset_recovery_tracking(self) -> None:
        """Clear recovery-sequence telemetry so the next attempt starts fresh."""
        self.recovery_start_time = None
        self.recovery_attempt_count = 0

    @staticmethod
    def _creation_flags() -> int:
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    @staticmethod
    def _quote_powershell(value: str) -> str:
        return value.replace("'", "''")

    @staticmethod
    def _command_output(result: Optional[subprocess.CompletedProcess]) -> str:
        return "" if result is None else (result.stderr or result.stdout or "").strip()

    def trigger_reconnect(self, interface: Optional[str] = None, ssid: Optional[str] = None) -> LinkInfo:
        """Recover through a radio cycle and observe native Windows auto-association."""
        initial_link = self.detector.get_link_info()
        target_interface = (interface or initial_link.interface or self.config.interface or "").strip()
        if not target_interface:
            logger.error("Wi-Fi reset skipped because Windows did not report a wireless interface.")
            return initial_link

        if self.recovery_start_time is None:
            self.recovery_start_time = datetime.now()
        self.recovery_attempt_count += 1

        delay = max(1.0, float(self.config.reconnect_delay))
        target_ssid = ssid or self.config.target_ssid
        logger.warning(
            "Starting native Windows auto-association recovery on '%s' (target SSID: '%s').",
            target_interface,
            target_ssid or "Auto",
        )
        self._log_link_snapshot("Initial", initial_link)

        self._disconnect_interface(target_interface)
        logger.info("Waiting 1.5 seconds after WLAN disconnect before radio recovery.")
        time.sleep(1.5)
        self._flush_network_caches()
        link_info = initial_link
        for cycle in range(1, self._MICRO_CYCLE_LIMIT + 1):
            radio_path = cycle_preferred_radio_state(hold_seconds=delay)
            if radio_path == "unavailable":
                logger.warning("[RADIO] No radio-cycle path was confirmed; observing Windows AutoConfig anyway.")
            else:
                logger.info("[RADIO] %s ON - waiting for AutoConfig auto-connect.", radio_path)
            
            logger.info("Triggering active 5 GHz probe scan with VHT80 capabilities.")
            self._trigger_active_scan(target_interface)

            started = time.monotonic()
            link_info = self._wait_for_native_auto_association(
                target_interface,
                target_ssid,
                timeout_seconds=self._NATIVE_ASSOCIATION_TIMEOUT_SECONDS,
            )
            elapsed = time.monotonic() - started
            if self._is_target_policy_good(link_info, target_ssid):
                logger.info("[AUTO] associated to %s in %.1fs.", target_ssid or "target", elapsed)
                logger.info("[QUALITY] PHY=%s result=SUCCESS", link_info.radio_type or link_info.phy_summary)
                return link_info
            if not link_info.connected or (target_ssid and (link_info.ssid or "").casefold() != target_ssid.casefold()):
                logger.warning("[AUTO] no target association in %.1fs; using post-window profile fallback.", elapsed)
                self._connect_interface(target_interface, target_ssid)
                link_info = self._wait_for_native_auto_association(target_interface, target_ssid, timeout_seconds=10.0)
                if self._is_target_policy_good(link_info, target_ssid):
                    logger.info("[QUALITY] PHY=%s result=SUCCESS", link_info.radio_type or link_info.phy_summary)
                    return link_info
            if link_info.connected and target_ssid and (link_info.ssid or "").casefold() == target_ssid.casefold():
                logger.warning(
                    "[QUALITY] PHY=%s band=%s result=PHY_STUCK_HT -> micro-cycle %s/%s",
                    link_info.radio_type or link_info.phy_summary,
                    self._band_for_link(link_info),
                    cycle,
                    self._MICRO_CYCLE_LIMIT,
                )
            if cycle < self._MICRO_CYCLE_LIMIT:
                cooldown = max(0.0, float(self.config.recovery_cooldown))
                logger.warning(
                    "[RECOVERY] Cycle %s/%s did not lock an approved PHY; waiting %.1fs recovery cool-down before cycle %s.",
                    cycle,
                    self._MICRO_CYCLE_LIMIT,
                    cooldown,
                    cycle + 1,
                )
                time.sleep(cooldown)
        return link_info

    def _run_powershell(self, script: str) -> Optional[subprocess.CompletedProcess]:
        try:
            return subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=self._COMMAND_TIMEOUT_SECONDS,
                creationflags=self._creation_flags(),
            )
        except (OSError, subprocess.SubprocessError) as error:
            logger.error("PowerShell Wi-Fi adapter command could not start: %s", error)
            return None

    def _set_adapter_state(self, interface: str, *, enabled: bool) -> bool:
        action = "Enable-NetAdapter" if enabled else "Disable-NetAdapter"
        verb = "enable" if enabled else "disable"
        script = (
            "$ErrorActionPreference = 'Stop'; "
            f"{action} -Name '{self._quote_powershell(interface)}' -Confirm:$false -ErrorAction Stop"
        )
        result = self._run_powershell(script)
        if result is not None and result.returncode == 0:
            logger.info("Wi-Fi adapter '%s' %s command completed.", interface, verb)
            return True
        detail = self._command_output(result)
        logger.error("Windows could not %s Wi-Fi adapter '%s'%s.", verb, interface, f": {detail}" if detail else "")
        return False

    def _wait_for_adapter_state(self, interface: str, *, expected_disabled: bool) -> bool:
        deadline = time.monotonic() + self._STATE_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            state = self._get_adapter_state(interface)
            if expected_disabled and state == "disabled":
                return True
            if not expected_disabled and state and state != "disabled":
                return True
            time.sleep(0.5)
        return False

    def _get_adapter_state(self, interface: str) -> str:
        script = (
            "$ErrorActionPreference = 'Stop'; "
            f"(Get-NetAdapter -Name '{self._quote_powershell(interface)}' -ErrorAction Stop).Status"
        )
        result = self._run_powershell(script)
        return "" if result is None or result.returncode != 0 else (result.stdout or "").strip().lower()

    def _run_command(self, command: list[str], timeout: int = 15) -> Optional[subprocess.CompletedProcess]:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=self._creation_flags(),
            )
        except (OSError, subprocess.SubprocessError) as error:
            logger.error("Windows recovery command could not start (%s): %s", command[0] if command else "unknown", error)
            return None

    def _disconnect_interface(self, interface: str) -> bool:
        result = self._run_command(["netsh", "wlan", "disconnect", f'interface="{interface}"'], timeout=5)
        if result is not None and result.returncode == 0:
            logger.info("Requested WLAN disconnect on '%s' before radio recovery.", interface)
            return True
        logger.warning("WLAN disconnect request returned: %s", self._command_output(result))
        return False

    def _flush_network_caches(self) -> None:
        for command, label in (
            (["netsh", "interface", "ip", "delete", "arpcache"], "ARP cache"),
            (["ipconfig", "/flushdns"], "DNS cache"),
        ):
            result = self._run_command(command, timeout=5)
            if result is not None and result.returncode == 0:
                logger.info("Flushed local %s before WLAN reassociation.", label)
            else:
                logger.warning("Could not flush local %s: %s", label, self._command_output(result))

    def _trigger_network_inventory(self) -> bool:
        result = self._run_command(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=10)
        if result is not None and result.returncode == 0:
            logger.info("Requested Windows WLAN BSSID inventory after radio recovery.")
            return True
        logger.warning("Windows WLAN BSSID inventory request returned: %s", self._command_output(result))
        return False

    def _log_link_snapshot(self, label: str, link: LinkInfo) -> None:
        logger.info(
            "[RECOVERY] %s link: SSID=%s, BSSID=%s, Channel=%s, Frequency=%s MHz, Signal=%s%%, PHY=%s, TX=%s, RX=%s.",
            label,
            link.ssid or "N/A",
            link.bssid or "N/A",
            link.channel if link.channel is not None else "N/A",
            link.freq_mhz if link.freq_mhz is not None else "N/A",
            link.signal_pct if link.signal_pct is not None else 0,
            link.phy_summary,
            link.tx_bitrate or "N/A",
            link.rx_bitrate or "N/A",
        )

    def _select_bssid_candidate(self, ssid: Optional[str], excluded_bssids: set[str]) -> Optional[BssidCandidate]:
        target_ssid = (ssid or "").strip()
        if not target_ssid:
            return None
        candidates = self.detector.get_bssid_candidates(target_ssid)
        usable = [candidate for candidate in candidates if candidate.bssid.casefold() not in excluded_bssids]
        for candidate in candidates:
            logger.info(
                "[SCAN] Target SSID=%s, BSSID=%s, Band=%s, Channel=%s, Signal=%s%%, PHY=%s.",
                target_ssid,
                candidate.bssid,
                candidate.band,
                candidate.channel if candidate.channel is not None else "N/A",
                candidate.signal_pct if candidate.signal_pct is not None else 0,
                candidate.radio_type or "Unknown",
            )
        if not usable:
            logger.info("[SELECT] No suitable visible BSSID candidate; using normal SSID association.")
            return None

        preference = self.config.preferred_bssids.get(target_ssid.casefold(), {})
        preferred_bssid = str(preference.get("preferred_bssid") or "").casefold()

        def rank(candidate: BssidCandidate) -> tuple[int, int, int, int]:
            return (
                0 if candidate.bssid.casefold() == preferred_bssid else 1,
                0 if candidate.band in {"5GHz", "6GHz"} else 1,
                0 if candidate.phy_mode in APPROVED_PHY_MODES else 1,
                -(candidate.signal_pct or 0),
            )

        selected = sorted(usable, key=rank)[0]
        logger.info(
            "[SELECT] Chosen BSSID=%s, Band=%s, Channel=%s%s.",
            selected.bssid,
            selected.band,
            selected.channel if selected.channel is not None else "N/A",
            " (previously verified)" if selected.bssid.casefold() == preferred_bssid else "",
        )
        return selected

    def _trigger_active_scan(self, interface: str) -> bool:
        """Request a Windows WLAN API scan for the selected wireless interface.

        WlanScan requests a driver-level scan; Windows and the driver retain
        authority over the resulting probe requests and channel selection.
        """
        script = f"""
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class GuardianWlanScan {{
    [DllImport("wlanapi.dll", SetLastError = true)]
    public static extern uint WlanOpenHandle(uint clientVersion, IntPtr reserved, out uint negotiatedVersion, out IntPtr clientHandle);
    [DllImport("wlanapi.dll", SetLastError = true)]
    public static extern uint WlanCloseHandle(IntPtr clientHandle, IntPtr reserved);
    [DllImport("wlanapi.dll", SetLastError = true)]
    public static extern uint WlanScan(IntPtr clientHandle, ref Guid interfaceGuid, IntPtr dot11Ssid, IntPtr ieData, IntPtr reserved);
}}
'@
$adapter = Get-NetAdapter -Name '{self._quote_powershell(interface)}' -ErrorAction Stop
$interfaceGuid = [Guid]$adapter.InterfaceGuid
[uint32]$version = 0
$clientHandle = [IntPtr]::Zero
$openResult = [GuardianWlanScan]::WlanOpenHandle(2, [IntPtr]::Zero, [ref]$version, [ref]$clientHandle)
if ($openResult -ne 0) {{ throw "WlanOpenHandle failed with code $openResult" }}
try {{
    $scanResult = [GuardianWlanScan]::WlanScan($clientHandle, [ref]$interfaceGuid, [IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero)
    if ($scanResult -ne 0) {{ throw "WlanScan failed with code $scanResult" }}
}} finally {{
    if ($clientHandle -ne [IntPtr]::Zero) {{ [void][GuardianWlanScan]::WlanCloseHandle($clientHandle, [IntPtr]::Zero) }}
}}
"""
        result = self._run_powershell(script)
        if result is not None and result.returncode == 0:
            logger.info("Requested Windows WLAN API scan on '%s' after radio recovery.", interface)
            return True
        logger.warning("Windows WLAN API scan request returned: %s", self._command_output(result))
        return False

    def _connect_interface(self, interface: str, ssid: Optional[str], desired_bssid: Optional[str] = None) -> bool:
        command = ["netsh", "wlan", "connect"]
        if ssid:
            command.append(f"name={ssid}")
        command.append(f"interface={interface}")
        result = self._run_command(command, timeout=15)
        if result is not None and result.returncode == 0:
            logger.info("[FALLBACK] Post-observation profile connection request succeeded for '%s'.", ssid or "Auto")
            return True
        logger.warning("[FALLBACK] Profile connection request returned: %s", self._command_output(result))
        return False

    def _is_target_policy_good(self, link_info: LinkInfo, target_ssid: Optional[str]) -> bool:
        target = (target_ssid or "").casefold()
        return (
            link_info.connected
            and (not target or (link_info.ssid or "").casefold() == target)
            and link_info.has_approved_phy()
        )

    @staticmethod
    def _band_for_link(link_info: LinkInfo) -> str:
        if link_info.channel is None:
            return "unknown"
        if link_info.channel <= 14:
            return "2.4GHz"
        if link_info.channel >= 181:
            return "6GHz"
        return "5GHz"

    def _connect_with_desired_bssid(self, interface: str, ssid: str, bssid: str) -> bool:
        """Request profile association with one desired BSSID through WlanConnect.

        Drivers and profile policy may reject a desired BSSID. The caller falls
        back to normal profile association in that documented failure case.
        """
        script = f"""
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class GuardianWlanConnect {{
    [StructLayout(LayoutKind.Sequential)] public struct WLAN_CONNECTION_PARAMETERS {{ public int wlanConnectionMode; [MarshalAs(UnmanagedType.LPWStr)] public string strProfile; public IntPtr pDot11Ssid; public IntPtr pDesiredBssidList; public int dot11BssType; public uint dwFlags; }}
    [DllImport("wlanapi.dll", SetLastError=true)] public static extern uint WlanOpenHandle(uint clientVersion, IntPtr reserved, out uint negotiatedVersion, out IntPtr clientHandle);
    [DllImport("wlanapi.dll", SetLastError=true)] public static extern uint WlanCloseHandle(IntPtr clientHandle, IntPtr reserved);
    [DllImport("wlanapi.dll", SetLastError=true)] public static extern uint WlanConnect(IntPtr clientHandle, ref Guid interfaceGuid, ref WLAN_CONNECTION_PARAMETERS connectionParameters, IntPtr reserved);
    public static uint Connect(Guid interfaceGuid, string profile, string mac) {{
        string[] parts = mac.Split(':'); if (parts.Length != 6) throw new ArgumentException("Invalid BSSID");
        byte[] bssid = new byte[6]; for (int i=0; i<6; i++) bssid[i] = Convert.ToByte(parts[i], 16);
        uint version; IntPtr handle; uint open = WlanOpenHandle(2, IntPtr.Zero, out version, out handle); if (open != 0) return open;
        IntPtr list = IntPtr.Zero;
        try {{
            const int listSize = 20; list = Marshal.AllocHGlobal(listSize); for (int i=0; i<listSize; i++) Marshal.WriteByte(list, i, 0);
            Marshal.WriteByte(list, 0, 0x80); Marshal.WriteByte(list, 1, 1); Marshal.WriteInt16(list, 2, 20);
            Marshal.WriteInt32(list, 4, 1); Marshal.WriteInt32(list, 8, 1); Marshal.Copy(bssid, 0, IntPtr.Add(list, 12), 6);
            WLAN_CONNECTION_PARAMETERS parameters = new WLAN_CONNECTION_PARAMETERS {{ wlanConnectionMode=0, strProfile=profile, pDot11Ssid=IntPtr.Zero, pDesiredBssidList=list, dot11BssType=1, dwFlags=0 }};
            return WlanConnect(handle, ref interfaceGuid, ref parameters, IntPtr.Zero);
        }} finally {{ if (list != IntPtr.Zero) Marshal.FreeHGlobal(list); WlanCloseHandle(handle, IntPtr.Zero); }}
    }}
}}
'@
$adapter = Get-NetAdapter -Name '{self._quote_powershell(interface)}' -ErrorAction Stop
$result = [GuardianWlanConnect]::Connect([Guid]$adapter.InterfaceGuid, '{self._quote_powershell(ssid)}', '{self._quote_powershell(bssid)}')
if ($result -ne 0) {{ throw "WlanConnect failed with code $result" }}
"""
        result = self._run_powershell(script)
        if result is not None and result.returncode == 0:
            logger.info("[CONNECT] Requested desired BSSID=%s for profile '%s'.", bssid, ssid)
            return True
        logger.warning("Desired BSSID connection request returned: %s", self._command_output(result))
        return False

    def _requires_micro_recovery(self, link_info: LinkInfo) -> bool:
        """Return True only for a connected link with a confirmed policy mismatch."""
        if not link_info.connected:
            return False
        if link_info.phy_mode not in APPROVED_PHY_MODES:
            return True
        return link_info.max_bitrate_mbps > 0 and not link_info.is_good(self.config.min_bitrate_threshold)

    def _wait_for_connection(
        self,
        interface: str,
        timeout_seconds: float = 15.0,
        return_on_first_connection: bool = False,
    ) -> LinkInfo:
        deadline = time.monotonic() + timeout_seconds
        link_info = self.detector.get_link_info()
        while time.monotonic() < deadline:
            if link_info.connected and link_info.is_good(self.config.min_bitrate_threshold):
                logger.info(
                    "Wi-Fi connection re-established on '%s': SSID='%s', PHY=%s, bitrate=%s.",
                    interface,
                    link_info.ssid,
                    link_info.phy_summary,
                    link_info.tx_bitrate or link_info.rx_bitrate or "N/A",
                )
                return link_info
            if link_info.connected:
                logger.info(
                    "Wi-Fi connected on '%s' but PHY verification is pending: PHY=%s, bitrate=%s.",
                    interface,
                    link_info.phy_summary,
                    link_info.tx_bitrate or link_info.rx_bitrate or "N/A",
                )
                if return_on_first_connection:
                    return link_info
            time.sleep(1.0)
            link_info = self.detector.get_link_info()
        logger.warning("Timed out waiting for Wi-Fi connection stabilization on '%s'.", interface)
        return link_info

    def _wait_for_native_auto_association(
        self,
        interface: str,
        target_ssid: Optional[str],
        timeout_seconds: float,
    ) -> LinkInfo:
        """Passively observe the link restored by Windows WLAN AutoConfig.

        The first association to the selected target is returned whether it
        meets policy or not, allowing the guardian to make the final truthful
        PHY/rate decision without issuing a profile connection command.
        """
        deadline = time.monotonic() + timeout_seconds
        link_info = self.detector.get_link_info()
        target = (target_ssid or "").casefold()
        while time.monotonic() < deadline:
            if link_info.connected:
                observed_ssid = (link_info.ssid or "").casefold()
                if not target or observed_ssid == target:
                    self._log_link_snapshot("Native AutoConfig association", link_info)
                    return link_info
                logger.info(
                    "Windows AutoConfig associated '%s' while waiting for target '%s'; continuing passive observation.",
                    link_info.ssid or "N/A",
                    target_ssid or "Auto",
                )
            time.sleep(1.0)
            link_info = self.detector.get_link_info()
        logger.warning(
            "Timed out after %.1f seconds waiting for native Windows AutoConfig association on '%s'.",
            timeout_seconds,
            interface,
        )
        return link_info
