# Engineering Decision Log — WiFi AC Guardian

Permanent record of architectural and UX decisions. Every significant decision is recorded here with
its reasoning, alternatives considered, and current status.

**Status values**: `Accepted` (in effect) · `Proposed` (agreed in principle, not yet implemented) ·
`Superseded` (replaced by a later decision) · `Rejected` (considered and declined)

> Decisions marked `Proposed` are **not** reflected in the current code. Do not assume them when
> reading `wifi_ac_guardian_win/`.

---

## D-001 — Spec-Driven Development as the Governing Workflow

**Date**: 2026-08-05  
**Status**: Accepted

**Decision**: All features begin with a written specification. Development follows the Spec Kit Plus
workflow: Constitution → Spec → Plan → Tasks → Implement.

**Reason**: Prevents feature drift and guessing. Produces reviewable, traceable changes and keeps
project knowledge in the repository rather than in chat history.

**Alternatives considered**:
- Ad-hoc development with direct code changes — fast but produces undocumented drift
- Issue-driven development only — captures *what* but not *why* or *how*

**Consequences**: Higher upfront cost per feature; significantly lower rework cost. Enforced by
Constitution Principle V (Professional Engineering).

---

## D-002 — Never Remove Existing Functionality Without Explicit Approval

**Date**: 2026-08-05  
**Status**: Accepted

**Decision**: No existing feature may be removed during a redesign or refactor. Every redesign must
preserve full feature parity. Removal requires explicit approval from the lead developer.

**Reason**: Users depend on the Guardian for continuous protection. Silent feature loss breaks trust
and is the single most damaging class of regression for a background utility.

**Alternatives considered**:
- Allow removal of "unused" features — rejected; usage cannot be reliably measured with no telemetry
- Deprecation cycle with warnings — deferred; adds complexity not yet justified at current scale

**Consequences**: Redesigns must be additive or transformative, never subtractive. Codified as
Constitution Principle II (Zero Feature Regression).

---

## D-003 — Improve Presentation Only, Unless Change Is Explicitly Requested

**Date**: 2026-08-05  
**Status**: Accepted

**Decision**: UI work changes presentation (layout, spacing, typography, iconography, color) without
altering underlying behavior, thresholds, or engine logic unless the change is explicitly requested.

**Reason**: The protection engine is verified and working against a real hardware bug. Coupling
visual work to behavioral change makes regressions hard to isolate and risks breaking a
known-good detection path.

**Alternatives considered**:
- Combined UI + logic refactors — rejected; conflates two independent risk profiles in one diff

**Consequences**: Clean separation between UI and engine changes. Reinforces Constitution
Principle X (separation of UI and business logic).

---

## D-004 — Tkinter as the GUI Framework

**Date**: Pre-2026-08-05 (original implementation)  
**Status**: Accepted — under review

**Decision**: The dashboard is built with Python's stdlib Tkinter, with a custom
`SegmentedSpeedBar` canvas widget for the bitrate quality meter.

**Reason**: Zero additional runtime dependency, guaranteed availability with any CPython install,
no packaging complexity, and full control over custom canvas drawing.

**Alternatives considered**:
- **CustomTkinter** — modern themed widgets over Tkinter; adds a dependency, still inherits
  Tkinter's rendering limits (no true DPI-aware compositing, no hardware acceleration)
- **WinUI 3 / .NET** — native Windows 11 look, but requires abandoning the Python engine or adding
  an IPC boundary
- **Electron / Tauri** — best visual ceiling, unacceptable memory footprint for a background utility
- **PySide6 / Qt** — strong widget set and DPI handling; large distribution size and licensing weight

**Open tension**: Constitution Principle III requires the app to feel comparable to PowerToys and
Docker Desktop. Tkinter's rendering ceiling is the primary constraint on reaching that bar. This
decision is a candidate for a formal ADR before any major UI rewrite.

**Consequences**: Custom canvas widgets are required for any non-standard visual. Visual polish is
achieved through asset quality and layout discipline rather than framework features.

