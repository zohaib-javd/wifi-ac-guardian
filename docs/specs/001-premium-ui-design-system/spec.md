# Feature Specification: Premium UI & Design System

**Feature Branch**: `001-premium-ui-design-system`
**Created**: 2026-08-06
**Status**: Clarified — Ready for Planning
**Input**: Autonomous engineering session — bring the WiFi AC Guardian interface up to the bar set by Constitution Principle III (PowerToys / Docker Desktop / Windows 11), by extracting a real design system and applying it consistently across the dashboard, settings, tray, and status messaging. Presentation-only per decision D-003; no engine, threshold, or detection changes.

---

## Product & Design Philosophy *(mandatory context)*

WiFi AC Guardian is a **Guardian**, not a networking utility, Wi-Fi analyzer, or speed tester. Every screen must let a non-technical user answer three questions within **three seconds**:

1. **Am I protected?**
2. **Is my Wi-Fi healthy?**
3. **Do I need to do anything?**

The application must feel **reassuring, not technical**. Commercial polish is mandatory: the reference bar is Microsoft PowerToys, Windows 11 Settings, Docker Desktop, GitHub Desktop, Logitech G Hub, Malwarebytes, and NordVPN Desktop.

This feature changes **what the interface presents and how consistently it presents it**. It does not change the protection engine, quality thresholds (802.11ac/ax/be AND >300 Mbps), the reset sequence, the standby logic, or any detection code.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - "Am I protected?" answered at a glance (Priority: P1) 🎯 MVP

A user opens the dashboard (or glances at it already open) and, without reading any number, knows within three seconds whether their Wi-Fi is protected, healthy, and whether action is needed. The hero status region is the single dominant element: a large state-colored router illustration, a plain-language headline ("You're protected" / "Restoring your connection…" / "Wi-Fi downgraded" / "On backup network" / "Protection paused"), and one supporting sentence.

**Why this priority**: This is the core promise (Constitution Principle I). If a user cannot answer the three questions pre-attentively, every other refinement is cosmetic. This story alone delivers a viable premium product.

**Independent Test**: With protection running, force each `StatusState` (GOOD, RETRYING, FAILED, DISCONNECTED, STANDBY, IDLE) and confirm the hero headline, illustration, and accent color change correctly and legibly, and that a first-time viewer can name the state without reading the metrics grid.

**Acceptance Scenarios**:

1. **Given** the link is GOOD, **When** the dashboard is shown, **Then** the hero shows the green router artwork, a reassuring headline in plain language, and the accent color is the single green token — no jargon in the headline.
2. **Given** the engine transitions GOOD → downgraded, **When** the state machine enters RETRYING, **Then** the hero switches to the amber "restoring" treatment and communicates that the Guardian is handling it and the user need not act.
3. **Given** protection is stopped, **When** the dashboard renders, **Then** the hero clearly reads as paused/inactive (muted, not alarming red) and offers the primary action to resume.

---

### User Story 2 - One design language across every surface (Priority: P1)

Every card, button, label, icon, spacing value, corner radius, and color is drawn from a single named token set rather than ad-hoc literals. A developer changing the accent green changes it in exactly one place and it propagates everywhere: dashboard, settings dialog, about dialog, tray tooltip text, and status labels.

**Why this priority**: Constitution Principle VIII (Consistency) is currently aspirational, not mechanically checkable — `ui.py` contains ~30 hardcoded color/spacing literals and the settings dialog uses different font tuples (`"Segoe UI"`, `"Consolas"`) than the dashboard. Without a token module, "consistent" cannot be verified or maintained.

**Independent Test**: Grep the UI layer for raw hex color literals and magic spacing numbers outside the token module; the count trends to zero. Changing one token value visibly and uniformly updates all surfaces.

**Acceptance Scenarios**:

1. **Given** the design-token module exists, **When** any UI element needs a color, font, spacing, or radius, **Then** it references a named token, not a literal.
2. **Given** the settings and about dialogs, **When** they render, **Then** their typography, colors, and spacing match the dashboard's token set exactly.
3. **Given** a single token value is changed, **When** the app is relaunched, **Then** the change appears consistently on every surface that uses that token.

