"""
Design tokens for WiFi AC Guardian — the single source of truth for the visual
language (color, type, spacing, radius) plus a WCAG contrast helper.

Values are lifted verbatim from the original ``ui.py`` constants so that routing
the UI through these tokens produces no visual change (feature 001, M1).

`core/` must never import this module — it is presentation-only.
"""

from typing import Tuple

# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------
# Surfaces (backgrounds, cards, panels, borders)
BG = "#151515"               # Main dark background
CARD = "#1E1E1E"             # Card surface background
PANEL = "#252525"            # Secondary panel background
BORDER = "#323232"           # Soft border

# Semantic accents, each with a paired subtle background
ACCENT = "#24C26A"           # Primary accent (emerald green) — GOOD / protected
ACCENT_BG = "#1A2F22"
WARN = "#F4B740"             # Warning (amber) — restoring / retrying
WARN_BG = "#2E2616"
ERROR = "#E74C3C"            # Error (red) — downgraded / disconnected
ERROR_BG = "#2E1818"
INFO = "#3B82F6"             # Information (blue) — standby / idle
INFO_BG = "#182438"

# Text ramp (3 levels)
TEXT_PRIMARY = "#FFFFFF"     # High-contrast white
TEXT_SECONDARY = "#B6B6B6"   # Readable secondary text
TEXT_MUTED = "#8C8C8C"       # De-emphasized captions/labels (WCAG-AA on all surfaces; F-13/T011)

# Accent foreground ink (text drawn on top of a filled accent surface)
ON_ACCENT = "#0A1C11"        # Ink on emerald accent (buttons)
ON_ERROR = "#FFFFFF"         # Ink on red accent
ON_WARN = "#121212"          # Ink on amber accent

# Interaction states — hover fills
ACCENT_HOVER = "#2AE07B"     # Emerald button hover
ERROR_HOVER = "#FF6255"      # Red button hover
PANEL_HOVER = "#303030"      # Neutral panel button hover
FOCUS_RING = "#FFFFFF"       # Keyboard focus outline drawn inset on the button fill (FR-018/FR-019; T050)

# Speed-bar zone colors (bitrate quality meter)
TRACK = "#333333"            # Empty track behind the segmented bar
ZONE_RED = "#E74C3C"         # 0–200 Mbps zone
ZONE_ORANGE = "#F39C12"      # 200–300 Mbps zone + threshold caption
ZONE_GREEN = "#2ECC71"       # 300+ Mbps zone
SCALE_LABEL = "#BBBBBB"      # Scale end labels (0 / max Mbps)

# ---------------------------------------------------------------------------
# Typography tokens
# ---------------------------------------------------------------------------
FONT_UI = "Segoe UI Variable"
FONT_DISPLAY = "Segoe UI Variable Display"
FONT_MONO = "Cascadia Mono"

# Type ramp: (family, size, weight) — named by role.
TYPE_DISPLAY = (FONT_DISPLAY, 19, "bold")   # App title
TYPE_TITLE = (FONT_UI, 12, "bold")          # Dialog / section title
TYPE_SECTION = (FONT_UI, 10, "bold")        # Section header
TYPE_HERO = (FONT_UI, 11, "bold")           # Hero status headline
TYPE_BODY = (FONT_UI, 9)                     # Body text
TYPE_CAPTION = (FONT_UI, 8)                  # Caption / helper text
TYPE_LABEL = (FONT_UI, 7, "bold")            # Uppercase KPI/field labels
TYPE_SUBTITLE = (FONT_UI, 9)                 # Header subtitle
TYPE_MONO = (FONT_MONO, 9, "bold")           # Metric values (mono)
TYPE_MONO_SM = (FONT_MONO, 8, "bold")        # Small metric values (mono)
TYPE_BUTTON = (FONT_UI, 9, "bold")           # Primary button label
TYPE_BUTTON_SM = (FONT_UI, 8, "bold")        # Toolbar button label

# ---------------------------------------------------------------------------
# Spacing & radius scales
# ---------------------------------------------------------------------------
# Spacing scale (px)
SPACE_XS = 3
SPACE_SM = 6
SPACE_MD = 12
SPACE_LG = 18
SPACE_XL = 24
SPACE_2XL = 28

# Radius scale (px)
RADIUS_SM = 10
RADIUS_MD = 12
RADIUS_LG = 14
RADIUS_XL = 16


# ---------------------------------------------------------------------------
# Contrast helper (WCAG 2.1 relative luminance / contrast ratio)
# ---------------------------------------------------------------------------
def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _relative_luminance(color: str) -> float:
    """WCAG 2.1 relative luminance of an sRGB hex color."""
    def _channel(c: int) -> float:
        srgb = c / 255.0
        return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4

    r, g, b = _hex_to_rgb(color)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """Return the WCAG contrast ratio (1.0–21.0) between two hex colors."""
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)