---

## D-005 — Fluent UI 3D Emoji Icons for Iconography

**Date**: Pre-2026-08-05 (original implementation)  
**Status**: Accepted

**Decision**: Interface iconography uses Microsoft Fluent UI 3D emoji assets, stored as PNG in
`wifi_ac_guardian_win/assets/fluent/`. Current set: shield, wireless, gear, information,
high voltage, desktop computer, clockwise vertical arrows.

**Reason**: Native Windows 11 visual language, consistent rendering across DPI scales, no icon-font
dependency, and instantly recognizable metaphors that need no explanation.

**Alternatives considered**:
- Font-based icon sets (Segoe Fluent Icons) — monochrome only; less visual warmth at large sizes
- Custom-drawn vector icons — highest consistency, high authoring cost, no clear benefit here
- Unicode emoji rendered as text — inconsistent across Windows versions and font fallbacks

**Consequences**: Icons are raster assets and must be pre-scaled per display size. Supports
Constitution Principle VIII via centralized icon management.

---

## D-006 — Hero Router Status Artwork for Primary Status Communication

**Date**: Pre-2026-08-05 (original implementation)  
**Status**: Accepted

**Decision**: The dashboard's primary status indicator is a large router illustration that changes
per state, stored in `assets/router_status/`: `good.png`, `retrying.png`, `failed.png`,
`standby.png`.

**Reason**: Answers "Am I protected?" pre-attentively — recognized before any text is read. A
single glance conveys state from across a room.

**Alternatives considered**:
- Text-only status label — requires reading; weak visual hierarchy
- Small status badge or dot — insufficient prominence for the screen's primary question
- Animated illustration — deferred; conflicts with Principle VI until measured

**Consequences**: Four artwork variants must be maintained in visual lockstep. Directly serves
Constitution Principle I (User First).

---

## D-007 — Single-Instance Enforcement via Loopback TCP Socket

**Date**: Pre-2026-08-05 (original implementation)  
**Status**: Accepted

**Decision**: A TCP socket bound to `127.0.0.1:39145` enforces single-instance behavior. Secondary
launches send a `SHOW_GUI` signal to the running instance and exit with code 0.

**Reason**: Prevents duplicate tray icons and duplicate monitoring engines — two engines racing to
reset the same adapter would fight each other. Loopback IPC also gives free
focus-existing-window behavior with zero flicker.

**Alternatives considered**:
- Named mutex (Win32) — prevents duplicates but provides no channel to signal the running instance
- Lock file — fragile; stale locks survive crashes and require timeout heuristics

**Consequences**: Port 39145 is reserved. Codified as a hard architecture invariant in the
constitution's Development Standards.

---

## D-008 — Standby Mode on Non-Target Networks

**Date**: Pre-2026-08-05 (original implementation)  
**Status**: Accepted

**Decision**: When connected to an SSID other than the protected target, the Guardian enters
`StatusState.STANDBY` (blue), suspends all radio resets, and background-scans for the target SSID
with a one-click failback.

**Reason**: The backup router (`Metalgear`, 802.11n-only) can never satisfy the >300 Mbps rule.
Without Standby, the Guardian would reset the adapter in an endless loop and destroy the user's
only working connection.

**Alternatives considered**:
- Apply quality rules to all networks — rejected; actively harmful on legitimate slow networks
- Fully disable the Guardian off-target — loses automatic failback to the primary router

**Consequences**: Requires SSID-aware state machine and a distinct fourth visual state. Serves
Constitution Principle IX (Reliability).

---

## D-009 — Strict >300 Mbps AND Wi-Fi 5+ Quality Threshold

**Date**: Pre-2026-08-05 (original implementation)  
**Status**: Accepted

**Decision**: A connection is GOOD only if PHY mode is 802.11ac/ax/be **and** TX or RX bitrate is
strictly greater than 300.0 Mbps. Otherwise it is DOWNGRADED and triggers a hardware reset.

