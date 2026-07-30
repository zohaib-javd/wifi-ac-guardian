"""
GTK3 Graphical User Interface (GUI) Control Panel for WiFi AC Guardian.
Provides real-time link monitoring, status indicators, manual control,
and timing selectors for check interval and reconnection delay.
"""

import sys
import os
import threading
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from wifi_ac_guardian.core.models import GuardianConfig, StatusState, LinkInfo, PhyMode
from wifi_ac_guardian.core.detector import WifiDetector
from wifi_ac_guardian.core.reconnector import WifiReconnector
from wifi_ac_guardian.config import load_config, save_config
from wifi_ac_guardian.logger import get_logger

logger = get_logger()

# Modern CSS Styling for GTK3 UI
CUSTOM_CSS = b"""
window {
    background-color: #1E1E2E;
    color: #CDD6F4;
    font-family: 'Ubuntu', 'Segoe UI', sans-serif;
}

.header-title {
    font-size: 20px;
    font-weight: bold;
    color: #F5E0DC;
}

.status-card-good {
    background-color: #11111B;
    border: 2px solid #A6E3A1;
    border-radius: 12px;
    padding: 16px;
}

.status-card-retrying {
    background-color: #11111B;
    border: 2px solid #F9E2AF;
    border-radius: 12px;
    padding: 16px;
}

.status-card-failed {
    background-color: #11111B;
    border: 2px solid #F38BA8;
    border-radius: 12px;
    padding: 16px;
}

.badge-good {
    background-color: #A6E3A1;
    color: #11111B;
    font-weight: bold;
    font-size: 14px;
    border-radius: 6px;
    padding: 4px 12px;
}

.badge-warning {
    background-color: #F9E2AF;
    color: #11111B;
    font-weight: bold;
    font-size: 14px;
    border-radius: 6px;
    padding: 4px 12px;
}

.badge-danger {
    background-color: #F38BA8;
    color: #11111B;
    font-weight: bold;
    font-size: 14px;
    border-radius: 6px;
    padding: 4px 12px;
}

.metric-label {
    color: #89B4FA;
    font-size: 12px;
    font-weight: bold;
}

.metric-value {
    color: #CDD6F4;
    font-size: 15px;
}

.btn-primary {
    background: linear-gradient(135deg, #89B4FA, #74C7EC);
    color: #11111B;
    font-weight: bold;
    border-radius: 8px;
    border: none;
    padding: 8px 16px;
}

.btn-secondary {
    background-color: #313244;
    color: #CDD6F4;
    border-radius: 8px;
    border: 1px solid #45475A;
    padding: 8px 16px;
}

.section-header {
    font-size: 15px;
    font-weight: bold;
    color: #CBA6F7;
    margin-top: 10px;
}
"""


