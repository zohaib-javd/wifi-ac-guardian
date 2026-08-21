"""
Icon generation and manager for WiFi AC Guardian system tray.
Generates dynamic status icons (Green, Yellow, Red) using Pillow.
"""

import os
from typing import Dict
from PIL import Image, ImageDraw, ImageFont
from wifi_ac_guardian.core.models import StatusState
from wifi_ac_guardian.logger import get_logger

logger = get_logger()

ICON_CACHE_DIR = os.path.expanduser("~/.local/share/wifi_ac_guardian/icons")


def ensure_icon_directory() -> str:
    """Creates cache directory for generated status icons if missing."""
    os.makedirs(ICON_CACHE_DIR, exist_ok=True)
    return ICON_CACHE_DIR


def generate_status_icon(color_hex: str, label: str, filename: str) -> str:
    """
    Renders a 64x64 PNG tray icon with rounded background and high-contrast label.

    Args:
        color_hex: Primary status color hex code (e.g. '#2ECC71').
        label: Short text overlay (e.g. '5G', '...', '!').
        filename: Destination filename (e.g. 'green.png').

    Returns:
        Absolute filepath to created icon PNG.
    """
    ensure_icon_directory()
    filepath = os.path.join(ICON_CACHE_DIR, filename)

    size = (64, 64)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw rounded rectangle badge
    margin = 4
    draw.rounded_rectangle(
        [margin, margin, size[0] - margin, size[1] - margin],
        radius=14,
        fill=color_hex,
        outline="#1C2833",
        width=3
    )

    # Inner Wi-Fi arc arcs / text symbol
    draw.arc([16, 16, 48, 48], start=210, end=330, fill="#FFFFFF", width=3)
    draw.arc([22, 24, 42, 44], start=210, end=330, fill="#FFFFFF", width=3)
    draw.ellipse([30, 38, 34, 42], fill="#FFFFFF")

    # Add text overlay at top-right or center
    try:
        font = ImageFont.load_default()
        draw.text((36, 10), label, fill="#FFFFFF", font=font)
    except Exception:
        pass

    image.save(filepath, "PNG")
    return filepath


def get_icon_paths() -> Dict[StatusState, str]:
    """
    Generates and returns map of StatusState -> icon filepath.

    Returns:
        Dictionary mapping StatusState to icon PNG filepaths.
    """
    paths = {
        StatusState.GOOD: generate_status_icon("#2ECC71", "AC", "wifi_ac_green.png"),
        StatusState.RETRYING: generate_status_icon("#F39C12", "N", "wifi_ac_yellow.png"),
        StatusState.FAILED: generate_status_icon("#E74C3C", "ERR", "wifi_ac_red.png"),
        StatusState.DISCONNECTED: generate_status_icon("#7F8C8D", "OFF", "wifi_ac_gray.png"),
        StatusState.IDLE: generate_status_icon("#3498DB", "IDLE", "wifi_ac_blue.png"),
    }
    return paths


def create_pillow_icon_for_state(state: StatusState) -> Image.Image:
    """Returns PIL Image object for pystray integration."""
    icon_paths = get_icon_paths()
    path = icon_paths.get(state, icon_paths[StatusState.IDLE])
    return Image.open(path)
