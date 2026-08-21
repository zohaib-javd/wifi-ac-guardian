"""
Local IPC Server for WiFi AC Guardian.
Bridge between Python Guardian Engine and Next.js Commercial Desktop UI.
Runs an HTTP/JSON RPC endpoint on 127.0.0.1:39146.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from wifi_ac_guardian_win.logger import get_logger
from wifi_ac_guardian_win.config import save_config

logger = get_logger()

def _format_datetime(value):
    """Serialize backend timestamps for the local dashboard API."""
    return value.isoformat(timespec="seconds") if value else None


IPC_PORT = 39146
_guardian_instance = None


class GuardianIPCHandler(BaseHTTPRequestHandler):
    """Handles HTTP RPC requests from the Next.js frontend."""

    def log_message(self, format, *args):
        pass  # Quiet logging for routine IPC requests

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        """Return current live telemetry to Next.js frontend."""
        if not _guardian_instance:
            self._set_headers(503)
            self.wfile.write(json.dumps({"error": "Guardian engine inactive"}).encode('utf-8'))
            return

        link = _guardian_instance.state.current_link
        saved_profiles = _guardian_instance.detector.get_saved_wifi_profiles()
        nearby_ssids = _guardian_instance.detector.get_available_ssids()
        nearby_keys = {ssid.strip().casefold() for ssid in nearby_ssids if ssid and ssid.strip()}
        eligible_ssids = [
            ssid for ssid in saved_profiles
            if ssid and ssid.strip() and ssid.strip().casefold() in nearby_keys
        ]
        data = {
            "connected": link.connected if link else False,
            "ssid": (link.ssid if link and link.ssid else _guardian_instance.config.target_ssid) or "lab5g",
            "linkSpeed": link.max_bitrate_mbps if link and link.connected else 866.5,
            "signalPct": link.signal_pct if link and link.signal_pct is not None else 95,
            "txBitrate": link.tx_bitrate if link else "866.5 Mbps",
            "rxBitrate": link.rx_bitrate if link else "866.5 Mbps",
            "phyMode": (link.phy_summary if link else "Wi-Fi 5 (802.11ac)"),
            "adapter": (link.adapter if link and link.adapter else (link.interface if link else "Wi-Fi")),
            "status": _guardian_instance.state.status.value if hasattr(_guardian_instance.state.status, 'value') else str(_guardian_instance.state.status),
            "reconnectAttempts": _guardian_instance.state.attempts_count,
            "maxAttempts": _guardian_instance.config.max_attempts,
            "protectionRunning": _guardian_instance.state.running,
            "lastRecovery": _format_datetime(_guardian_instance.state.last_reconnect),
            "lastCheck": _format_datetime(_guardian_instance.state.last_check),
            "checkInterval": _guardian_instance.config.check_interval,
            "reconnectDelay": _guardian_instance.config.reconnect_delay,
            "minBitrateThreshold": _guardian_instance.config.min_bitrate_threshold,
            "autoSwitchPrimary": _guardian_instance.config.auto_switch_primary,
            "enableNotifications": _guardian_instance.config.enable_notifications,
            "enableSoundAlerts": _guardian_instance.config.sound_alerts,
            "autoStart": _guardian_instance.config.auto_start,
            "startMinimized": _guardian_instance.config.start_minimized,
            "targetSsid": _guardian_instance.config.target_ssid,
            "available_ssids": eligible_ssids,
        }
        self._set_headers(200)
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        """Process incoming actions from Next.js frontend."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            payload = json.loads(post_data.decode('utf-8'))
            action = payload.get("action")

            if action == "reconnect_now" and _guardian_instance:
                link = _guardian_instance.detector.get_link_info()
                target = _guardian_instance.config.target_ssid or "lab5g"
                threading.Thread(
                    target=_guardian_instance.reconnector.trigger_reconnect,
                    args=(link.interface, target),
                    daemon=True
                ).start()
                resp = {"status": "ok", "message": "Reconnect triggered"}


            elif action == "save_settings" and _guardian_instance:
                settings = payload.get("settings") or {}
                mapping = {
                    "targetSsid": "target_ssid", "checkInterval": "check_interval",
                    "reconnectDelay": "reconnect_delay", "maxAttempts": "max_attempts",
                    "minBitrateThreshold": "min_bitrate_threshold",
                    "autoSwitchPrimary": "auto_switch_primary", "enableNotifications": "enable_notifications",
                    "enableSoundAlerts": "sound_alerts", "autoStart": "auto_start", "startMinimized": "start_minimized"
                }
                for incoming, field in mapping.items():
                    if incoming not in settings or not hasattr(_guardian_instance.config, field): continue
                    value = settings[incoming]
                    if field in {"check_interval", "reconnect_delay", "min_bitrate_threshold"}: value = max(1.0, min(10000.0, float(value)))
                    elif field == "max_attempts": value = max(1, min(999, int(value)))
                    elif field == "target_ssid": value = str(value).strip()[:64] or _guardian_instance.config.target_ssid
                    elif field in {"auto_switch_primary", "enable_notifications", "sound_alerts", "auto_start", "start_minimized"}: value = bool(value)
                    setattr(_guardian_instance.config, field, value)
                _guardian_instance.notifier.enabled = _guardian_instance.config.enable_notifications
                _guardian_instance.notifier.sound_enabled = _guardian_instance.config.sound_alerts
                _guardian_instance.reconnector.config = _guardian_instance.config
                config_path = save_config(_guardian_instance.config, sync_startup_shortcut=False)
                resp = {
                    "status": "ok",
                    "message": "Settings saved",
                    "configPath": config_path,
                    "settings": {
                        "targetSsid": _guardian_instance.config.target_ssid,
                        "checkInterval": _guardian_instance.config.check_interval,
                        "reconnectDelay": _guardian_instance.config.reconnect_delay,
                        "maxAttempts": _guardian_instance.config.max_attempts,
                        "minBitrateThreshold": _guardian_instance.config.min_bitrate_threshold,
                        "autoSwitchPrimary": _guardian_instance.config.auto_switch_primary,
                        "enableNotifications": _guardian_instance.config.enable_notifications,
                        "enableSoundAlerts": _guardian_instance.config.sound_alerts,
                        "autoStart": _guardian_instance.config.auto_start,
                        "startMinimized": _guardian_instance.config.start_minimized,
                    },
                }
            elif action == "toggle_protection" and _guardian_instance:
                if _guardian_instance.state.running:
                    _guardian_instance.stop_protection()
                else:
                    _guardian_instance.start_protection()
                resp = {"status": "ok", "protectionRunning": _guardian_instance.state.running}

            else:
                resp = {"status": "error", "message": "Unknown action"}

            self._set_headers(200)
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))


def start_ipc_server(guardian) -> None:
    """Start local IPC HTTP server in background thread."""
    global _guardian_instance
    _guardian_instance = guardian

    def run_server():
        try:
            server = HTTPServer(('127.0.0.1', IPC_PORT), GuardianIPCHandler)
            logger.info(f"WiFi AC Guardian Local IPC Server listening on http://127.0.0.1:{IPC_PORT}")
            server.serve_forever()
        except Exception as e:
            logger.warning(f"Could not start IPC server: {e}")

    threading.Thread(target=run_server, daemon=True, name="GuardianIPCThread").start()


