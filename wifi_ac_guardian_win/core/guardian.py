"""
Main monitoring engine for WiFi AC Guardian Windows Edition.
"""

import time
import signal
import threading
from datetime import datetime
from typing import Optional
from wifi_ac_guardian_win.core.models import (
    GuardianConfig,
    GuardianState,
    StatusState,
    LinkInfo,
    PhyMode,
)
from wifi_ac_guardian_win.core.detector_win import WifiDetectorWin
from wifi_ac_guardian_win.core.reconnector_win import WifiReconnectorWin
from wifi_ac_guardian_win.core.notifier_win import WindowsNotifier
from wifi_ac_guardian_win.tray import SystemTrayAppWin
from wifi_ac_guardian_win.logger import get_logger, setup_logger

logger = get_logger()


class WifiACGuardianWin:
    """Core monitoring engine for Windows 11."""

    def __init__(self, config: Optional[GuardianConfig] = None):
        self.config = config or GuardianConfig()
        setup_logger(log_file_path=self.config.log_file_path)

        self.detector = WifiDetectorWin(interface=self.config.interface)
        self.reconnector = WifiReconnectorWin(config=self.config)
        self.notifier = WindowsNotifier(enabled=self.config.enable_notifications, sound_enabled=self.config.sound_alerts)
        self.state = GuardianState()

        self.stop_event = threading.Event()
        self._lock = threading.Lock()
        self._loop_thread: Optional[threading.Thread] = None
        # During boot, Windows may report a disconnected or incomplete link while
        # NetworkManager is still associating. Observe those states without
        # touching the adapter until a valid target-link reading is available.
        self._has_established_target_link = False
        self._consecutive_degraded_readings = 0

        try:
            from wifi_ac_guardian_win.ipc_server import start_ipc_server
            start_ipc_server(self)
        except Exception as e:
            logger.debug(f"IPC server init note: {e}")

        self.tray_app: Optional[SystemTrayAppWin] = None
        if self.config.enable_tray:
            self.tray_app = SystemTrayAppWin(
                on_reconnect_click=self.force_reconnect,
                on_stop_protection_click=self.stop_protection,
                on_quit_click=self.stop,
                config=self.config
            )

    def force_reconnect(self) -> None:
        logger.info("Manual reconnection requested on Windows.")
        threading.Thread(target=self._execute_reconnection_sequence, daemon=True).start()

    def start(self) -> None:
        logger.info("==================================================")
        logger.info("  WiFi AC Guardian (Windows 11 Edition) Starting  ")
        logger.info("==================================================")
        logger.info(f"Target Interface: {self.config.interface or 'Wi-Fi'}")
        logger.info(f"Check Interval:   {self.config.check_interval:.1f}s")
        logger.info(f"Reconnect Delay:  {self.config.reconnect_delay:.1f}s")
        logger.info(f"Max Attempts:     {self.config.max_attempts}")
        logger.info("==================================================")

        self.state.running = True

        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except (ValueError, TypeError):
            pass

        if self.tray_app:
            self.tray_app.start()

        self._run_loop()

    def start_background(self) -> threading.Thread:
        logger.info("Starting WiFi AC Guardian background monitoring thread...")
        self.state.running = True
        self.stop_event.clear()
        if self.tray_app:
            self.tray_app.start()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True, name="GuardianLoopThread")
        self._loop_thread.start()
        return self._loop_thread

    def stop(self) -> None:
        logger.info("Stopping WiFi AC Guardian service...")
        self.stop_protection()
        self.stop_event.set()

        if self.tray_app:
            self.tray_app.stop()

        logger.info("WiFi AC Guardian stopped cleanly.")

    def stop_protection(self) -> None:
        """Stop monitoring while keeping the tray service available."""
        logger.info("Stopping WiFi AC Guardian protection...")
        self.state.running = False
        self.config.is_paused = True
        self.state.status = StatusState.IDLE
        if self.tray_app:
            self.tray_app.set_protection_running(False)
            self.tray_app.update_status(StatusState.IDLE, self.state.current_link)

    def start_protection(self) -> threading.Thread:
        """Start monitoring again without rebuilding the guardian instance."""
        if self._loop_thread and self._loop_thread.is_alive():
            self.config.is_paused = False
            self.state.running = True
            return self._loop_thread
        logger.info("Starting WiFi AC Guardian protection...")
        self.config.is_paused = False
        self.state.running = True
        self.stop_event.clear()
        if self.tray_app:
            self.tray_app.set_protection_running(True)
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True, name="GuardianLoopThread")
        self._loop_thread.start()
        return self._loop_thread

    def _handle_signal(self, signum: int, frame: object) -> None:
        self.stop()

    def _run_loop(self) -> None:
        self.perform_check()

        while not self.stop_event.is_set():
            if self.stop_event.wait(timeout=self.config.check_interval):
                break

            self.perform_check()

    def _reset_degraded_confirmation(self) -> None:
        self._consecutive_degraded_readings = 0

    def _is_confirmable_degraded_link(self, link: LinkInfo) -> bool:
        """Return True only for a complete, actionable degraded target link.

        Unknown PHY/rate data is common while Windows is negotiating at boot and
        deliberately remains observation-only. A confirmed Wi-Fi 4-or-older PHY
        is actionable even when its rate is missing; Wi-Fi 5+ requires a real
        measured rate below the configured threshold.
        """
        if not link.connected or link.phy_mode in {PhyMode.UNKNOWN, PhyMode.DISCONNECTED}:
            return False
        if link.phy_mode not in {PhyMode.VHT, PhyMode.HE, PhyMode.EHT}:
            return True
        return 0 < link.max_bitrate_mbps < self.config.min_bitrate_threshold

    def _observe_degraded_target_link(self, link: LinkInfo) -> bool:
        """Count stable degraded readings and return True after two samples."""
        if not self._is_confirmable_degraded_link(link):
            self._reset_degraded_confirmation()
            self._set_status(StatusState.STANDBY, link)
            return False

        self._consecutive_degraded_readings += 1
        if self._consecutive_degraded_readings < 2:
            logger.warning(
                "Observed a valid degraded target link; waiting for a second "
                "consecutive reading before recovery (%s/2).",
                self._consecutive_degraded_readings,
            )
            self._set_status(StatusState.STANDBY, link)
            return False

        self._reset_degraded_confirmation()
        return True

    def perform_check(self) -> LinkInfo:
        with self._lock:
            self.state.last_check = datetime.now()
            try:
                link = self.detector.get_link_info()
            except Exception as e:
                logger.error(f"Error fetching link info: {e}")
                link = LinkInfo(connected=False, interface=self.config.interface or "Wi-Fi")
            self.state.current_link = link

            primary_target = (self.config.target_ssid or "lab5g").strip()

            if self.config.is_paused:
                logger.info("Reconnection protection is PAUSED by user.")
                self.state.primary_available = False
                self._set_status(StatusState.IDLE, link)
                return link

            # Case A: Disconnected
            if not link.connected:
                logger.info("Wi-Fi status: Disconnected.")
                self.state.primary_available = False
                self._reset_degraded_confirmation()
                if self._has_established_target_link and primary_target:
                    logger.info(
                        f"Previously healthy target '{primary_target}' disconnected. "
                        "Initiating normal outage recovery..."
                    )
                    self._execute_reconnection_sequence(target_ssid=primary_target)
                    return self.state.current_link

                logger.info("Boot/association observation mode: waiting for Windows to establish a valid Wi-Fi link.")
                self._set_status(StatusState.STANDBY, link)
                return link

            curr_ssid = (link.ssid or "").strip()
            logger.info(
                f"Wi-Fi status on {link.interface}: SSID='{curr_ssid}' | "
                f"Radio='{link.radio_type}' | PHY Mode={link.phy_summary} | "
                f"Bitrate={link.tx_bitrate or link.rx_bitrate or 'N/A'} | Signal={link.signal_pct}%"
            )

            is_primary = curr_ssid.lower() == primary_target.lower()

            # Case B: Connected to Primary Target Network (e.g. lab5g)
            if is_primary:
                self.state.primary_available = False
                if link.is_good(min_bitrate_threshold=self.config.min_bitrate_threshold):
                    logger.info(f"Primary Network '{primary_target}' is GOOD ({link.phy_summary}, Bitrate >= {self.config.min_bitrate_threshold}Mbps). Continuous protection active.")
                    self._has_established_target_link = True
                    self._reset_degraded_confirmation()
                    self.state.attempts_count = 0
                    self._set_status(StatusState.GOOD, link)
                    return link

                # Quality downgrade confirmation: never reset while PHY/rate
                # data is incomplete during association. Two valid degraded
                # readings are required before touching the adapter.
                if not self._observe_degraded_target_link(link):
                    return link

                logger.warning(
                    f"[ALERT] Primary Network '{primary_target}' downgraded to {link.phy_summary} (Bitrate={link.max_bitrate_mbps:.1f} Mbps < {self.config.min_bitrate_threshold}Mbps). "
                    "Confirmed on two consecutive readings; initiating Hardware Wi-Fi Adapter Radio Reset to restore Wi-Fi 5+..."
                )
                self._execute_reconnection_sequence(target_ssid=primary_target)
                return self.state.current_link

            # Case C: Connected to Backup / Secondary Network (e.g. Metalgear)
            else:
                self._reset_degraded_confirmation()
                logger.info(
                    f"Connected to Backup/Secondary Network '{curr_ssid}' (Primary: '{primary_target}'). "
                    "Protection in STANDBY mode to prevent unwanted radio resets on backup router."
                )

                # Scan in background to see if Primary Target SSID (lab5g) has come back online
                available_ssids = self.detector.get_available_ssids()
                primary_in_range = any(s.strip().lower() == primary_target.lower() for s in available_ssids if s)
                self.state.primary_available = primary_in_range

                if primary_in_range:
                    logger.info(f"⚡ Primary Network '{primary_target}' detected back online in range!")
                    if self.config.auto_switch_primary:
                        logger.info(f"Auto-Switch active: Returning to Primary Network '{primary_target}'...")
                        self.reconnector._connect_interface(link.interface or "Wi-Fi", primary_target)
                        time.sleep(3.0)
                        updated = self.detector.get_link_info()
                        self.state.current_link = updated
                        if updated.ssid and updated.ssid.lower() == primary_target.lower():
                            self._set_status(StatusState.GOOD if updated.is_good(min_bitrate_threshold=self.config.min_bitrate_threshold) else StatusState.RETRYING, updated)
                            return updated

                self._set_status(StatusState.STANDBY, link)
                return link

    def _execute_reconnection_sequence(self, target_ssid: Optional[str] = None) -> None:
        link = self.state.current_link or self.detector.get_link_info()
        interface = link.interface or self.config.interface or "Wi-Fi"
        ssid_to_connect = target_ssid or self.config.target_ssid or link.ssid

        self.state.attempts_count += 1
        current_attempt = self.state.attempts_count
        attempts_label = "Continuous" if self.config.max_attempts == 0 else f"{current_attempt}/{self.config.max_attempts}"

        logger.warning(
            f"Attempt {attempts_label}: "
            f"Toggling Wi-Fi Adapter Device Reset on Windows interface '{interface}' (Target SSID: '{ssid_to_connect or 'Auto'}')..."
        )

        self._set_status(StatusState.RETRYING, link)
        self.state.last_reconnect = datetime.now()

        updated_link = self.reconnector.trigger_reconnect(interface, ssid=ssid_to_connect)
        self.state.current_link = updated_link

        target = (self.config.target_ssid or "").strip()
        is_target_good = (not target or (updated_link.ssid and updated_link.ssid.lower() == target.lower())) and updated_link.is_good(min_bitrate_threshold=self.config.min_bitrate_threshold)

        if is_target_good:
            logger.info(f"Reconnection successful! Re-established {updated_link.phy_summary} on SSID '{updated_link.ssid}' (Bitrate: {updated_link.tx_bitrate or updated_link.rx_bitrate}).")
            self._has_established_target_link = True
            self._reset_degraded_confirmation()
            self.state.attempts_count = 0
            self._set_status(StatusState.GOOD, updated_link)
        else:
            if self.config.max_attempts > 0 and current_attempt >= self.config.max_attempts:
                self._set_status(StatusState.FAILED, updated_link)
            else:
                self._set_status(StatusState.RETRYING, updated_link)

    def _set_status(self, status: StatusState, link: Optional[LinkInfo] = None) -> None:
        self.state.status = status
        self.notifier.notify_status(
            status=status,
            link=link,
            attempts=self.state.attempts_count,
            max_attempts=self.config.max_attempts
        )
        if self.tray_app:
            self.tray_app.update_status(status, link)