class WifiACGuardianWindow(Gtk.Window):
    """Main Application Window for WiFi AC Guardian."""

    def __init__(self, config: Optional[GuardianConfig] = None):
        super().__init__(title="WiFi AC Guardian Control Panel")
        self.set_default_size(520, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(18)

        self.config = config or load_config()
        self.detector = WifiDetector(interface=self.config.interface)
        self.reconnector = WifiReconnector(config=self.config)

        self._apply_css()
        self._build_ui()

        # Start periodic UI update timer (every 2 seconds)
        GLib.timeout_add_seconds(2, self._refresh_status)
        self._refresh_status()

    def _apply_css(self) -> None:
        """Injects custom CSS provider into Gdk screen."""
        provider = Gtk.CssProvider()
        provider.load_from_data(CUSTOM_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self) -> None:
        """Constructs GTK widget layout."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(main_box)

        # 1. Header Bar
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_label = Gtk.Label(label="🛡️ WiFi AC Guardian")
        title_label.get_style_context().add_class("header-title")
        header_box.pack_start(title_label, False, False, 0)

        subtitle_label = Gtk.Label(label="Wi-Fi 5 (802.11ac) Enforcer")
        subtitle_label.set_halign(Gtk.Align.END)
        header_box.pack_end(subtitle_label, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # 2. Status Card Container
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.card_box.get_style_context().add_class("status-card-good")
        main_box.pack_start(self.card_box, False, False, 0)

        # Status Top Line: Badge & SSID
        status_top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.badge_label = Gtk.Label(label="GOOD")
        self.badge_label.get_style_context().add_class("badge-good")
        status_top_box.pack_start(self.badge_label, False, False, 0)

        self.ssid_label = Gtk.Label(label="SSID: Detecting...")
        self.ssid_label.set_halign(Gtk.Align.START)
        status_top_box.pack_start(self.ssid_label, True, True, 0)

        self.card_box.pack_start(status_top_box, False, False, 0)

        # Metrics Grid (2x3)
        grid = Gtk.Grid(column_spacing=24, row_spacing=8)
        self.card_box.pack_start(grid, False, False, 4)

        # Row 0: PHY Mode & Bitrate
        grid.attach(self._make_label("PHY Mode:", "metric-label"), 0, 0, 1, 1)
        self.phy_val = self._make_label("-", "metric-value")
        grid.attach(self.phy_val, 1, 0, 1, 1)

        grid.attach(self._make_label("Bitrate:", "metric-label"), 2, 0, 1, 1)
        self.bitrate_val = self._make_label("-", "metric-value")
        grid.attach(self.bitrate_val, 3, 0, 1, 1)

        # Row 1: Frequency/Chan & Signal
        grid.attach(self._make_label("Channel / Freq:", "metric-label"), 0, 1, 1, 1)
        self.freq_val = self._make_label("-", "metric-value")
        grid.attach(self.freq_val, 1, 1, 1, 1)

        grid.attach(self._make_label("Signal Level:", "metric-label"), 2, 1, 1, 1)
        self.signal_val = self._make_label("-", "metric-value")
        grid.attach(self.signal_val, 3, 1, 1, 1)

        # Row 2: Interface & Retries
        grid.attach(self._make_label("Interface:", "metric-label"), 0, 2, 1, 1)
        self.iface_val = self._make_label("-", "metric-value")
        grid.attach(self.iface_val, 1, 2, 1, 1)

        grid.attach(self._make_label("Retry Attempts:", "metric-label"), 2, 2, 1, 1)
        self.attempts_val = self._make_label("0 / 10", "metric-value")
        grid.attach(self.attempts_val, 3, 2, 1, 1)

        # 3. Timing & Selector Settings Section
        sec_label = Gtk.Label(label="⚙️ Timing & Reattempt Controls")
        sec_label.get_style_context().add_class("section-header")
        sec_label.set_halign(Gtk.Align.START)
        main_box.pack_start(sec_label, False, False, 0)

        ctrl_frame = Gtk.Frame()
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        ctrl_box.set_border_width(12)
        ctrl_frame.add(ctrl_box)
        main_box.pack_start(ctrl_frame, False, False, 0)

        # Check Interval Selector (Polling interval)
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_interval = Gtk.Label(label="Check Interval (seconds):")
        lbl_interval.set_tooltip_text("Time between continuous iw PHY mode checks (default: 10s)")
        interval_box.pack_start(lbl_interval, True, True, 0)

        self.spin_interval = Gtk.SpinButton.new_with_range(2.0, 60.0, 1.0)
        self.spin_interval.set_value(self.config.check_interval)
        interval_box.pack_start(self.spin_interval, False, False, 0)
        ctrl_box.pack_start(interval_box, False, False, 0)

        # Reconnect Delay Selector (Delay before reattempts)
        delay_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_delay = Gtk.Label(label="Reconnection Delay (seconds):")
        lbl_delay.set_tooltip_text("Delay between interface disconnect and reconnect attempt (default: 2.0s)")
        delay_box.pack_start(lbl_delay, True, True, 0)

        self.spin_delay = Gtk.SpinButton.new_with_range(0.5, 10.0, 0.5)
        self.spin_delay.set_value(self.config.reconnect_delay)
        delay_box.pack_start(self.spin_delay, False, False, 0)
        ctrl_box.pack_start(delay_box, False, False, 0)

        # Max Attempts Selector
        max_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_max = Gtk.Label(label="Max Reconnect Attempts:")
        lbl_max.set_tooltip_text("Maximum consecutive reconnection retries before giving up")
        max_box.pack_start(lbl_max, True, True, 0)

        self.spin_max_attempts = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.spin_max_attempts.set_value(self.config.max_attempts)
        max_box.pack_start(self.spin_max_attempts, False, False, 0)
        ctrl_box.pack_start(max_box, False, False, 0)

        # Desktop Notifications Checkbox
        notify_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.chk_notifications = Gtk.CheckButton(label="Enable Desktop Notification Popups")
        self.chk_notifications.set_active(self.config.enable_notifications)
        self.chk_notifications.set_tooltip_text("Uncheck to silence status bar desktop popups")
        notify_box.pack_start(self.chk_notifications, True, True, 0)
        ctrl_box.pack_start(notify_box, False, False, 0)

        # Pause Protection Checkbox
        pause_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.chk_pause = Gtk.CheckButton(label="Pause Automatic Wi-Fi Reconnection Protection")
        self.chk_pause.set_active(self.config.is_paused)
        pause_box.pack_start(self.chk_pause, True, True, 0)
        ctrl_box.pack_start(pause_box, False, False, 0)

        # Save Settings Button
        btn_save = Gtk.Button(label="💾 Save Settings")
        btn_save.get_style_context().add_class("btn-secondary")
        btn_save.connect("clicked", self._on_save_settings_clicked)
        ctrl_box.pack_start(btn_save, False, False, 0)

        # 4. Action Buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(action_box, False, False, 0)

        self.btn_reconnect = Gtk.Button(label="🔄 Reconnect Now")
        self.btn_reconnect.get_style_context().add_class("btn-primary")
        self.btn_reconnect.connect("clicked", self._on_reconnect_clicked)
        action_box.pack_start(self.btn_reconnect, True, True, 0)

        btn_view_logs = Gtk.Button(label="📋 View Log File")
        btn_view_logs.get_style_context().add_class("btn-secondary")
        btn_view_logs.connect("clicked", self._on_view_logs_clicked)
        action_box.pack_start(btn_view_logs, True, True, 0)

    def _make_label(self, text: str, css_class: str) -> Gtk.Label:
        """Helper to build styled Gtk.Label."""
        lbl = Gtk.Label(label=text)
        lbl.set_halign(Gtk.Align.START)
        lbl.get_style_context().add_class(css_class)
        return lbl

    def _refresh_status(self) -> bool:
        """Background poll method called by GLib timer every 2 seconds."""
        def worker():
            link = self.detector.get_link_info()
            GLib.idle_add(self._update_status_ui, link)

        threading.Thread(target=worker, daemon=True).start()
        return True

    def _update_status_ui(self, link: LinkInfo) -> None:
        """Updates UI elements with fresh LinkInfo state."""
        ctx = self.card_box.get_style_context()
        badge_ctx = self.badge_label.get_style_context()

        # Remove existing status classes
        for cls in ["status-card-good", "status-card-retrying", "status-card-failed"]:
            ctx.remove_class(cls)
        for cls in ["badge-good", "badge-warning", "badge-danger"]:
            badge_ctx.remove_class(cls)

        if not link.connected:
            ctx.add_class("status-card-failed")
            badge_ctx.add_class("badge-danger")
            self.badge_label.set_text("DISCONNECTED")
            self.ssid_label.set_text("SSID: Not connected")
            self.phy_val.set_text("Disconnected")
            self.bitrate_val.set_text("N/A")
            self.freq_val.set_text("N/A")
            self.signal_val.set_text("N/A")
            self.iface_val.set_text(link.interface or "-")
            return

        self.ssid_label.set_text(f"SSID: {link.ssid or 'Unknown'}")
        self.phy_val.set_text(link.phy_summary)
        self.bitrate_val.set_text(link.tx_bitrate or link.rx_bitrate or "N/A")

        freq_str = f"{int(link.freq_mhz)} MHz" if link.freq_mhz else "N/A"
        chan_str = f"Ch {link.channel}" if link.channel is not None else ""
        self.freq_val.set_text(f"{freq_str} ({chan_str})" if chan_str else freq_str)

        self.signal_val.set_text(f"{link.signal_dbm} dBm" if link.signal_dbm is not None else "N/A")
        self.iface_val.set_text(link.interface)

        if link.is_good:
            ctx.add_class("status-card-good")
            badge_ctx.add_class("badge-good")
            self.badge_label.set_text("GOOD (Wi-Fi 5+)")
        else:
            ctx.add_class("status-card-retrying")
            badge_ctx.add_class("badge-warning")
            self.badge_label.set_text("Wi-Fi 4 (HT) DOWNGRADE")

    def _on_save_settings_clicked(self, widget: Gtk.Button) -> None:
        """Saves timing & attempt selector values to config.json."""
        self.config.check_interval = self.spin_interval.get_value()
        self.config.reconnect_delay = self.spin_delay.get_value()
        self.config.max_attempts = int(self.spin_max_attempts.get_value())
        self.config.enable_notifications = self.chk_notifications.get_active()
        self.config.is_paused = self.chk_pause.get_active()

        saved_path = save_config(self.config)
        logger.info(f"Updated configuration: check_interval={self.config.check_interval}s, "
                    f"reconnect_delay={self.config.reconnect_delay}s, max_attempts={self.config.max_attempts}, "
                    f"enable_notifications={self.config.enable_notifications}, is_paused={self.config.is_paused}")

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Settings Saved Successfully!"
        )
        dialog.format_secondary_text(
            f"Check Interval: {self.config.check_interval:.1f}s\n"
            f"Reconnect Delay: {self.config.reconnect_delay:.1f}s\n"
            f"Max Attempts: {self.config.max_attempts}\n"
            f"Notifications Enabled: {self.config.enable_notifications}\n"
            f"Protection Paused: {self.config.is_paused}\n\n"
            f"Saved to {saved_path}"
        )
        dialog.run()
        dialog.destroy()

    def _on_reconnect_clicked(self, widget: Gtk.Button) -> None:
        """Triggers manual reconnection."""
        self.btn_reconnect.set_sensitive(False)
        self.btn_reconnect.set_label("Reconnecting...")

        def worker():
            link = self.detector.get_link_info()
            iface = link.interface or self.detector.get_interface()
            self.reconnector.trigger_reconnect(iface, ssid=link.ssid)

            def done():
                self.btn_reconnect.set_sensitive(True)
                self.btn_reconnect.set_label("🔄 Reconnect Now")
                self._refresh_status()

            GLib.idle_add(done)

        threading.Thread(target=worker, daemon=True).start()

    def _on_view_logs_clicked(self, widget: Gtk.Button) -> None:
        """Opens log file in default text viewer or displays in dialog."""
        log_path = os.path.expanduser(self.config.log_file_path)
        if os.path.exists(log_path):
            try:
                os.system(f"xdg-open {log_path} &")
            except Exception as e:
                logger.error(f"Failed to open log file: {e}")
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Log File Not Found",
            )
            dialog.format_secondary_text(f"No log file found at {log_path}")
            dialog.run()
            dialog.destroy()


def launch_gui(config: Optional[GuardianConfig] = None) -> None:
    """Entrypoint to launch GTK application window."""
    app = WifiACGuardianWindow(config=config)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    launch_gui()
