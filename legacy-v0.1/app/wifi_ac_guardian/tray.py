"""
System tray interface for WiFi AC Guardian.
Displays status icon (Green, Yellow, Red) and context menu using pystray or GTK.
Provides quick actions to Pause/Resume, Toggle Notifications, and Stop/Quit Service.
"""

import os
import subprocess
import threading
from typing import Optional, Callable
from wifi_ac_guardian.core.models import StatusState, LinkInfo, GuardianConfig
from wifi_ac_guardian.icons import create_pillow_icon_for_state
from wifi_ac_guardian.config import load_config, save_config
from wifi_ac_guardian.logger import get_logger

logger = get_logger()

# Try importing pystray using appindicator, gtk, or xorg backend
PYSTRAY_AVAILABLE = False
try:
    if "PYSTRAY_BACKEND" not in os.environ:
        for backend in ["appindicator", "gtk", "xorg"]:
            try:
                os.environ["PYSTRAY_BACKEND"] = backend
                import pystray
                from pystray import MenuItem as item, Menu
                PYSTRAY_AVAILABLE = True
                break
            except Exception:
                continue
    else:
        import pystray
        from pystray import MenuItem as item, Menu
        PYSTRAY_AVAILABLE = True
except (ImportError, ValueError, Exception) as err:
    logger.debug(f"pystray module backend initialization warning: {err}. Tray applet will run in headless mode.")
    PYSTRAY_AVAILABLE = False


