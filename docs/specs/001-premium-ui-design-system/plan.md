# Implementation Plan: Premium UI & Design System

**Branch**: `001-premium-ui-design-system` | **Date**: 2026-08-06 | **Spec**: `specs/001-premium-ui-design-system/spec.md`
**Input**: Feature specification from `specs/001-premium-ui-design-system/spec.md`

## Summary

Extract a single design-token module and a small reusable component layer from the existing `ui.py`, then re-express the current 540×740 dashboard, settings dialog, about dialog, tray tooltips, and CLI status output in terms of those tokens — adding keyboard/focus accessibility, verified WCAG-AA contrast, plain-language terminology (Upload/Download Link Speed), and optional budget-bounded animation. **Presentation-only**: no engine, threshold, reset, standby, detection, or config-schema changes (D-003). The work is sequenced so each milestone is independently reviewable and the app stays shippable after every step.

## Technical Context

**Language/Version**: Python ≥ 3.8 (dev/runtime observed: CPython 3.14)
**Primary Dependencies**: stdlib Tkinter (+`tkinter.ttk`, `tkinter.font`); `pystray` ≥ 0.19; `Pillow` ≥ 9.0. No new runtime dependencies introduced.
**Storage**: JSON config at `%APPDATA%\wifi-ac-guardian\config.json` (unchanged; read-only from this feature's perspective except existing save paths).
**Testing**: `pytest` / `unittest` (6 tests today, all passing). New pure-logic units (token contrast, status descriptor mapping) are unit-testable headlessly; Tkinter rendering is validated manually.
**Target Platform**: Windows 11 (Windows 10 compatible); dark theme only.
**Project Type**: Single desktop application package (`wifi_ac_guardian_win/`).
**Performance Goals**: No perceptible stutter on state transition/reset; animation frame budget ≤ 16 ms/frame target, hard degrade-to-instant if a frame would exceed ~33 ms; zero per-frame asset reloads (assets stay cached).
**Constraints**: Fixed 540×740 non-resizable window (current shipping reality, C-09); must remain legible and in-bounds at 100–200% Windows scaling; four architecture invariants are non-negotiable; no feature regression (FR-025).
**Scale/Scope**: Single window + 2 dialogs + tray + CLI status. ~2 source files heavily touched (`ui.py`, small edits to `tray.py`, `cli.py`, `notifier_win.py`), ~2 new modules (`theme.py`, `status_presentation.py`), 1 design-system doc.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify against `.specify/memory/constitution.md` (v1.0.0):

- [x] **I. User First** — Hero-first hierarchy + plain-language headlines directly implement the three questions (US1, FR-005–FR-008).
- [x] **II. Zero Feature Regression** — FR-025 enumerates every capability that must survive; non-regression is an explicit acceptance gate (SC-006).
- [x] **III. Premium Desktop Experience** — Token system + component consistency + focus/motion raise fidelity toward the reference bar within Tkinter (D-004 tension acknowledged, not resolved here).
- [x] **IV. Beautiful Simplicity** — Consolidating literals into tokens and enforcing one hierarchy reduces clutter; no new surfaces added.
- [x] **V. Professional Engineering** — Spec-first; milestones are small, independently reviewable commits.
- [x] **VI. Performance First** — Animation is budget-bounded with mandatory degrade-to-instant (FR-023); asset caching preserved (FR-028).
- [x] **VII. Accessibility** — Keyboard traversal, focus rings, WCAG-AA contrast are first-class requirements (US4, FR-018–FR-021).
- [x] **VIII. Consistency** — Single token source + single status-presentation descriptor make consistency mechanically checkable (SC-002).
- [x] **IX. Reliability** — Presentation-only; engine untouched, so perceived and actual reliability are preserved.
- [x] **X. Code Quality** — Removes duplication (literals → tokens), separates presentation config from layout code, keeps `core/` free of UI imports.

Architecture invariants (non-negotiable):

- [x] Single-instance enforcement preserved (`SingleInstanceChecker`) — untouched.
- [x] All subprocess calls pass `CREATE_NO_WINDOW` — no new subprocess calls introduced; existing ones untouched.
- [x] Background-thread Tkinter updates dispatched via `widget.after(0, ...)` — existing `_refresh_status`/tray callback pattern preserved; no new background→UI path added without `after(0,…)`.
- [x] Tray icon reassigned only on state change — `tray.py` icon-caching logic preserved; only tooltip/label text sourced from the new descriptor.

**Result: PASS.** No violations; Complexity Tracking table intentionally empty.

## Recommended Architecture (presentation layer only)

Only now are architectural recommendations made, per session protocol.

### Recommendation R-1 — Introduce `wifi_ac_guardian_win/theme.py` (design tokens)

- **Why**: `ui.py` currently defines ~20 module-level color constants plus dozens of inline literals and font tuples; the settings dialog even uses different font families (`"Segoe UI"`, `"Consolas"`) than the dashboard. Principle VIII cannot be enforced while the language is scattered.
- **Benefit**: One source of truth; a token change propagates everywhere (SC-002); enables headless contrast unit tests.
- **Risk**: Low. Mechanical extraction; existing constant names can alias to tokens to minimize churn.
- **Alternatives considered**: (a) Leave constants in `ui.py` — rejected, not reusable by `tray.py`/dialogs and not a single source. (b) A JSON/TOML theme file loaded at runtime — rejected as over-engineering for a single built-in dark theme (Principle IV); a Python module is simpler and importable.

### Recommendation R-2 — Introduce `wifi_ac_guardian_win/status_presentation.py` (status descriptor)

- **Why**: State→visual mapping is currently duplicated and divergent across `ui.py._update_ui` (headline/color/artwork), `tray.py._get_status_text`/`_get_reconnect_label` (tooltip/action), and `notifier_win.py`. They can disagree.
- **Benefit**: Single mapping of `StatusState` → (accent, headline, supporting text, artwork, tray tooltip, action label) consumed by all three (FR-010). Removes duplication (Principle X) and guarantees agreement (Principle IX).
- **Risk**: Low–medium. Must preserve every existing state's current wording/behavior (FR-025); mitigated by a mapping unit test.
- **Alternatives considered**: Embed mapping in `models.py` — rejected; `core/` must not carry presentation concerns (Principle X / architecture rule that `core/` imports no UI). Keep per-surface — rejected; that is the current defect.

### Recommendation R-3 — Make custom Canvas buttons focusable (`RoundedButton`)

- **Why**: `RoundedButton` (a `tk.Canvas`) does not participate in focus traversal; Principle VII is unmet for the primary actions.
- **Benefit**: Full keyboard operability + visible focus ring (FR-018/FR-019).
- **Risk**: Medium — must add `takefocus`, `<FocusIn>/<FocusOut>`, `<Return>/<space>` bindings and a focus-ring draw path without regressing hover/press visuals.
- **Alternatives considered**: Replace custom buttons with `ttk.Button` — rejected; loses the established rounded premium look (Principle III) and would be a larger visual change than warranted.

### Recommendation R-4 — Defer the Tkinter-vs-native framework question to a dedicated ADR

- **Why**: D-004 records an open tension between Principle III and Tkinter's rendering ceiling. This feature deliberately does not resolve it.
- **Benefit**: Keeps this feature small and reversible; the design-token module is framework-agnostic enough to survive a later migration.
- **Risk**: The fidelity ceiling may cap how "premium" the result can look. Accepted for now.
- **Action**: 📋 Architectural decision candidate — see ADR suggestion at end of plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-premium-ui-design-system/
├── spec.md              # Complete (includes Clarifications)
├── plan.md              # This file
├── tasks.md             # /sp.tasks output
└── analysis.md          # Repository analysis (this session)
```

Design-system reference lives in `docs/DESIGN_SYSTEM.md` (product memory), not under specs/, so it stays discoverable long-term.

### Source Code (repository root)

```text
wifi_ac_guardian_win/
├── theme.py                     # NEW — design tokens (color/type/spacing/radius) + contrast helper
├── status_presentation.py       # NEW — StatusState → presentation descriptor (single source)
├── ui.py                        # MODIFY — consume theme + descriptor + components; a11y; terminology
├── tray.py                      # MODIFY — tooltip/action text from descriptor (icon caching untouched)
├── cli.py                       # MODIFY — --status label terminology only
├── core/
│   └── notifier_win.py          # MODIFY (light) — notification text from descriptor
│   └── (models.py, guardian.py, detector_win.py, reconnector_win.py — UNTOUCHED)
└── assets/                      # UNTOUCHED (reused via existing cache)

tests/
├── test_theme.py                # NEW — token contrast (WCAG-AA) unit tests, headless
├── test_status_presentation.py  # NEW — every StatusState maps to a complete descriptor
└── (test_detector.py, test_reconnector.py, test_target_ssid.py — UNTOUCHED)

docs/
└── DESIGN_SYSTEM.md             # NEW — documented tokens, type ramp, contrast ratios, components
```

**Structure Decision**: Single-project desktop package. Two new leaf modules (`theme.py`, `status_presentation.py`) carry the reusable design language; `ui.py` is refactored to consume them. `core/` remains free of UI imports (architecture rule preserved). No package layout change, no new dependency.

## Phase Plan / Milestones

Each milestone is independently reviewable, leaves the app shippable, and passes both quality gates before the next begins.

- **M0 — Baseline & safety net** (checkpoint): capture current UI screenshots per state; confirm gates green; record literal-count baseline. Enables before/after verification (SC-002, SC-006).
- **M1 — Design tokens** (US2, R-1): create `theme.py`; add contrast unit test; alias existing `ui.py` constants to tokens (no visual change yet). *Checkpoint: gates green, app visually identical.*
- **M2 — Status presentation descriptor** (US1/US2, R-2): create `status_presentation.py` + unit test; route `ui.py`, `tray.py`, `notifier_win.py` through it. *Checkpoint: every state renders exactly as before, from one source.*
- **M3 — Component pass** (US1/US2, FR-011/FR-012): refactor card/button/KPI/section-header/meter to consume tokens; enforce hero-first hierarchy (FR-013); derive displayed defaults from live config (FR-015). *Checkpoint: visual polish lands; no feature lost.*
- **M4 — Terminology** (US3, FR-016/FR-017): Upload/Download Link Speed across dashboard, hero grid, tray tooltip, `cli.py --status`. *Checkpoint: zero TX/RX strings (SC-005).*
- **M5 — Accessibility & DPI** (US4, R-3): focusable custom buttons, tab order, focus rings, Enter/Space activation; verify 100–200% scaling; finalize `docs/DESIGN_SYSTEM.md` with measured contrast. *Checkpoint: SC-003/SC-004/SC-007.*
- **M6 — Animation (optional, budget-gated)** (US5, FR-023/FR-024): eased transitions + speed-bar tween + subtle reset progress, each with degrade-to-instant. *Checkpoint: SC-008; if any animation misses budget, it ships disabled.*

### Dependencies

- M1 blocks M2–M6 (everything consumes tokens).
- M2 blocks M3 (hero/components render from the descriptor).
- M3 blocks M4–M6 (terminology/a11y/motion apply to finalized components).
- M6 depends on M3 (components) and M5 (focus visuals must not fight animation).

### Reusable components (already present — restyle, don't rebuild)

`RoundedCard`, `RoundedButton`, `SegmentedSpeedBar`, `LineIcon` (currently unused — either adopt in M3 or remove as dead code; decide in tasks), `_fluent_image`/`_router_status_image` caches (keep; satisfy FR-028).

### Engineering checkpoints (gates at every milestone)

1. `python -m compileall -q wifi_ac_guardian_win` passes.
2. `python -m pytest -q` — all tests pass (6 existing + new).
3. Manual visual inspection vs. M0 baseline for each of the 6 states.
4. Feature-parity checklist (FR-025) re-verified.

## Complexity Tracking

> No Constitution Check violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

---

📋 **Architectural decision detected**: Tkinter is retained for premium UI work despite the Principle III fidelity ceiling (D-004 open tension), and this feature introduces a framework-agnostic token layer to keep a future migration open. Document reasoning and tradeoffs? Run `/sp.adr tkinter-retention-and-design-token-layer`
