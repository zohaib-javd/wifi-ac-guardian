"""
Windows wireless interface detector and netsh wlan link parser.
Parses output of 'netsh wlan show interfaces' to extract physical mode, bitrate, frequency,
channel, signal percentage, and connection state on Windows 11.
"""

import json
import re
import subprocess
from typing import List, Optional
from wifi_ac_guardian_win.core.models import BssidCandidate, LinkInfo, PhyMode, RadioState
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()


def parse_netsh_output(raw_output: str, interface_fallback: str = "") -> LinkInfo:
    """
    Parses output of 'netsh wlan show interfaces' command on Windows 11.

    Args:
        raw_output: Command stdout string.
        interface_fallback: Optional interface name to use only if Windows did
            not report a name. Production discovery never supplies a fixed name.

    Returns:
        LinkInfo dataclass populated with parsed parameters.
    """
    info = LinkInfo(interface=interface_fallback, raw_output=raw_output)

    if not raw_output or "disconnected" in raw_output.lower() and "connected" not in raw_output.lower():
        info.connected = False
        info.phy_mode = PhyMode.DISCONNECTED
        info.radio_state = RadioState.NO_ADAPTER if not raw_output else RadioState.DISCONNECTED
        info.signal_pct = 0
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
        info.adapter = key_val.get("description") or info.interface

    # State check
    state_str = key_val.get("state", "").lower()
    # Do not use a substring match here: ``disconnected`` contains the word
    # ``connected`` and would otherwise be selected ahead of the real active
    # adapter on systems that expose multiple wireless interfaces.
    if state_str == "connected":
        info.connected = True
        info.radio_state = RadioState.ACTIVE
    else:
        info.connected = False
        info.phy_mode = PhyMode.DISCONNECTED
        info.radio_state = RadioState.DISCONNECTED
        # Do not carry a prior signal/rate forward when the user disconnected.
        # The dashboard must show the actual unavailable link as 0 Mbps / 0%.
        info.signal_pct = 0
        info.rx_bitrate = None
        info.tx_bitrate = None
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


def parse_netsh_interfaces(raw_output: str, interface_fallback: str = "") -> List[LinkInfo]:
    """Parse every interface block emitted by ``netsh wlan show interfaces``.

    Windows can expose adapters with customer-specific names such as ``Wi-Fi``,
    ``Wireless Network Connection``, or an OEM-renamed interface. Selecting from
    these blocks avoids assuming any adapter name or vendor model.
    """
    if not raw_output:
        return [parse_netsh_output(raw_output, interface_fallback=interface_fallback)]

    starts = [match.start() for match in re.finditer(r"(?mi)^\s*name\s*:\s*.+$", raw_output)]
    if not starts:
        return [parse_netsh_output(raw_output, interface_fallback=interface_fallback)]

    blocks = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(raw_output)
        blocks.append(parse_netsh_output(raw_output[start:end], interface_fallback=interface_fallback))
    return blocks


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


def parse_netsh_bssid_candidates(raw_output: str, target_ssid: str) -> List[BssidCandidate]:
    """Parse `netsh wlan show networks mode=bssid` records for one target SSID."""
    candidates: List[BssidCandidate] = []
    current_ssid = ""
    current: Optional[dict[str, object]] = None

    def commit() -> None:
        nonlocal current
        if not current or current_ssid.casefold() != target_ssid.casefold():
            current = None
            return
        bssid = str(current.get("bssid") or "").strip()
        if not bssid:
            current = None
            return
        candidates.append(
            BssidCandidate(
                ssid=current_ssid,
                bssid=bssid,
                channel=current.get("channel") if isinstance(current.get("channel"), int) else None,
                signal_pct=current.get("signal_pct") if isinstance(current.get("signal_pct"), int) else None,
                radio_type=str(current.get("radio_type") or ""),
                phy_mode=determine_win_phy_mode(str(current.get("radio_type") or ""), ""),
            )
        )
        current = None

    for raw_line in raw_output.splitlines():
        line = raw_line.strip()
        ssid_match = re.match(r"(?i)^SSID\s+\d+\s*:\s*(.*)$", line)
        if ssid_match:
            commit()
            current_ssid = ssid_match.group(1).strip()
            continue

        bssid_match = re.match(r"(?i)^BSSID\s+\d+\s*:\s*([0-9a-f:.-]+)$", line)
        if bssid_match:
            commit()
            current = {"bssid": bssid_match.group(1).strip()}
            continue

        if current is None or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.casefold()
        if key == "signal":
            try:
                current["signal_pct"] = int(value.replace("%", "").strip())
            except ValueError:
                pass
        elif key == "channel":
            try:
                current["channel"] = int(value)
            except ValueError:
                pass
        elif key == "radio type":
            current["radio_type"] = value

    commit()
    return candidates