---

### User Story 3 - Plain-language metrics and clear terminology (Priority: P2)

Metrics use human terminology. "TX Rate" / "RX Rate" become "Upload Link Speed" / "Download Link Speed" (decision D-010), applied consistently across the dashboard KPIs, the hero grid, the tray tooltip, and the `--status` CLI output. Values that are link sync rates are labeled as such so users are not misled into reading them as measured throughput.

**Why this priority**: Directly serves Principle I (clarity over jargon) and Principle VIII (consistency), but depends on the token/layout work of US1–US2 being in place first.

**Independent Test**: Every user-facing surface shows the new terminology with no remaining "TX"/"RX" strings; the meaning (link/sync speed, not throughput) is unambiguous.

**Acceptance Scenarios**:

1. **Given** a connected link, **When** the dashboard renders, **Then** the two speed metrics read "Upload Link Speed" and "Download Link Speed" (or an approved shorter equivalent that preserves "Link Speed").
2. **Given** the `--status` CLI command, **When** it prints, **Then** its labels match the GUI terminology.

---

### User Story 4 - Accessible and keyboard-navigable (Priority: P2)

Every interactive element is reachable and operable by keyboard, shows a visible focus state, and meets WCAG AA contrast against the dark palette. Text sizes are legible; the app respects Windows display scaling.

**Why this priority**: Principle VII (Accessibility) is the least-implemented principle today — custom Canvas widgets (`RoundedButton`) do not participate in Tk focus traversal at all. High-value but layered on top of the component system from US1–US2.

**Independent Test**: Tab through the entire dashboard and settings dialog using only the keyboard; every actionable control receives focus in a logical order with a visible focus ring, and Enter/Space activates it. A contrast check of every text/background token pair passes WCAG AA.

**Acceptance Scenarios**:

1. **Given** the dashboard, **When** the user presses Tab repeatedly, **Then** focus moves through Reconnect, Stop/Start protection, Settings, View Log, and About in a predictable order with a visible focus indicator.
2. **Given** any focused control, **When** the user presses Enter or Space, **Then** the control activates identically to a mouse click.
3. **Given** each color token pair used for text, **When** measured, **Then** contrast is ≥ 4.5:1 for body text and ≥ 3:1 for large text/UI components.

---

### User Story 5 - Calm motion that never costs responsiveness (Priority: P3)

State changes and the speed-bar cursor animate smoothly rather than snapping, and a subtle progress indication accompanies the ~45-second reset sequence — but only where measured frame cost stays within budget (Principle VI). Motion is subtle, purposeful, and can degrade to instant updates without breaking meaning.

**Why this priority**: Enhances the premium feel and answers "do I need to do anything?" during a reset, but is explicitly last because it must not regress responsiveness and depends on the state machine and components being finalized.

**Independent Test**: Trigger a state transition and a reset; observe animated (not instant) transitions with no perceptible UI stutter, and confirm the app remains responsive to clicks throughout.

**Acceptance Scenarios**:

1. **Given** a state transition, **When** it occurs, **Then** color/label changes ease in over a short duration rather than snapping, and the app stays responsive.
2. **Given** a reset sequence, **When** it runs, **Then** a subtle, non-alarming progress indication communicates that recovery is underway and roughly how long remains.
3. **Given** animation is active, **When** frame cost is measured, **Then** it stays within the performance budget defined in this spec; if not, the animation degrades to an instant update.

---

### Edge Cases

