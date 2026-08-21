---
description: "Task list for Premium UI & Design System"
---

# Tasks: Premium UI & Design System

**Input**: Design documents from `specs/001-premium-ui-design-system/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Included where they add value as headless, deterministic checks (token contrast, status-descriptor completeness). Tkinter rendering is verified manually per milestone checkpoint.

**Organization**: Grouped by milestone (M0–M6) mapped to user stories (US1–US5). Each task is independently reviewable and testable. Every task is presentation-only (D-003); none may alter engine, thresholds, reset, standby, detection, or config schema.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency)
- Complexity: **S** (≤~1h), **M** (~half day), **L** (~1 day)

---

## Phase M0: Baseline & Safety Net (Shared)

**Purpose**: Establish a verifiable before/after baseline. No production code changes.

### T001 [P] [US-all] Capture per-state UI baseline

- **Purpose**: Enable visual regression comparison across the whole feature.
- **Description**: Launch the current GUI; capture screenshots of all 6 `StatusState` presentations (GOOD, RETRYING, FAILED, DISCONNECTED, STANDBY, IDLE) by forcing each state. Store under `specs/001-premium-ui-design-system/baseline/`.
- **Dependencies**: none.
- **Expected files**: `specs/001-premium-ui-design-system/baseline/*.png` (new, non-shipping).
- **Acceptance**: 6 labeled screenshots exist; each state visibly distinct.
- **Complexity**: S.

### T002 [P] [US2] Record literal-count baseline

- **Purpose**: Make SC-002 measurable.
- **Description**: Count raw hex color literals and magic spacing integers in `ui.py`/`tray.py` outside any token module; record the number in `analysis.md` / commit message.
- **Dependencies**: none.
- **Expected files**: note appended to `specs/001-premium-ui-design-system/analysis.md`.
- **Acceptance**: baseline integer recorded (expected ~30+).
- **Complexity**: S.

### T003 [US-all] Confirm quality gates green at baseline

- **Purpose**: Prove starting state is clean.
- **Description**: Run `python -m compileall -q wifi_ac_guardian_win` and `python -m pytest -q`; record results.
- **Dependencies**: none.
- **Acceptance**: compile clean; 6 tests pass.
- **Complexity**: S.

**Checkpoint M0**: baseline captured, gates green.

---

## Phase M1: Design Tokens (US2 — Priority P1)

**Goal**: Single source of truth for the visual language. No visible change yet.

### T010 [US2] Create `theme.py` token module

- **Purpose**: Centralize color, type, spacing, radius, elevation (FR-001, FR-002).
- **Description**: Define named tokens: backgrounds (bg, card, panel, border), 4 semantic accents each with a paired subtle background, 3-level text ramp, type ramp (display/title/body/caption/mono with size+weight), spacing scale, radius scale. Values sourced from the current `ui.py` constants so nothing shifts visually.
- **Dependencies**: T003.
- **Expected files**: `wifi_ac_guardian_win/theme.py` (new).
- **Acceptance**: module imports cleanly; every current `ui.py` color/font/spacing value has a corresponding token.
- **Complexity**: M.

### T011 [US2][P] Add contrast helper + WCAG-AA unit test

- **Purpose**: Make FR-020/SC-004 checkable headlessly.
- **Description**: Add a pure `contrast_ratio(fg, bg)` helper in `theme.py`; write `tests/test_theme.py` asserting every text/background token pairing meets AA (≥4.5 body, ≥3.0 large/UI).
- **Dependencies**: T010.
- **Expected files**: `wifi_ac_guardian_win/theme.py` (edit), `tests/test_theme.py` (new).
- **Acceptance**: test passes for all shipping pairs; any failing pair is adjusted (token tweak) until AA holds, recorded.
- **Complexity**: M.

### T012 [US2] Alias `ui.py` constants to tokens

- **Purpose**: Route existing UI through tokens with zero visual change (FR-003, first pass).
- **Description**: Replace the module-level `COLOR_*`/`FONT_*` definitions in `ui.py` with imports/aliases from `theme.py`. No layout edits yet.
- **Dependencies**: T010.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: app launches visually identical to T001 baseline; gates green.
- **Complexity**: M.

**Checkpoint M1**: tokens exist, contrast test passes, app unchanged visually.

---

## Phase M2: Status Presentation Descriptor (US1/US2 — Priority P1)

**Goal**: One mapping of state → presentation, consumed by dashboard, tray, notifier.

### T020 [US1] Create `status_presentation.py`

- **Purpose**: Single source for state visuals (FR-010).
- **Description**: For each `StatusState`, define (accent token, headline, supporting sentence, artwork asset key, tray tooltip, primary action label). Headlines must be jargon-free (FR-007). Wording must preserve current meanings (FR-025).
- **Dependencies**: T010.
- **Expected files**: `wifi_ac_guardian_win/status_presentation.py` (new).
- **Acceptance**: every `StatusState` has a complete descriptor.
- **Complexity**: M.

### T021 [US1][P] Descriptor completeness unit test

- **Purpose**: Guarantee no state is missing/partial.
- **Description**: `tests/test_status_presentation.py` asserts every `StatusState` yields a descriptor with all fields non-empty and a valid accent token + existing artwork asset filename.
- **Dependencies**: T020.
- **Expected files**: `tests/test_status_presentation.py` (new).
- **Acceptance**: test passes for all 6 states.
- **Complexity**: S.

### T022 [US1] Route `ui.py._update_ui` through the descriptor

- **Purpose**: Dashboard reads presentation from one place.
- **Description**: Replace the per-state `if/elif` color/headline/artwork literals in `_update_ui` with descriptor lookups. Behavior identical.
- **Dependencies**: T020, T012.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: each state matches baseline; gates green.
- **Complexity**: M.

### T023 [US1][P] Route tray + notifier through the descriptor

- **Purpose**: Tray/notification text can never disagree with the dashboard (FR-010, Principle IX).
- **Description**: `tray.py` tooltip/reconnect-label and `core/notifier_win.py` text sourced from the descriptor. **Do not touch** the icon-caching `_last_icon_state` logic (invariant).
- **Dependencies**: T020.
- **Expected files**: `wifi_ac_guardian_win/tray.py` (edit), `wifi_ac_guardian_win/core/notifier_win.py` (edit).
- **Acceptance**: tray tooltip/menu text unchanged in meaning; icon reassignment still only on state change.
- **Complexity**: M.

**Checkpoint M2**: all surfaces render each state from one descriptor; no visual/behavioral change.

---

## Phase M3: Component & Hierarchy Pass (US1/US2 — Priority P1)

**Goal**: Premium polish lands; hero-first hierarchy; no literals in layout.

### T030 [US2] Finalize reusable components on tokens

- **Purpose**: FR-011/FR-012 consistent component set.
- **Description**: Ensure `RoundedCard`, `RoundedButton`, KPI tile, metric row, section header, `SegmentedSpeedBar` all consume tokens for color/spacing/radius/type and expose consistent default/hover/active/disabled states.
- **Dependencies**: T012, T022.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: no raw hex/spacing literals remain in component draw code (SC-002 progress); components visually consistent.
- **Complexity**: L.

### T031 [US1] Enforce hero-first information hierarchy

- **Purpose**: FR-005/FR-006/FR-013 — status dominates; 3-second answer.
- **Description**: Ensure layout order hero → metrics → connection detail → engine controls → toolbar; hero shows artwork + plain headline + supporting sentence + primary action. Keep within 540×740.
- **Dependencies**: T030.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: SC-001 informal check (viewer names state in 3s) for all 6 states; nothing clipped.
- **Complexity**: M.

### T032 [US2][P] Derive displayed defaults from live config/state

- **Purpose**: FR-015 — kill baked-in example values ("10 sec", "99 (Auto)", "780 Mbps", "0 / 99").
- **Description**: Initialize KPI/engine/hero labels from `self.config`/state, not string literals in `_build_ui`.
- **Dependencies**: T030.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: fresh launch shows real config values; no placeholder literals.
- **Complexity**: S.

### T033 [US2][P] Resolve dead/unused UI code

- **Purpose**: Principle X; decide on `LineIcon` (unused), `_open_advanced_dialog` (unreferenced), `tray._get_status_text`/`_get_phy_text` (unused).
- **Description**: Adopt in the component pass or remove. Removal of internal dead code is allowed (not a user-facing feature, so D-002/FR-025 do not apply); confirm no references first.
- **Dependencies**: T030.
- **Expected files**: `wifi_ac_guardian_win/ui.py`, `wifi_ac_guardian_win/tray.py` (edit).
- **Acceptance**: no unreferenced UI helpers remain; gates green; no user-facing capability lost.
- **Complexity**: S.

**Checkpoint M3**: polished, consistent, hero-first dashboard; feature parity intact.

---

## Phase M4: Terminology (US3 — Priority P2)

### T040 [US3] Upload/Download Link Speed in the GUI

- **Purpose**: FR-016/FR-017, D-010.
- **Description**: Replace "TX Rate"/"RX Rate" (KPI tiles + hero grid) with "Upload Link Speed"/"Download Link Speed" (or approved short form retaining "Link Speed"); ensure sync-rate meaning is clear.
- **Dependencies**: T031.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: no "TX"/"RX" strings in GUI.
- **Complexity**: S.

### T041 [US3][P] Terminology in tray tooltip + CLI `--status`

- **Purpose**: SC-005 uniformity across surfaces.
- **Description**: Update tray tooltip text (via descriptor) and `cli.py` `print_status_report` labels to match GUI terminology.
- **Dependencies**: T040, T023.
- **Expected files**: `wifi_ac_guardian_win/cli.py`, `wifi_ac_guardian_win/tray.py` (edit).
- **Acceptance**: zero TX/RX strings anywhere user-facing (SC-005).
- **Complexity**: S.

**Checkpoint M4**: terminology uniform; SC-005 met.

---

## Phase M5: Accessibility & DPI (US4 — Priority P2)

### T050 [US4] Make `RoundedButton` focusable + operable

- **Purpose**: FR-018/FR-019, R-3.
- **Description**: Add `takefocus=1`, `<FocusIn>/<FocusOut>` handlers drawing a token focus ring, and `<Return>`/`<space>` bindings invoking the command — without regressing hover/press visuals.
- **Dependencies**: T030.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: each custom button focuses via Tab, shows ring, activates on Enter/Space.
- **Complexity**: M.

### T051 [US4] Logical tab order across dashboard + settings

- **Purpose**: FR-018 predictable traversal.
- **Description**: Order: Reconnect → Stop/Start protection → Settings → View Log → About (dashboard); logical order in settings dialog. Verify focus never gets trapped.
- **Dependencies**: T050.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: SC-003 — 100% of controls focusable in a sensible order.
- **Complexity**: M.

### T052 [US4][P] Verify 100–200% Windows scaling

- **Purpose**: FR-021/SC-007.
- **Description**: Test the window at 100/125/150/175/200% scaling; confirm legibility and that nothing clips outside 540×740. Add Tk DPI-awareness call only if needed and safe (no invariant impact); record findings.
- **Dependencies**: T031.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit, only if a fix is required); notes in `docs/DESIGN_SYSTEM.md`.
- **Acceptance**: SC-007 recorded for each scale.
- **Complexity**: M.

### T053 [US4][P] Author `docs/DESIGN_SYSTEM.md`

- **Purpose**: FR-004/FR-020 — documented, checkable design language.
- **Description**: Document every token, the type ramp, spacing/radius scales, component states, and the measured WCAG-AA contrast ratios from T011.
- **Dependencies**: T011, T050.
- **Expected files**: `docs/DESIGN_SYSTEM.md` (new).
- **Acceptance**: SC-004 ratios recorded; doc matches `theme.py`.
- **Complexity**: M.

**Checkpoint M5**: keyboard + contrast + DPI verified and documented.

---

## Phase M6: Animation (US5 — Priority P3, optional, budget-gated)

### T060 [US5] Eased state transitions

- **Purpose**: FR-023 calm motion.
- **Description**: Ease hero color/label changes over a short duration via `after()`-driven steps; **degrade to instant** if a frame would exceed budget. No background-thread UI writes (invariant).
- **Dependencies**: T031, T050.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: transitions animate with no perceptible stutter; app click-responsive throughout (SC-008).
- **Complexity**: M.

### T061 [US5][P] Speed-bar cursor tween

- **Purpose**: FR-023 — animated cursor instead of jumps.
- **Description**: Tween `SegmentedSpeedBar` cursor between values; cap redraw rate; degrade to instant under budget.
- **Dependencies**: T030.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: smooth cursor motion; no stutter.
- **Complexity**: M.

### T062 [US5][P] Subtle reset-progress indication

- **Purpose**: FR-024 — communicate recovery is underway.
- **Description**: Non-alarming progress cue during the ~45s reset; must not imply user action; degrade-safe.
- **Dependencies**: T060.
- **Expected files**: `wifi_ac_guardian_win/ui.py` (edit).
- **Acceptance**: cue appears during RETRYING and clears on resolution; no stutter (SC-008).
- **Complexity**: M.

**Checkpoint M6**: motion within budget; any animation missing budget ships disabled.

---

## Dependencies & Execution Order

- **M0** → no deps.
- **M1** (tokens) blocks M2–M6.
- **M2** (descriptor) blocks M3.
- **M3** (components/hierarchy) blocks M4, M5, M6.
- **M4** terminology depends on M3 (+ T023 for tray).
- **M5** a11y depends on M3.
- **M6** motion depends on M3 + M5.

### Parallel opportunities

- M0: T001, T002 in parallel.
- M1: T011 parallel to T012 (after T010).
- M2: T021, T023 parallel to T022.
- M3: T032, T033 parallel (after T030).
- M4: T041 parallel to T040.
- M5: T052, T053 parallel to T051.
- M6: T061, T062 (T062 after T060).

## Implementation Strategy

- **MVP** = M0 + M1 + M2 + M3 (hero-first, token-consistent, polished dashboard with feature parity). Ship/demo here.
- **Increment 2** = M4 + M5 (terminology + accessibility).
- **Increment 3** = M6 (motion), only where budget allows.
- Run both quality gates + the FR-025 parity checklist at every checkpoint. Commit per task or logical group.

## Notes

- Every task is presentation-only; none may touch `core/models.py`, `core/guardian.py`, `core/detector_win.py`, `core/reconnector_win.py` behavior, or the config schema.
- The notifications-toggle bug (C-04) and config-default doc mismatch (C-03) are explicitly **not** tasks here — recorded in analysis.md for separate follow-up.
