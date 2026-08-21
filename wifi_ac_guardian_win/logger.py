"""
Logging system for WiFi AC Guardian Windows Edition.
Logs messages with ISO timestamps to ~/wifi_ac_guardian_win.log and stdout.
"""

import os
import logging


def setup_logger(
    log_file_path: str = os.path.join(os.path.expanduser("~"), "wifi_ac_guardian_win.log"),
    level: int = logging.INFO
) -> logging.Logger:
    """Configures central logger instance."""
    logger = logging.getLogger("wifi_ac_guardian_win")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    expanded_path = os.path.expanduser(log_file_path)
    log_dir = os.path.dirname(expanded_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(expanded_path, encoding="utf-8")
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def get_logger() -> logging.Logger:
    """Returns logger instance."""
    return logging.getLogger("wifi_ac_guardian_win")
