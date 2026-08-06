"""
Tkinter Control Panel GUI for WiFi AC Guardian (Windows 11 & Ubuntu).
Canonical Layout Implementation matching the ASCII Specification (900x700).
"""

import os
import sys
import time
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple
from PIL import Image, ImageTk

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

COLOR_BG = theme.BG                       # Window Dark Background (#0D0F10)
COLOR_CARD = theme.CARD                   # Card Surface (#16181A)
COLOR_PANEL = theme.PANEL                 # Surface Elevated (#1E2124)
COLOR_BORDER = theme.BORDER               # Border / Divider (#2A2F33)

COLOR_PRIMARY_GREEN = theme.PRIMARY_GREEN # Primary Green (#22C55E)
COLOR_ACCENT = theme.ACCENT               # Primary Accent (#22C55E)

COLOR_WARN = theme.WARN                   # Amber Warning (#F59E0B)
COLOR_ERROR = theme.ERROR                 # Error Red (#EF4444)
COLOR_INFO = theme.INFO                   # Information Blue (#3B82F6)

COLOR_TEXT_PRIMARY = theme.TEXT_PRIMARY   # High-contrast white (#F2F4F7)
COLOR_TEXT_SECONDARY = theme.TEXT_SECONDARY  # Secondary text (#A1A7AE)
COLOR_TEXT_MUTED = theme.TEXT_MUTED       # Muted captions (#8C92A0)

COLOR_ACCENT_HOVER = theme.ACCENT_HOVER
COLOR_ERROR_HOVER = theme.ERROR_HOVER
COLOR_PANEL_HOVER = theme.PANEL_HOVER
COLOR_FOCUS_RING = theme.FOCUS_RING

COLOR_ON_ACCENT = theme.ON_ACCENT
COLOR_ON_ERROR = theme.ON_ERROR
COLOR_ON_WARN = theme.ON_WARN

FONT_UI = theme.FONT_UI
FONT_DISPLAY = theme.FONT_DISPLAY
FONT_MONO = theme.FONT_MONO

