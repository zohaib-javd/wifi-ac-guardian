# Design System — WiFi AC Guardian

Single source of truth: [`wifi_ac_guardian_win/theme.py`](../wifi_ac_guardian_win/theme.py).
Every value below is defined there; `ui.py` consumes them through thin `COLOR_*` / `FONT_*`
aliases. **Edit tokens in `theme.py`, never in `ui.py`.** `core/` must never import `theme.py`
(presentation-only boundary).

This document satisfies FR-004/FR-020 (documented, checkable design language) and records the
measured WCAG-AA contrast ratios from the `tests/test_theme.py` suite (T011).

---

## 1. Color tokens

### Surfaces

| Token | Value | Role |
|-------|-------|------|
| `BG` | `#151515` | Main window background |
| `CARD` | `#1E1E1E` | Card surface |
| `PANEL` | `#252525` | Secondary panel |
| `BORDER` | `#323232` | Soft border / disabled fill |

### Semantic accents (each with a paired subtle background)

| Token | Value | Paired BG | Meaning |
|-------|-------|-----------|---------|
| `ACCENT` | `#24C26A` | `ACCENT_BG` `#1A2F22` | GOOD / protected (emerald) |
| `WARN` | `#F4B740` | `WARN_BG` `#2E2616` | Reconnecting / retrying (amber) |
| `ERROR` | `#E74C3C` | `ERROR_BG` `#2E1818` | Downgraded / disconnected (red) |
| `INFO` | `#3B82F6` | `INFO_BG` `#182438` | Standby / idle (blue) |

### Text ramp

| Token | Value | Role |
|-------|-------|------|
| `TEXT_PRIMARY` | `#FFFFFF` | High-contrast primary |
| `TEXT_SECONDARY` | `#B6B6B6` | Readable secondary |
| `TEXT_MUTED` | `#8C8C8C` | De-emphasized captions/labels (lightened from `#666666` per D-011 to clear AA on all surfaces) |

### Accent foreground ink (text drawn on a filled accent)

| Token | Value | Drawn on |
|-------|-------|----------|
| `ON_ACCENT` | `#0A1C11` | `ACCENT` |
| `ON_ERROR` | `#FFFFFF` | `ERROR` |
| `ON_WARN` | `#121212` | `WARN` |

### Interaction states

| Token | Value | Role |
|-------|-------|------|
| `ACCENT_HOVER` | `#2AE07B` | Emerald button hover |
| `ERROR_HOVER` | `#FF6255` | Red button hover |
| `PANEL_HOVER` | `#303030` | Neutral panel button hover |
| `FOCUS_RING` | `#FFFFFF` | Keyboard focus outline, drawn inset on the button fill (T050) |

### Speed-bar zones (bitrate quality meter)

| Token | Value | Role |
|-------|-------|------|
| `TRACK` | `#333333` | Empty track behind the segmented bar |
| `ZONE_RED` | `#E74C3C` | 0–200 Mbps |
| `ZONE_ORANGE` | `#F39C12` | 200–300 Mbps + threshold caption |
| `ZONE_GREEN` | `#2ECC71` | 300+ Mbps |
| `SCALE_LABEL` | `#BBBBBB` | Scale end labels |

---

## 2. Typography

Families: `FONT_UI` = *Segoe UI Variable*, `FONT_DISPLAY` = *Segoe UI Variable Display*,
`FONT_MONO` = *Cascadia Mono*.

Type ramp — `(family, size, weight)`, named by role:

| Token | Spec | Role |
|-------|------|------|
| `TYPE_DISPLAY` | Display / 19 / bold | App title |
| `TYPE_TITLE` | UI / 12 / bold | Dialog / section title |
| `TYPE_SECTION` | UI / 10 / bold | Section header |
| `TYPE_HERO` | UI / 11 / bold | Hero status headline |
| `TYPE_BODY` | UI / 9 | Body text |
| `TYPE_CAPTION` | UI / 8 | Caption / helper text |
| `TYPE_LABEL` | UI / 7 / bold | Uppercase KPI / field labels |
| `TYPE_SUBTITLE` | UI / 9 | Header subtitle |
| `TYPE_MONO` | Mono / 9 / bold | Metric values |
| `TYPE_MONO_SM` | Mono / 8 / bold | Small metric values |
| `TYPE_BUTTON` | UI / 9 / bold | Primary button label |
| `TYPE_BUTTON_SM` | UI / 8 / bold | Toolbar button label |

---

## 3. Spacing & radius scales

Spacing (px): `SPACE_XS` 3 · `SPACE_SM` 6 · `SPACE_MD` 12 · `SPACE_LG` 18 · `SPACE_XL` 24 ·
`SPACE_2XL` 28.

Radius (px): `RADIUS_SM` 10 · `RADIUS_MD` 12 · `RADIUS_LG` 14 · `RADIUS_XL` 16.

---

## 4. Component states

### `RoundedButton`

| State | Fill | Foreground | Notes |
|-------|------|------------|-------|
| Normal | `bg` arg | `fg` arg | — |
| Hover | `activebackground` | `activeforeground` | mouse over, normal state only |
| Focused | (unchanged fill) | (unchanged fg) | inset `FOCUS_RING` outline; `Tab` to reach, `Enter`/`Space` activate (T050) |
| Disabled | `BORDER` | `TEXT_MUTED` | no hover, no activation |

Tab order (T051): **Reconnect → Stop/Start protection → Settings → View Log → About**, matching
widget creation order (Tk traversal follows creation order). Decorative canvases
(`SegmentedSpeedBar`, card backdrops) carry no keyboard bindings and are skipped by Tk focus
traversal.

