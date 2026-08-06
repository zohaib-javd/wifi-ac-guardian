"""
Tkinter Control Panel GUI for WiFi AC Guardian (Windows 11 & Ubuntu).
Exact Commercial Product UI implementation matching the approved visual mockup.
"""

import os
import sys
import time
import math
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple
from PIL import Image, ImageTk, ImageFilter

from wifi_ac_guardian_win.core.models import GuardianConfig, StatusState, LinkInfo
from wifi_ac_guardian_win.core.detector_win import WifiDetectorWin
from wifi_ac_guardian_win.core.reconnector_win import WifiReconnectorWin
from wifi_ac_guardian_win.core.guardian import WifiACGuardianWin
from wifi_ac_guardian_win.single_instance import SingleInstanceChecker
from wifi_ac_guardian_win.config import load_config, save_config
from wifi_ac_guardian_win.logger import get_logger
from wifi_ac_guardian_win import animation

logger = get_logger()

# --- DESIGN SYSTEM TOKENS ---
from wifi_ac_guardian_win import theme

COLOR_BG = theme.BG                       # Window Dark Background (#151515)
COLOR_CARD = theme.CARD                   # Card Surface Background (#1E1E1E)
COLOR_PANEL = theme.PANEL                 # Secondary Panel Surface (#252525)
COLOR_BORDER = theme.BORDER               # Soft Border Outline (#323232)

COLOR_ACCENT = theme.ACCENT               # Emerald Green Accent (#24C26A)
COLOR_ACCENT_BG = theme.ACCENT_BG
COLOR_WARN = theme.WARN                   # Amber Orange Warning (#F4B740)
COLOR_WARN_BG = theme.WARN_BG
COLOR_ERROR = theme.ERROR                 # Error Red (#E74C3C)
COLOR_ERROR_BG = theme.ERROR_BG
COLOR_INFO = theme.INFO                   # Information Blue (#3B82F6)
COLOR_INFO_BG = theme.INFO_BG

COLOR_TEXT_PRIMARY = theme.TEXT_PRIMARY   # High-contrast white (#FFFFFF)
COLOR_TEXT_SECONDARY = theme.TEXT_SECONDARY  # Readable secondary text (#B6B6B6)
COLOR_TEXT_MUTED = theme.TEXT_MUTED       # De-emphasized captions (#8C8C8C)

# Interaction states
COLOR_ACCENT_HOVER = theme.ACCENT_HOVER
COLOR_ERROR_HOVER = theme.ERROR_HOVER
COLOR_PANEL_HOVER = theme.PANEL_HOVER
COLOR_FOCUS_RING = theme.FOCUS_RING

# Speed-bar / Arc Gauge tokens
COLOR_TRACK = "#2A2A2A"
COLOR_ZONE_RED = theme.ZONE_RED
COLOR_ZONE_ORANGE = theme.ZONE_ORANGE
COLOR_ZONE_GREEN = theme.ZONE_GREEN
COLOR_SCALE_LABEL = theme.SCALE_LABEL

# Button ink
COLOR_ON_ACCENT = theme.ON_ACCENT
COLOR_ON_ERROR = theme.ON_ERROR
COLOR_ON_WARN = theme.ON_WARN

FONT_UI = theme.FONT_UI
FONT_DISPLAY = theme.FONT_DISPLAY
FONT_MONO = theme.FONT_MONO

FLUENT_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "fluent")
FLUENT_ASSETS = {
    "app": "../router.png",
    "shield": "shield_3d.png",
    "wifi": "wireless_3d.png",
    "bolt": "high_voltage_3d.png",
    "history": "clockwise_vertical_arrows_3d.png",
    "settings": "gear_3d.png",
    "info": "information_3d.png",
    "desktop": "desktop_computer_3d.png",
}
ROUTER_STATUS_ASSETS = {
    StatusState.GOOD: "good.png",
    StatusState.RETRYING: "retrying.png",
    StatusState.FAILED: "failed.png",
    StatusState.DISCONNECTED: "failed.png",
    StatusState.STANDBY: "standby.png",
    StatusState.IDLE: "standby.png",
}


