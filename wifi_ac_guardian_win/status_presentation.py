"""
Status presentation descriptor — single source of truth for state→visual mapping.

Maps each StatusState to (accent color, headline, supporting text, artwork key, tray
tooltip, primary-action label) so the dashboard, tray, and notifications can never
disagree (analysis F-07, plan R-2, task T020).

`core/` must never import this module — it is presentation-only.
"""

from dataclasses import dataclass
from typing import Optional

from wifi_ac_guardian_win.core.models import StatusState
from wifi_ac_guardian_win import theme


@dataclass(frozen=True)
class StatusPresentation:
    """Complete visual descriptor for one StatusState."""
    accent: str                # Token name or hex — the primary color for this state
    headline: str              # Dashboard hero headline (plain language, FR-007)
    supporting: str            # Dashboard supporting sentence (optional, use "" if none)
    artwork: str               # Router status artwork filename (from ROUTER_STATUS_ASSETS)
    tray_tooltip_prefix: str   # Tray tooltip emoji + short label (e.g., "🟢 GOOD")
    action_label: str          # Primary action button label for this state


def get_presentation(state: StatusState, target_ssid: Optional[str] = None) -> StatusPresentation:
    """
    Return the visual presentation descriptor for a given state.

    :param state: The StatusState to describe.
    :param target_ssid: The protected target SSID (used for Standby action label).
    :return: A StatusPresentation with all visual attributes.
    """
    target = target_ssid or "lab5g"

    if state == StatusState.GOOD:
        return StatusPresentation(
            accent=theme.ACCENT,
            headline="HIGH-SPEED WI-FI PROTECTED",
            supporting="Your connection is using Wi-Fi 5 or better at premium speeds.",
            artwork="good.png",
            tray_tooltip_prefix="🟢 GOOD",
            action_label="Reconnect now",
        )

    elif state == StatusState.RETRYING:
        return StatusPresentation(
            accent=theme.WARN,
            headline="RESTORING WI-FI 5 SPEED...",
            supporting="Resetting the adapter to restore your high-speed connection.",
            artwork="retrying.png",
            tray_tooltip_prefix="🟡 RESTORING",
            action_label="Reconnecting...",
        )

    elif state == StatusState.FAILED:
        return StatusPresentation(
            accent=theme.ERROR,
            headline="WI-FI DOWNGRADED",
            supporting="Your connection dropped to Wi-Fi 4 or a lower speed. Try reconnecting.",
            artwork="failed.png",
            tray_tooltip_prefix="🔴 DOWNGRADED",
            action_label="Reconnect now",
        )

    elif state == StatusState.STANDBY:
        return StatusPresentation(
            accent=theme.INFO,
            headline="BACKUP NETWORK (STANDBY)",
            supporting="You're connected to a backup network. Protection is paused.",
            artwork="standby.png",
            tray_tooltip_prefix="🔵 BACKUP",
            action_label=f"Switch to {target}",
        )

    elif state == StatusState.DISCONNECTED:
        return StatusPresentation(
            accent=theme.ERROR,
            headline="DISCONNECTED",
            supporting="No Wi-Fi connection detected.",
            artwork="failed.png",
            tray_tooltip_prefix="🔴 DISCONNECTED",
            action_label="Reconnect now",
        )

    else:  # IDLE or unknown
        return StatusPresentation(
            accent=theme.INFO,
            headline="INITIALIZING",
            supporting="",
            artwork="standby.png",
            tray_tooltip_prefix="WiFi AC Guardian",
            action_label="Reconnect now",
        )
