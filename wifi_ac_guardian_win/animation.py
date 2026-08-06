"""
Event-driven UI micro-animations (feature 001, M6). Presentation-only.

Principles (per approved M6 direction):
- Event-driven only — no idle / looping / pulsing / continuous motion.
- 150-250 ms, cubic ease-in-out.
- Runs solely on the Tk main thread via ``widget.after()``. Interpolation is
  time-based, so a slow frame drops intermediate steps rather than stretching
  the animation — responsiveness is preserved and total duration stays fixed.
- Zero cost when the Control Panel is closed or in the tray: ``after()`` only
  fires while the mainloop runs, and we refuse to animate a non-viewable widget.
- One global setting, default OFF, with automatic fallback to instant updates
  if a frame budget is missed (stutter / CPU pressure) — never re-enabled until
  the user explicitly opts back in.
- ``core/`` must never import this module — monitoring/threading are untouched.
"""

from __future__ import annotations

import time
from typing import Callable, Optional, Tuple

DURATION_MS = 200          # within the 150-250 ms band
_FRAME_MS = 16             # ~60 fps cadence
_BUDGET_SLIP_MS = 40       # a frame later than cadence+this counts as a stutter
_MAX_SLIPS = 2             # this many stutters -> fall back to instant this session

# Single global setting (default OFF) + session fallback latch.
_enabled = False
_disabled_by_fallback = False


def set_enabled(value: bool) -> None:
    """Set the global animation preference. Re-enabling clears a prior fallback."""
    global _enabled, _disabled_by_fallback
    _enabled = bool(value)
    if _enabled:
        _disabled_by_fallback = False


def is_enabled() -> bool:
    """True only when the user opted in and no stutter fallback has tripped."""
    return _enabled and not _disabled_by_fallback


def _trip_fallback() -> None:
    global _disabled_by_fallback
    _disabled_by_fallback = True


def ease_in_out(t: float) -> float:
    """Cubic ease-in-out over t in [0, 1]."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    if t < 0.5:
        return 4.0 * t * t * t
    f = (2.0 * t) - 2.0
    return 0.5 * f * f * f + 1.0


def _hex_to_rgb(color: str) -> Optional[Tuple[int, int, int]]:
    if not isinstance(color, str) or not color.startswith("#") or len(color) != 7:
        return None
    try:
        return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    except ValueError:
        return None


def lerp_color(start_hex: str, end_hex: str, t: float) -> str:
    """Linear interpolation between two ``#RRGGBB`` colors; falls back to end."""
    a = _hex_to_rgb(start_hex)
    b = _hex_to_rgb(end_hex)
    if a is None or b is None:
        return end_hex
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    r = round(a[0] + (b[0] - a[0]) * t)
    g = round(a[1] + (b[1] - a[1]) * t)
    bl = round(a[2] + (b[2] - a[2]) * t)
    return f"#{r:02X}{g:02X}{bl:02X}"


def _is_viewable(widget) -> bool:
    """False when the window is closed, iconified, or withdrawn to the tray."""
    try:
        return bool(widget.winfo_viewable())
    except Exception:
        return False


class _Anim:
    __slots__ = ("widget", "after_id", "stopped")

    def __init__(self, widget) -> None:
        self.widget = widget
        self.after_id = None
        self.stopped = False

    def cancel(self) -> None:
        self.stopped = True
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None


def animate(widget, apply_fn: Callable[[float], None], *,
            duration_ms: int = DURATION_MS,
            on_done: Optional[Callable[[], None]] = None) -> Optional[_Anim]:
    """Drive ``apply_fn(eased_t)`` from 0->1 over ``duration_ms`` via ``after()``.

    When animations are disabled or the widget is not viewable, ``apply_fn(1.0)``
    is invoked once (instant update) and ``None`` is returned. Otherwise returns
    an ``_Anim`` handle whose ``.cancel()`` stops the tween.
    """
    if not is_enabled() or not _is_viewable(widget):
        apply_fn(1.0)
        if on_done:
            on_done()
        return None

    anim = _Anim(widget)
    start = time.perf_counter()
    state = {"last": start, "slips": 0}

    def step() -> None:
        if anim.stopped:
            return
        now = time.perf_counter()
        gap_ms = (now - state["last"]) * 1000.0
        state["last"] = now
        if gap_ms > (_FRAME_MS + _BUDGET_SLIP_MS):
            state["slips"] += 1
            if state["slips"] >= _MAX_SLIPS:
                _trip_fallback()
                anim.stopped = True
                apply_fn(1.0)
                if on_done:
                    on_done()
                return
        frac = ((now - start) * 1000.0) / duration_ms if duration_ms > 0 else 1.0
        if frac >= 1.0:
            anim.stopped = True
            apply_fn(1.0)
            if on_done:
                on_done()
            return
        apply_fn(ease_in_out(frac))
        anim.after_id = widget.after(_FRAME_MS, step)

    apply_fn(0.0)
    anim.after_id = widget.after(_FRAME_MS, step)
    return anim
