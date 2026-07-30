"""
Configuration manager for WiFi AC Guardian.
"""

import os
import json
from typing import Optional
from wifi_ac_guardian.core.models import GuardianConfig
from wifi_ac_guardian.logger import get_logger

logger = get_logger()

CONFIG_DIR = os.path.expanduser("~/.config/wifi-ac-guardian")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config(config_path: Optional[str] = None) -> GuardianConfig:
    """
    Loads configuration settings from JSON file or returns defaults.

    Args:
        config_path: Path to config JSON file.

    Returns:
        GuardianConfig instance.
    """
    target_path = os.path.expanduser(config_path) if config_path else CONFIG_FILE

    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = GuardianConfig(
                interface=data.get("interface"),
                check_interval=float(data.get("check_interval", 10.0)),
                reconnect_delay=float(data.get("reconnect_delay", 2.0)),
                max_attempts=int(data.get("max_attempts", 10)),
                log_file_path=data.get("log_file_path", "~/wifi_ac_guardian.log"),
                enable_notifications=bool(data.get("enable_notifications", True)),
                enable_tray=bool(data.get("enable_tray", True)),
            )
            logger.info(f"Loaded configuration settings from {target_path}")
            return config
        except Exception as e:
            logger.warning(f"Error reading configuration file {target_path}: {e}. Using defaults.")

    return GuardianConfig()


def save_config(config: GuardianConfig, config_path: Optional[str] = None) -> str:
    """
    Saves GuardianConfig settings to JSON file.

    Args:
        config: GuardianConfig instance.
        config_path: Destination JSON file path.

    Returns:
        Filepath string where saved.
    """
    target_path = os.path.expanduser(config_path) if config_path else CONFIG_FILE
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    data = {
        "interface": config.interface,
        "check_interval": config.check_interval,
        "reconnect_delay": config.reconnect_delay,
        "max_attempts": config.max_attempts,
        "log_file_path": config.log_file_path,
        "enable_notifications": config.enable_notifications,
        "enable_tray": config.enable_tray,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    logger.info(f"Saved configuration to {target_path}")
    return target_path