class SystemTrayApp:
    """Manages system tray icon and interactive menu."""

    def __init__(
        self,
        on_reconnect_click: Optional[Callable[[], None]] = None,
        on_quit_click: Optional[Callable[[], None]] = None,
        config: Optional[GuardianConfig] = None
    ):
        self.on_reconnect_click = on_reconnect_click
        self.on_quit_click = on_quit_click
        self.config = config or load_config()
        self.current_state = StatusState.IDLE
        self.current_link: Optional[LinkInfo] = None
        self.icon_instance: Optional[object] = None
        self._thread: Optional[threading.Thread] = None
        self._quitting = False

    def is_display_available(self) -> bool:
        """Checks if an X11 or Wayland display server environment is active."""
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    def start(self) -> None:
        """Starts system tray loop in a daemon thread if display is available."""
        if not PYSTRAY_AVAILABLE:
            logger.info("pystray module not installed. Running in headless mode (no tray icon).")
            return

        if not self.is_display_available():
            logger.info("No DISPLAY or WAYLAND_DISPLAY environment found. Running tray in headless mode.")
            return

        self._thread = threading.Thread(target=self._run_tray, daemon=True, name="SystemTrayThread")
        self._thread.start()
        logger.info("System tray applet started.")

    def _run_tray(self) -> None:
        """Internal worker function to construct menu and start pystray loop."""
        try:
            initial_image = create_pillow_icon_for_state(self.current_state)
            menu = Menu(
                item(self._get_status_text, None, enabled=False),
                item(self._get_phy_text, None, enabled=False),
                Menu.SEPARATOR,
                item("▶️ Start Protection / Reconnecting Retries", self._handle_start_protection),
                item("⏸️ Pause Protection", self._handle_toggle_pause),
                item("🔄 Reconnect Once Now", self._handle_reconnect),
                item("⚙️ Open Control Panel UI", self._handle_open_ui),
                Menu.SEPARATOR,
                item("❌ Quit App", self._handle_quit),
                item("🛑 Exit", self._handle_quit),
            )

            self.icon_instance = pystray.Icon(
                "wifi_ac_guardian",
                initial_image,
                "WiFi AC Guardian",
                menu
            )
            self.icon_instance.run()
            # If icon.run() terminates (e.g. Exit option in fallback backend), perform complete app shutdown
            if not self._quitting:
                self._handle_quit()
        except Exception as e:
            logger.error(f"Error running system tray icon: {e}")

    def _get_status_text(self, item_obj=None) -> str:
        state_str = self.current_state.value
        if self.config.is_paused:
            return "Status: PAUSED"
        if self.current_link and self.current_link.ssid:
            return f"Status: {state_str} ({self.current_link.ssid})"
        return f"Status: {state_str}"

    def _get_phy_text(self, item_obj=None) -> str:
        if self.current_link and self.current_link.connected:
            return f"Mode: {self.current_link.phy_summary}"
        return "Mode: Disconnected"

    def _get_pause_text(self, item_obj=None) -> str:
        return "▶️ Resume Protection" if self.config.is_paused else "⏸️ Pause Protection"

    def _get_notify_text(self, item_obj=None) -> str:
        return "🔕 Notifications: OFF" if not self.config.enable_notifications else "🔔 Notifications: ON"

    def _handle_start_protection(self, icon=None, item_obj=None) -> None:
        self.config.is_paused = False
        save_config(self.config)
        logger.info("Tray menu: 'Start Protection / Reconnecting Retries' clicked.")
        if self.on_reconnect_click:
            self.on_reconnect_click()
        if self.icon_instance:
            self.icon_instance.update_menu()

    def _handle_reconnect(self, icon=None, item_obj=None) -> None:
        logger.info("Tray menu: 'Reconnect Now' clicked.")
        if self.on_reconnect_click:
            self.on_reconnect_click()

    def _handle_toggle_pause(self, icon=None, item_obj=None) -> None:
        self.config.is_paused = not self.config.is_paused
        save_config(self.config)
        logger.info(f"Tray menu: Protection paused set to {self.config.is_paused}")
        if self.icon_instance:
            self.icon_instance.update_menu()

    def _handle_toggle_notify(self, icon=None, item_obj=None) -> None:
        self.config.enable_notifications = not self.config.enable_notifications
        save_config(self.config)
        logger.info(f"Tray menu: Enable notifications set to {self.config.enable_notifications}")
        if self.icon_instance:
            self.icon_instance.update_menu()

    def _handle_open_ui(self, icon=None, item_obj=None) -> None:
        logger.info("Tray menu: Opening Control Panel UI...")
        try:
            subprocess.Popen(["wifi-ac-guardian", "--gui"])
        except Exception as e:
            logger.error(f"Failed to launch UI from tray menu: {e}")

    def _handle_quit(self, icon=None, item_obj=None) -> None:
        """Callback for 'Quit App' / 'Exit' menu click."""
        if self._quitting:
            return
        self._quitting = True
        logger.info("Tray menu: Quit app option clicked by user.")

        # Stop tray icon UI immediately
        self.stop()

        # Stop monitoring loop if callback is registered
        if self.on_quit_click:
            try:
                self.on_quit_click()
            except Exception as e:
                logger.error(f"Error during on_quit_click callback: {e}")

        # Stop systemd user service if active
        try:
            subprocess.run(["systemctl", "--user", "stop", "wifi-ac-guardian.service"], check=False)
        except Exception as e:
            logger.error(f"Failed to stop systemd user service: {e}")

        # Kill any remaining instances if process is still running
        try:
            subprocess.run(["pkill", "-f", "wifi-ac-guardian"], check=False)
        except Exception:
            pass

    def update_status(self, state: StatusState, link: Optional[LinkInfo] = None) -> None:
        self.current_state = state
        self.current_link = link

        if not self.icon_instance or not PYSTRAY_AVAILABLE:
            return

        try:
            new_image = create_pillow_icon_for_state(state)
            self.icon_instance.icon = new_image

            if link and link.connected:
                title = f"WiFi AC Guardian: {link.phy_summary} ({link.ssid})"
            else:
                title = f"WiFi AC Guardian: {state.value}"
            self.icon_instance.title = title
        except Exception as e:
            logger.debug(f"Failed to update tray icon image: {e}")

    def stop(self) -> None:
        if self.icon_instance and PYSTRAY_AVAILABLE:
            try:
                self.icon_instance.stop()
                logger.info("System tray icon stopped.")
            except Exception as e:
                logger.debug(f"Error stopping tray icon: {e}")
