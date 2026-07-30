"""
Command Line Interface (CLI) for WiFi AC Guardian.
Supports 'wifi-ac-guardian --status', '--daemon', '--reconnect', and configuration options.
"""

import sys
import argparse
from typing import List, Optional
from wifi_ac_guardian import __version__
from wifi_ac_guardian.core.models import GuardianConfig, StatusState
from wifi_ac_guardian.core.detector import WifiDetector
from wifi_ac_guardian.core.reconnector import WifiReconnector
from wifi_ac_guardian.core.guardian import WifiACGuardian
from wifi_ac_guardian.config import load_config
from wifi_ac_guardian.logger import setup_logger, get_logger

logger = get_logger()


def print_status_report(interface_override: Optional[str] = None) -> None:
    """
    Queries current Wi-Fi link parameters and prints status summary to stdout.
    Satisfies Requirement 9:
    Current SSID
    Frequency
    Channel
    Signal
    PHY Mode
    Bitrate
    Attempts
    Status
    """
    detector = WifiDetector(interface=interface_override)
    link = detector.get_link_info()

    if not link.connected:
        print("==================================================")
        print("                 WiFi AC Guardian                 ")
        print("==================================================")
        print(f"Interface:    {link.interface or 'Unknown'}")
        print("Current SSID: Disconnected")
        print("Frequency:    N/A")
        print("Channel:      N/A")
        print("Signal:       N/A")
        print("PHY Mode:     Disconnected")
        print("Bitrate:      N/A")
        print("Attempts:     0")
        print("Status:       DISCONNECTED")
        print("==================================================")
        return

    ssid_str = link.ssid or "Unknown"
    freq_str = f"{int(link.freq_mhz)} MHz" if link.freq_mhz else "N/A"
    chan_str = str(link.channel) if link.channel is not None else "N/A"
    sig_str = f"{link.signal_dbm} dBm" if link.signal_dbm is not None else "N/A"
    phy_str = link.phy_summary
    bitrate_str = link.tx_bitrate or link.rx_bitrate or "N/A"
    attempts_str = "0"
    status_str = "GOOD (Wi-Fi 5+)" if link.is_good else f"POOR ({phy_str})"

    print("==================================================")
    print("                 WiFi AC Guardian                 ")
    print("==================================================")
    print(f"Interface:    {link.interface}")
    print(f"Current SSID: {ssid_str}")
    print(f"Frequency:    {freq_str}")
    print(f"Channel:      {chan_str}")
    print(f"Signal:       {sig_str}")
    print(f"PHY Mode:     {phy_str}")
    print(f"Bitrate:      {bitrate_str}")
    print(f"Attempts:     {attempts_str}")
    print(f"Status:       {status_str}")
    print("==================================================")


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for CLI.

    Args:
        args: Command line arguments list (defaults to sys.argv[1:]).

    Returns:
        Exit status code (0 for success).
    """
    parser = argparse.ArgumentParser(
        prog="wifi-ac-guardian",
        description="Continuously ensures Wi-Fi is negotiated using Wi-Fi 5 (802.11ac) or higher."
    )

    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        help="Launch the GTK graphical user interface (Control Panel & Timing Selectors)."
    )

    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="Outputs current SSID, Frequency, Channel, Signal, PHY Mode, Bitrate, Attempts, and Status."
    )

    parser.add_argument(
        "-d", "--daemon",
        action="store_true",
        help="Run continuously in background monitoring mode."
    )

    parser.add_argument(
        "-r", "--reconnect",
        action="store_true",
        help="Force immediate disconnection and reconnection attempt via NetworkManager."
    )

    parser.add_argument(
        "-i", "--interface",
        type=str,
        default=None,
        help="Override auto-detected wireless interface (e.g. wlp3s0, wlan0)."
    )

    parser.add_argument(
        "-t", "--interval",
        type=float,
        default=10.0,
        help="Polling interval in seconds (default: 10)."
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=10,
        help="Maximum reconnection retry attempts before stopping (default: 10)."
    )

    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Disable system tray icon applet."
    )

    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Disable desktop popups."
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parsed = parser.parse_args(args)

    setup_logger()

    if parsed.gui:
        from wifi_ac_guardian.ui import launch_gui
        config = load_config()
        if parsed.interface:
            config.interface = parsed.interface
        launch_gui(config=config)
        return 0

    # Default action if no flag is specified: if running in terminal (isatty), print status; if non-TTY (desktop icon click), open GUI.
    if parsed.status:
        print_status_report(interface_override=parsed.interface)
        return 0

    if not parsed.daemon and not parsed.reconnect and not parsed.gui and not parsed.status:
        if sys.stdout and sys.stdout.isatty():
            print_status_report(interface_override=parsed.interface)
        else:
            from wifi_ac_guardian.ui import launch_gui
            config = load_config()
            if parsed.interface:
                config.interface = parsed.interface
            launch_gui(config=config)
        return 0

    if parsed.reconnect:
        print("Initiating immediate Wi-Fi reconnection...")
        config = load_config()
        if parsed.interface:
            config.interface = parsed.interface
        reconnector = WifiReconnector(config=config)
        detector = WifiDetector(interface=config.interface)
        iface = detector.get_interface()
        link = detector.get_link_info()
        res_link = reconnector.trigger_reconnect(iface, ssid=link.ssid)
        print(f"Reconnection completed. Updated PHY Mode: {res_link.phy_summary}")
        return 0

    if parsed.daemon:
        config = load_config()
        if parsed.interface:
            config.interface = parsed.interface
        config.check_interval = parsed.interval
        config.max_attempts = parsed.max_attempts
        if parsed.no_tray:
            config.enable_tray = False
        if parsed.no_notify:
            config.enable_notifications = False

        guardian = WifiACGuardian(config=config)
        guardian.start()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