class ArcSpeedMeter(tk.Canvas):
    """Semicircular Arc Gauge Bitrate Meter matching the visual mockup."""

    def __init__(
        self,
        master,
        current_speed: float = 780.0,
        threshold: float = 300.0,
        max_speed: float = 1000.0,
        width: int = 420,
        height: int = 180,
        bg: str = COLOR_CARD,
        **kwargs
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            **kwargs
        )

        self.width = width
        self.height = height
        self.current_speed = float(current_speed)
        self.threshold = float(threshold)
        self.max_speed = float(max_speed)
        self._anim = None

        self.bind("<Configure>", self._on_resize)
        self.draw()

    def _on_resize(self, event=None) -> None:
        if event and event.width > 20:
            self.width = event.width
            self.draw()

    def set_speed(self, speed: float) -> None:
        target = max(0.0, float(speed))
        if self._anim is not None:
            self._anim.cancel()
            self._anim = None
        start = self.current_speed
        if abs(target - start) < 0.5:
            self.current_speed = target
            self.draw()
            return

        def apply(t: float) -> None:
            self.current_speed = start + (target - start) * t
            self.draw()

        self._anim = animation.animate(self, apply)

    def draw(self) -> None:
        self.delete("all")

        cx = self.width / 2
        cy = self.height - 24
        r = min(self.width / 2 - 30, self.height - 50)
        thickness = 18

        # Background Track Arc (180 degrees: 180 to 0)
        self.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=0, extent=180,
            style="arc", outline=COLOR_TRACK, width=thickness
        )

        # Active Green Fill Arc
        ratio = max(0.0, min(1.0, self.current_speed / self.max_speed))
        extent_angle = ratio * 180
        if extent_angle > 0:
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=180 - extent_angle, extent=extent_angle,
                style="arc", outline=COLOR_ACCENT, width=thickness
            )

        # 300 Mbps Threshold Arrow & Marker Line
        thresh_ratio = self.threshold / self.max_speed
        thresh_angle_deg = 180 * (1.0 - thresh_ratio)
        thresh_rad = math.radians(thresh_angle_deg)

        tx_inner = cx + (r - thickness / 2 - 4) * math.cos(thresh_rad)
        ty_inner = cy - (r - thickness / 2 - 4) * math.sin(thresh_rad)
        tx_outer = cx + (r + thickness / 2 + 6) * math.cos(thresh_rad)
        ty_outer = cy - (r + thickness / 2 + 6) * math.sin(thresh_rad)

        self.create_line(tx_inner, ty_inner, tx_outer, ty_outer, fill=COLOR_TEXT_PRIMARY, width=2)

        # Arrow indicator pointing to 300 Mbps threshold
        arrow_x = cx + (r - thickness / 2 - 12) * math.cos(thresh_rad)
        arrow_y = cy - (r - thickness / 2 - 12) * math.sin(thresh_rad)
        self.create_text(arrow_x, arrow_y, text="▲", fill=COLOR_TEXT_PRIMARY, font=(FONT_UI, 9))

        # Needle Cursor Pin at current speed
        curr_angle_deg = 180 * (1.0 - ratio)
        curr_rad = math.radians(curr_angle_deg)
        nx_inner = cx + (r - thickness / 2 - 8) * math.cos(curr_rad)
        ny_inner = cy - (r - thickness / 2 - 8) * math.sin(curr_rad)
        nx_outer = cx + (r + thickness / 2 + 8) * math.cos(curr_rad)
        ny_outer = cy - (r + thickness / 2 + 8) * math.sin(curr_rad)

        self.create_line(nx_inner, ny_inner, nx_outer, ny_outer, fill=COLOR_ACCENT, width=4)

        # Center Text Block
        self.create_text(cx, cy - 48, text="Live Link Speed:", fill=COLOR_TEXT_SECONDARY, font=(FONT_UI, 9))
        self.create_text(cx, cy - 24, text=f"{self.current_speed:.0f} Mbps", fill=COLOR_TEXT_PRIMARY, font=(FONT_MONO, 16, "bold"))
        self.create_text(cx, cy - 4, text=f"Minimum Required: {int(self.threshold)} Mbps", fill=COLOR_TEXT_MUTED, font=(FONT_UI, 8))

        # Scale End Labels
        self.create_text(cx - r - 5, cy + 10, text="0", fill=COLOR_SCALE_LABEL, font=(FONT_UI, 8))
        self.create_text(cx + r + 5, cy + 10, text=f"0-{int(self.max_speed)} Mbps", fill=COLOR_SCALE_LABEL, font=(FONT_UI, 8))


# Alias for backward compatibility with tests
SegmentedSpeedBar = ArcSpeedMeter


