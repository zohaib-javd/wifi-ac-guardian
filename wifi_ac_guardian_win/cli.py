"""
Command Line Interface (CLI) for WiFi AC Guardian Windows Edition.
"""

import sys
import argparse
from typing import List, Optional
from wifi_ac_guardian_win import __version__
from wifi_ac_guardian_win.core.detector_win import WifiDetectorWin
from wifi_ac_guardian_win.core.reconnector_win import WifiReconnectorWin
from wifi_ac_guardian_win.core.guardian import WifiACGuardianWin
from wifi_ac_guardian_win.config import load_config
from wifi_ac_guardian_win.logger import setup_logger


def print_status_report(interface_override: Optional[str] = None) -> None:
    detector = WifiDetectorWin(interface=interface_override)
    link = detector.get_link_info()

    if not link.connected:
        print("==================================================")
        print("    WiFi AC Guardian (Windows 11 Edition)        ")
        print("==================================================")
        print(f"Interface:    {link.interface or 'Wi-Fi'}")
        print("Current SSID: Disconnected")
        print("Frequency:    N/A")
        print("Channel:      N/A")
        print("Signal:       N/A")
        print("PHY Mode:     Disconnected")
        print("Link Speed:   N/A")
        print("Attempts:     0")
        print("Status:       DISCONNECTED")
        print("==================================================")
        return

    ssid_str = link.ssid or "Unknown"
    freq_str = f"{int(link.freq_mhz)} MHz" if link.freq_mhz else "N/A"
    chan_str = str(link.channel) if link.channel is not None else "N/A"
    sig_str = f"{link.signal_pct}%" if link.signal_pct is not None else "N/A"
    phy_str = link.phy_summary
    bitrate_str = link.tx_bitrate or "N/A"
    status_str = "GOOD (Wi-Fi 5+)" if link.is_good else f"POOR ({phy_str})"

    print("==================================================")
    print("    WiFi AC Guardian (Windows 11 Edition)        ")
    print("==================================================")
    print(f"Interface:    {link.interface}")
    print(f"Current SSID: {ssid_str}")
    print(f"Radio Type:   {link.radio_type}")
    print(f"Frequency:    {freq_str}")
    print(f"Channel:      {chan_str}")
    print(f"Signal:       {sig_str}")
    print(f"PHY Mode:     {phy_str}")
    print(f"Link Speed:   {bitrate_str}")
    print(f"Attempts:     0")
    print(f"Status:       {status_str}")
    print("==================================================")


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wifi-ac-guardian-win",
        description="Continuously ensures Wi-Fi 5 (802.11ac) or higher negotiation on Windows 11."
    )

    parser.add_argument("-g", "--gui", action="store_true", help="Launch Tkinter Control Panel GUI.")
    parser.add_argument("-s", "--status", action="store_true", help="Display current status report.")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run background monitoring daemon.")
    parser.add_argument("-r", "--reconnect", action="store_true", help="Force immediate reconnection attempt.")
    parser.add_argument("-i", "--interface", type=str, default="Wi-Fi", help="Target wireless interface name.")
    parser.add_argument("--target-ssid", type=str, default="", help="Target SSID to lock onto.")
    parser.add_argument("-t", "--interval", type=float, default=15.0, help="Poll interval in seconds.")
    parser.add_argument("--max-attempts", type=int, default=0, help="Max reconnection retries (0 = Unlimited).")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    parsed = parser.parse_args(args)

    setup_logger()

    if parsed.gui:
        from wifi_ac_guardian_win.ui import launch_gui_win
        config = load_config()
        if parsed.interface:
            config.interface = parsed.interface
        if parsed.target_ssid:
            config.target_ssid = parsed.target_ssid
        launch_gui_win(config=config)
        return 0

    if parsed.status:
        print_status_report(interface_override=parsed.interface)
        return 0

    if not parsed.daemon and not parsed.reconnect and not parsed.gui and not parsed.status:
        if sys.stdout and sys.stdout.isatty():
            print_status_report(interface_override=parsed.interface)
        else:
            from wifi_ac_guardian_win.ui import launch_gui_win
            config = load_config()
            if parsed.interface:
                config.interface = parsed.interface
            if parsed.target_ssid:
                config.target_ssid = parsed.target_ssid
            launch_gui_win(config=config)
        return 0

    if parsed.reconnect:
        print("Initiating immediate Windows Wi-Fi reconnection...")
        config = load_config()
        if parsed.interface:
            config.interface = parsed.interface
        if parsed.target_ssid:
            config.target_ssid = parsed.target_ssid
        reconnector = WifiReconnectorWin(config=config)
        detector = WifiDetectorWin(interface=config.interface)
        link = detector.get_link_info()
        res_link = reconnector.trigger_reconnect(link.interface, ssid=config.target_ssid or link.ssid)
        print(f"Reconnection completed. Updated PHY Mode: {res_link.phy_summary}")
        return 0

    if parsed.daemon:
        from wifi_ac_guardian_win.single_instance import SingleInstanceChecker
        checker = SingleInstanceChecker()
        if not checker.try_claim_single_instance():
            print("WiFi AC Guardian is already running in the background.")
            return 0

        config = load_config()
        if parsed.interface:
            config.interface = parsed.interface
        if parsed.target_ssid:
            config.target_ssid = parsed.target_ssid
        config.check_interval = parsed.interval
        config.max_attempts = parsed.max_attempts

        guardian = WifiACGuardianWin(config=config)
        guardian.start()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