- **Very long SSID / interface names** must truncate with ellipsis, never break layout or overflow the fixed window.
- **Missing or unreadable assets** (router artwork, Fluent icons) must fall back gracefully to a drawn placeholder, never crash.
- **Windows display scaling at 125% / 150% / 175% / 200%** must keep all text legible and all controls fully within the window bounds.
- **Rapid state flapping** (GOOD↔RETRYING within one poll) must not cause flicker or animation thrash; the last state wins.
- **Disconnected / no adapter**: hero must present a clear, non-alarming "not connected" state with the correct next action, not a raw error.
- **Standby with primary in range vs. not in range** must present visibly different primary actions ("Switch to <primary>" enabled vs. informational).
- **Light-on-light or theme-forced-colors mode** (Windows high-contrast): out of scope for this feature but must not crash; documented as a known limitation.

---

## Requirements *(mandatory)*

### Functional Requirements — Design System Foundation

- **FR-001**: The UI layer MUST source all colors, fonts, spacing, corner radii, and elevation/border values from a single named design-token definition rather than inline literals.
- **FR-002**: The design tokens MUST define, at minimum: a color system (backgrounds, surfaces, borders, four semantic accents with paired subtle backgrounds, and a three-level text ramp), a typographic ramp (display, title, body, caption, mono) with sizes and weights, a spacing scale, and a corner-radius scale.
- **FR-003**: Every existing hardcoded color hex and magic spacing literal in the UI layer MUST be replaced by a token reference, with the count of remaining raw literals trending to zero (measurable).
- **FR-004**: The token set MUST be documented in human-readable form (a design-system reference document) so Principle VIII becomes checkable.

### Functional Requirements — Information Hierarchy & Hero Status

- **FR-005**: The dashboard MUST present the protection state as the single dominant visual element (hero), above all metrics, answering "Am I protected?" pre-attentively.
- **FR-006**: The hero MUST include: state-colored router artwork, a plain-language headline, one supporting sentence, and the primary contextual action for that state.
- **FR-007**: Hero headlines MUST be free of networking jargon (no "PHY", "802.11", "TX/RX", "bitrate" in the headline; technical detail may appear in a secondary metrics area).
- **FR-008**: The interface MUST render a consistent status treatment for each `StatusState` value: GOOD, RETRYING, FAILED, DISCONNECTED, STANDBY, IDLE — each mapped to exactly one semantic accent color and one router artwork asset.

### Functional Requirements — Status State Machine (presentation)

- **FR-009**: The presentation MUST map engine states to visual states without altering engine logic: GOOD→green/"protected", RETRYING→amber/"restoring", FAILED→red/"downgraded", DISCONNECTED→red-muted/"not connected", STANDBY→blue/"backup network", IDLE→muted/"paused or starting".
- **FR-010**: The state-to-visual mapping MUST be defined in one place (single source of truth) covering color, headline text, supporting text, artwork, tray tooltip text, and primary action label — so the tray, dashboard, and notifications never disagree about the current state's presentation.

### Functional Requirements — Components & Layout

- **FR-011**: The UI MUST provide a reusable component set (card/surface, primary/secondary/tertiary button, KPI tile, metric row, section header, segmented quality meter, icon) all consuming the design tokens.
- **FR-012**: Buttons MUST have consistent, token-driven default / hover / active / disabled / focused states.
- **FR-013**: The dashboard layout MUST present, in priority order: hero status → key metrics → connection detail → protection engine controls → utility toolbar (Settings, View Log, About), within the existing window.
- **FR-014**: The `SegmentedSpeedBar` quality meter MUST retain its three zones (red 0–200, orange 200–300, green 300–max), the 300 Mbps threshold marker, and a live current-speed cursor, restyled to the token system.
- **FR-015**: All labels currently rendering hardcoded example values (e.g. "10 sec", "99 (Auto)", "780 Mbps", "0 / 99") MUST derive their displayed defaults from live config/state, not literals baked into layout code.

### Functional Requirements — Terminology

- **FR-016**: User-facing speed metrics MUST use "Upload Link Speed" / "Download Link Speed" terminology (or approved equivalent retaining "Link Speed"), replacing "TX Rate" / "RX Rate", applied on the dashboard, hero grid, tray tooltip, and CLI `--status` output.
- **FR-017**: Terminology MUST make clear these are negotiated link/sync rates, not measured throughput.

