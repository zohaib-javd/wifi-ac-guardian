---
id: 0005
title: Implement M6 Animation Engine
stage: green
date: 2026-08-06
surface: agent
model: claude-opus-4-8
feature: 001-premium-ui-design-system
branch: master
user: Zohaib
command: "Implement M6."
labels: ["m6", "animation", "motion", "tkinter", "after", "design-system", "feature-001"]
links:
  spec: specs/001-premium-ui-design-system/spec.md
  ticket: null
  adr: docs/DECISIONS.md#D-014
  pr: null
files:
 - wifi_ac_guardian_win/animation.py
 - wifi_ac_guardian_win/ui.py
 - wifi_ac_guardian_win/config.py
 - wifi_ac_guardian_win/core/models.py
 - tests/test_animation.py
 - docs/DECISIONS.md
 - docs/DESIGN_SYSTEM.md
 - PROJECT_STATUS.md
 - docs/SESSION_LOG.md
tests:
 - python -m compileall -q wifi_ac_guardian_win (clean, exit 0)
 - python -m pytest -q (26 passed / 141 subtests)
 - tests/test_animation.py (9 tests: ease_in_out, lerp_color, enable/fallback state machine)
---

## Prompt

Implement M6. Animations must enhance perceived quality without drawing attention. This is a background utility, not a dashboard. Animation principles: • Duration: 150–250 ms • Smooth ease-in/ease-out curves • No continuous animations • No pulsing • No looping • No idle animations • No animated backgrounds • No glowing effects • No particle effects • No unnecessary fades. Allow only event-driven animations, such as: • Status card cross-fade when state changes • Progress bar value transition • Button hover transitions • Card hover highlights • Success/error toast fade • Hero artwork fade when protection state changes. Do not animate while the application is minimized or only running in the system tray. Animations must consume effectively zero CPU when the Control Panel is closed. Animations must never affect monitoring performance or reconnect timing. All animations must use Tkinter's after() mechanism on the main UI thread. Provide a single global animation setting. Default it to OFF until performance is validated on a real desktop. If enabling animations causes measurable CPU usage or reduced responsiveness, automatically fall back to instant updates.

## Response snapshot

Implemented M6 (Animation) of feature `001-premium-ui-design-system` to the stated principles.

- New `wifi_ac_guardian_win/animation.py` — a small `after()`-driven, main-thread engine.
  Event-driven only; `DURATION_MS=200` (in the 150–250 ms band); cubic `ease_in_out`;
  **time-based** interpolation so a slow frame drops intermediate steps rather than stretching
  the tween (fixed total duration, responsive UI). `winfo_viewable()` guard → when the panel is
  closed/minimized/in the tray, `animate()` applies the final value once and does no per-frame
  work (zero cost, satisfies the "no motion in tray / zero CPU when closed" rules). Automatic
  **session fallback to instant**: two frame-budget slips in one tween latch `is_enabled()` to
  False until the user re-opts-in. `core/` never imports it (presentation-only boundary, D-003).
- T060 — hero status headline **color** cross-fade between state accents via `lerp_color`, routed
  through a new `_set_hero_headline(text, accent)`; text swaps instantly, only the color eases
  (ghost-free), and it no-ops on first paint / same accent.
- T061 — `SegmentedSpeedBar.set_speed` value tween that cancels any in-flight tween on restart
  and snaps instantly for sub-0.5 Mbps deltas (avoids needless `after()` churn each poll).
- Single global setting: `animations_enabled` (default **False**) added to `GuardianConfig`
  (models.py), wired through `config.py` load/save, exposed as the "Enable animations
  (experimental)" checkbox in Settings, applied via `animation.set_enabled(...)`.
- Deferred with rationale (DESIGN_SYSTEM.md §7 + D-014): hero artwork alpha-fade (Tk `PhotoImage`
  has no cheap per-frame alpha), hover tweens (rapid-fire; already instant), and the T062 ~45 s
  reset-progress cue (would be continuous/idle motion, forbidden by policy).
- Added `tests/test_animation.py` (9 tests) over the pure logic. Synced PROJECT_STATUS.md
  (M6 complete) and SESSION_LOG.md; committed M6 (f163dd9).

## Outcome

- ✅ Impact: optional, calm, event-driven motion (US5) that is invisible by default and cannot
  affect monitoring/reconnect timing; existing instant behavior fully preserved (FR-025).
- 🧪 Tests: compileall clean; pytest 26 passed / 141 subtests (was 17/40; +9 animation tests).
- 📁 Files: 9 changed, +416/-12 (animation.py + test_animation.py new).
- 🔁 Next prompts: final Engineering Implementation Report; desktop SC-007 (DPI) + SC-008 (motion) passes.
- 🧠 Reflection: motion is presentation-only and default-OFF, so the risky part (perceived
  smoothness) is a desktop check; the engine self-limits under load rather than trusting the host.

## Evaluation notes (flywheel)

- Failure modes observed: the `after()` loop needs a live mainloop and the full UI can't run
  headless (live monitor thread + single-instance socket) — so only the pure logic is unit-tested;
  perceived smoothness / click-responsiveness (SC-008) is deferred to the desktop.
- Graders run and results (PASS/FAIL): compileall PASS; pytest PASS (26/141); animation unit tests PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): on desktop, enable the toggle and confirm no perceptible
  stutter during a real state change / speed sweep; if any slip is seen, the session fallback should
  already have snapped to instant — verify the latch trips as designed.