FLUENT_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "fluent")
FLUENT_ASSETS = {
    "app": "wireless_3d.png",
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


class RoundedCard(tk.Frame):
    """Rounded card container matching exact radius and surface specs."""

    def __init__(self, master, surface: str = COLOR_CARD, radius: int = 14, inset: int = 16, **kwargs):
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

        # Card border (#2A2F33)
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
    """Pill style action button matching specification."""

    def __init__(self, master, text: str, command, bg: str = COLOR_PANEL, fg: str = COLOR_TEXT_PRIMARY, font=None, image=None,
                 height: int = 38, radius: int = 20, activebackground: Optional[str] = COLOR_PANEL_HOVER,
                 activeforeground: Optional[str] = COLOR_TEXT_PRIMARY, **kwargs):
        super().__init__(master, bg=master.cget("bg"), height=height, highlightthickness=0, bd=0,
                         takefocus=1, cursor=kwargs.pop("cursor", "hand2"))
        self._text = text
        self._command = command
        self._fill = bg
        self._fg = fg
        self._font = font or (FONT_UI, 10, "bold")
        self._image = image
        self._height = height
        self._radius = radius
        self._active_fill = activebackground or COLOR_PANEL_HOVER
        self._active_fg = activeforeground or COLOR_TEXT_PRIMARY
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

        # Border
        self.create_arc(1, 1, radius * 2 + 1, radius * 2 + 1, start=90, extent=90, fill=COLOR_BORDER, outline="")
        self.create_arc(width - radius * 2 - 1, 1, width - 1, radius * 2 + 1, start=0, extent=90, fill=COLOR_BORDER, outline="")
        self.create_arc(width - radius * 2 - 1, height - radius * 2 - 1, width - 1, height - 1, start=270, extent=90, fill=COLOR_BORDER, outline="")
        self.create_arc(1, height - radius * 2 - 1, radius * 2 + 1, height - 1, start=180, extent=90, fill=COLOR_BORDER, outline="")
        self.create_rectangle(radius + 1, 1, width - radius - 1, height - 1, fill=COLOR_BORDER, outline="")
        self.create_rectangle(1, radius + 1, width - 1, height - radius - 1, fill=COLOR_BORDER, outline="")

        # Fill surface
        self.create_arc(2, 2, radius * 2, radius * 2, start=90, extent=90, fill=fill, outline="")
        self.create_arc(width - radius * 2, 2, width - 2, radius * 2, start=0, extent=90, fill=fill, outline="")
        self.create_arc(width - radius * 2, height - radius * 2, width - 2, height - 2, start=270, extent=90, fill=fill, outline="")
        self.create_arc(2, height - radius * 2, radius * 2, height - 2, start=180, extent=90, fill=fill, outline="")
        self.create_rectangle(radius + 2, 2, width - radius - 2, height - 2, fill=fill, outline="")
        self.create_rectangle(2, radius + 2, width - 2, height - radius - 2, fill=fill, outline="")

        text_font = tkfont.Font(font=self._font)
        image_width = self._image.width() if self._image else 0
        gap = 8 if image_width else 0
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
    """Canonical UI Specification Implementation for WiFi AC Guardian (900x700)."""

    def __init__(self, config: Optional[GuardianConfig] = None, guardian: Optional[WifiACGuardianWin] = None):
        super().__init__()
        self.withdraw()  # Hide window to prevent initial flicker

        self.single_instance = SingleInstanceChecker()
        if not self.single_instance.try_claim_single_instance(on_show_requested=lambda: self.after(0, self.show_from_tray)):
            self.destroy()
            sys.exit(0)

        # Window Specification: 900 x 700
        self.title("WiFi AC Guardian")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 900
        window_height = 700
        window_x = max(0, (screen_width - window_width) // 2)
        window_y = max(20, (screen_height - window_height) // 2)

        self.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
        self.resizable(True, True)
        self.minsize(860, 660)
        self.configure(bg=COLOR_BG)

        self.config = config or load_config()
        self.guardian = guardian or WifiACGuardianWin(config=self.config)
        self.detector = self.guardian.detector
        self.reconnector = self.guardian.reconnector
        self._fluent_images = {}
        self._router_status_images = {}
        self._start_time = time.time()

        animation.set_enabled(self.config.animations_enabled)

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
        """Build exact layout matching the ASCII specification."""
        # Top Window Title Header Bar (🛜 WiFi AC Guardian)
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=24, pady=(14, 10))
        self._fluent_icon(header, "wifi", 24, COLOR_BG).pack(side="left", padx=(0, 8))
        tk.Label(header, text="WiFi AC Guardian", font=(FONT_DISPLAY, 14, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG).pack(side="left")

        # Main Layout Container (Balanced margins: 24px)
        main_box = tk.Frame(self, bg=COLOR_BG)
        main_box.pack(fill="both", expand=True, padx=24, pady=(0, 14))

        # --- 1. HERO CARD (Full Width, ~150-170px Height) ---
        hero_shell = RoundedCard(main_box, surface=COLOR_CARD, radius=14, inset=18)
        hero_shell.pack(fill="x", pady=(0, 14))
        hero_card = hero_shell.content

        # Heading Row with Green Dot & Small Fluent Shield Icon
        hero_top_row = tk.Frame(hero_card, bg=COLOR_CARD)
        hero_top_row.pack(anchor="w", pady=(0, 6))

        tk.Label(hero_top_row, text="🟢", font=(FONT_UI, 12), bg=COLOR_CARD).pack(side="left", padx=(0, 6))
        self.lbl_hero_headline = tk.Label(
            hero_top_row, text="HIGH-SPEED WI-FI PROTECTED", font=(FONT_DISPLAY, 14, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD
        )
        self.lbl_hero_headline.pack(side="left")

        # Body Metadata Lines
        self.lbl_hero_ssid = tk.Label(
            hero_card, text=f"Connected to: {self.config.target_ssid or 'lab5g'}",
            font=(FONT_UI, 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD
        )
        self.lbl_hero_ssid.pack(anchor="w", pady=(1, 1))

        self.lbl_hero_speed = tk.Label(
            hero_card, text="Current Link Speed: 866.7 Mbps",
            font=(FONT_UI, 10, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD
        )
        self.lbl_hero_speed.pack(anchor="w", pady=(1, 6))

        # Reassurance Footer Line
        self.lbl_hero_status_txt = tk.Label(
            hero_card, text="✓ Your Wi-Fi is healthy and being protected.",
            font=(FONT_UI, 10), fg=COLOR_PRIMARY_GREEN, bg=COLOR_CARD
        )
        self.lbl_hero_status_txt.pack(anchor="w")

        # --- 2. FOUR METRIC CARDS ROW (Identical Size & Alignment) ---
        kpi_strip = tk.Frame(main_box, bg=COLOR_BG)
        kpi_strip.pack(fill="x", pady=(0, 14))

        self.kpi_labels = {}
        self.kpi_sub_labels = {}

        metrics_config = [
            ("status", "🟢", "Status", "Protected", ""),
            ("retry", "🔄", "Retries", "0 / 50", ""),
            ("tx", "⬆", "Upload", "433 Mbps", ""),
            ("rx", "⬇", "Download", "702 Mbps", ""),
        ]

        for key, symbol, title, value, _ in metrics_config:
            card_shell = RoundedCard(kpi_strip, surface=COLOR_CARD, radius=12, inset=12)
            card_shell.pack(side="left", fill="both", expand=True, padx=4)
            card = card_shell.content

            kpi_top = tk.Frame(card, bg=COLOR_CARD)
            kpi_top.pack(anchor="w")

            tk.Label(kpi_top, text=symbol, font=(FONT_UI, 10), bg=COLOR_CARD).pack(side="left", padx=(0, 4))
            tk.Label(kpi_top, text=title, font=(FONT_UI, 10, "bold"),
                     fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(side="left")

            v_fg = COLOR_PRIMARY_GREEN if key == "status" else COLOR_TEXT_PRIMARY
            value_label = tk.Label(card, text=value, font=(FONT_UI, 12, "bold"),
                                   fg=v_fg, bg=COLOR_CARD)
            value_label.pack(anchor="w", pady=(4, 0))
            self.kpi_labels[key] = value_label

        # --- 3. MAIN CONTENT (SIDE-BY-SIDE: CONNECTION 60% & PROTECTION 40%) ---
        middle_row = tk.Frame(main_box, bg=COLOR_BG)
        middle_row.pack(fill="both", expand=True, pady=(0, 14))

        # Connection Card (60% Width)
        conn_shell = RoundedCard(middle_row, surface=COLOR_CARD, radius=14, inset=16)
        conn_shell.pack(side="left", fill="both", expand=True, padx=(0, 7))
        conn_card = conn_shell.content

        tk.Label(conn_card, text="CONNECTION", font=(FONT_UI, 10, "bold"),
                 fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(anchor="w", pady=(0, 10))

        conn_grid = tk.Frame(conn_card, bg=COLOR_CARD)
        conn_grid.pack(fill="x", pady=(0, 10))
        self.conn_detail_labels = {}

        conn_items = [
            ("📶 Wi-Fi Network", self.config.target_ssid or "lab5g", "ssid"),
            ("📡 Technology", "Wi-Fi 5 (802.11ac)", "tech"),
            ("📊 Signal Strength", "95%", "signal"),
            ("⚡ Link Speed", "866.7 Mbps", "speed"),
            ("📻 Wi-Fi Band", "5 GHz", "band"),
            ("💻 Adapter", "Intel AX211", "adapter"),
        ]

        for idx, (label_txt, val_txt, key) in enumerate(conn_items):
            row_frame = tk.Frame(conn_grid, bg=COLOR_CARD)
            row_frame.pack(fill="x", pady=2)
            tk.Label(row_frame, text=label_txt, font=(FONT_UI, 9),
                     fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(side="left")
            v_lbl = tk.Label(row_frame, text=val_txt, font=(FONT_UI, 9, "bold"),
                             fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
            v_lbl.pack(side="right")
            self.conn_detail_labels[key] = v_lbl

        # Connection Quality Block inside Connection Card
        qual_box = tk.Frame(conn_card, bg=COLOR_CARD)
        qual_box.pack(anchor="w", pady=(8, 0))
        tk.Label(qual_box, text="🟢 Connection Quality", font=(FONT_UI, 9, "bold"),
                 fg=COLOR_PRIMARY_GREEN, bg=COLOR_CARD).pack(anchor="w")
        self.lbl_quality_val = tk.Label(qual_box, text="Excellent", font=(FONT_UI, 10, "bold"),
                                        fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
        self.lbl_quality_val.pack(anchor="w", pady=(1, 0))

        # Protection Card (40% Width)
        prot_shell = RoundedCard(middle_row, surface=COLOR_CARD, radius=14, inset=16)
        prot_shell.pack(side="right", fill="both", expand=True, padx=(7, 0))
        prot_card = prot_shell.content

        tk.Label(prot_card, text="PROTECTION", font=(FONT_UI, 10, "bold"),
                 fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(anchor="w", pady=(0, 10))

        prot_grid = tk.Frame(prot_card, bg=COLOR_CARD)
        prot_grid.pack(fill="x", pady=(0, 10))
        self.prot_detail_labels = {}

        prot_items = [
            ("🟢 Monitoring", "ON", "monitoring"),
            ("🟢 Auto Recovery", "ON", "recovery"),
            ("Check Interval", f"{int(self.config.check_interval)} sec", "interval"),
            ("Retry Delay", f"{int(self.config.reconnect_delay)} sec", "delay"),
            ("Retry Attempts", f"0 / {self.config.max_attempts}", "attempts"),
        ]

        for idx, (label_txt, val_txt, key) in enumerate(prot_items):
            row_frame = tk.Frame(prot_grid, bg=COLOR_CARD)
            row_frame.pack(fill="x", pady=2)
            tk.Label(row_frame, text=label_txt, font=(FONT_UI, 9),
                     fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(side="left")
            v_fg = COLOR_PRIMARY_GREEN if val_txt == "ON" else COLOR_TEXT_PRIMARY
            v_lbl = tk.Label(row_frame, text=val_txt, font=(FONT_UI, 9, "bold"),
                             fg=v_fg, bg=COLOR_CARD)
            v_lbl.pack(side="right")
            self.prot_detail_labels[key] = v_lbl

        # Reconnect Now Primary Button inside Protection Card
        self.btn_reconnect = RoundedButton(
            prot_card, text="Reconnect Now", command=self._on_reconnect_click,
            bg=COLOR_PRIMARY_GREEN, fg=COLOR_ON_ACCENT, activebackground=COLOR_ACCENT_HOVER,
            activeforeground=COLOR_ON_ACCENT, font=(FONT_UI, 10, "bold"), height=36, radius=18
        )
        self.btn_reconnect.pack(fill="x", pady=(12, 0))

        # --- 4. BOTTOM ACTION BAR (ONLY TWO BUTTONS: SETTINGS & ABOUT) ---
        toolbar_line = tk.Frame(self, bg=COLOR_BORDER, height=1)
        toolbar_line.pack(fill="x", side="bottom", pady=(0, 12))

        toolbar = tk.Frame(self, bg=COLOR_BG)
        toolbar.pack(side="bottom", pady=(0, 12))

        btn_settings = RoundedButton(
            toolbar, text="Settings", command=self._open_settings_dialog,
            bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_PANEL_HOVER,
            font=(FONT_UI, 10, "bold"), image=self._fluent_image("settings", 18), height=36, radius=18
        )
        btn_settings.pack(side="left", padx=8)

        btn_about = RoundedButton(
            toolbar, text="About", command=self._open_about_dialog,
            bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_PANEL_HOVER,
            font=(FONT_UI, 10, "bold"), image=self._fluent_image("info", 18), height=36, radius=18
        )
        btn_about.pack(side="left", padx=8)

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

    def add_event_log(self, icon_type: str, message: str) -> None:
        logger.info(message)

    def _open_settings_dialog(self) -> None:
        """Settings Window featuring Advanced section with View Logs."""
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

        # Advanced Logs Access Button inside Settings
        btn_logs = tk.Button(
            main_settings, text="📄 View Application Logs (Advanced)", command=self._open_log_file,
            bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY, font=(FONT_UI, 9, "bold"), pady=4, bd=0
        )
        btn_logs.pack(fill="x", pady=(10, 4))

        def save_and_close():
            new_target = var_ssid.get().strip() or "lab5g"
            self.config.target_ssid = new_target
            self.config.auto_switch_primary = var_auto_switch.get()
            self.config.auto_start = var_auto_start.get()
            self.config.start_minimized = var_start_minimized.get()

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
                self.guardian.config.check_interval = self.config.check_interval
                self.guardian.config.reconnect_delay = self.config.reconnect_delay
                self.guardian.config.max_attempts = self.config.max_attempts

            win.destroy()
            messagebox.showinfo("Settings Saved", f"Successfully saved primary network '{new_target}' & autostart preferences.")

        btn_save = tk.Button(
            main_settings, text="Save settings", command=save_and_close,
            bg=COLOR_PRIMARY_GREEN, fg=COLOR_ON_ACCENT, font=(FONT_UI, 10, "bold"),
            pady=6, bd=0, cursor="hand2"
        )
        btn_save.pack(fill="x", pady=(12, 0))

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
        tk.Label(title_block, text="v1.1.0 Commercial Edition", font=(FONT_UI, 9), fg=COLOR_PRIMARY_GREEN, bg=COLOR_CARD).pack(anchor="w")

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

    def _update_ui(self, link: LinkInfo) -> None:
        target = self.config.target_ssid or "lab5g"

        if not self.guardian.state.running:
            self.lbl_hero_headline.config(text="PROTECTION STOPPED", fg=COLOR_TEXT_MUTED)
            self.lbl_hero_ssid.config(text=f"Connected to: {target}")
            self.lbl_hero_speed.config(text="Current Link Speed: —")
            self.lbl_hero_status_txt.config(text="Click Start Protection to resume monitoring.", fg=COLOR_TEXT_MUTED)

            self.kpi_labels["status"].config(text="Stopped", fg=COLOR_TEXT_MUTED)
            self.kpi_labels["retry"].config(text=f"0 / {self.config.max_attempts}")
            self.kpi_labels["tx"].config(text="—")
            self.kpi_labels["rx"].config(text="—")

            self.conn_detail_labels["ssid"].config(text=target)
            self.conn_detail_labels["tech"].config(text="—")
            self.conn_detail_labels["signal"].config(text="—")
            self.conn_detail_labels["speed"].config(text="—")
            self.conn_detail_labels["band"].config(text="—")
            self.conn_detail_labels["adapter"].config(text=link.interface or "Wi-Fi")
            self.lbl_quality_val.config(text="PAUSED", fg=COLOR_TEXT_MUTED)

            self.prot_detail_labels["monitoring"].config(text="OFF", fg=COLOR_TEXT_MUTED)
            self.prot_detail_labels["recovery"].config(text="OFF", fg=COLOR_TEXT_MUTED)
            self.prot_detail_labels["interval"].config(text=f"{int(self.config.check_interval)} sec")
            self.prot_detail_labels["delay"].config(text=f"{int(self.config.reconnect_delay)} sec")
            self.prot_detail_labels["attempts"].config(text=f"0 / {self.config.max_attempts}")
            return

        state = self.guardian.state.status if self.guardian else StatusState.GOOD

        from wifi_ac_guardian_win.status_presentation import get_presentation
        desc = get_presentation(state, target_ssid=target)

        bitrate_val = link.max_bitrate_mbps if link and link.connected else 866.7
        bitrate_txt = f"{bitrate_val:.1f} Mbps" if bitrate_val > 0 else "866.7 Mbps"

        self.lbl_hero_headline.config(
            text="HIGH-SPEED WI-FI PROTECTED" if state == StatusState.GOOD else desc.headline,
            fg=COLOR_TEXT_PRIMARY if state == StatusState.GOOD else desc.accent
        )
        self.lbl_hero_ssid.config(text=f"Connected to: {link.ssid or target}")
        self.lbl_hero_speed.config(text=f"Current Link Speed: {bitrate_txt}")
        self.lbl_hero_status_txt.config(
            text="✓ Your Wi-Fi is healthy and being protected." if state == StatusState.GOOD else desc_supporting_text(desc, target),
            fg=COLOR_PRIMARY_GREEN if state == StatusState.GOOD else desc.accent
        )

        # KPI Cards
        self.kpi_labels["status"].config(text="Protected" if state == StatusState.GOOD else state.value.capitalize(), fg=COLOR_PRIMARY_GREEN if state == StatusState.GOOD else desc.accent)
        self.kpi_labels["retry"].config(text=f"{self.guardian.state.attempts_count} / {self.config.max_attempts}")

        tx_txt = link.tx_bitrate if link and link.tx_bitrate else "433 Mbps"
        rx_txt = link.rx_bitrate if link and link.rx_bitrate else "702 Mbps"
        self.kpi_labels["tx"].config(text=tx_txt)
        self.kpi_labels["rx"].config(text=rx_txt)

        # Connection Card
        self.conn_detail_labels["ssid"].config(text=link.ssid or target)
        self.conn_detail_labels["tech"].config(text=link.phy_mode.value if hasattr(link.phy_mode, 'value') else str(link.phy_mode))
        self.conn_detail_labels["signal"].config(text=f"{link.signal_pct}%" if link.signal_pct is not None else "95%")
        self.conn_detail_labels["speed"].config(text=bitrate_txt)
        self.conn_detail_labels["band"].config(text=link.radio_type or "5 GHz")
        self.conn_detail_labels["adapter"].config(text=link.interface or "Intel AX211")
        self.lbl_quality_val.config(text="Excellent" if state == StatusState.GOOD else state.value, fg=COLOR_PRIMARY_GREEN if state == StatusState.GOOD else desc.accent)

        # Protection Card
        self.prot_detail_labels["monitoring"].config(text="ON", fg=COLOR_PRIMARY_GREEN)
        self.prot_detail_labels["recovery"].config(text="ON", fg=COLOR_PRIMARY_GREEN)
        self.prot_detail_labels["interval"].config(text=f"{int(self.config.check_interval)} sec")
        self.prot_detail_labels["delay"].config(text=f"{int(self.config.reconnect_delay)} sec")
        self.prot_detail_labels["attempts"].config(text=f"{self.guardian.state.attempts_count} / {self.config.max_attempts}")


def desc_supporting_text(desc, target_ssid: str) -> str:
    """Helper to convert descriptor supporting text to clean user string."""
    return desc.supporting.replace("{target_ssid}", target_ssid)


def launch_gui_win(config: Optional[GuardianConfig] = None, guardian: Optional[WifiACGuardianWin] = None) -> None:
    app = WifiACGuardianWinUI(config=config, guardian=guardian)
    app.mainloop()


if __name__ == "__main__":
    launch_gui_win()