**Reason**: Targets a specific, reproducible hardware bug in the PTCL Huawei HG8141V5 router, which
silently downgrades to 802.11n or caps at exactly 300 Mbps. Both conditions are required because the
router sometimes reports 802.11ac while delivering 300 Mbps.

**Alternatives considered**:
- Bitrate-only threshold — misses PHY-mode downgrades that still report high sync rates
- PHY-mode-only check — misses the 300 Mbps cap case
- User-configurable threshold — deferred; 300 Mbps is the exact bug boundary, not a preference

**Consequences**: Thresholds are hardcoded in `core/models.py`. Making them configurable is a
future roadmap item, not a current requirement.

---

## D-010 — Terminology: "Upload / Download Link Speed" over "TX / RX Rate"

**Date**: 2026-08-05  
**Status**: Proposed — not yet implemented

**Decision**: User-facing labels should read "Upload Link Speed" and "Download Link Speed" instead
of "TX Rate" and "RX Rate".

**Reason**: Constitution Principle I mandates clarity over technical jargon. "TX/RX" is radio
terminology that a non-technical user must translate; "Upload/Download" is immediately understood.

**Alternatives considered**:
- Keep TX/RX — precise for technical users, opaque for everyone else
- Show both ("Upload (TX)") — hedges, adds visual noise, contradicts Principle IV
- Icons with arrows only — ambiguous without a legend

**Current state**: `ui.py` still renders "TX Rate" and "RX Rate". The dashboard KPI cards and the
Connection Overview panel both need updating.

**Caveat worth noting**: These values are *link sync rates* negotiated with the router, not
measured throughput. "Link Speed" in the label is doing important work — dropping it to plain
"Upload"/"Download" would imply measured bandwidth and mislead users.

**Consequences**: Requires a label pass in `ui.py`, tray tooltip text, and the CLI `--status`
output for consistency (Principle VIII).

---

## D-011 — TEXT_MUTED Lightened for WCAG-AA Compliance

**Date**: 2026-08-06  
**Status**: Accepted — implemented in feature 001, M1

**Decision**: The muted-text gray token was lightened from `#666666` to `#8C8C8C` to meet WCAG 2.1 AA contrast (≥4.5:1) on all surfaces (`BG`, `CARD`, `PANEL`).

**Reason**: Analysis finding F-13 identified that the original `#666666` failed AA on `CARD` (2.90:1) and `PANEL` (2.67:1). Muted captions are rendered at 7–8px and used for de-emphasized labels; WCAG requires ≥4.5:1 for normal text regardless of size (AA-large ≥3.0 applies only to 18pt+ or bold 14pt+, not to small labels). Principle VII (Accessibility) mandates verified contrast.

**Alternatives considered**:
- Keep `#666666` — rejected; materially non-compliant
- Lighten further to `#999999` — rejected; unnecessarily high contrast (6.41:1) loses the "muted" quality

**Consequences**: `#8C8C8C` clears AA on all three surfaces with minimal perceptual change (4.96:1 on CARD, 4.56:1 on PANEL, 5.43:1 on BG). This is the only intentional visual change in M1 (design tokens extraction); the new `test_theme.py` unit test enforces AA for all future palette edits. Implements task T011, resolves F-13.

---

## Decision Template

```markdown
## D-0XX — [Decision Title]

**Date**: YYYY-MM-DD
**Status**: Accepted | Proposed | Superseded | Rejected

**Decision**: [What was decided, stated as a rule]

**Reason**: [Why — the driving constraint or principle]

**Alternatives considered**:
- [Option] — [why not chosen]

**Consequences**: [What this commits the project to; which principle it serves]
```

---

## Maintenance

Append new decisions with the next sequential ID. Never delete or rewrite a past decision — mark it
`Superseded` and add a new entry that references it. When a decision meets the ADR significance test
(long-term impact + multiple viable alternatives + cross-cutting scope), promote it to a full ADR in
`history/adr/` via `/sp.adr` and link it here.