### `SegmentedSpeedBar`

Purely decorative meter: `TRACK` behind, red/orange/green zones, `SCALE_LABEL` end labels,
`ORANGE` threshold caption. Not a tab stop.

### Status surfaces

All status-dependent color/text (hero, KPI, tray tooltip, toast) derives from one
`StatusState → StatusPresentation` mapping in `status_presentation.py` (M2) — never hand-mapped
per surface.

---

## 5. Measured WCAG-AA contrast (from `tests/test_theme.py`, T011)

Thresholds: **≥ 4.5:1** normal text, **≥ 3.0:1** large text / non-text UI.

### Text on surfaces

| Foreground | `BG` | `CARD` | `PANEL` |
|------------|------|--------|---------|
| `TEXT_PRIMARY` | 18.26:1 | 16.67:1 | 15.33:1 |
| `TEXT_SECONDARY` | 9.01:1 | 8.22:1 | 7.56:1 |
| `TEXT_MUTED` | 5.43:1 | 4.96:1 | 4.56:1 |

All clear AA-normal (≥ 4.5:1).

### Accent status text on `CARD` (AA-large ≥ 3.0:1)

`ACCENT` 7.14:1 · `WARN` 9.28:1 · `ERROR` 4.36:1 · `INFO` 4.53:1.

### Button ink on accent fills (AA-large ≥ 3.0:1)

`ON_ACCENT` on `ACCENT` 7.58:1 · `ON_ERROR` on `ERROR` 3.82:1 · `ON_WARN` on `WARN` 10.43:1.

SC-004 satisfied: every shipping pairing meets or exceeds its AA threshold.

---

## 6. DPI & scaling (SC-007)

Target window: **540 × 740** logical px. Verification at 100 / 125 / 150 / 175 / 200% Windows
display scaling is an informal visual check performed on a real desktop session (the full UI binds
a live monitoring thread and single-instance socket that do not run in a headless shell). Findings
per scale are recorded below.

| Scale | Legible? | Clipping outside 540×740? | Notes |
|-------|----------|---------------------------|-------|
| 100% | _pending desktop check_ | | |
| 125% | _pending desktop check_ | | |
| 150% | _pending desktop check_ | | |
| 175% | _pending desktop check_ | | |
| 200% | _pending desktop check_ | | |

No Tk DPI-awareness call was added: Tk on Windows already scales fonts/geometry with the system
DPI, and adding `SetProcessDpiAwareness` risks disturbing the window/tray behavior guarded by the
architecture invariants. A call will be added only if the desktop check reveals a concrete legibility
or clipping defect (T052 acceptance).

---

## 7. Motion (M6, `wifi_ac_guardian_win/animation.py`)

WiFi AC Guardian is a background utility, not a dashboard. Motion may only sharpen perceived
quality; it must never draw attention. The engine is a single small module; `core/` must never
import it (presentation-only boundary).

### Policy

- **Event-driven only.** Motion runs in response to a discrete state/value change — never idle,
  looping, pulsing, or continuous. No animated backgrounds, glows, or particles.
- **Duration 150–250 ms** (`DURATION_MS = 200`), **cubic ease-in-out** (`ease_in_out`).
- **Main thread only.** Every tween is driven by `widget.after()`; nothing touches the monitor
  or reconnect threads, so timing is unaffected (FR-016).
- **Time-based interpolation.** A slow frame drops intermediate steps rather than stretching the
  animation — total duration is fixed and the UI stays responsive.
- **Zero cost when closed / tray / minimized.** `after()` only fires inside a running mainloop,
  and `animate()` refuses a non-viewable widget (`winfo_viewable()` → instant `apply(1.0)`), so a
  hidden or withdrawn window does no per-frame work.
- **Single global setting, default OFF.** `Settings → “Enable animations (experimental)”`
  persists to `animations_enabled` (default `False`) until validated on real hardware.
- **Automatic fallback.** If frames slip past the budget (`_FRAME_MS + _BUDGET_SLIP_MS`) twice
  in one tween, the engine snaps to the final value and disables motion for the rest of the
  session (`is_enabled()` returns `False` until the user re-opts-in). Stutter never persists.

### Shipped animations

| ID | Surface | What animates | Trigger |
|----|---------|---------------|---------|
| T060 | Hero headline | Foreground color cross-fade between status accents (`lerp_color`) | Protection **state** change |
| T061 | `SegmentedSpeedBar` | Fill value tween toward the new speed; restart cancels the prior tween; sub-0.5 Mbps deltas snap instantly | New link-speed **reading** |

### Deferred (documented, not shipped)

- **Hero artwork alpha-fade** — Tk `PhotoImage` has no cheap per-frame alpha; a real cross-fade
  would need pre-blended frames per state pair. Deferred to avoid asset/CPU cost for a background
  app; the headline color cross-fade already signals the state change.
- **Hover tweens (buttons/cards)** — hover fires rapidly; instant hover feedback is already
  crisp and rapid-fire tweens risk visible churn. Kept instant.
- **Reset-progress cue (T062, ~45 s)** — a continuous progress indicator during the reconnect
  wait would be idle/looping motion, which the policy forbids. Left as an instant state label.

These are intentional scope boundaries, not omissions: each would either violate the “no
continuous/idle motion” rule or add cost disproportionate to a background utility.

### Verification

Pure logic (easing curve, color interpolation, enable/fallback state machine) is unit-tested in
`tests/test_animation.py`. The `after()`-driven loop needs a live mainloop; perceived smoothness
and click-responsiveness (SC-008) are confirmed on the desktop, where the toggle is also exercised.
