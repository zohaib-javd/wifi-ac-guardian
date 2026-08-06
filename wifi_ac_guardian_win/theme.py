"""
Design tokens for WiFi AC Guardian — the single source of truth for the visual
language (color, type, spacing, radius) matching the exact specification.
"""

from typing import Tuple

# ---------------------------------------------------------------------------
# Color tokens (EXACT SPECIFICATION)
# ---------------------------------------------------------------------------
BG = "#0D0F10"               # Main dark background (#0D0F10)
SURFACE = "#16181A"          # Surface / Card (#16181A)
CARD = "#16181A"             # Card surface (#16181A)
ELEVATED = "#1E2124"         # Surface Elevated (#1E2124)
PANEL = "#1E2124"            # Panel surface (#1E2124)
BORDER = "#2A2F33"           # Border / Divider (#2A2F33)

PRIMARY_GREEN = "#22C55E"    # Primary Green (#22C55E)
ACCENT = "#22C55E"           # Primary accent (#22C55E)
GLOW_GREEN = "#22C55E"       # Green Glow (#22C55E 30% opacity)

ACCENT_BG = "#16281E"
WARN = "#F59E0B"             # Amber Warning (#F59E0B)
WARN_BG = "#2E2416"
ERROR = "#EF4444"            # Error Red (#EF4444)
ERROR_BG = "#2E1818"
INFO = "#3B82F6"             # Information Blue (#3B82F6)
INFO_BG = "#182438"

# Text ramp (3 levels)
TEXT_PRIMARY = "#F2F4F7"     # High-contrast white (#F2F4F7)
TEXT_SECONDARY = "#A1A7AE"   # Secondary text (#A1A7AE)
TEXT_MUTED = "#8C92A0"       # De-emphasized captions (#8C92A0)

# Accent foreground ink
ON_ACCENT = "#051D0D"        # Ink on primary green accent
ON_ERROR = "#FFFFFF"         # Ink on red accent
ON_WARN = "#121212"          # Ink on amber accent

# Interaction states
ACCENT_HOVER = "#2BE06B"     # Green button hover
ERROR_HOVER = "#F87171"      # Red button hover
PANEL_HOVER = "#252A2F"      # Neutral pill hover (#252A2F)
FOCUS_RING = "#22C55E"       # Keyboard focus outline (#22C55E)

# Speed-bar zone colors
TRACK = "#2A2F33"            # Track Background (#2A2F33)
ZONE_RED = "#EF4444"         # 0–200 Mbps (#EF4444)
ZONE_ORANGE = "#F59E0B"      # 200–300 Mbps (#F59E0B)
ZONE_GREEN = "#22C55E"       # 300–1000 Mbps (#22C55E)
SCALE_LABEL = "#6B7280"      # Scale end labels (#6B7280)

# ---------------------------------------------------------------------------
# Typography tokens
# ---------------------------------------------------------------------------
FONT_UI = "Segoe UI Variable"
FONT_DISPLAY = "Segoe UI Variable Display"
FONT_MONO = "Cascadia Mono"


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates WCAG 2.1 relative luminance contrast ratio between two hex colors."""
    def luminance(hex_col: str) -> float:
        hex_col = hex_col.lstrip("#")
        r, g, b = [int(hex_col[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        def srgb(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b)

    l1, l2 = luminance(hex1), luminance(hex2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


wcag_contrast_ratio = contrast_ratio
