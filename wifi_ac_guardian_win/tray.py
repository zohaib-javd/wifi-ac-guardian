"""
System tray interface for Windows 11.
"""

import os
import sys
import subprocess
import threading
import ctypes
from typing import Optional, Callable
from wifi_ac_guardian_win.core.models import StatusState, LinkInfo, GuardianConfig
from wifi_ac_guardian_win.icons import create_pillow_icon_for_state
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()

PYSTRAY_AVAILABLE = False
try:
    import pystray
    from pystray import MenuItem as item, Menu
    PYSTRAY_AVAILABLE = True
except Exception as e:
    PYSTRAY_AVAILABLE = False

TRAY_MENU_ICON_DIR = os.path.join(os.path.dirname(__file__), "assets", "tray_menu")

if PYSTRAY_AVAILABLE and sys.platform == "win32":
    from pystray import _win32
    from pystray._util import win32

    class PremiumWin32Icon(_win32.Icon):
        """Windows tray icon with small bitmap icons in its native menu."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._menu_bitmaps = []

        def _update_menu(self):
            old_bitmaps = self._menu_bitmaps
            self._menu_bitmaps = []
            super()._update_menu()
            for bitmap in old_bitmaps:
                try:
                    ctypes.windll.gdi32.DeleteObject(bitmap)
                except Exception:
                    pass

        def _menu_icon_path(self, text: str) -> Optional[str]:
            lower = text.lower()
            if "open dashboard" in lower or text == "WiFi AC Guardian":
                name = "dashboard.bmp"
            elif "reconnect" in lower:
                name = "reconnect.bmp"
            elif "stop protection" in lower or "start protection" in lower:
                name = "protection.bmp"
            elif "exit" in lower:
                name = "exit.bmp"
            elif "802.11" in lower or "phy" in lower:
                name = "phy.bmp"
            elif any(state in lower for state in ("good", "restoring", "downgraded", "backup", "disconnected")):
                name = "status.bmp"
            else:
                name = "header.bmp"
            path = os.path.join(TRAY_MENU_ICON_DIR, name)
            return path if os.path.exists(path) else None

        def _create_menu_item(self, descriptor, callbacks):
            menu_item = super()._create_menu_item(descriptor, callbacks)
            if descriptor is not Menu.SEPARATOR:
                bitmap_path = self._menu_icon_path(descriptor.text)
                if bitmap_path:
                    bitmap = win32.LoadImage(
                        None, bitmap_path, 0, 0, 0, win32.LR_LOADFROMFILE
                    )
                    if bitmap:
                        menu_item.fMask |= win32.MIIM_BITMAP
                        menu_item.hbmpItem = bitmap
                        self._menu_bitmaps.append(bitmap)
            return menu_item
else:
    PremiumWin32Icon = None


class SystemTrayAppWin:
    """Manages system tray icon and menu on Windows 11 taskbar."""

    def __init__(
        self,
        on_reconnect_click: Optional[Callable[[], None]] = None,
        on_stop_protection_click: Optional[Callable[[], None]] = None,
        on_quit_click: Optional[Callable[[], None]] = None,
        on_open_ui_click: Optional[Callable[[], None]] = None,
        config: Optional[GuardianConfig] = None
    ):
        self.on_reconnect_click = on_reconnect_click
        self.on_stop_protection_click = on_stop_protection_click
        self.on_quit_click = on_quit_click
        self.on_open_ui_click = on_open_ui_click
        self.config = config or GuardianConfig()
        self.current_state = StatusState.IDLE
        self.current_link: Optional[LinkInfo] = None
        self.icon_instance: Optional[object] = None
        self._thread: Optional[threading.Thread] = None
        self.protection_running = True

    def start(self) -> None:
        if not PYSTRAY_AVAILABLE:
            logger.info("pystray not available. Tray applet disabled.")
            return

        self._thread = threading.Thread(target=self._run_tray, daemon=True, name="WinTrayThread")
        self._thread.start()

    def _run_tray(self) -> None:
        try:
            import ctypes
            try:
                ctypes.windll.ole32.CoInitialize(None)
            except Exception:
                pass

            initial_image = create_pillow_icon_for_state(self.current_state)
            menu = Menu(
                item("Open Dashboard", self._handle_open_ui, default=True),
                item("Reconnect now", self._handle_reconnect),
                item(self._get_protection_text, self._handle_toggle_protection),
                Menu.SEPARATOR,
                item("Exit", self._handle_quit),
            )

            self.icon_instance = pystray.Icon(
                "wifi_ac_guardian_win",
                initial_image,
                "WiFi AC Guardian (Windows 11)",
                menu
            )
            self.icon_instance.run()
        except Exception as e:
            logger.error(f"Error running Windows system tray icon: {e}")

    def _get_protection_text(self, item_obj=None) -> str:
        return "Stop Protection" if self.protection_running else "Start Protection"

    def _handle_reconnect(self, icon=None, item_obj=None) -> None:
        if self.on_reconnect_click:
            self.on_reconnect_click()

    def _handle_toggle_protection(self, icon=None, item_obj=None) -> None:
        if self.on_stop_protection_click:
            self.on_stop_protection_click()

    def set_protection_running(self, running: bool) -> None:
        self.protection_running = running
        if self.icon_instance:
            try:
                self.icon_instance.update_menu()
            except Exception:
                pass

    def _handle_open_ui(self, icon=None, item_obj=None) -> None:
        if self.on_open_ui_click:
            try:
                self.on_open_ui_click()
            except Exception as e:
                logger.error(f"Error in on_open_ui_click callback: {e}")
        else:
            try:
                pythonw = os.path.join(sys.prefix, "pythonw.exe")
                exe = pythonw if os.path.exists(pythonw) else sys.executable
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.Popen([exe, "-m", "wifi_ac_guardian_win", "--gui"], creationflags=flags)
            except Exception:
                pass

    def _handle_quit(self, icon=None, item_obj=None) -> None:
        self.stop()
        if self.on_quit_click:
            self.on_quit_click()

    def update_status(self, state: StatusState, link: Optional[LinkInfo] = None) -> None:
        self.current_state = state
        self.current_link = link

        if not self.icon_instance or not PYSTRAY_AVAILABLE:
            return

        try:
            # Only recreate and reassign HICON handle if state actually changed to prevent Win32 GDI handle exhaustion
            if not hasattr(self, "_last_icon_state") or state != self._last_icon_state:
                self._last_icon_state = state
                new_image = create_pillow_icon_for_state(state)
                self.icon_instance.icon = new_image

            # Route tooltip through the descriptor (feature 001, T023)
            from wifi_ac_guardian_win.status_presentation import get_presentation
            target = self.config.target_ssid or "lab5g"
            desc = get_presentation(state, target_ssid=target)

            if link and link.connected:
                ssid = link.ssid or "Unknown"
                bitrate_str = f" ({link.max_bitrate_mbps:.0f} Mbps)" if link.max_bitrate_mbps > 0 else ""
                title = f"{desc.tray_tooltip_prefix} — {ssid}{bitrate_str}"
            else:
                title = desc.tray_tooltip_prefix

            self.icon_instance.title = title
            try:
                self.icon_instance.update_menu()
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Error updating tray icon: {e}")

    def stop(self) -> None:
        if self.icon_instance and PYSTRAY_AVAILABLE:
            try:
                self.icon_instance.stop()
            except Exception:
                pass