### Functional Requirements — Accessibility, DPI, Keyboard, Interaction

- **FR-018**: Every interactive control MUST be keyboard-focusable in a logical tab order and activatable via Enter/Space, including custom Canvas-based buttons.
- **FR-019**: Every focusable control MUST render a visible, consistent, token-driven focus indicator.
- **FR-020**: All text/background token pairings MUST meet WCAG AA (≥4.5:1 body, ≥3:1 large text and UI component boundaries); the design-system doc MUST record the measured ratios.
- **FR-021**: The interface MUST remain fully legible and fully within window bounds at Windows display scaling of 100%–200%.
- **FR-022**: Interaction feedback (hover, press, disabled) MUST be consistent across all interactive components and never leave a control in an ambiguous state.

### Functional Requirements — Animation

- **FR-023**: State transitions and the speed-bar cursor MAY animate, but every animation MUST have a defined duration/easing and MUST degrade to an instant update if it would exceed the performance budget.
- **FR-024**: A subtle, non-alarming progress indication MAY accompany the reset sequence; it MUST NOT imply the user must act.

### Functional Requirements — Non-Regression & Constraints (binding)

- **FR-025**: This feature MUST NOT remove any existing user-facing capability (Principle II / D-002): dashboard metrics, reconnect, stop/start protection, settings (SSID, intervals, autostart, start-minimized, notifications toggle, auto-switch), view log, about, tray menu, CLI flags, single-instance behavior.
- **FR-026**: This feature MUST NOT modify engine logic, quality thresholds, the reset sequence, standby logic, detection/parsing, or config schema semantics (D-003). Changes are presentation-only.
- **FR-027**: The four architecture invariants MUST hold in every change: single-instance enforcement, `CREATE_NO_WINDOW` on all subprocess calls, `widget.after(0,…)` for background-thread UI updates, tray icon reassigned only on state change.
- **FR-028**: All UI-referenced assets MUST continue to be cached and reused (Principle VI) — no per-frame reloads.

### Key Entities *(presentation-layer concepts, not new persisted data)*

- **Design Token Set**: named constants for color, type, spacing, radius, elevation. Single source of truth for the visual language.
- **Status Presentation Descriptor**: for each `StatusState`, the tuple (accent color, headline, supporting text, artwork asset, tray tooltip, primary action label). Consumed by dashboard, tray, notifier.
- **UI Component**: reusable, token-consuming widget (card, button, KPI tile, metric row, section header, meter, icon).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time viewer shown any single status state can correctly state "protected / not protected / being fixed / on backup / paused" within **3 seconds**, without reading the metrics grid (target: ≥90% of test viewers across the 6 states).
- **SC-002**: The number of raw color-hex and magic-spacing literals in the UI layer outside the token module drops to **≤ 5** (from ~30+ today), and one token change propagates to all surfaces.
- **SC-003**: **100%** of interactive controls are keyboard-focusable, show a visible focus ring, and activate via Enter/Space.
- **SC-004**: **100%** of text/background token pairs used in the shipping UI meet WCAG AA, with ratios recorded in the design-system document.
- **SC-005**: No "TX Rate"/"RX Rate" strings remain in any user-facing surface; terminology is uniform across dashboard, tray, and CLI.
- **SC-006**: Both quality gates still pass (`python -m compileall -q wifi_ac_guardian_win`; `python -m pytest -q` → all tests pass) and no existing feature (per FR-025) is removed.
- **SC-007**: At Windows scaling 100–200%, all controls remain within window bounds and all text remains legible (manual verification recorded).
- **SC-008**: With animations enabled, the dashboard shows no perceptible stutter during a state transition or reset, and remains click-responsive throughout (Principle VI budget in plan.md upheld).

---

## Clarifications

This section resolves ambiguities and conflicts using repository evidence. Items marked **ASSUMPTION** could not be fully resolved from the repo and are the recommended defaults; they are the primary Outstanding Questions for the lead developer.

### Resolved from repository evidence

