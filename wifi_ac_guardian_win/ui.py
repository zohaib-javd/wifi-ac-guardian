"""
Tkinter Control Panel GUI for WiFi AC Guardian (Windows 11 & Ubuntu).
Commercial PowerToys-inspired desktop design system (900x720) with SegmentedSpeedBar Bitrate Meter.
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

COLOR_BG = theme.BG                       # Main Dark Background (#151515)
COLOR_CARD = theme.CARD                   # Card Surface Background (#1E1E1E)
COLOR_PANEL = theme.PANEL                 # Secondary Panel Background (#252525)
COLOR_BORDER = theme.BORDER               # Soft Border (#323232)

COLOR_ACCENT = theme.ACCENT               # Primary Accent Emerald (#24C26A)
COLOR_ACCENT_BG = theme.ACCENT_BG
COLOR_WARN = theme.WARN                   # Warning Amber (#F4B740)
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

# Speed-bar tokens
COLOR_TRACK = theme.TRACK
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


class SegmentedSpeedBar(tk.Canvas):
    """Custom Canvas Widget displaying a 3-zone segmented bitrate quality bar with markers."""

    def __init__(
        self,
        master,
        current_speed: float = 780.0,
        threshold: float = 300.0,
        max_speed: float = 1000.0,
        width: int = 620,
        height: int = 65,
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
        """Move cursor to speed, tweening value when animations are enabled."""
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

        left = 18
        right = max(left + 50, self.width - 18)
        top = 22
        bar_height = 18

        total_width = right - left

        def x(value: float) -> float:
            v_clamped = max(0.0, min(value, self.max_speed))
            return left + (v_clamped / self.max_speed) * total_width

        # Track
        radius = bar_height / 2
        self.create_arc(left, top, left + bar_height, top + bar_height, start=90, extent=180, fill=COLOR_TRACK, outline="")
        self.create_rectangle(left + radius, top, right - radius, top + bar_height, fill=COLOR_TRACK, outline="")
        self.create_arc(right - bar_height, top, right, top + bar_height, start=270, extent=180, fill=COLOR_TRACK, outline="")

        # Zones
        self.create_rectangle(x(0), top, x(200), top + bar_height, fill=COLOR_ZONE_RED, outline="")
        self.create_rectangle(x(200), top, x(300), top + bar_height, fill=COLOR_ZONE_ORANGE, outline="")
        self.create_rectangle(x(300), top, x(1000), top + bar_height, fill=COLOR_ZONE_GREEN, outline="")

        # Threshold Line (300 Mbps)
        tx = x(self.threshold)
        self.create_line(tx, top - 6, tx, top + bar_height + 6, fill=COLOR_TEXT_PRIMARY, width=2)
        self.create_text(tx, top - 12, text="300 Mbps", fill=COLOR_ZONE_ORANGE, font=(FONT_UI, 8, "bold"))

        # Cursor
        sx = x(self.current_speed)
        self.create_line(sx, top - 2, sx, top + bar_height + 2, fill=COLOR_TEXT_PRIMARY, width=3)
        self.create_text(sx, top + 32, text=f"{self.current_speed:.0f} Mbps", fill=COLOR_TEXT_PRIMARY, font=(FONT_MONO, 8, "bold"))

        # End labels
        self.create_text(left, top - 12, anchor="w", text="0 Mbps", fill=COLOR_SCALE_LABEL, font=(FONT_UI, 8))
        self.create_text(right, top - 12, anchor="e", text=f"{int(self.max_speed)} Mbps", fill=COLOR_SCALE_LABEL, font=(FONT_UI, 8))


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
                 height: int = 40, radius: int = 10, activebackground: Optional[str] = None,
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
    """Commercial PowerToys-inspired desktop control panel for WiFi AC Guardian."""

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

        animation.set_enabled(self.config.animations_enabled)
        self._prev_hero_accent = None
        self._hero_anim = None

        # Connect tray callbacks safely to main thread
        if self.guardian.tray_app:
            self.guardian.tray_app.on_open_ui_click = lambda: self.after(0, self.show_from_tray)
            self.guardian.tray_app.on_quit_click = lambda: self.after(0, self.quit_app)
            self.guardian.tray_app.on_stop_protection_click = lambda: self.after(0, self._on_protection_toggle)

        # Start guardian background loop if inactive
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
        """Build the commercial PowerToys-inspired desktop layout."""
        # Top Header Bar
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=28, pady=(20, 14))
        self._fluent_icon(header, "app", 42, COLOR_BG).pack(side="left", padx=(0, 12))
        title_block = tk.Frame(header, bg=COLOR_BG)
        title_block.pack(side="left")
        tk.Label(title_block, text="WiFi AC Guardian", font=(FONT_DISPLAY, 19, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG).pack(anchor="w")
        tk.Label(title_block, text="High-Speed Wi-Fi 5+ Protection", font=(FONT_UI, 9),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG).pack(anchor="w", pady=(1, 0))

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

        # --- 1. HERO SECTION (Dominant identity of the product) ---
        hero_shell = RoundedCard(main_box, surface=COLOR_CARD, radius=16, inset=20)
        hero_shell.pack(fill="x", pady=(0, 16))
        hero_card = hero_shell.content

        hero_center = tk.Frame(hero_card, bg=COLOR_CARD)
        hero_center.pack(fill="x", pady=(8, 12))

        # Large 96px router status artwork
        self.lbl_status_icon = tk.Label(
            hero_center, image=self._router_status_image(StatusState.IDLE, 96),
            bg=COLOR_CARD, bd=0, highlightthickness=0
        )
        self.lbl_status_icon.pack(anchor="center", pady=(0, 12))

        # Large Hero Headline Typography
        from wifi_ac_guardian_win.status_presentation import get_presentation
        idle_desc = get_presentation(StatusState.IDLE, target_ssid=self.config.target_ssid)

        self.lbl_hero_state = tk.Label(
            hero_center, text=idle_desc.headline, font=(FONT_DISPLAY, 16, "bold"),
            fg=COLOR_INFO, bg=COLOR_CARD
        )
        self.lbl_hero_state.pack(anchor="center", pady=(0, 4))

        self.lbl_hero_sub = tk.Label(
            hero_center, text=f"Connected to {self.config.target_ssid}  •  Link Speed: —",
            font=(FONT_UI, 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD
        )
        self.lbl_hero_sub.pack(anchor="center", pady=(0, 4))

        self.lbl_target_info = tk.Label(
            hero_center, text=desc_supporting_text(idle_desc, self.config.target_ssid),
            font=(FONT_UI, 9), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD
        )
        self.lbl_target_info.pack(anchor="center")

        # --- 2. METRIC CARDS STRIP (4 KPI Cards) ---
        kpi_strip = tk.Frame(main_box, bg=COLOR_BG)
        kpi_strip.pack(fill="x", pady=(0, 16))

        self.kpi_labels = {}
        for key, icon, title, value in [
            ("status", "shield", "Status", StatusState.IDLE.value.capitalize()),
            ("tx", "bolt", "Upload link speed", "— Mbps"),
            ("rx", "bolt", "Download link speed", "— Mbps"),
            ("retry", "history", "Reconnect attempts", f"0 / {self.config.max_attempts}"),
        ]:
            card_shell = RoundedCard(kpi_strip, surface=COLOR_CARD, radius=12, inset=12)
            card_shell.pack(side="left", fill="both", expand=True, padx=4)
            card = card_shell.content

            kpi_header = tk.Frame(card, bg=COLOR_CARD)
            kpi_header.pack(anchor="w")

            if key == "status":
                self.kpi_status_icon = tk.Label(
                    kpi_header, image=self._router_status_image(StatusState.GOOD, 20),
                    bg=COLOR_CARD, bd=0, highlightthickness=0
                )
                self.kpi_status_icon.pack(side="left", padx=(0, 5))
            else:
                self._fluent_icon(kpi_header, icon, 20, COLOR_CARD).pack(side="left", padx=(0, 5))

            tk.Label(kpi_header, text=title.upper(), font=(FONT_UI, 7, "bold"),
                     fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(side="left")

            value_label = tk.Label(card, text=value, font=(FONT_MONO, 10, "bold"),
                                   fg=COLOR_ACCENT, bg=COLOR_CARD)
            value_label.pack(anchor="w", pady=(6, 0))
            self.kpi_labels[key] = value_label

        # --- 3. MIDDLE ROW (Side-by-Side: Connection Overview & Protection Engine) ---
        middle_row = tk.Frame(main_box, bg=COLOR_BG)
        middle_row.pack(fill="x", pady=(0, 16))

        # Left Card: Connection Overview Card
        left_shell = RoundedCard(middle_row, surface=COLOR_CARD, radius=15, inset=16)
        left_shell.pack(side="left", fill="both", expand=True, padx=(0, 8))
        left_card = left_shell.content
        self._section_header(left_card, "wifi", "Connection Card & Bitrate Meter")

        overview_grid = tk.Frame(left_card, bg=COLOR_CARD)
        overview_grid.pack(fill="x", pady=(10, 10))
        self.overview_labels = {}

        pairs_left = [
            ("Wi-Fi Network", self.config.target_ssid, "ssid"),
            ("Wi-Fi Technology", "—", "phy"),
            ("Signal Strength", "—", "signal"),
            ("Current Link Speed", "— Mbps", "speed"),
            ("Network Adapter", "Wi-Fi", "interface"),
            ("Frequency / Band", "—", "freq"),
            ("Channel", "—", "channel"),
            ("Quality State", "—", "quality")
        ]
        for idx, (k_txt, v_txt, key) in enumerate(pairs_left):
            r, c = divmod(idx, 2)
            cell = tk.Frame(overview_grid, bg=COLOR_CARD)
            cell.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
            overview_grid.columnconfigure(c, weight=1)
            tk.Label(cell, text=k_txt, font=(FONT_UI, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(anchor="w")
            v_lbl = tk.Label(cell, text=v_txt, font=(FONT_MONO, 9, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
            v_lbl.pack(anchor="w", pady=(2, 0))
            self.overview_labels[key] = v_lbl

        # Integrated SegmentedSpeedBar Bitrate Meter
        meter_hdr = tk.Frame(left_card, bg=COLOR_CARD)
        meter_hdr.pack(fill="x", pady=(8, 2))
        tk.Label(meter_hdr, text="BITRATE QUALITY METER", font=(FONT_UI, 8, "bold"),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(side="left")
        tk.Label(meter_hdr, text="300 Mbps threshold", font=(FONT_UI, 8),
                 fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(side="right")

        self.speed_bar = SegmentedSpeedBar(left_card, current_speed=0.0, threshold=300.0,
                                           max_speed=1000.0, height=65, bg=COLOR_CARD)
        self.speed_bar.pack(fill="x", pady=(0, 0))

        # Right Card: Protection Engine Card
        right_shell = RoundedCard(middle_row, surface=COLOR_CARD, radius=15, inset=16)
        right_shell.pack(side="right", fill="both", expand=True, padx=(8, 0))
        right_card = right_shell.content
        self._section_header(right_card, "bolt", "Protection Engine")

        engine_grid = tk.Frame(right_card, bg=COLOR_CARD)
        engine_grid.pack(fill="x", pady=(10, 10))
        self.engine_labels = {}

        interval_str = f"{self.config.check_interval:.0f} sec"
        delay_str = f"{self.config.reconnect_delay:.0f} sec"
        attempts_str = f"{self.config.max_attempts} (Auto)"

        pairs_engine = [
            ("Protection status", "Active", "status"),
            ("Check interval", interval_str, "interval"),
            ("Reconnect delay", delay_str, "delay"),
            ("Retry attempts", attempts_str, "attempts"),
            ("Last check", "—", "last_check"),
            ("Last recovery", "None", "last_recovery")
        ]
        for idx, (k_txt, v_txt, key) in enumerate(pairs_engine):
            r, c = divmod(idx, 2)
            cell = tk.Frame(engine_grid, bg=COLOR_CARD)
            cell.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
            engine_grid.columnconfigure(c, weight=1)
            tk.Label(cell, text=k_txt, font=(FONT_UI, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).pack(anchor="w")
            v_lbl = tk.Label(cell, text=v_txt, font=(FONT_MONO, 9, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
            v_lbl.pack(anchor="w", pady=(2, 0))
            self.engine_labels[key] = v_lbl

        self.btn_reconnect = RoundedButton(
            right_card, text="Reconnect now", command=self._on_reconnect_click,
            bg=COLOR_ACCENT, fg=COLOR_ON_ACCENT, activebackground=COLOR_ACCENT_HOVER,
            activeforeground=COLOR_ON_ACCENT, font=(FONT_UI, 9, "bold"),
            image=self._fluent_image("history", 22), height=42
        )
        self.btn_reconnect.pack(fill="x", pady=(12, 0))

        self.btn_protection = RoundedButton(
            right_card, text="Stop protection", command=self._on_protection_toggle,
            bg=COLOR_ERROR, fg=COLOR_ON_ERROR, activebackground=COLOR_ERROR_HOVER,
            activeforeground=COLOR_ON_ERROR, font=(FONT_UI, 9, "bold"),
            image=self._fluent_image("shield", 22), height=42
        )
        self.btn_protection.pack(fill="x", pady=(8, 0))

        # --- 4. BOTTOM ACTION BAR (Pinned Toolbar) ---
        toolbar = tk.Frame(self, bg=COLOR_BG)
        toolbar.pack(side="bottom", fill="x", padx=28, pady=(0, 16))

        for name, icon, label, cmd in [
            ("settings", "settings", "Settings", self._open_settings_dialog),
            ("log", "desktop", "View Logs", self._open_log_file),
            ("info", "info", "About", self._open_about_dialog)
        ]:
            btn = RoundedButton(
                toolbar, text=label, command=cmd, bg=COLOR_PANEL, fg=COLOR_TEXT_PRIMARY,
                activebackground=COLOR_PANEL_HOVER, activeforeground=COLOR_TEXT_PRIMARY,
                font=(FONT_UI, 9, "bold"), image=self._fluent_image(icon, 22), height=40
            )
            btn.pack(side="left", fill="x", expand=True, padx=4)

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
        self.lbl_status_icon.configure(image=self._router_status_image(state, 96))
        self.kpi_status_icon.configure(image=self._router_status_image(state, 20))

    def _fluent_icon(self, parent, name: str, size: int, bg: str):
        return tk.Label(parent, image=self._fluent_image(name, size), bg=bg, bd=0, highlightthickness=0)

    def _section_header(self, parent, icon: str, title: str) -> None:
        row = tk.Frame(parent, bg=COLOR_CARD)
        row.pack(fill="x")
        self._fluent_icon(row, icon, 24, COLOR_CARD).pack(side="left", padx=(0, 7))
        tk.Label(row, text=title, font=(FONT_UI, 11, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(side="left")

    def add_event_log(self, icon_type: str, message: str) -> None:
        logger.info(message)

    def _open_settings_dialog(self) -> None:
        """Windows 11 / PowerToys inspired Settings Window."""
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

        if not self.guardian.state.running:
            self._set_router_status(StatusState.IDLE)
            self._set_hero_headline("PROTECTION STOPPED", COLOR_TEXT_MUTED)
            self.lbl_hero_sub.config(text=f"Target: {target}  •  Status: PAUSED")
            self.lbl_target_info.config(text="Click Start Protection to resume background monitoring.")
            self.kpi_labels["status"].config(text="Stopped", fg=COLOR_TEXT_MUTED)
            self.kpi_labels["tx"].config(text="— Mbps")
            self.kpi_labels["rx"].config(text="— Mbps")
            self.kpi_labels["retry"].config(text="—")

            self.overview_labels["ssid"].config(text=target)
            self.overview_labels["phy"].config(text="—")
            self.overview_labels["signal"].config(text="—")
            self.overview_labels["speed"].config(text="— Mbps")
            self.overview_labels["interface"].config(text=link.interface or "Wi-Fi")
            self.overview_labels["freq"].config(text="—")
            self.overview_labels["channel"].config(text="—")
            self.overview_labels["quality"].config(text="PAUSED", fg=COLOR_TEXT_MUTED)

            self.engine_labels["status"].config(text="Stopped", fg=COLOR_TEXT_MUTED)
            self.engine_labels["interval"].config(text="Stopped")
            self.engine_labels["delay"].config(text="Stopped")
            self.engine_labels["attempts"].config(text="—")
            self.engine_labels["last_check"].config(text="—")

            self._sync_protection_controls()
            return

        self._sync_protection_controls()
        state = self.guardian.state.status if self.guardian else StatusState.IDLE

        from wifi_ac_guardian_win.status_presentation import get_presentation
        desc = get_presentation(state, target_ssid=target)

        self._set_router_status(state)
        self._set_hero_headline(desc.headline, desc.accent)

        bitrate_val = link.max_bitrate_mbps if link and link.connected else 0.0
        bitrate_txt = f"{bitrate_val:.1f} Mbps" if bitrate_val > 0 else "0.0 Mbps"

        self.lbl_hero_sub.config(text=f"Connected to {link.ssid or target}  •  Link Speed: {bitrate_txt}")
        self.lbl_target_info.config(text=desc_supporting_text(desc, target))

        self.kpi_labels["status"].config(text=state.value.capitalize(), fg=desc.accent)
        self.kpi_labels["tx"].config(text=f"{link.tx_bitrate or '—'}")
        self.kpi_labels["rx"].config(text=f"{link.rx_bitrate or '—'}")
        self.kpi_labels["retry"].config(text=f"{self.guardian.state.attempts_count} / {self.config.max_attempts}")

        # Overview Card
        self.overview_labels["ssid"].config(text=link.ssid or "Disconnected")
        self.overview_labels["phy"].config(text=link.phy_mode.value if hasattr(link.phy_mode, 'value') else str(link.phy_mode))
        self.overview_labels["signal"].config(text=f"{link.signal_pct}%" if link.signal_pct is not None else "N/A")
        self.overview_labels["speed"].config(text=bitrate_txt, fg=COLOR_ACCENT if bitrate_val > 300.0 else COLOR_WARN)
        self.overview_labels["interface"].config(text=link.interface or "Wi-Fi")
        freq_txt = f"{link.freq_mhz:.0f} MHz" if link.freq_mhz else (link.radio_type or "5 GHz")
        self.overview_labels["freq"].config(text=freq_txt)
        self.overview_labels["channel"].config(text=str(link.channel) if link.channel else "Auto")
        self.overview_labels["quality"].config(text=state.value, fg=desc.accent)

        # Protection Engine Card
        self.engine_labels["status"].config(text=state.value, fg=desc.accent)
        self.engine_labels["interval"].config(text=f"{self.config.check_interval:.0f} sec")
        self.engine_labels["delay"].config(text=f"{self.config.reconnect_delay:.0f} sec")
        self.engine_labels["attempts"].config(text=f"{self.config.max_attempts} (Auto)")
        self.engine_labels["last_check"].config(text="Just now" if link.connected else "2 sec ago")

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
