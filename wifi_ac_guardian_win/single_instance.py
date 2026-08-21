"""
Single-instance application manager using localhost socket IPC for Windows 11.
Ensures only one instance of WiFi AC Guardian runs at a time.
If a secondary instance is launched (e.g. clicking Desktop shortcut again),
it notifies the primary instance to unhide/focus its Control Panel window and exits.
"""

import os
import sys
import socket
import threading
from typing import Callable, Optional
from wifi_ac_guardian_win.logger import get_logger

logger = get_logger()

LOCK_DIR = os.path.expanduser("~/.wifi_ac_guardian_win")
LOCK_FILE = os.path.join(LOCK_DIR, "app.lock")


class SingleInstanceChecker:
    """Ensures a single instance of WiFi AC Guardian runs on Windows 11."""

    def __init__(self):
        self.server_socket: Optional[socket.socket] = None
        self._listener_thread: Optional[threading.Thread] = None
        self.is_primary = False
        self.on_show_requested: Optional[Callable[[], None]] = None

    def try_claim_single_instance(self, on_show_requested: Optional[Callable[[], None]] = None) -> bool:
        """
        Attempts to claim single-instance ownership.
        If another instance is running, notifies it to restore GUI and returns False.
        """
        self.on_show_requested = on_show_requested

        # 1. Check existing lock file
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, "r", encoding="utf-8") as f:
                    port_str = f.read().strip()
                if port_str.isdigit():
                    existing_port = int(port_str)
                    if self._try_notify(existing_port):
                        logger.info(f"Notified existing primary instance on port {existing_port}.")
                        return False
            except Exception as e:
                logger.debug(f"Could not read existing lock file: {e}")

        # 2. Try binding a local IPC port
        os.makedirs(LOCK_DIR, exist_ok=True)
        for port in range(39145, 39150):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
                sock.listen(5)
                self.server_socket = sock
                self.is_primary = True

                with open(LOCK_FILE, "w", encoding="utf-8") as f:
                    f.write(str(port))

                self._listener_thread = threading.Thread(
                    target=self._listen_loop,
                    daemon=True,
                    name="SingleInstanceIPCThread"
                )
                self._listener_thread.start()
                logger.info(f"Registered primary single instance on port {port}.")
                return True
            except (OSError, socket.error):
                if self._try_notify(port):
                    return False
                continue

        logger.warning("Could not bind IPC port. Operating as fallback primary instance.")
        return True

    def _try_notify(self, port: int) -> bool:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1.5)
            client.connect(("127.0.0.1", port))
            client.sendall(b"SHOW_GUI\n")
            response = client.recv(1024).decode("utf-8", errors="ignore")
            client.close()
            if "ACK" in response or "OK" in response:
                return True
        except Exception:
            pass
        return False

    def _listen_loop(self) -> None:
        while self.is_primary and self.server_socket:
            try:
                conn, _ = self.server_socket.accept()
                data = conn.recv(1024).decode("utf-8", errors="ignore").strip()
                if "SHOW_GUI" in data:
                    conn.sendall(b"ACK\n")
                    conn.close()
                    if self.on_show_requested:
                        try:
                            self.on_show_requested()
                        except Exception as e:
                            logger.error(f"Error handling show request: {e}")
                else:
                    conn.close()
            except Exception:
                if not self.is_primary:
                    break

    def stop(self) -> None:
        self.is_primary = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        if os.path.exists(LOCK_FILE):
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass
