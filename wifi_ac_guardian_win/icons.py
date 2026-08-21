"""
Icon generation and manager for Windows System Tray.
"""

import os
from typing import Dict
from PIL import Image, ImageDraw, ImageFont
from wifi_ac_guardian_win.core.models import StatusState

ICON_CACHE_DIR = os.path.expanduser("~/.wifi_ac_guardian_win/icons")
FLUENT_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "fluent", "shield_3d.png")
ROUTER_STATUS_DIR = os.path.join(os.path.dirname(__file__), "assets", "router_status")
ROUTER_STATUS_PATHS = {
    StatusState.GOOD: os.path.join(ROUTER_STATUS_DIR, "good.png"),
    StatusState.RETRYING: os.path.join(ROUTER_STATUS_DIR, "retrying.png"),
    StatusState.FAILED: os.path.join(ROUTER_STATUS_DIR, "failed.png"),
    StatusState.DISCONNECTED: os.path.join(ROUTER_STATUS_DIR, "failed.png"),
    StatusState.STANDBY: os.path.join(ROUTER_STATUS_DIR, "standby.png"),
    StatusState.IDLE: os.path.join(ROUTER_STATUS_DIR, "standby.png"),
}


def ensure_icon_directory() -> str:
    os.makedirs(ICON_CACHE_DIR, exist_ok=True)
    return ICON_CACHE_DIR


def generate_status_icon(color_hex: str, label: str, filename: str) -> str:
    ensure_icon_directory()
    filepath = os.path.join(ICON_CACHE_DIR, filename)

    size = (64, 64)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = 4
    draw.rounded_rectangle(
        [margin, margin, size[0] - margin, size[1] - margin],
        radius=14,
        fill=color_hex,
        outline="#1C2833",
        width=3
    )

    draw.arc([16, 16, 48, 48], start=210, end=330, fill="#FFFFFF", width=3)
    draw.arc([22, 24, 42, 44], start=210, end=330, fill="#FFFFFF", width=3)
    draw.ellipse([30, 38, 34, 42], fill="#FFFFFF")

    image.save(filepath, "PNG")
    return filepath


def generate_disconnected_icon(filename: str = "wifi_ac_disconnected.png") -> str:
    """Create the red-X tray icon used when there is no Wi-Fi connection."""
    ensure_icon_directory()
    filepath = os.path.join(ICON_CACHE_DIR, filename)
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([4, 4, 60, 60], fill="#E74C3C", outline="#7A1710", width=2)
    draw.line([20, 20, 44, 44], fill="#FFFFFF", width=6)
    draw.line([44, 20, 20, 44], fill="#FFFFFF", width=6)
    image.save(filepath, "PNG")
    return filepath


def get_icon_paths() -> Dict[StatusState, str]:
    return {
        StatusState.GOOD: generate_status_icon("#2ECC71", "AC", "wifi_ac_green.png"),
        StatusState.RETRYING: generate_status_icon("#F39C12", "RST", "wifi_ac_yellow.png"),
        StatusState.FAILED: generate_status_icon("#E74C3C", "DOWN", "wifi_ac_red.png"),
        StatusState.DISCONNECTED: generate_disconnected_icon(),
        StatusState.STANDBY: generate_status_icon("#3498DB", "STBY", "wifi_ac_blue.png"),
        StatusState.IDLE: generate_status_icon("#3498DB", "IDLE", "wifi_ac_blue.png"),
    }


def create_pillow_icon_for_state(state: StatusState) -> Image.Image:
    paths = get_icon_paths()
    path = paths.get(state, paths[StatusState.IDLE])
    return Image.open(path)