class WifiDetectorWin:
    """High-level interface for querying current wireless link status using netsh wlan."""

    def __init__(self, interface: Optional[str] = None):
        # A supplied interface is a deliberate advanced override. Normal app
        # operation leaves this unset and discovers the connected Windows Wi-Fi
        # interface on every telemetry query.
        self.interface = (interface or "").strip() or None

    def _select_interface(self, links: List[LinkInfo]) -> LinkInfo:
        """Select an explicit override first, otherwise the active wireless link."""
        if self.interface:
            for link in links:
                if link.interface.lower() == self.interface.lower():
                    return link
            logger.warning("Configured Wi-Fi interface '%s' was not reported by Windows; using dynamic discovery.", self.interface)

        for link in links:
            if link.connected:
                return link
        for link in links:
            if link.interface:
                return link
        return LinkInfo(interface=self.interface or "", phy_mode=PhyMode.UNKNOWN)

    def get_interface_links(self) -> List[LinkInfo]:
        """Return all wireless interfaces reported by Windows without vendor assumptions."""
        cmd = ["netsh", "wlan", "show", "interfaces"]
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=flags,
            )
            return parse_netsh_interfaces(res.stdout.strip())
        except Exception as error:
            logger.error("Error running 'netsh wlan show interfaces': %s", error)
            return [
                LinkInfo(
                    connected=False,
                    interface=self.interface or "",
                    phy_mode=PhyMode.UNKNOWN,
                    radio_state=RadioState.UNKNOWN,
                    raw_output=f"Error executing command: {error}",
                )
            ]

    def _get_radio_state(self, adapter_description: str = "") -> RadioState:
        """Read Windows WLAN software/hardware radio state through the Native Wi-Fi API."""
        try:
            from wifi_ac_guardian_win.core.radio_control_win import WifiRadioControllerWin
            radio_is_on = WifiRadioControllerWin().is_radio_on(adapter_description)
            if radio_is_on is False:
                return RadioState.RADIO_OFF
        except Exception as error:
            logger.debug("Unable to query Windows Wi-Fi radio status: %s", error)
        return RadioState.UNKNOWN

    def _get_unreported_adapter_state(self) -> LinkInfo:
        """Classify an adapter Windows no longer exposes through the WLAN interface list.

        This query is only used when `netsh wlan show interfaces` does not return
        an interface. It allows the GUI to distinguish a user-disabled Wi-Fi
        adapter from Airplane Mode/radio-off without guessing vendor hardware.
        """
        radio_state = self._get_radio_state()
        script = (
            "$ErrorActionPreference = 'SilentlyContinue'; "
            "Get-NetAdapter -IncludeHidden | Where-Object { "
            "$_.NdisPhysicalMedium -eq 'Native 802.11' -or "
            "$_.MediaType -eq 'Native 802.11' -or "
            "$_.InterfaceDescription -match 'Wireless|Wi-Fi|WiFi|WLAN|802.11' "
            "} | Select-Object -First 1 Name, InterfaceDescription, Status | ConvertTo-Json -Compress"
        )
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=flags,
            )
            parsed = json.loads((result.stdout or "").strip() or "null")
        except Exception as error:
            logger.debug("Unable to classify an unreported Wi-Fi adapter: %s", error)
            parsed = None

        status = str((parsed or {}).get("Status") or "").strip().lower()
        if status == "disabled":
            # Disabled adapters are deliberately hidden from the GUI so a stale
            # device name cannot imply that Guardian can still control it.
            return LinkInfo(
                connected=False,
                signal_pct=0,
                phy_mode=PhyMode.DISCONNECTED,
                radio_state=RadioState.ADAPTER_DISABLED,
            )
        if radio_state == RadioState.RADIO_OFF:
            return LinkInfo(
                connected=False,
                interface=str((parsed or {}).get("Name") or ""),
                adapter=str((parsed or {}).get("InterfaceDescription") or "") or None,
                signal_pct=0,
                phy_mode=PhyMode.DISCONNECTED,
                radio_state=RadioState.RADIO_OFF,
            )
        return LinkInfo(
            connected=False,
            signal_pct=0,
            phy_mode=PhyMode.DISCONNECTED,
            radio_state=RadioState.NO_ADAPTER,
        )

    def _is_reported_adapter_disabled(self, interface: str) -> bool:
        """Check whether an interface still named by netsh has been disabled by the user/policy."""
        if not interface:
            return False
        quoted_interface = interface.replace("'", "''")
        script = (
            "$ErrorActionPreference = 'SilentlyContinue'; "
            f"(Get-NetAdapter -Name '{quoted_interface}' -ErrorAction SilentlyContinue).Status"
        )
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=flags,
            )
            return (result.stdout or "").strip().casefold() == "disabled"
        except Exception as error:
            logger.debug("Unable to read adapter state for '%s': %s", interface, error)
            return False

    @staticmethod
    def _apply_unavailable_radio_state(link: LinkInfo, state: RadioState) -> LinkInfo:
        """Clear live link values that are not valid once Windows radios are unavailable."""
        link.connected = False
        link.ssid = None
        link.bssid = None
        link.signal_pct = 0
        link.rx_bitrate = None
        link.tx_bitrate = None
        link.radio_type = ""
        link.phy_mode = PhyMode.DISCONNECTED
        link.radio_state = state
        if state in {RadioState.ADAPTER_DISABLED, RadioState.NO_ADAPTER}:
            link.interface = ""
            link.adapter = None
        return link

    def get_link_info(self) -> LinkInfo:
        """
        Executes 'netsh wlan show interfaces' and returns parsed LinkInfo object.
        """
        links = self.get_interface_links()
        if not any(link.interface for link in links):
            return self._get_unreported_adapter_state()

        selected = self._select_interface(links)
        radio_state = self._get_radio_state(selected.adapter or selected.interface)
        if radio_state == RadioState.RADIO_OFF:
            return self._apply_unavailable_radio_state(selected, RadioState.RADIO_OFF)

        if selected.connected:
            selected.radio_state = RadioState.ACTIVE
            return selected

        if self._is_reported_adapter_disabled(selected.interface):
            return self._apply_unavailable_radio_state(selected, RadioState.ADAPTER_DISABLED)

        # The Wi-Fi adapter still exists, but the user disconnected or Windows
        # has not associated yet. Preserve its identity while clearing metrics.
        return self._apply_unavailable_radio_state(selected, RadioState.DISCONNECTED)

    def get_saved_wifi_profiles(self) -> List[str]:
        """
        Executes 'netsh wlan show profiles' and returns a list of saved SSIDs (profiles) paired with the OS.
        """
        cmd = ["netsh", "wlan", "show", "profiles"]
        profiles = []
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
                if "All User Profile" in line and ":" in line:
                    parts = line.split(":", 1)
                    val = parts[1].strip()
                    if val and val not in profiles:
                        profiles.append(val)
        except Exception as e:
            logger.error(f"Error fetching saved profiles: {e}")
        return profiles

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

    def get_default_gateway(self, interface: Optional[str] = None) -> Optional[str]:
        """Return the IPv4 default gateway for the given interface, if Windows reports one."""
        quoted_interface = (interface or "").strip().replace("'", "''")
        if quoted_interface:
            script = (
                "$ErrorActionPreference = 'SilentlyContinue'; "
                f"(Get-NetIPConfiguration -InterfaceAlias '{quoted_interface}' -ErrorAction SilentlyContinue)"
                ".IPv4DefaultGateway.NextHop"
            )
        else:
            script = (
                "$ErrorActionPreference = 'SilentlyContinue'; "
                "Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | "
                "Select-Object -First 1 -ExpandProperty NextHop"
            )
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=flags,
            )
            output = (result.stdout or "").strip()
            gateway = output.splitlines()[0].strip() if output else ""
            return gateway or None
        except Exception as error:
            logger.debug("Unable to resolve default gateway for '%s': %s", interface or "Auto", error)
            return None

    def get_bssid_candidates(self, target_ssid: str) -> List[BssidCandidate]:
        """Return discovered BSSID candidates for the requested saved target SSID."""
        target = (target_ssid or "").strip()
        if not target:
            return []
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=flags,
            )
            return parse_netsh_bssid_candidates(result.stdout or "", target)
        except Exception as error:
            logger.warning("Unable to inventory target BSSID candidates: %s", error)
            return []
