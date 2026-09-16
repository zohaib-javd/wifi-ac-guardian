"""
Logging system for WiFi AC Guardian Windows Edition.
Logs messages with ISO timestamps to a dedicated per-user log directory and stdout.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def default_log_directory() -> str:
    """Dedicated per-user log directory, keeping rolling logs out of the profile root."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return os.path.join(local_appdata, "WiFi AC Guardian", "logs")
    return os.path.join(os.path.expanduser("~"), ".wifi-ac-guardian", "logs")


DEFAULT_LOG_FILE_PATH = os.path.join(default_log_directory(), "wifi_ac_guardian_win.log")

_ORPHAN_CLEANUP_DONE = False


def cleanup_orphan_home_logs(target_log_dir: str) -> None:
    """One-time relocation of pre-existing ``wifi_ac_guardian_win.log*`` files left in the
    user home directory by prior builds that logged directly to the profile root.

    Each orphan is moved into the dedicated log directory; if a same-named file already
    exists there, the orphan is deleted instead. Best-effort only: any filesystem error
    (locked file, permissions, antivirus) is swallowed so logging always keeps working.
    """
    global _ORPHAN_CLEANUP_DONE
    if _ORPHAN_CLEANUP_DONE:
        return
    _ORPHAN_CLEANUP_DONE = True

    try:
        os.makedirs(target_log_dir, exist_ok=True)
    except OSError:
        return

    try:
        orphans = list(Path.home().glob("wifi_ac_guardian_win.log*"))
    except OSError:
        return

    for orphan in orphans:
        try:
            if not orphan.is_file():
                continue
            destination = Path(target_log_dir) / orphan.name
            if destination.exists():
                orphan.unlink()
            else:
                orphan.rename(destination)
        except OSError:
            continue


def setup_logger(
    log_file_path: str = DEFAULT_LOG_FILE_PATH,
    level: int = logging.INFO
) -> logging.Logger:
    """Configures central logger instance.

    Logs roll over at midnight and only the current and previous day are kept
    (``backupCount=1``), so the log directory stays small without custom pruning.
    """
    logger = logging.getLogger("wifi_ac_guardian_win")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    expanded_path = os.path.expanduser(log_file_path)
    log_dir = os.path.dirname(expanded_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    cleanup_orphan_home_logs(log_dir or default_log_directory())

    file_handler = TimedRotatingFileHandler(
        expanded_path,
        when="midnight",
        backupCount=1,
        encoding="utf-8",
    )
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
