"""
Main monitoring engine for WiFi AC Guardian Windows Edition.
"""

import subprocess
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Optional
from wifi_ac_guardian_win.core.models import (
    GuardianConfig,
    GuardianState,
    StatusState,
    LinkInfo,
    PhyMode,
    RadioState,
)
from wifi_ac_guardian_win.core.detector_win import WifiDetectorWin
from wifi_ac_guardian_win.core.reconnector_win import WifiReconnectorWin
from wifi_ac_guardian_win.core.notifier_win import WindowsNotifier
from wifi_ac_guardian_win.config import save_config
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
        self._schedule_changed = threading.Event()
        self._lock = threading.Lock()
        self._loop_thread: Optional[threading.Thread] = None
        # During boot, Windows may report a disconnected or incomplete link while
        # NetworkManager is still associating. Observe those states without
        # touching the adapter until a valid target-link reading is available.
        self._has_established_target_link = False
        self._consecutive_degraded_readings = 0
        self._consecutive_good_readings = 0
        # Monotonic deadline for the VHT warm-up grace window (see
        # `_vht_warmup_grace_expired`); None while no fresh 802.11n
        # association is being observed.
        self._vht_grace_deadline: Optional[float] = None

        try:
            from wifi_ac_guardian_win.ipc_server import start_ipc_server
            start_ipc_server(self)
        except Exception as e:
            logger.debug(f"IPC server init note: {e}")

        self.tray_app = None
        if self.config.enable_tray:
            # Electron owns the production tray. Import the legacy Python tray
            # only when it is explicitly enabled so the packaged --no-tray
            # backend does not require tray/UI libraries at startup.
            from wifi_ac_guardian_win.tray import SystemTrayAppWin
            self.tray_app = SystemTrayAppWin(
                on_reconnect_click=self.force_reconnect,
                on_stop_protection_click=self.stop_protection,
                on_quit_click=self.stop,
                config=self.config
            )

    def force_reconnect(self) -> None:
        logger.info("Manual reconnection requested on Windows.")
        threading.Thread(target=self._execute_reconnection_sequence, daemon=True).start()

    @property
    def recovery_start_time(self) -> Optional[datetime]:
        """When the current/most recent recovery sequence began (owned by the reconnector)."""
        return self.reconnector.recovery_start_time

    @property
    def recovery_attempt_count(self) -> int:
        """How many attempts the current/most recent recovery sequence has taken."""
        return self.reconnector.recovery_attempt_count

    def start(self) -> None:
        logger.info("==================================================")
        logger.info("  WiFi AC Guardian (Windows 11 Edition) Starting  ")
        logger.info("==================================================")
        logger.info(f"Target Interface: {self.config.interface or 'Auto-detect active Wi-Fi adapter'}")
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
        self.state.next_check = None
        self._schedule_changed.set()
        self.state.status = StatusState.IDLE
        if self.tray_app:
            self.tray_app.set_protection_running(False)
            self.tray_app.update_status(StatusState.IDLE, self.state.current_link)

    def start_protection(self) -> threading.Thread:
        """Start monitoring again without rebuilding the guardian instance."""
        if self._loop_thread and self._loop_thread.is_alive():
            self.config.is_paused = False
            self.state.running = True
            self._schedule_changed.set()
            return self._loop_thread
        logger.info("Starting WiFi AC Guardian protection...")
        self.config.is_paused = False
        self.state.running = True
        self.stop_event.clear()
        self._schedule_changed.set()
        if self.tray_app:
            self.tray_app.set_protection_running(True)
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True, name="GuardianLoopThread")
        self._loop_thread.start()
        return self._loop_thread

    def _handle_signal(self, signum: int, frame: object) -> None:
        self.stop()

    def reschedule_checks(self) -> None:
        """Apply a saved monitoring interval immediately to the live scheduler."""
        if self.state.running and not self.config.is_paused:
            self.state.next_check = datetime.now() + timedelta(seconds=self.config.check_interval)
        else:
            self.state.next_check = None
        self._schedule_changed.set()

    def _run_loop(self) -> None:
        """Monitor on a reschedulable deadline so dashboard countdown matches settings."""
        while not self.stop_event.is_set():
            if self.config.is_paused or not self.state.running:
                self.state.next_check = None
                if self.stop_event.wait(timeout=0.25):
                    break
                continue

            self.perform_check()
            if self.config.is_paused or not self.state.running:
                self.state.next_check = None
                continue

            self.state.next_check = datetime.now() + timedelta(seconds=self.config.check_interval)
            self._schedule_changed.clear()
            while not self.stop_event.is_set():
                remaining = (self.state.next_check - datetime.now()).total_seconds() if self.state.next_check else 0
                if remaining <= 0:
                    break
                if self.stop_event.wait(timeout=min(0.25, remaining)):
                    break
                if self._schedule_changed.is_set():
                    self._schedule_changed.clear()
                    # Start the next monitoring cycle immediately, using the
                    # newly saved interval for the following displayed deadline.
                    break

    def _reset_degraded_confirmation(self) -> None:
        self._consecutive_degraded_readings = 0
        self._vht_grace_deadline = None

    def _reset_good_confirmation(self) -> None:
        self._consecutive_good_readings = 0

    def _probe_gateway_to_encourage_rate_step_up(self, interface: str) -> None:
        """Send a couple of lightweight ICMP pings to the default gateway.

        A fresh association often negotiates 802.11n first; a small burst of
        traffic gives the driver's rate-adaptation algorithm a reason to step
        the MCS up to VHT80 during the warm-up grace window instead of idling
        at the baseline rate.
        """
        gateway = self.detector.get_default_gateway(interface)
        if not gateway:
            logger.debug("[VHT-WARMUP] No default gateway reported for '%s'; skipping probe.", interface)
            return
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            subprocess.run(
                ["ping", "-n", "2", "-w", "1000", gateway],
                capture_output=True,
                timeout=10,
                creationflags=flags,
            )
            logger.info("[VHT-WARMUP] Sent 2 ICMP probes to gateway %s on '%s'.", gateway, interface)
        except (OSError, subprocess.SubprocessError) as error:
            logger.debug("[VHT-WARMUP] Gateway probe to %s failed: %s", gateway, error)

    def _vht_warmup_grace_expired(self) -> bool:
        """Observe a fresh 802.11n association without escalating until the grace period elapses.

        Router firmware and driver rate adaptation frequently need a few
        seconds after association to step a link up from 802.11n to
        802.11ac/ax/be. Returns False while still inside the grace window
        (the caller should keep observing rather than starting recovery), and
        True once the window has elapsed and the caller should proceed to the
        normal degraded-link handling.
        """
        now = time.monotonic()
        if self._vht_grace_deadline is None:
            grace_period = max(0.0, float(self.config.vht_grace_period))
            self._vht_grace_deadline = now + grace_period
            logger.info(
                "[VHT-WARMUP] Negotiated 802.11n; observing for up to %.1fs before considering recovery.",
                grace_period,
            )
            interface = (self.state.current_link.interface if self.state.current_link else "") or self.config.interface or ""
            if interface:
                self._probe_gateway_to_encourage_rate_step_up(interface)
            return False
        if now < self._vht_grace_deadline:
            return False
        logger.warning("[VHT-WARMUP] Grace window elapsed without an approved PHY; proceeding to recovery.")
        self._vht_grace_deadline = None
        return True

    def _observe_good_target_link(self, link: LinkInfo) -> bool:
        """Stop recovery immediately once the target regains an approved PHY.

        Link bitrate naturally fluctuates after association and is displayed as
        telemetry only. It must not restart the recovery engine while Windows
        continues to report Wi-Fi 5/6/7 on the target SSID.
        """
        if not link.has_approved_phy():
            self._reset_good_confirmation()
            return False
        self._consecutive_good_readings = 1
        return True

    def _remember_verified_bssid(self, link: LinkInfo) -> None:
        """Persist a BSSID preference only after an approved PHY is observed."""
        ssid = (link.ssid or self.config.target_ssid or "").strip()
        bssid = (link.bssid or "").strip()
        if not ssid or not bssid:
            return
        band = "6GHz" if (link.channel or 0) >= 181 else "5GHz" if (link.channel or 0) > 14 else "2.4GHz"
        preference = {
            "preferred_bssid": bssid,
            "preferred_band": band,
            "preferred_channel": link.channel,
            "last_verified_phy": link.radio_type or link.phy_mode.value,
            "last_verified_bitrate_mbps": link.max_bitrate_mbps,
        }
        key = ssid.casefold()
        if self.config.preferred_bssids.get(key) == preference:
            return
        self.config.preferred_bssids[key] = preference
        try:
            save_config(self.config, sync_startup_shortcut=False)
            logger.info("[RECOVERY] Preferred BSSID updated for SSID '%s': %s.", ssid, bssid)
        except Exception as error:
            logger.warning("Unable to persist verified BSSID preference: %s", error)

    def _is_confirmable_degraded_link(self, link: LinkInfo) -> bool:
        """Return True only when the target has lost its approved Wi-Fi PHY.

        Bitrate is intentionally excluded: 802.11ac/ax/be remains a successful
        association even when current TX/RX telemetry temporarily dips below the
        configured display threshold.
        """
        if not link.connected or link.phy_mode in {PhyMode.UNKNOWN, PhyMode.DISCONNECTED}:
            return False
        return not link.has_approved_phy()

    def _observe_degraded_target_link(self, link: LinkInfo) -> bool:
        """Act on the first confirmed loss of the approved target PHY.

        Unknown/disconnected negotiation telemetry remains observation-only, but
        once Windows explicitly reports a non-approved PHY on the target, the
        recovery engine starts immediately rather than waiting for a second poll.
        """
        if not self._is_confirmable_degraded_link(link):
            self._reset_degraded_confirmation()
            return False

        self._reset_good_confirmation()
        self._reset_degraded_confirmation()
        return True

    def perform_check(self) -> LinkInfo:
        with self._lock:
            self.state.last_check = datetime.now()
            try:
                link = self.detector.get_link_info()
            except Exception as e:
                logger.error(f"Error fetching link info: {e}")
                link = LinkInfo(connected=False, interface=self.config.interface or "")
            self.state.current_link = link

            primary_target = (self.config.target_ssid or "").strip()

            if self.config.is_paused:
                logger.info("Reconnection protection is PAUSED by user.")
                self.state.primary_available = False
                self._set_status(StatusState.IDLE, link)
                return link

            # Case A: Disconnected
            if not link.connected:
                logger.info("Wi-Fi status: %s.", link.radio_state.value)
                self.state.primary_available = False
                self._reset_degraded_confirmation()
                self._reset_good_confirmation()
                if link.radio_state in {RadioState.RADIO_OFF, RadioState.ADAPTER_DISABLED, RadioState.NO_ADAPTER}:
                    logger.info(
                        "User-controlled Wi-Fi availability state '%s' detected; Guardian will observe and will not override it.",
                        link.radio_state.value,
                    )
                    self._set_status(StatusState.STANDBY, link)
                    return link
                if self._has_established_target_link and primary_target:
                    logger.info(
                        f"Previously healthy target '{primary_target}' disconnected. "
                        "Initiating configured radio recovery..."
                    )
                    self._execute_reconnection_sequence(target_ssid=primary_target)
                    return self.state.current_link

                logger.info("Boot/association observation mode: waiting for Windows to establish a valid Wi-Fi link.")
                self._set_status(StatusState.STANDBY, link)
                return link

            curr_ssid = (link.ssid or "").strip()
            if not primary_target and curr_ssid:
                # On a new commercial installation, use the first real active
                # connection as the session target instead of shipping a named
                # customer network in the application defaults.
                primary_target = curr_ssid
                self.config.target_ssid = curr_ssid
                logger.info("No target SSID is configured; dynamically protecting active network '%s'.", primary_target)
            logger.info(
                f"Wi-Fi status on {link.interface}: SSID='{curr_ssid}' | "
                f"Radio='{link.radio_type}' | PHY Mode={link.phy_summary} | "
                f"Bitrate={link.tx_bitrate or link.rx_bitrate or 'N/A'} | Signal={link.signal_pct}%"
            )

            is_primary = curr_ssid.lower() == primary_target.lower()

            # Case B: Connected to Primary Target Network (e.g. lab5g)
            if is_primary:
                self.state.primary_available = False
                if link.has_approved_phy():
                    self._reset_degraded_confirmation()
                    if self._observe_good_target_link(link):
                        logger.info(f"Primary Network '{primary_target}' is VERIFIED GOOD ({link.phy_summary}); transient bitrate telemetry will not restart recovery.")
                        self._has_established_target_link = True
                        self.state.attempts_count = 0
                        self._remember_verified_bssid(link)
                        self._set_status(StatusState.GOOD, link)
                    return link

                # VHT warm-up grace window: a fresh association commonly
                # negotiates 802.11n first, so give the driver time to step
                # up to an approved PHY before flagging PHY_STUCK_HT.
                if link.connected and link.phy_mode == PhyMode.HT and not self._vht_warmup_grace_expired():
                    self._set_status(StatusState.RETRYING, link)
                    return link

                # Quality downgrade confirmation: never reset while PHY/rate
                # data is incomplete during association. Two valid degraded
                # readings are required before touching the adapter.
                if not self._observe_degraded_target_link(link):
                    return link

                logger.warning(
                    f"[ALERT] Primary Network '{primary_target}' lost its approved PHY and is now {link.phy_summary}. "
                    "Initiating configured Wi-Fi recovery immediately..."
                )
                self._execute_reconnection_sequence(target_ssid=primary_target)
                return self.state.current_link

            # Case C: Connected to Backup / Secondary Network (e.g. Metalgear)
            else:
                self._reset_degraded_confirmation()
                self._reset_good_confirmation()
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
                        if not link.interface:
                            logger.warning("Windows did not report a Wi-Fi interface; skipping automatic primary-network switch.")
                            self._set_status(StatusState.STANDBY, link)
                            return link
                        self.reconnector._connect_interface(link.interface, primary_target)
                        time.sleep(3.0)
                        updated = self.detector.get_link_info()
                        self.state.current_link = updated
                        if updated.ssid and updated.ssid.lower() == primary_target.lower():
                            if updated.has_approved_phy() and self._observe_good_target_link(updated):
                                self._set_status(StatusState.GOOD, updated)
                            else:
                                self._set_status(StatusState.RETRYING, updated)
                            return updated

                self._set_status(StatusState.STANDBY, link)
                return link

    def _execute_reconnection_sequence(self, target_ssid: Optional[str] = None) -> None:
        link = self.state.current_link or self.detector.get_link_info()
        interface = (link.interface or self.config.interface or "").strip()
        if not interface:
            logger.error("Recovery skipped because Windows did not report a Wi-Fi adapter interface.")
            self._set_status(StatusState.FAILED, link)
            return
        ssid_to_connect = target_ssid or self.config.target_ssid or link.ssid

        if self.config.max_attempts > 0 and self.state.attempts_count >= self.config.max_attempts:
            logger.error(
                "Recovery attempt limit reached (%s/%s); recovery is stopping until a healthy link is observed or the user changes settings.",
                self.state.attempts_count,
                self.config.max_attempts,
            )
            self._set_status(StatusState.FAILED, link)
            return

        if self.state.attempts_count == 0:
            # First attempt of a fresh degraded-link sequence: clear the
            # reconnector's recovery-sequence telemetry so a stale start
            # time/attempt count from a previous, already-resolved sequence
            # doesn't leak into the new one.
            self.reconnector.reset_recovery_tracking()

        self.state.attempts_count += 1
        current_attempt = self.state.attempts_count
        attempts_label = f"{current_attempt}/∞" if self.config.max_attempts == 0 else f"{current_attempt}/{self.config.max_attempts}"

        logger.warning(
            f"Attempt {attempts_label}: "
            f"Starting Windows Wi-Fi recovery on interface '{interface}' (Target SSID: '{ssid_to_connect or 'Auto'}')..."
        )

        self._set_status(StatusState.RETRYING, link)
        self.state.last_reconnect = datetime.now()
        self.state.recovery_active = True
        self.state.recovery_status = "Connecting"
        self.state.next_check = None

        try:
            updated_link = self.reconnector.trigger_reconnect(interface, ssid=ssid_to_connect)
            self.state.current_link = updated_link

            target = (self.config.target_ssid or "").strip()
            is_target_good = (not target or (updated_link.ssid and updated_link.ssid.lower() == target.lower())) and updated_link.has_approved_phy()

            if is_target_good:
                self._reset_degraded_confirmation()
                if self._observe_good_target_link(updated_link):
                    logger.info(f"Reconnection verified! Re-established {updated_link.phy_summary} on SSID '{updated_link.ssid}'; recovery is stopping regardless of transient bitrate.")
                    self._has_established_target_link = True
                    self.state.attempts_count = 0
                    self._remember_verified_bssid(updated_link)
                    self._set_status(StatusState.GOOD, updated_link)
                else:
                    self._set_status(StatusState.GOOD, updated_link)
            else:
                self._reset_good_confirmation()
                logger.warning(
                    "Recovery attempt %s did not verify the policy target: SSID='%s', BSSID='%s', PHY=%s, TX=%s, RX=%s. "
                    "The next policy check remains scheduled using the configured %.1fs interval.",
                    attempts_label,
                    updated_link.ssid or "N/A",
                    updated_link.bssid or "N/A",
                    updated_link.phy_summary,
                    updated_link.tx_bitrate or "N/A",
                    updated_link.rx_bitrate or "N/A",
                    self.config.check_interval,
                )
                if self.config.max_attempts > 0 and current_attempt >= self.config.max_attempts:
                    self._set_status(StatusState.FAILED, updated_link)
                else:
                    self._set_status(StatusState.RETRYING, updated_link)
        finally:
            self.state.recovery_active = False
            self.state.recovery_status = ""

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