class RoundedCard(tk.Frame):
    """Soft elevated rounded panel with custom border drawing."""

    def __init__(self, master, surface: str = COLOR_CARD, radius: int = 14, inset: int = 12, **kwargs):
        outer_bg = kwargs.pop("bg", master.cget("bg"))
        super().__init__(master, bg=outer_bg, highlightthickness=0, bd=0, **kwargs)
        self.surface = surface
        self.radius = radius
        self.inset = inset
        self._backdrop = tk.Canvas(self, bg=outer_bg, highlightthickness=0, bd=0)
        self._backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        self.content = tk.Frame(self, bg=surface, highlightthickness=0, bd=0)
        self.content.pack(fill="both", expand=True, padx=inset, pady=inset)
        self._backdrop.bind("<Configure>", self._draw_surface)

    def _draw_surface(self, event=None) -> None:
        canvas = self._backdrop
        canvas.delete("surface")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 4 or height < 4:
            return
        radius = min(self.radius, width // 2, height // 2)
        canvas.create_rectangle(radius, 0, width - radius, height, fill=COLOR_BORDER, outline="", tags="surface")
        canvas.create_rectangle(0, radius, width, height - radius, fill=COLOR_BORDER, outline="", tags="surface")
        for x, y, start in ((0, 0, 90), (width - radius * 2, 0, 0), (width - radius * 2, height - radius * 2, 270), (0, height - radius * 2, 180)):
            canvas.create_arc(x, y, x + radius * 2, y + radius * 2, start=start, extent=90, fill=COLOR_BORDER, outline="", tags="surface")
        inner = 1
        radius = max(1, radius - inner)
        canvas.create_rectangle(radius + inner, inner, width - radius - inner, height - inner, fill=self.surface, outline="", tags="surface")
        canvas.create_rectangle(inner, radius + inner, width - inner, height - radius - inner, fill=self.surface, outline="", tags="surface")
        for x, y, start in ((inner, inner, 90), (width - radius * 2 - inner, inner, 0),
                            (width - radius * 2 - inner, height - radius * 2 - inner, 270),
                            (inner, height - radius * 2 - inner, 180)):
            canvas.create_arc(x, y, x + radius * 2, y + radius * 2, start=start, extent=90, fill=self.surface, outline="", tags="surface")


class RoundedButton(tk.Canvas):
    """Compact rounded action button with hover effects and focus ring."""

    def __init__(self, master, text: str, command, bg: str, fg: str, font, image=None,
                 height: int = 38, radius: int = 10, activebackground: Optional[str] = None,
                 activeforeground: Optional[str] = None, **kwargs):
        super().__init__(master, bg=master.cget("bg"), height=height, highlightthickness=0, bd=0,
                         takefocus=1, cursor=kwargs.pop("cursor", "hand2"))
        self._text = text
        self._command = command
        self._fill = bg
        self._fg = fg
        self._font = font
        self._image = image
        self._height = height
        self._radius = radius
        self._active_fill = activebackground or bg
        self._active_fg = activeforeground or fg
        self._state = "normal"
        self._hovered = False
        self._focused = False
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", self._on_click)
        self.bind("<space>", self._on_click)

    def _on_focus_in(self, _event=None) -> None:
        self._focused = True
        self._draw()

    def _on_focus_out(self, _event=None) -> None:
        self._focused = False
        self._draw()

    def _on_enter(self, _event=None) -> None:
        if self._state == "normal":
            self._hovered = True
            self._draw()

    def _on_leave(self, _event=None) -> None:
        self._hovered = False
        self._draw()

    def _on_click(self, _event=None) -> None:
        if self._state == "normal" and self._command:
            self.focus_set()
            self._command()

    def _draw(self) -> None:
        self.delete("all")
        width = max(1, self.winfo_width())
        height = self._height
        fill = COLOR_BORDER if self._state == "disabled" else (self._active_fill if self._hovered else self._fill)
        fg = COLOR_TEXT_MUTED if self._state == "disabled" else (self._active_fg if self._hovered else self._fg)
        radius = min(self._radius, height // 2, width // 2)
        self.create_arc(1, 1, radius * 2 + 1, radius * 2 + 1, start=90, extent=90, fill=fill, outline="")
        self.create_arc(width - radius * 2 - 1, 1, width - 1, radius * 2 + 1, start=0, extent=90, fill=fill, outline="")
        self.create_arc(width - radius * 2 - 1, height - radius * 2 - 1, width - 1, height - 1, start=270, extent=90, fill=fill, outline="")
        self.create_arc(1, height - radius * 2 - 1, radius * 2 + 1, height - 1, start=180, extent=90, fill=fill, outline="")
        self.create_rectangle(radius + 1, 1, width - radius - 1, height - 1, fill=fill, outline="")
        self.create_rectangle(1, radius + 1, width - 1, height - radius - 1, fill=fill, outline="")
        text_font = tkfont.Font(font=self._font)
        image_width = self._image.width() if self._image else 0
        gap = 7 if image_width else 0
        group_width = image_width + gap + text_font.measure(self._text)
        start_x = (width - group_width) // 2
        if self._image:
            self.create_image(start_x + image_width // 2, height // 2, image=self._image)
        self.create_text(start_x + image_width + gap, height // 2, anchor="w", text=self._text, fill=fg, font=self._font)
        if self._focused and self._state == "normal":
            self._draw_focus_ring(width, height, radius)

    def _draw_focus_ring(self, width: int, height: int, radius: int) -> None:
        pad = 3
        x0, y0, x1, y1 = pad, pad, width - pad - 1, height - pad - 1
        r = max(0, min(radius, (y1 - y0) // 2, (x1 - x0) // 2))
        ring = COLOR_FOCUS_RING
        self.create_arc(x0, y0, x0 + 2 * r, y0 + 2 * r, start=90, extent=90, style="arc", outline=ring, width=2)
        self.create_arc(x1 - 2 * r, y0, x1, y0 + 2 * r, start=0, extent=90, style="arc", outline=ring, width=2)
        self.create_arc(x1 - 2 * r, y1 - 2 * r, x1, y1, start=270, extent=90, style="arc", outline=ring, width=2)
        self.create_arc(x0, y1 - 2 * r, x0 + 2 * r, y1, start=180, extent=90, style="arc", outline=ring, width=2)
        self.create_line(x0 + r, y0, x1 - r, y0, fill=ring, width=2)
        self.create_line(x0 + r, y1, x1 - r, y1, fill=ring, width=2)
        self.create_line(x0, y0 + r, x0, y1 - r, fill=ring, width=2)
        self.create_line(x1, y0 + r, x1, y1 - r, fill=ring, width=2)

    def config(self, cnf=None, **kwargs):
        options = dict(cnf or {})
        options.update(kwargs)
        self._text = options.pop("text", self._text)
        self._command = options.pop("command", self._command)
        self._fill = options.pop("bg", self._fill)
        self._fg = options.pop("fg", self._fg)
        self._image = options.pop("image", self._image)
        self._state = options.pop("state", self._state)
        self._active_fill = options.pop("activebackground", self._active_fill)
        self._active_fg = options.pop("activeforeground", self._active_fg)
        if options:
            super().config(**options)
        self._draw()

    configure = config


class WifiACGuardianWinUI(tk.Tk):
    """Commercial Product UI for WiFi AC Guardian matching the approved visual mockup."""

    def __init__(self, config: Optional[GuardianConfig] = None, guardian: Optional[WifiACGuardianWin] = None):
        super().__init__()
        self.withdraw()  # Hide window to prevent initial flicker

        self.single_instance = SingleInstanceChecker()
        if not self.single_instance.try_claim_single_instance(on_show_requested=lambda: self.after(0, self.show_from_tray)):
            self.destroy()
            sys.exit(0)

        self.title("WiFi AC Guardian")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = min(900, max(820, int(screen_width * 0.72)))
        window_height = min(720, max(680, int(screen_height * 0.72)))
        window_x = max(0, (screen_width - window_width) // 2)
        window_y = max(20, (screen_height - window_height) // 2)

        self.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
        self.resizable(True, True)
        self.minsize(820, 640)
        self.configure(bg=COLOR_BG)

        self.config = config or load_config()
        self.guardian = guardian or WifiACGuardianWin(config=self.config)
        self.detector = self.guardian.detector
        self.reconnector = self.guardian.reconnector
        self._fluent_images = {}
        self._router_status_images = {}
        self._start_time = time.time()

        animation.set_enabled(self.config.animations_enabled)
        self._prev_hero_accent = None
        self._hero_anim = None

        if self.guardian.tray_app:
            self.guardian.tray_app.on_open_ui_click = lambda: self.after(0, self.show_from_tray)
            self.guardian.tray_app.on_quit_click = lambda: self.after(0, self.quit_app)
            self.guardian.tray_app.on_stop_protection_click = lambda: self.after(0, self._on_protection_toggle)

        if not self.guardian.state.running:
            self.guardian.start_background()

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.bind("<Unmap>", self._on_unmap)

        self._configure_ttk_styles()
        self._build_ui()
        self._refresh_status()
        if not self.config.start_minimized:
            self.deiconify()

    def _configure_ttk_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground=COLOR_PANEL,
            background=COLOR_PANEL,
            foreground=COLOR_TEXT_PRIMARY,
            bordercolor=COLOR_BORDER,
            darkcolor=COLOR_CARD,
            lightcolor=COLOR_CARD,
            arrowcolor=COLOR_TEXT_SECONDARY
        )
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_PANEL)])

    def hide_to_tray(self) -> None:
        self.withdraw()

    def _on_unmap(self, event=None) -> None:
        if self.state() == "iconic":
            self.withdraw()

    def show_from_tray(self) -> None:
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()

    def quit_app(self) -> None:
        try:
            self.single_instance.stop()
        except Exception:
            pass
        try:
            self.guardian.stop()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)

    def _build_ui(self) -> None:
        """Build the product layout matching the visual mockup."""
        # Top Header Bar
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=28, pady=(16, 12))
        self._fluent_icon(header, "app", 36, COLOR_BG).pack(side="left", padx=(0, 10))
        title_block = tk.Frame(header, bg=COLOR_BG)
        title_block.pack(side="left")
        tk.Label(title_block, text="WiFi AC Guardian", font=(FONT_DISPLAY, 16, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG).pack(anchor="w")

        # Main Scrollable Host Container
        content_host = tk.Frame(self, bg=COLOR_BG)
        content_host.pack(fill="both", expand=True, padx=0, pady=(0, 10))

        content_canvas = tk.Canvas(content_host, bg=COLOR_BG, highlightthickness=0, bd=0)
        content_scroll = ttk.Scrollbar(content_host, orient="vertical", command=content_canvas.yview)
        content_canvas.configure(yscrollcommand=content_scroll.set)
        content_canvas.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")

        main_box = tk.Frame(content_canvas, bg=COLOR_BG)
        content_window = content_canvas.create_window((24, 0), window=main_box, anchor="nw")

        def update_scroll_region(_event=None):
            content_canvas.configure(scrollregion=content_canvas.bbox("all"))

        def fit_content_width(event):
            max_content_width = 920
            content_width = min(max_content_width, max(1, event.width - 48))
            content_canvas.coords(content_window, max(24, (event.width - content_width) // 2), 0)
            content_canvas.itemconfigure(content_window, width=content_width)

        main_box.bind("<Configure>", update_scroll_region)
        content_canvas.bind("<Configure>", fit_content_width)
        content_canvas.bind_all("<MouseWheel>", lambda event: content_canvas.yview_scroll(-int(event.delta / 120), "units"))

        # --- 1. TOP HERO BANNER CARD (Identical to Mockup) ---
        hero_shell = RoundedCard(main_box, surface=COLOR_CARD, radius=16, inset=18)
        hero_shell.pack(fill="x", pady=(0, 14))
        hero_card = hero_shell.content

        hero_row = tk.Frame(hero_card, bg=COLOR_CARD)
        hero_row.pack(fill="x", pady=6)

        # Left 3D Router Image with green status LED base
        self.lbl_status_icon = tk.Label(
            hero_row, image=self._router_status_image(StatusState.IDLE, 110),
            bg=COLOR_CARD, bd=0, highlightthickness=0
        )
        self.lbl_status_icon.pack(side="left", padx=(12, 24))

        hero_text_box = tk.Frame(hero_row, bg=COLOR_CARD)
        hero_text_box.pack(side="left", fill="both", expand=True, pady=4)

        from wifi_ac_guardian_win.status_presentation import get_presentation
        idle_desc = get_presentation(StatusState.IDLE, target_ssid=self.config.target_ssid)

        head_row = tk.Frame(hero_text_box, bg=COLOR_CARD)
        head_row.pack(anchor="w", pady=(0, 4))

        self.lbl_hero_state = tk.Label(
            head_row, text=idle_desc.headline, font=(FONT_DISPLAY, 18, "bold"),
            fg=COLOR_ACCENT, bg=COLOR_CARD
        )
        self.lbl_hero_state.pack(side="left")

        # Green Checkmark Badge
        self.lbl_hero_badge = tk.Label(
            head_row, text=" ✔", font=(FONT_DISPLAY, 14, "bold"),
            fg=COLOR_ACCENT, bg=COLOR_CARD
        )
        self.lbl_hero_badge.pack(side="left", padx=(6, 0))

        # Green Dot + Status Glow Text
        sub_glow_row = tk.Frame(hero_text_box, bg=COLOR_CARD)
        sub_glow_row.pack(anchor="w", pady=(0, 2))

        self.lbl_glow_dot = tk.Label(
            sub_glow_row, text="●", font=(FONT_UI, 10),
            fg=COLOR_ACCENT, bg=COLOR_CARD
        )
        self.lbl_glow_dot.pack(side="left", padx=(0, 6))

        self.lbl_target_info = tk.Label(
            sub_glow_row, text="Subtle status glow", font=(FONT_UI, 9),
            fg=COLOR_TEXT_MUTED, bg=COLOR_CARD
        )
        self.lbl_target_info.pack(side="left")

        # --- 2. METRIC CARDS STRIP (4 KPI Cards Matching Mockup) ---
        kpi_strip = tk.Frame(main_box, bg=COLOR_BG)
        kpi_strip.pack(fill="x", pady=(0, 14))

        self.kpi_labels = {}
        self.kpi_sub_labels = {}

        metrics_config = [
            ("status", "shield", "Status", StatusState.IDLE.value.capitalize(), "1 hr 12 m uptime"),
            ("retry", "history", "Reconnect Attempts", "0", "Last 24 hours"),
            ("tx", "bolt", "Upload Link Speed", "— Mbps", "5.0 GHz / Ch 48"),
            ("rx", "wifi", "Download Link Speed", "— Mbps", "TX Rate: — Mbps"),
        ]

        for key, icon, title, value, subtext in metrics_config:
            card_shell = RoundedCard(kpi_strip, surface=COLOR_CARD, radius=12, inset=12)
            card_shell.pack(side="left", fill="both", expand=True, padx=4)
            card = card_shell.content

            kpi_top = tk.Frame(card, bg=COLOR_CARD)
            kpi_top.pack(anchor="w")

            if key == "status":
                self.kpi_status_icon = tk.Label(
                    kpi_top, image=self._router_status_image(StatusState.GOOD, 24),
                    bg=COLOR_CARD, bd=0, highlightthickness=0
                )
                self.kpi_status_icon.pack(side="left", padx=(0, 6))
            else:
                self._fluent_icon(kpi_top, icon, 24, COLOR_CARD).pack(side="left", padx=(0, 6))

            title_box = tk.Frame(kpi_top, bg=COLOR_CARD)
            title_box.pack(side="left")

            tk.Label(title_box, text=title, font=(FONT_UI, 8),
                     fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(anchor="w")

            v_fg = COLOR_ACCENT if key == "status" else COLOR_TEXT_PRIMARY
            value_label = tk.Label(card, text=value, font=(FONT_MONO, 12, "bold"),
                                   fg=v_fg, bg=COLOR_CARD)
            value_label.pack(anchor="w", pady=(4, 0))
            self.kpi_labels[key] = value_label

            sub_label = tk.Label(card, text=subtext, font=(FONT_UI, 8),
                                 fg=COLOR_TEXT_MUTED, bg=COLOR_CARD)
            sub_label.pack(anchor="w", pady=(2, 0))
            self.kpi_sub_labels[key] = sub_label

        # --- 3. MIDDLE ROW (Connection Card & Protection Engine Matching Mockup) ---
        middle_row = tk.Frame(main_box, bg=COLOR_BG)
        middle_row.pack(fill="x", pady=(0, 14))

        # Left Card: Connection Card with Arc Speed Meter
        left_shell = RoundedCard(middle_row, surface=COLOR_CARD, radius=15, inset=16)
        left_shell.pack(side="left", fill="both", expand=True, padx=(0, 7))
        left_card = left_shell.content

        conn_hdr = tk.Frame(left_card, bg=COLOR_CARD)
        conn_hdr.pack(fill="x")
        tk.Label(conn_hdr, text="Connection Card", font=(FONT_UI, 11, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(side="left")
        tk.Label(conn_hdr, text="•••", font=(FONT_UI, 10, "bold"),
                 fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(side="right")

        # Arc Speed Meter Gauge
        self.speed_bar = ArcSpeedMeter(left_card, current_speed=0.0, threshold=300.0,
                                       max_speed=1000.0, height=170, bg=COLOR_CARD)
        self.speed_bar.pack(fill="both", expand=True, pady=(10, 0))

        # Right Card: Protection Engine Panel
        right_shell = RoundedCard(middle_row, surface=COLOR_CARD, radius=15, inset=16)
        right_shell.pack(side="right", fill="both", expand=True, padx=(7, 0))
        right_card = right_shell.content

        tk.Label(right_card, text="Protection Engine", font=(FONT_UI, 11, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(anchor="w", pady=(0, 10))

        # Toggle Row 1: Connection Monitoring Active
        row1_panel = RoundedCard(right_card, surface=COLOR_PANEL, radius=10, inset=10, bg=COLOR_CARD)
        row1_panel.pack(fill="x", pady=4)
        r1_box = row1_panel.content
        tk.Label(r1_box, text="Connection Monitoring", font=(FONT_UI, 9), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL).pack(side="left")
        self.lbl_toggle_monitoring = tk.Label(r1_box, text="Active  ●", font=(FONT_UI, 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL)
        self.lbl_toggle_monitoring.pack(side="right")

        # Toggle Row 2: Low Speed Recovery Active
        row2_panel = RoundedCard(right_card, surface=COLOR_PANEL, radius=10, inset=10, bg=COLOR_CARD)
        row2_panel.pack(fill="x", pady=4)
        r2_box = row2_panel.content
        tk.Label(r2_box, text="Low Speed Recovery", font=(FONT_UI, 9), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL).pack(side="left")
        self.lbl_toggle_recovery = tk.Label(r2_box, text="Active  ●", font=(FONT_UI, 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL)
        self.lbl_toggle_recovery.pack(side="right")

        # Toggle Row 3: Current Network SSID Pill
        row3_panel = RoundedCard(right_card, surface=COLOR_PANEL, radius=10, inset=10, bg=COLOR_CARD)
        row3_panel.pack(fill="x", pady=4)
        r3_box = row3_panel.content
        self.lbl_network_ssid = tk.Label(r3_box, text=f"Current Network: {self.config.target_ssid} (SSID)",
                                         font=(FONT_UI, 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL)
        self.lbl_network_ssid.pack(anchor="w")

        # Action Buttons inside Protection Engine Card
        self.btn_reconnect = RoundedButton(
            right_card, text="Reconnect now", command=self._on_reconnect_click,
            bg=COLOR_ACCENT, fg=COLOR_ON_ACCENT, activebackground=COLOR_ACCENT_HOVER,
            activeforeground=COLOR_ON_ACCENT, font=(FONT_UI, 9, "bold"),
            image=self._fluent_image("history", 20), height=38
        )
        self.btn_reconnect.pack(fill="x", pady=(10, 0))

        self.btn_protection = RoundedButton(
            right_card, text="Stop protection", command=self._on_protection_toggle,
            bg=COLOR_ERROR, fg=COLOR_ON_ERROR, activebackground=COLOR_ERROR_HOVER,
            activeforeground=COLOR_ON_ERROR, font=(FONT_UI, 9, "bold"),
            image=self._fluent_image("shield", 20), height=38
        )
        self.btn_protection.pack(fill="x", pady=(6, 0))

        # --- 4. BOTTOM ACTION BAR (Floating Pill Toolbar Matching Mockup) ---
        toolbar_shell = RoundedCard(self, surface=COLOR_PANEL, radius=20, inset=6, bg=COLOR_BG)
        toolbar_shell.pack(side="bottom", pady=(0, 14))
        toolbar = toolbar_shell.content

        for name, icon, label, cmd in [
            ("settings", "settings", "Settings", self._open_settings_dialog),
            ("log", "desktop", "View Logs", self._open_log_file),
            ("info", "info", "About", self._open_about_dialog)
        ]:
            btn = RoundedButton(
                toolbar, text=label, command=cmd, bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY,
                activebackground=COLOR_PANEL_HOVER, activeforeground=COLOR_TEXT_PRIMARY,
                font=(FONT_UI, 9), image=self._fluent_image(icon, 18), height=32, radius=14
            )
            btn.pack(side="left", padx=4)

    def _fluent_image(self, name: str, size: int):
        cache_key = (name, size)
        if cache_key not in self._fluent_images:
            source = os.path.join(FLUENT_ASSET_DIR, FLUENT_ASSETS[name])
            image = Image.open(source).convert("RGBA")
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
            self._fluent_images[cache_key] = ImageTk.PhotoImage(canvas)
        return self._fluent_images[cache_key]

    def _router_status_image(self, state: StatusState, size: int):
        cache_key = (state, size)
        if cache_key not in self._router_status_images:
            source = os.path.join(os.path.dirname(__file__), "assets", "router_status", ROUTER_STATUS_ASSETS[state])
            image = Image.open(source).convert("RGBA")
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
            self._router_status_images[cache_key] = ImageTk.PhotoImage(canvas)
        return self._router_status_images[cache_key]

    def _set_router_status(self, state: StatusState) -> None:
        self.lbl_status_icon.configure(image=self._router_status_image(state, 110))
        self.kpi_status_icon.configure(image=self._router_status_image(state, 24))

    def _fluent_icon(self, parent, name: str, size: int, bg: str):
        return tk.Label(parent, image=self._fluent_image(name, size), bg=bg, bd=0, highlightthickness=0)

    def add_event_log(self, icon_type: str, message: str) -> None:
        logger.info(message)

    def _open_settings_dialog(self) -> None:
        """Settings Window."""
        win = tk.Toplevel(self)
        win.title("WiFi AC Guardian — Settings")
        win.geometry("640x520")
        win.configure(bg=COLOR_CARD)
        win.transient(self)
        win.grab_set()

        sidebar = tk.Frame(win, bg=COLOR_PANEL, width=160)
        sidebar.pack(side="left", fill="y")

        main_settings = tk.Frame(win, bg=COLOR_CARD)
        main_settings.pack(side="right", fill="both", expand=True, padx=20, pady=16)

        tk.Label(sidebar, text="SETTINGS", font=(FONT_UI, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(anchor="w", padx=16, pady=(18, 12))

        lbl_t = tk.Label(main_settings, text="Primary Network & Protection Preferences", font=(FONT_UI, 13, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
        lbl_t.pack(anchor="w", pady=(0, 8))

        lbl_desc = tk.Label(
            main_settings,
            text="Configure your target Wi-Fi network (e.g. lab5g), interval timings, autostart, and animation settings:",
            font=(FONT_UI, 9),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD,
            wraplength=420,
            justify="left"
        )
        lbl_desc.pack(anchor="w", pady=(0, 12))

        row_ssid = tk.Frame(main_settings, bg=COLOR_CARD)
        row_ssid.pack(fill="x", pady=6)
        tk.Label(row_ssid, text="Target SSID:", font=(FONT_UI, 9, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(side="left", padx=(0, 8))

        var_ssid = tk.StringVar(value=self.config.target_ssid or "lab5g")
        combo = ttk.Combobox(row_ssid, textvariable=var_ssid, font=(FONT_MONO, 10))
        combo.pack(side="left", fill="x", expand=True)

        ssids = self.detector.get_available_ssids()
        combo.configure(values=sorted(list(set([s for s in ssids if s] + [self.config.target_ssid or "lab5g"]))))

        settings_grid = tk.Frame(main_settings, bg=COLOR_CARD)
        settings_grid.pack(fill="x", pady=(12, 8))
        setting_vars = {}
        for row, (label, key, value) in enumerate([
            ("Check interval (sec)", "check_interval", self.config.check_interval),
            ("Reconnect delay (sec)", "reconnect_delay", self.config.reconnect_delay),
            ("Max attempts", "max_attempts", self.config.max_attempts),
        ]):
            tk.Label(settings_grid, text=label, font=(FONT_UI, 9), fg=COLOR_TEXT_SECONDARY,
                     bg=COLOR_CARD).grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(value))
            setting_vars[key] = var
            tk.Entry(settings_grid, textvariable=var, width=10, justify="right",
                     font=(FONT_MONO, 9), bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY,
                     insertbackground=COLOR_TEXT_PRIMARY, relief="flat",
                     highlightthickness=1, highlightbackground=COLOR_BORDER).grid(
                         row=row, column=1, sticky="e", padx=(12, 0), pady=4)
        settings_grid.columnconfigure(0, weight=1)

        var_auto_switch = tk.BooleanVar(value=self.config.auto_switch_primary)
        chk_switch = tk.Checkbutton(
            main_settings, text="Automatically return to Primary Network when back online",
            variable=var_auto_switch, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_PANEL, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT_PRIMARY,
            font=(FONT_UI, 9)
        )
        chk_switch.pack(anchor="w", pady=4)

        var_auto_start = tk.BooleanVar(value=self.config.auto_start)
        chk_start = tk.Checkbutton(
            main_settings, text="Start WiFi AC Guardian when Windows starts",
            variable=var_auto_start, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_PANEL, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT_PRIMARY,
            font=(FONT_UI, 9)
        )
        chk_start.pack(anchor="w", pady=4)

        var_start_minimized = tk.BooleanVar(value=self.config.start_minimized)
        chk_minimized = tk.Checkbutton(
            main_settings, text="Start minimized in system tray",
            variable=var_start_minimized, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_PANEL, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT_PRIMARY,
            font=(FONT_UI, 9)
        )
        chk_minimized.pack(anchor="w", pady=4)

        var_notifications = tk.BooleanVar(value=self.config.enable_notifications)
        chk_notifications = tk.Checkbutton(
            main_settings, text="Enable Windows Toast Notifications",
            variable=var_notifications, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_PANEL, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT_PRIMARY,
            font=(FONT_UI, 9)
        )
        chk_notifications.pack(anchor="w", pady=4)

        var_animations = tk.BooleanVar(value=self.config.animations_enabled)
        chk_animations = tk.Checkbutton(
            main_settings, text="Enable micro-animations (experimental)",
            variable=var_animations, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_PANEL, activebackground=COLOR_CARD, activeforeground=COLOR_TEXT_PRIMARY,
            font=(FONT_UI, 9)
        )
        chk_animations.pack(anchor="w", pady=4)

        def save_and_close():
            new_target = var_ssid.get().strip() or "lab5g"
            self.config.target_ssid = new_target
            self.config.auto_switch_primary = var_auto_switch.get()
            self.config.auto_start = var_auto_start.get()
            self.config.start_minimized = var_start_minimized.get()
            self.config.enable_notifications = var_notifications.get()
            self.config.animations_enabled = var_animations.get()
            animation.set_enabled(self.config.animations_enabled)

            try:
                self.config.check_interval = max(2.0, min(120.0, float(setting_vars["check_interval"].get())))
                self.config.reconnect_delay = max(1.0, min(60.0, float(setting_vars["reconnect_delay"].get())))
                self.config.max_attempts = max(0, min(999, int(setting_vars["max_attempts"].get())))
            except ValueError:
                messagebox.showerror("Invalid settings", "Use numeric values for timing and retry settings.", parent=win)
                return

            save_config(self.config)
            if self.guardian:
                self.guardian.config.target_ssid = new_target
                self.guardian.config.auto_switch_primary = self.config.auto_switch_primary
                self.guardian.config.auto_start = self.config.auto_start
                self.guardian.config.start_minimized = self.config.start_minimized
                self.guardian.config.enable_notifications = self.config.enable_notifications
                self.guardian.config.check_interval = self.config.check_interval
                self.guardian.config.reconnect_delay = self.config.reconnect_delay
                self.guardian.config.max_attempts = self.config.max_attempts

            win.destroy()
            messagebox.showinfo("Settings Saved", f"Successfully saved primary network '{new_target}' & autostart preferences.")

        btn_save = tk.Button(
            main_settings, text="Save settings", command=save_and_close,
            bg=COLOR_ACCENT, fg=COLOR_ON_ACCENT, font=(FONT_UI, 10, "bold"),
            pady=6, bd=0, cursor="hand2"
        )
        btn_save.pack(fill="x", pady=(16, 0))

    def _open_log_file(self) -> None:
        log_path = self.config.log_file_path
        if os.path.exists(log_path):
            try:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.Popen(["notepad.exe", log_path], creationflags=flags)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open log file: {e}")
        else:
            messagebox.showinfo("Log File", f"Log file not created yet: {log_path}")

    def _open_about_dialog(self) -> None:
        win = tk.Toplevel(self)
        win.title("About WiFi AC Guardian")
        win.geometry("480x360")
        win.configure(bg=COLOR_CARD)
        win.transient(self)
        win.grab_set()

        header = tk.Frame(win, bg=COLOR_CARD)
        header.pack(fill="x", padx=24, pady=(20, 12))
        self._fluent_icon(header, "app", 48, COLOR_CARD).pack(side="left", padx=(0, 12))
        title_block = tk.Frame(header, bg=COLOR_CARD)
        title_block.pack(side="left")
        tk.Label(title_block, text="WiFi AC Guardian", font=(FONT_DISPLAY, 16, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(anchor="w")
        tk.Label(title_block, text="v1.1.0 Commercial Edition", font=(FONT_UI, 9), fg=COLOR_ACCENT, bg=COLOR_CARD).pack(anchor="w")

        desc_card = RoundedCard(win, surface=COLOR_PANEL, radius=12, inset=12, bg=COLOR_CARD)
        desc_card.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        c = desc_card.content

        tk.Label(c, text="Created by Zohaib Javed", font=(FONT_UI, 10, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_PANEL).pack(anchor="w", pady=(0, 4))
        tk.Label(
            c,
            text="WiFi AC Guardian is a high-speed Wi-Fi 5+ protection service designed for Windows 11 & Ubuntu 26.04 LTS.\n\n"
                 "It continuously monitors radio link sync rates (>300 Mbps) and automatically performs hardware resets whenever link quality drops.",
            font=(FONT_UI, 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_PANEL, wraplength=400, justify="left"
        ).pack(anchor="w")

        tk.Button(win, text="Close", command=win.destroy, bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY, font=(FONT_UI, 9, "bold"), pady=4, bd=0).pack(fill="x", padx=24, pady=(0, 16))

    def _on_reconnect_click(self) -> None:
        def worker():
            link = self.detector.get_link_info()
            target = self.config.target_ssid or "lab5g"
            if self.guardian.state.status == StatusState.STANDBY:
                logger.info(f"User requested switch to primary network '{target}'...")
                self.add_event_log("yellow", f"Switching to Primary Network '{target}'...")
                self.reconnector._connect_interface(link.interface, target)
            else:
                self.add_event_log("yellow", f"Forcing hardware radio reset on interface '{link.interface}'...")
                self.reconnector.trigger_reconnect(link.interface, ssid=target)

        threading.Thread(target=worker, daemon=True).start()

    def _on_protection_toggle(self) -> None:
        if self.guardian.state.running:
            self.guardian.stop_protection()
            self.guardian.state.status = StatusState.IDLE
        else:
            self.guardian.start_protection()
        if self.guardian.tray_app:
            self.guardian.tray_app.set_protection_running(self.guardian.state.running)
        self._update_ui(self.guardian.state.current_link or LinkInfo(connected=False, interface="Wi-Fi"))

    def _refresh_status(self) -> None:
        def worker():
            link = self.detector.get_link_info()
            self.after(0, self._update_ui, link)

        threading.Thread(target=worker, daemon=True).start()
        self.after(2000, self._refresh_status)

    def _set_hero_headline(self, text: str, accent: str) -> None:
        self.lbl_hero_state.config(text=text, bg=COLOR_CARD)
        prev = self._prev_hero_accent
        self._prev_hero_accent = accent
        if self._hero_anim is not None:
            self._hero_anim.cancel()
            self._hero_anim = None
        if prev and prev != accent:
            self._hero_anim = animation.animate(
                self.lbl_hero_state,
                lambda t: self.lbl_hero_state.config(fg=animation.lerp_color(prev, accent, t)),
            )
        else:
            self.lbl_hero_state.config(fg=accent)

    def _update_ui(self, link: LinkInfo) -> None:
        target = self.config.target_ssid or "lab5g"

        # Calculate session uptime
        elapsed_sec = int(time.time() - self._start_time)
        hrs = elapsed_sec // 3600
        mins = (elapsed_sec % 3600) // 60
        uptime_str = f"{hrs} hr {mins} m uptime" if hrs > 0 else f"{mins} m uptime"

        if not self.guardian.state.running:
            self._set_router_status(StatusState.IDLE)
            self._set_hero_headline("PROTECTION STOPPED", COLOR_TEXT_MUTED)
            self.lbl_target_info.config(text="Click Start Protection to resume background monitoring.")
            self.lbl_hero_badge.config(text="", fg=COLOR_TEXT_MUTED)
            self.lbl_glow_dot.config(fg=COLOR_TEXT_MUTED)

            self.kpi_labels["status"].config(text="Stopped", fg=COLOR_TEXT_MUTED)
            self.kpi_sub_labels["status"].config(text=uptime_str)
            self.kpi_labels["retry"].config(text="0", fg=COLOR_TEXT_MUTED)
            self.kpi_sub_labels["retry"].config(text="Last 24 hours")
            self.kpi_labels["tx"].config(text="— Mbps", fg=COLOR_TEXT_MUTED)
            self.kpi_sub_labels["tx"].config(text="5.0 GHz / Ch --")
            self.kpi_labels["rx"].config(text="— Mbps", fg=COLOR_TEXT_MUTED)
            self.kpi_sub_labels["rx"].config(text="TX Rate: — Mbps")

            self.lbl_toggle_monitoring.config(text="Paused  ○", fg=COLOR_TEXT_MUTED)
            self.lbl_toggle_recovery.config(text="Paused  ○", fg=COLOR_TEXT_MUTED)
            self.lbl_network_ssid.config(text=f"Current Network: {target} (SSID)")

            self.speed_bar.set_speed(0.0)
            self._sync_protection_controls()
            return

        self._sync_protection_controls()
        state = self.guardian.state.status if self.guardian else StatusState.IDLE

        from wifi_ac_guardian_win.status_presentation import get_presentation
        desc = get_presentation(state, target_ssid=target)

        self._set_router_status(state)
        self._set_hero_headline(desc.headline, desc.accent)
        self.lbl_hero_badge.config(text=" ✔" if state == StatusState.GOOD else "", fg=desc.accent)
        self.lbl_glow_dot.config(fg=desc.accent)

        self.lbl_target_info.config(text=desc_supporting_text(desc, target))

        bitrate_val = link.max_bitrate_mbps if link and link.connected else 0.0
        bitrate_txt = f"{bitrate_val:.0f} Mbps" if bitrate_val > 0 else "0 Mbps"

        # Update KPI Cards to match mockup
        self.kpi_labels["status"].config(text=state.value.capitalize() if state == StatusState.GOOD else state.value, fg=desc.accent)
        self.kpi_sub_labels["status"].config(text=uptime_str)

        self.kpi_labels["retry"].config(text=str(self.guardian.state.attempts_count), fg=COLOR_TEXT_PRIMARY)
        self.kpi_sub_labels["retry"].config(text="Last 24 hours")

        tx_txt = f"{float(link.tx_bitrate.split()[0]):.0f} Mbps" if link and link.tx_bitrate and link.tx_bitrate.split()[0].replace('.','',1).isdigit() else (bitrate_txt if link.connected else "0 Mbps")
        rx_txt = f"{float(link.rx_bitrate.split()[0]):.0f} Mbps" if link and link.rx_bitrate and link.rx_bitrate.split()[0].replace('.','',1).isdigit() else (bitrate_txt if link.connected else "0 Mbps")

        self.kpi_labels["tx"].config(text=tx_txt, fg=COLOR_TEXT_PRIMARY)
        band_ch = f"5.0 GHz / Ch {link.channel}" if link and link.channel else "5.0 GHz / Ch 48"
        self.kpi_sub_labels["tx"].config(text=band_ch)

        self.kpi_labels["rx"].config(text=rx_txt, fg=COLOR_TEXT_PRIMARY)
        self.kpi_sub_labels["rx"].config(text=f"TX Rate: {tx_txt}")

        # Update Protection Engine Card
        self.lbl_toggle_monitoring.config(text="Active  ●", fg=COLOR_ACCENT)
        self.lbl_toggle_recovery.config(text="Active  ●", fg=COLOR_ACCENT)
        self.lbl_network_ssid.config(text=f"Current Network: {link.ssid or target} (SSID)")

        self.speed_bar.set_speed(bitrate_val)

        # Button Styling
        if state == StatusState.GOOD:
            self.btn_reconnect.config(text=desc.action_label, bg=COLOR_ACCENT, fg=theme.ON_ACCENT)
        elif state == StatusState.RETRYING:
            self.btn_reconnect.config(text=desc.action_label, bg=COLOR_WARN, fg=theme.ON_WARN)
        elif state == StatusState.FAILED:
            self.btn_reconnect.config(text=desc.action_label, bg=COLOR_ERROR, fg=theme.ON_ERROR)
        elif state == StatusState.STANDBY:
            if self.guardian and self.guardian.state.primary_available:
                self.btn_reconnect.config(text=desc.action_label, bg=COLOR_ACCENT, fg=theme.ON_ACCENT)
            else:
                self.btn_reconnect.config(text=desc.action_label, bg=COLOR_INFO, fg=theme.ON_ERROR)
        else:
            self.btn_reconnect.config(text=desc.action_label, bg=COLOR_ERROR, fg=theme.ON_ERROR)

    def _sync_protection_controls(self) -> None:
        if self.guardian.tray_app:
            self.guardian.tray_app.set_protection_running(self.guardian.state.running)
        if self.guardian.state.running:
            self.btn_protection.config(
                text="Stop protection", bg=COLOR_ERROR, fg=COLOR_ON_ERROR,
                activebackground=COLOR_ERROR_HOVER, activeforeground=COLOR_ON_ERROR
            )
            self.btn_reconnect.config(state="normal")
        else:
            self.btn_protection.config(text="Start protection", bg=COLOR_ACCENT, fg=COLOR_ON_ACCENT, activebackground=COLOR_ACCENT_HOVER)
            self.btn_reconnect.config(state="disabled")


def desc_supporting_text(desc, target_ssid: str) -> str:
    """Helper to convert descriptor supporting text to clean user string."""
    return desc.supporting.replace("{target_ssid}", target_ssid)


def launch_gui_win(config: Optional[GuardianConfig] = None, guardian: Optional[WifiACGuardianWin] = None) -> None:
    app = WifiACGuardianWinUI(config=config, guardian=guardian)
    app.mainloop()


if __name__ == "__main__":
    launch_gui_win()
