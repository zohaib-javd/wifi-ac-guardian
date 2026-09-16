"""Windows Native Wi-Fi software-radio control for WiFi AC Guardian.

This module uses Wlanapi.dll's documented `wlan_intf_opcode_radio_state`
operation. It cycles *only* the selected Wi-Fi interface's software radio; it
does not disable the network adapter, toggle global Airplane Mode, or touch
Bluetooth/cellular radios.
"""

from __future__ import annotations

import ctypes
import subprocess
import time
from ctypes import wintypes
from dataclasses import dataclass
from typing import List, Optional

from wifi_ac_guardian_win.logger import get_logger


logger = get_logger()


def cycle_system_radio_state(hold_seconds: float) -> bool:
    """Attempt a platform system-radio toggle only when that API exists at runtime.

    Microsoft documents individual-radio `SetStateAsync`; the requested static
    system method is probed rather than assumed. A false return instructs the
    caller to use the supported per-radio fallback.
    """
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
    $systemMethod = [Windows.Devices.Radios.Radio].GetMethod('SetSystemRadioStateAsync')
    if ($null -eq $systemMethod) {{ throw 'System radio-state method is unavailable on this Windows runtime.' }}
    $asTaskMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 }} | Select-Object -First 1
    function Await-WinRt([object]$operation, [type]$resultType) {{ $task = $asTaskMethod.MakeGenericMethod($resultType).Invoke($null, @($operation)); $task.Wait(); return $task.Result }}
    $off = Await-WinRt ($systemMethod.Invoke($null, @([Windows.Devices.Radios.RadioState]::Off))) ([Windows.Devices.Radios.RadioAccessStatus])
    if ($off -ne [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {{ throw "System radio OFF was not allowed: $off" }}
    Start-Sleep -Milliseconds {int(max(1.0, hold_seconds) * 1000)}
    $on = Await-WinRt ($systemMethod.Invoke($null, @([Windows.Devices.Radios.RadioState]::On))) ([Windows.Devices.Radios.RadioAccessStatus])
    if ($on -ne [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {{ throw "System radio ON was not allowed: $on" }}
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=int(max(1.0, hold_seconds)) + 30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        )
    except (OSError, subprocess.SubprocessError) as error:
        logger.warning("[RADIO] system-airplane request could not start: %s", error)
        return False
    if result.returncode == 0:
        logger.info("[RADIO] system-airplane OFF (%.1fs), then ON.", hold_seconds)
        return True
    logger.info("[RADIO] system-airplane unavailable: %s", (result.stderr or result.stdout or "unknown error").strip())
    return False


def cycle_airplane_mode_radios(hold_seconds: float = 5.0) -> bool:
    """Request an all-radio off/on cycle through the Windows Runtime radio API.

    Windows applies this request separately to each exposed radio. It is not a
    claim that global Airplane Mode was changed; every request is subject to
    Windows permission, device capability, and system policy.
    """
    hold_seconds = max(5.0, float(hold_seconds))
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
    $asTaskMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{
        $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1
    }} | Select-Object -First 1
    function Await-WinRt([object]$operation, [type]$resultType) {{
        $task = $asTaskMethod.MakeGenericMethod($resultType).Invoke($null, @($operation))
        $task.Wait()
        return $task.Result
    }}
    $radios = Await-WinRt ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
    foreach ($radio in $radios) {{
        $status = Await-WinRt ($radio.SetStateAsync([Windows.Devices.Radios.RadioState]::Off)) ([Windows.Devices.Radios.RadioAccessStatus])
        if ($status -ne [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {{ throw "Radio-off request was not allowed: $status" }}
    }}
    Start-Sleep -Seconds {hold_seconds}
    foreach ($radio in $radios) {{
        $status = Await-WinRt ($radio.SetStateAsync([Windows.Devices.Radios.RadioState]::On)) ([Windows.Devices.Radios.RadioAccessStatus])
        if ($status -ne [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {{ throw "Radio-on request was not allowed: $status" }}
    }}
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=int(hold_seconds) + 30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        )
    except (OSError, subprocess.SubprocessError) as error:
        logger.error("Windows Runtime all-radio cycle could not start: %s", error)
        return False
    if result.returncode == 0:
        logger.info("[RADIO] per-radio OFF (%.1fs), then ON.", hold_seconds)
        return True
    logger.error("Windows Runtime all-radio cycle failed: %s", (result.stderr or result.stdout or "unknown error").strip())
    return False


def cycle_preferred_radio_state(hold_seconds: float) -> str:
    """Return the actual radio-cycle path used: system-airplane, per-radio, or unavailable."""
    if cycle_system_radio_state(hold_seconds):
        return "system-airplane"
    if cycle_airplane_mode_radios(hold_seconds):
        return "per-radio"
    return "unavailable"

ERROR_SUCCESS = 0
WLAN_INTF_OPCODE_RADIO_STATE = 4
DOT11_RADIO_STATE_ON = 1
DOT11_RADIO_STATE_OFF = 2
WLAN_MAX_PHY_INDEX = 64


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid", GUID),
        ("strInterfaceDescription", ctypes.c_wchar * 256),
        ("isState", wintypes.DWORD),
    ]


class WLAN_INTERFACE_INFO_LIST_HEADER(ctypes.Structure):
    _fields_ = [("dwNumberOfItems", wintypes.DWORD), ("dwIndex", wintypes.DWORD)]


class WLAN_PHY_RADIO_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPhyIndex", wintypes.DWORD),
        ("dot11SoftwareRadioState", wintypes.DWORD),
        ("dot11HardwareRadioState", wintypes.DWORD),
    ]


class WLAN_RADIO_STATE_HEADER(ctypes.Structure):
    _fields_ = [("dwNumberOfPhys", wintypes.DWORD)]


@dataclass(frozen=True)
class WirelessInterface:
    """Native Windows WLAN interface identity used only for a radio operation."""

    description: str
    guid: GUID


class WifiRadioControllerWin:
    """Cycle the selected Windows Wi-Fi software radio without an adapter reset."""

    def __init__(self):
        self._wlan = ctypes.WinDLL("wlanapi.dll")
        self._configure_api()

    def _configure_api(self) -> None:
        self._wlan.WlanOpenHandle.argtypes = [
            wintypes.DWORD,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.HANDLE),
        ]
        self._wlan.WlanOpenHandle.restype = wintypes.DWORD
        self._wlan.WlanCloseHandle.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
        self._wlan.WlanCloseHandle.restype = wintypes.DWORD
        self._wlan.WlanEnumInterfaces.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.LPVOID),
        ]
        self._wlan.WlanEnumInterfaces.restype = wintypes.DWORD
        self._wlan.WlanQueryInterface.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(GUID),
            wintypes.DWORD,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.LPVOID),
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._wlan.WlanQueryInterface.restype = wintypes.DWORD
        self._wlan.WlanSetInterface.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(GUID),
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        self._wlan.WlanSetInterface.restype = wintypes.DWORD
        self._wlan.WlanFreeMemory.argtypes = [wintypes.LPVOID]
        self._wlan.WlanFreeMemory.restype = None

    def cycle_radio(self, adapter_description: str, hold_seconds: float) -> bool:
        """Turn the matching Wi-Fi software radio off then back on.

        Returns false without touching any device if Windows cannot identify the
        target adapter, policy/hardware rejects software radio control, or the
        operation cannot be verified. There is intentionally no adapter-disable
        fallback.
        """
        client_handle = self._open_client()
        if client_handle is None:
            return False
        try:
            interface = self._find_interface(client_handle, adapter_description)
            if interface is None:
                logger.error("Software radio recovery skipped: Windows did not expose adapter '%s'.", adapter_description or "Auto")
                return False
            phy_states = self._query_phy_states(client_handle, interface.guid)
            if not phy_states:
                logger.error("Software radio recovery skipped: no Wi-Fi PHY was reported for '%s'.", interface.description)
                return False

            logger.warning("Turning Wi-Fi software radio off for '%s' without disabling the adapter.", interface.description)
            if not self._set_software_radio(client_handle, interface.guid, [state.dwPhyIndex for state in phy_states], DOT11_RADIO_STATE_OFF):
                return False
            time.sleep(max(1.0, float(hold_seconds)))
            logger.warning("Turning Wi-Fi software radio back on for '%s'.", interface.description)
            if not self._set_software_radio(client_handle, interface.guid, [state.dwPhyIndex for state in phy_states], DOT11_RADIO_STATE_ON):
                return False
            return True
        finally:
            self._wlan.WlanCloseHandle(client_handle, None)

    def is_radio_on(self, adapter_description: str = "") -> Optional[bool]:
        """Return Wi-Fi radio availability without changing any Windows state.

        `False` means either the hardware or software Wi-Fi radio is off. The
        interface remains physically present; this is the condition exposed by
        Airplane Mode or an OS Wi-Fi software switch.
        """
        client_handle = self._open_client()
        if client_handle is None:
            return None
        try:
            interface = self._find_interface(client_handle, adapter_description)
            if interface is None:
                return None
            states = self._query_phy_states(client_handle, interface.guid)
            if not states:
                return None
            return all(
                state.dot11SoftwareRadioState == DOT11_RADIO_STATE_ON
                and state.dot11HardwareRadioState == DOT11_RADIO_STATE_ON
                for state in states
            )
        finally:
            self._wlan.WlanCloseHandle(client_handle, None)

    def _open_client(self) -> Optional[wintypes.HANDLE]:
        negotiated_version = wintypes.DWORD()
        handle = wintypes.HANDLE()
        result = self._wlan.WlanOpenHandle(2, None, ctypes.byref(negotiated_version), ctypes.byref(handle))
        if result != ERROR_SUCCESS:
            logger.error("WlanOpenHandle failed with Windows error %s.", result)
            return None
        return handle

    def _find_interface(self, handle: wintypes.HANDLE, adapter_description: str) -> Optional[WirelessInterface]:
        interface_list = wintypes.LPVOID()
        result = self._wlan.WlanEnumInterfaces(handle, None, ctypes.byref(interface_list))
        if result != ERROR_SUCCESS:
            logger.error("WlanEnumInterfaces failed with Windows error %s.", result)
            return None
        try:
            header = ctypes.cast(interface_list, ctypes.POINTER(WLAN_INTERFACE_INFO_LIST_HEADER)).contents
            base_address = ctypes.addressof(header) + ctypes.sizeof(WLAN_INTERFACE_INFO_LIST_HEADER)
            candidates: List[WirelessInterface] = []
            for index in range(header.dwNumberOfItems):
                item = WLAN_INTERFACE_INFO.from_address(base_address + index * ctypes.sizeof(WLAN_INTERFACE_INFO))
                candidates.append(WirelessInterface(description=item.strInterfaceDescription.strip(), guid=item.InterfaceGuid))

            requested = (adapter_description or "").strip().casefold()
            for candidate in candidates:
                if requested and candidate.description.casefold() == requested:
                    return candidate
            if len(candidates) == 1:
                return candidates[0]
            return None
        finally:
            self._wlan.WlanFreeMemory(interface_list)

    def _query_phy_states(self, handle: wintypes.HANDLE, interface_guid: GUID) -> List[WLAN_PHY_RADIO_STATE]:
        data_size = wintypes.DWORD()
        data = wintypes.LPVOID()
        opcode_type = wintypes.DWORD()
        result = self._wlan.WlanQueryInterface(
            handle,
            ctypes.byref(interface_guid),
            WLAN_INTF_OPCODE_RADIO_STATE,
            None,
            ctypes.byref(data_size),
            ctypes.byref(data),
            ctypes.byref(opcode_type),
        )
        if result != ERROR_SUCCESS:
            logger.error("WlanQueryInterface(radio_state) failed with Windows error %s.", result)
            return []
        try:
            header = ctypes.cast(data, ctypes.POINTER(WLAN_RADIO_STATE_HEADER)).contents
            max_count = min(header.dwNumberOfPhys, WLAN_MAX_PHY_INDEX)
            base_address = ctypes.addressof(header) + ctypes.sizeof(WLAN_RADIO_STATE_HEADER)
            return [
                WLAN_PHY_RADIO_STATE.from_address(base_address + index * ctypes.sizeof(WLAN_PHY_RADIO_STATE))
                for index in range(max_count)
            ]
        finally:
            self._wlan.WlanFreeMemory(data)

    def _set_software_radio(self, handle: wintypes.HANDLE, interface_guid: GUID, phy_indices: List[int], state: int) -> bool:
        for phy_index in phy_indices:
            radio_state = WLAN_PHY_RADIO_STATE(
                dwPhyIndex=phy_index,
                dot11SoftwareRadioState=state,
                dot11HardwareRadioState=0,
            )
            result = self._wlan.WlanSetInterface(
                handle,
                ctypes.byref(interface_guid),
                WLAN_INTF_OPCODE_RADIO_STATE,
                ctypes.sizeof(radio_state),
                ctypes.byref(radio_state),
                None,
            )
            if result != ERROR_SUCCESS:
                logger.error("WlanSetInterface(radio_state) failed with Windows error %s for PHY %s.", result, phy_index)
                return False
        return True
