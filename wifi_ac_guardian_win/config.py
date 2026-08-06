"""
Configuration manager for WiFi AC Guardian Windows Edition.
"""

import os
import json
from typing import Optional
from wifi_ac_guardian_win.core.models import GuardianConfig
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()

appdata = os.environ.get("APPDATA")
if appdata:
    CONFIG_DIR = os.path.join(appdata, "wifi-ac-guardian")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/wifi-ac-guardian-win")

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "wifi_ac_guardian.ico")


import sys
import subprocess

def _write_shortcut(shortcut_path: str, arguments: str, description: str) -> None:
    """Create a Windows shortcut with the bundled Fluent shield icon."""
    try:
        os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
        pythonw = os.path.join(sys.prefix, "pythonw.exe")
        exe = pythonw if os.path.exists(pythonw) else sys.executable
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        proj_dir = os.path.dirname(pkg_dir)
        ps_script = f"""
        $ws = New-Object -ComObject WScript.Shell
        $sc = $ws.CreateShortcut('{shortcut_path}')
        $sc.TargetPath = '{exe}'
        $sc.Arguments = '{arguments}'
        $sc.WorkingDirectory = '{proj_dir}'
        $sc.Description = '{description}'
        $sc.IconLocation = '{APP_ICON_PATH},0'
        $sc.Save()
        """
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=10, creationflags=flags)
        logger.info(f"Created shortcut at: {shortcut_path}")
    except Exception as e:
        logger.error(f"Failed to create shortcut: {e}")


def sync_autostart_shortcut(enable: bool) -> None:
    """Creates or removes Windows Startup folder shortcut based on enable flag."""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return
    startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_dir, "WiFi AC Guardian.lnk")

    if enable:
        _write_shortcut(shortcut_path, "-m wifi_ac_guardian_win --daemon", "WiFi AC Guardian Autostart")
    else:
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
                logger.info(f"Removed autostart shortcut from: {shortcut_path}")
            except Exception as e:
                logger.error(f"Failed to remove autostart shortcut: {e}")


def sync_desktop_shortcut() -> None:
    """Create the desktop shortcut with the bundled Fluent shield icon."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "WiFi AC Guardian.lnk")
    _write_shortcut(desktop_path, "-m wifi_ac_guardian_win --gui", "WiFi AC Guardian")


def load_config(config_path: Optional[str] = None) -> GuardianConfig:
    target_path = os.path.expanduser(config_path) if config_path else CONFIG_FILE

    # Fallback to legacy path if new path doesn't exist yet
    if not os.path.exists(target_path):
        legacy_path = os.path.expanduser("~/.config/wifi-ac-guardian-win/config.json")
        if os.path.exists(legacy_path):
            target_path = legacy_path

    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return GuardianConfig(
                interface=data.get("interface", "Wi-Fi"),
                target_ssid=data.get("target_ssid", "lab5g"),
                auto_switch_primary=bool(data.get("auto_switch_primary", True)),
                auto_start=bool(data.get("auto_start", True)),
                check_interval=float(data.get("check_interval", 10.0)),
                reconnect_delay=float(data.get("reconnect_delay", 15.0)),
                max_attempts=int(data.get("max_attempts", 99)),
                log_file_path=data.get("log_file_path", os.path.join(os.path.expanduser("~"), "wifi_ac_guardian_win.log")),
                enable_notifications=False,
                enable_tray=bool(data.get("enable_tray", True)),
                start_minimized=bool(data.get("start_minimized", False)),
                is_paused=bool(data.get("is_paused", False)),
                animations_enabled=bool(data.get("animations_enabled", False)),
            )
        except Exception as e:
            logger.warning(f"Error loading config: {e}. Using defaults.")

    return GuardianConfig()


def save_config(config: GuardianConfig, config_path: Optional[str] = None) -> str:
    target_path = os.path.expanduser(config_path) if config_path else CONFIG_FILE
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    data = {
        "interface": config.interface,
        "target_ssid": config.target_ssid,
        "auto_switch_primary": config.auto_switch_primary,
        "auto_start": config.auto_start,
        "check_interval": config.check_interval,
        "reconnect_delay": config.reconnect_delay,
        "max_attempts": config.max_attempts,
        "log_file_path": config.log_file_path,
        "enable_notifications": False,
        "enable_tray": config.enable_tray,
        "start_minimized": config.start_minimized,
        "is_paused": config.is_paused,
        "animations_enabled": config.animations_enabled,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    sync_autostart_shortcut(config.auto_start)
    return target_path
