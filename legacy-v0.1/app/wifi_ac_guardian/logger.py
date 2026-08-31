"""
Logging system for WiFi AC Guardian.
Logs messages with ISO timestamps to ~/wifi_ac_guardian.log and stdout.
"""

import os
import logging
from typing import Optional


def setup_logger(
    log_file_path: str = "~/wifi_ac_guardian.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configures and returns the central logger instance for wifi_ac_guardian.

    Args:
        log_file_path: Path to log file (supports ~ expansion).
        level: Logging level (default INFO).

    Returns:
        Configured logging.Logger object.
    """
    logger = logging.getLogger("wifi_ac_guardian")
    logger.setLevel(level)

    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    expanded_path = os.path.expanduser(log_file_path)
    
    # Ensure directory exists if path is custom
    log_dir = os.path.dirname(expanded_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # File Handler
    file_handler = logging.FileHandler(expanded_path, encoding="utf-8")
    file_handler.setLevel(level)
    
    # Stream Handler (stdout for journalctl / terminal)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    # Formatter with ISO-8601 timestamps
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
    """Get existing logger instance or initialize default."""
    return logging.getLogger("wifi_ac_guardian")
