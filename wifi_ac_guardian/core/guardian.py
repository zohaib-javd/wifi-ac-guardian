"""
Main monitoring engine for WiFi AC Guardian.
Executes periodic PHY mode checks every 10 seconds, evaluates connection quality,
triggers NetworkManager reconnections when downgraded to Wi-Fi 4, updates tray icon
and desktop notifications, and handles graceful shutdown signals.
"""

import time
import signal
import threading
from datetime import datetime
from typing import Optional, Callable
from wifi_ac_guardian.core.models import (
    GuardianConfig,
    GuardianState,
    StatusState,
    PhyMode,
    LinkInfo,
)
from wifi_ac_guardian.core.detector import WifiDetector
from wifi_ac_guardian.core.reconnector import WifiReconnector
from wifi_ac_guardian.core.notifier import DesktopNotifier
from wifi_ac_guardian.tray import SystemTrayApp
from wifi_ac_guardian.logger import get_logger, setup_logger

logger = get_logger()


class WifiACGuardian:
    """
    Core orchestrator that continuously monitors Wi-Fi physical mode
    and enforces Wi-Fi 5 (802.11ac) or higher negotiation.
    """

    def __init__(self, config: Optional[GuardianConfig] = None):
        self.config = config or GuardianConfig()
        setup_logger(log_file_path=self.config.log_file_path)

        self.detector = WifiDetector(interface=self.config.interface)
        self.reconnector = WifiReconnector(config=self.config)
        self.notifier = DesktopNotifier(enabled=self.config.enable_notifications)
        self.state = GuardianState()

        self.stop_event = threading.Event()
        self._lock = threading.Lock()

        # System tray applet
        self.tray_app: Optional[SystemTrayApp] = None
        if self.config.enable_tray:
            self.tray_app = SystemTrayApp(
                on_reconnect_click=self.force_reconnect,
                on_quit_click=self.stop
            )

    def force_reconnect(self) -> None:
        """Manually triggers immediate Wi-Fi reconnection routine."""
        logger.info("Manual reconnection requested.")
        threading.Thread(target=self._execute_reconnection_sequence, daemon=True).start()

    def start(self, run_tray_in_main_thread: bool = False) -> None:
        """
        Starts the Guardian monitoring daemon.

        Args:
            run_tray_in_main_thread: If True, tray runs blocking in main thread while loop runs in background.
        """
        logger.info("==================================================")
        logger.info("       WiFi AC Guardian Daemon Starting           ")
        logger.info("==================================================")
        logger.info(f"Target Interface: {self.config.interface or 'Auto-Detect'}")
        logger.info(f"Check Interval:   {self.config.check_interval:.1f}s")
        logger.info(f"Reconnect Delay:  {self.config.reconnect_delay:.1f}s")
        logger.info(f"Max Attempts:     {self.config.max_attempts}")
        logger.info(f"Log File Path:    {self.config.log_file_path}")
        logger.info("==================================================")

        self.state.running = True

        # Register OS signal handlers for graceful shutdown (SIGINT, SIGTERM)
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except (ValueError, TypeError):
            # Signal handling might fail if called outside main thread in testing
            pass

        # Start tray app if enabled
        if self.tray_app:
            self.tray_app.start()

        # Main monitoring loop
        self._run_loop()

    def stop(self) -> None:
        """Stops the monitoring engine and cleans up resources."""
        logger.info("Stopping WiFi AC Guardian service...")
        self.state.running = False
        self.stop_event.set()

        if self.tray_app:
            self.tray_app.stop()

        logger.info("WiFi AC Guardian stopped cleanly.")

    def _handle_signal(self, signum: int, frame: object) -> None:
        """Signal handler for SIGINT and SIGTERM."""
        sig_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.info(f"Received signal {sig_name}. Initiating graceful shutdown...")
        self.stop()

    def _run_loop(self) -> None:
        """Main loop executing every check_interval seconds."""
        # Initial link check
        self.perform_check()

        while not self.stop_event.is_set():
            # Wait check_interval seconds (responsive to stop_event)
            if self.stop_event.wait(timeout=self.config.check_interval):
                break

            self.perform_check()

    def perform_check(self) -> LinkInfo:
        """
        Performs a single evaluation cycle:
        1. Queries 'iw dev <interface> link'.
        2. Evaluates PHY mode (VHT / HE / EHT vs HT / Legacy / Disconnected).
        3. Takes corrective reconnection action if connection downgraded.
        4. Updates status, tray icon, and notifications.

        Returns:
            Current parsed LinkInfo instance.
        """
        with self._lock:
            self.state.last_check = datetime.now()
            link = self.detector.get_link_info()
            self.state.current_link = link

            if not link.connected:
                logger.info("Wi-Fi state: Disconnected.")
                self._set_status(StatusState.DISCONNECTED, link)
                return link

            logger.info(
                f"Wi-Fi state on {link.interface}: SSID='{link.ssid}' | "
                f"Freq={link.freq_mhz}MHz (Ch {link.channel}) | "
                f"PHY Mode={link.phy_summary} | TX Bitrate='{link.tx_bitrate}'"
            )

            # Check if PHY mode is GOOD (Wi-Fi 5 VHT, Wi-Fi 6 HE, or Wi-Fi 7 EHT)
            if link.is_good:
                logger.info(f"Connection quality is GOOD ({link.phy_summary}). Resetting retry counter.")
                self.state.attempts_count = 0
                self._set_status(StatusState.GOOD, link)
                return link

            # Check if monitoring/reconnection is paused by user
            if self.config.is_paused:
                logger.info("Automatic reconnection protection is currently PAUSED by user.")
                self._set_status(StatusState.IDLE, link)
                return link

            # Connection is NOT GOOD (e.g. Wi-Fi 4 / HT / 802.11n or Legacy)
            logger.warning(
                f"[WARNING] Wi-Fi connection downgraded to lower PHY mode: {link.phy_summary} "
                f"(TX: {link.tx_bitrate}). Wi-Fi 5 (802.11ac) or higher is required."
            )

            if self.state.attempts_count >= self.config.max_attempts:
                logger.error(
                    f"Reached maximum reconnection attempts ({self.config.max_attempts}). "
                    "Stopping automatic reconnection retries for this cycle."
                )
                self._set_status(StatusState.FAILED, link)
                return link

            # Connection is lower than Wi-Fi 5 and attempts < max_attempts -> trigger reconnect
            self._execute_reconnection_sequence()
            return self.state.current_link

    def _execute_reconnection_sequence(self) -> None:
        """Executes full disconnect/reconnect attempt cycle."""
        link = self.state.current_link or self.detector.get_link_info()
        interface = link.interface or self.detector.get_interface()
        ssid = link.ssid

        self.state.attempts_count += 1
        current_attempt = self.state.attempts_count

        logger.warning(
            f"Attempt {current_attempt}/{self.config.max_attempts}: "
            f"Disconnecting and reconnecting Wi-Fi on interface {interface}..."
        )

        # Notify Yellow (Retrying)
        self._set_status(StatusState.RETRYING, link)

        # Perform reconnection sequence
        self.state.last_reconnect = datetime.now()
        updated_link = self.reconnector.trigger_reconnect(interface, ssid=ssid)
        self.state.current_link = updated_link

        # Re-evaluate PHY mode after reconnection
        if updated_link.is_good:
            logger.info(
                f"Reconnection successful! Successfully established {updated_link.phy_summary} connection "
                f"on attempt {current_attempt}."
            )
            self.state.attempts_count = 0
            self._set_status(StatusState.GOOD, updated_link)
        else:
            if current_attempt >= self.config.max_attempts:
                logger.error(
                    f"Unable to obtain Wi-Fi 5 (802.11ac) after {self.config.max_attempts} attempts."
                )
                self._set_status(StatusState.FAILED, updated_link)
            else:
                logger.warning(
                    f"Attempt {current_attempt} resulted in {updated_link.phy_summary}. Will retry on next check."
                )
                self._set_status(StatusState.RETRYING, updated_link)

    def _set_status(self, status: StatusState, link: Optional[LinkInfo] = None) -> None:
        """Updates internal status, notifies desktop, and updates tray icon."""
        self.state.status = status

        # Update Desktop Notification
        self.notifier.notify_status(
            status=status,
            link=link,
            attempts=self.state.attempts_count,
            max_attempts=self.config.max_attempts
        )

        # Update System Tray Icon & Tooltip
        if self.tray_app:
            self.tray_app.update_status(status, link)