- **C-01 — Window geometry conflict (docs vs. code).** README/HANDOFF/PROJECT_STATUS/ROADMAP describe a responsive, ≥760×600, maximizable window; `current-ui.png` shows a wide layout. **Evidence**: `ui.py:402-411` sets a **fixed 540×740, non-resizable** window (`resizable(False, False)`, min=max=540×740). **Resolution**: The current shipping product is the fixed 540×740 compact layout. This spec targets that shipping reality. Whether to return to a responsive/maximizable window is a **product-direction decision** (see Outstanding Questions), not assumed here.
- **C-02 — Stale screenshot.** `current-ui.png` matches `ui_backup.py`, not `ui.py` (screenshot shows a 4-KPI horizontal strip + separate "Connection Overview" panel; code renders a 2×2 KPI grid with connection metadata merged into the hero and a "View Log" toolbar button). **Resolution**: Treat `ui.py` as ground truth; the screenshot and docs are out of date and are flagged for correction (documentation task, not a code change in this feature).
- **C-03 — Config default conflict.** Code (`models.py:92-94`, `config.py:95-97`) uses `check_interval=10.0`, `reconnect_delay=15.0`, `max_attempts=99`. Docs variously claim `15.0 / 0 (unlimited)` and `50`. **Resolution**: Code is authoritative for this presentation feature. FR-015 requires displayed defaults to come from live config, eliminating the mismatch at the UI. Reconciling documentation to code is a separate documentation task; changing the actual defaults is out of scope (D-003).
- **C-04 — Notifications toggle currently inert.** `config.py:99,123` force `enable_notifications=False` on load and save regardless of the Settings checkbox. **Resolution**: This is a pre-existing functional bug, **out of scope** for a presentation-only feature (touching it would change behavior, violating D-003). Recorded in analysis.md and Outstanding Questions; the checkbox remains visible (no feature removal, FR-025).
- **C-05 — Single-instance "invariant" wording.** Constitution/docs describe `127.0.0.1:39145` as a single fixed port; `single_instance.py:52` scans 39145–39149 with a lock file. **Resolution**: Presentation work does not touch this. Flagged for a constitution/docs wording correction; no code change here.
- **C-06 — Terminology direction.** D-010 (`Proposed`) specifies "Upload/Download Link Speed". **Resolution**: Adopted as FR-016/FR-017; this feature moves D-010 from `Proposed` toward `Accepted` upon implementation.
- **C-07 — Scope boundary.** Constitution Principle II + D-003 forbid feature removal and behavioral change. **Resolution**: All requirements here are additive/transformative on presentation only; FR-025/FR-026 encode the boundary.

### Assumptions (recommended defaults; confirm before implementation)

- **C-08 — ASSUMPTION**: The framework remains **stdlib Tkinter** for this feature. Reaching full PowerToys-grade fidelity may ultimately require a framework change (D-004 open tension), but that is a separate, ADR-gated decision. This feature maximizes polish within Tkinter and does not assume a rewrite.
- **C-09 — ASSUMPTION**: The window stays **fixed 540×740 compact** (current shipping reality) unless the lead developer decides otherwise. The design system is authored to be geometry-independent so a later responsive decision is not blocked.
- **C-10 — ASSUMPTION**: "Upload/Download Link Speed" is the approved wording; if space-constrained, "Upload speed"/"Download speed" with a "link/sync rate" caption is the fallback.
- **C-11 — ASSUMPTION**: Dark theme only (light theme is a Future Idea in ROADMAP); accessibility work targets the dark palette.

---

## Out of Scope (this feature)

- Engine, threshold, reset-sequence, standby, or detection changes (D-003).
- Fixing the notifications-toggle bug (C-04) — separate behavioral fix.
- Changing config defaults or schema (C-03).
- Framework migration away from Tkinter (D-004 — needs its own ADR).
- Light theme, localization, connection timeline/history, advanced notification triggers (later roadmap items).
- Responsive/maximizable window redesign (product-direction decision, C-09).
