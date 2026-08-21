# WiFi AC Guardian — Project Status

**Last Updated**: 2026-08-06  
**Version**: 1.0.0  
**Status**: Active Development — Feature 001 implementation in progress (M6 complete)

---

## Project Overview

**WiFi AC Guardian** is a premium Windows 11 desktop application that automatically protects high-speed Wi-Fi connections by monitoring link quality and performing hardware adapter resets when connections degrade.

**Mission**: Build the world's most polished Windows desktop application for automatically protecting high-speed Wi-Fi connections. The application must feel like a premium commercial Windows application that users immediately trust.

**Target Users**: Windows 11 users experiencing Wi-Fi degradation issues (802.11ac/ax/be → 802.11n downgrades, bitrate drops ≤300 Mbps).

---

## Current Development Stage

**Phase**: Foundation & Governance  
**Stage**: Spec-Driven Development Setup  
**Constitution**: v1.0.0 (ratified 2026-08-05)

### Completed Milestones

- ✅ v1.0.0 Application Released (functional, installed, running)
- ✅ Constitution Ratified (10 principles + governance framework)
- ✅ Spec Kit Integration (templates, workflows, PHR system)
- ✅ Project Memory Foundation (this document + engineering journal)

### Current Milestone

**Documentation Foundation** — Establish permanent project memory so future development sessions can begin without relying on chat history.

---

## Current Feature

**Active Work**: `001-premium-ui-design-system` — Premium UI & Design System (v1.1.0 first feature).

**Status**: Implementation in progress — M0 ✅, M1 ✅, M2 ✅, M3 ✅, M4 ✅, M5 ✅, M6 ✅.

**Completed Milestones**:
- [x] M0 — Baseline & Safety Net (T001 visual parity, literal count, test suite baseline)
- [x] M1 — Design Tokens (T010 token module, T011 contrast tests, T012 ui.py aliasing, D-011 TEXT_MUTED fix)
- [x] M2 — Status Presentation Descriptor (T020 descriptor module, T021 descriptor tests, T022 ui.py routing, T023 tray/notifier routing)
- [x] M3 — Component & Hierarchy Pass (T030 components on tokens / zero color literals in draw code, T031 hero-first order, T032 config-derived defaults + D-012, T033 dead-code removal: LineIcon, _open_advanced_dialog, tray helpers)
- [x] M4 — Terminology (T040 "Upload/Download link speed" in GUI KPI cards, T041 CLI `--status` "Link Speed:" relabel + tray parity via descriptor; D-010 Accepted, SC-005 met)
- [x] M5 — Accessibility & DPI (T050 focusable/operable RoundedButton with focus ring + Enter/Space, T051 logical tab order reconnect→protection→settings→log→about, T052 DPI verification framework + desktop-check deferral, T053 `docs/DESIGN_SYSTEM.md`; SC-003/SC-004 met, SC-007 pending desktop check)
- [x] M6 — Animation (T060 hero headline color cross-fade, T061 speed-bar value tween; single global `animations_enabled` setting default OFF with automatic session fallback to instant on frame-budget slip; `after()`-driven main-thread engine `animation.py`, presentation-only boundary preserved; D-014 Accepted, `DESIGN_SYSTEM.md` §7 Motion; artwork alpha-fade / hover tweens / T062 reset cue deferred with rationale; SC-008 pending desktop check)

**Artifacts produced** (all under `specs/001-premium-ui-design-system/`):
- [x] `spec.md` — 5 user stories, FR-001…FR-028, SC-001…SC-008, 11 clarifications
- [x] `plan.md` — Constitution Check (PASS), recommendations R-1…R-4, milestones M0–M6
- [x] `tasks.md` — T001…T062 across M0–M6, each with acceptance criteria and complexity
- [x] `analysis.md` — repository analysis (F-01…F-18) + cross-artifact consistency check

**Next Milestone**: None — M0–M6 complete. Remaining feature-001 work is desktop verification only: SC-007 (DPI scale pass at 100/125/150/175/200%) and SC-008 (animation smoothness / click-responsiveness with the toggle enabled), both deferred to a real desktop session per D-013/D-014.

---

## Technology Stack

### Core Technologies

| Component | Technology | Version/Constraint |
|-----------|-----------|-------------------|
| **Language** | Python | ≥ 3.8 |
| **GUI Framework** | Tkinter | (stdlib) |
| **System Tray** | pystray | ≥ 0.19.0 |
| **Image Processing** | Pillow | ≥ 9.0 |
| **Windows APIs** | PowerShell, netsh, WinRT Radio API | Native |
| **Testing** | pytest, unittest | stdlib + pytest |
| **Build System** | setuptools | ≥ 61.0 |

### Platform

- **OS**: Windows 11 (primary), Windows 10 (compatible)
- **Python Executable**: `C:\Python314\python.exe`
- **Installation Location**: `%APPDATA%\Roaming\Python\Python314\site-packages\wifi_ac_guardian_win`
- **Config Storage**: `%APPDATA%\wifi-ac-guardian\config.json`
- **Log File**: `%USERPROFILE%\wifi_ac_guardian_win.log`

---

## Project Structure

```
WiFi_AC_Guardian_Windows/
├── wifi_ac_guardian_win/          # Main package
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                     # CLI entrypoint & arg parser
│   ├── config.py                  # JSON config persistence
│   ├── icons.py                   # Tray icon generator (Pillow)
│   ├── logger.py                  # Logging subsystem
│   ├── single_instance.py         # Single-instance IPC (127.0.0.1:39145)
│   ├── tray.py                    # System tray applet
│   ├── ui.py                      # Tkinter dashboard (45KB)
│   ├── core/
│   │   ├── detector_win.py        # netsh parser & link detection
│   │   ├── guardian.py            # Background monitoring engine
│   │   ├── models.py              # Data models & quality rules
│   │   ├── notifier_win.py        # Windows toast notifications
│   │   └── reconnector_win.py     # Hardware radio reset engine
│   └── assets/
│       ├── router_status/         # Hero status imagery (Good/Retrying/Failed/Standby)
│       ├── fluent/                # Fluent UI 3D emoji icons
│       └── tray_menu/             # Tray menu BMP icons
├── tests/                         # Unit tests (26 tests, all passing)
├── .specify/                      # Spec Kit Plus templates & scripts
│   ├── memory/
│   │   └── constitution.md        # Project constitution (v1.0.0)
│   └── templates/
│       ├── spec-template.md
│       ├── plan-template.md
│       ├── tasks-template.md
│       ├── adr-template.md
│       └── phr-template.prompt.md
├── history/
│   └── prompts/
│       └── constitution/          # Prompt History Records
├── docs/                          # Permanent documentation
├── AGENT_STATUS.md                # AI agent handoff (architecture + rules)
├── HANDOFF.md                     # Human handoff documentation
├── CLAUDE.md                      # Agent development guidelines
├── README.md                      # User-facing README
├── pyproject.toml                 # Build configuration
├── setup.py                       # Package setup script
├── requirements.txt               # Python dependencies
├── install.bat                    # Automated installer
└── uninstall.bat                  # Automated uninstaller
```

---

## Active Assets

### Visual Assets

- **Router Status Hero Images** (PNG, 26KB each): `good.png`, `retrying.png`, `failed.png`, `standby.png`
- **Fluent UI 3D Emoji Icons** (PNG, 15-39KB): Shield, Wireless, Gear, Info, High Voltage, Desktop Computer, Clockwise Arrows
- **Tray Menu Icons** (BMP, 1.2KB each): Dashboard, Exit, Header, PHY, Protection, Reconnect, Status
- **Application Icon** (ICO, 26KB): `wifi_ac_guardian.ico`
- **Current UI Screenshot** (PNG): `current-ui.png` — dashboard at 820×720px

### Design Tokens (Established)

| Token | Value | Usage |
|-------|-------|-------|
| `bg-primary` | `#121212` | Main background |
| `bg-card` | `#1D1D1D` | Card backgrounds |
| `bg-panel` | `#252525` | Panel backgrounds |
| `accent-green` | `#24C26A` | Good status, success |
| `accent-yellow` | `#F4B740` | Warning, restoring |
| `accent-red` | `#E74C3C` | Error, disconnected |
| `accent-blue` | `#3B82F6` | Info, standby |

### Quality Rules (Hardcoded)

- **Good Connection**: 802.11ac/ax/be AND (TX > 300 Mbps OR RX > 300 Mbps)
- **Downgraded Connection**: 802.11n or lower OR bitrate ≤ 300 Mbps
- **Check Interval**: Default 15s (range: 2-120s)
- **Reconnect Delay**: Default 15s (range: 1-60s)
- **Max Attempts**: Default 0 (unlimited with 60s cooldown)

---

## Spec Kit Progress

| Artifact | Status | Location | Version/ID |
|----------|--------|----------|------------|
| **Constitution** | ✅ Ratified | `.specify/memory/constitution.md` | v1.0.0 |
| **Plan Template** | ✅ Updated | `.specify/templates/plan-template.md` | Constitution Check populated |
| **PHR System** | ✅ Active | `history/prompts/` | PHR 0001 recorded |
| **First Spec** | ✅ Complete | `specs/001-premium-ui-design-system/spec.md` | `/sp.specify` + `/sp.clarify` |
| **First Plan** | ✅ Complete | `specs/001-premium-ui-design-system/plan.md` | Constitution Check PASS |
| **First Tasks** | ✅ Complete | `specs/001-premium-ui-design-system/tasks.md` | T001–T062 |
| **First Analysis** | ✅ Complete | `specs/001-premium-ui-design-system/analysis.md` | `/sp.analyze` |

---

## Current Blockers

**None**.

All prerequisites for `/sp.specify` are in place:
- Constitution ratified ✅
- Spec Kit templates configured ✅
- Project memory foundation established ✅
- Git repository clean (after commit) ⏳

---

## Next Action

1. **Review the feature artifacts** in `specs/001-premium-ui-design-system/` (spec, plan, tasks, analysis).

2. **Approve implementation** — on approval, run `/sp.implement` starting at M0 → M1. Nothing in `wifi_ac_guardian_win/` has been modified yet; this session stopped at the analysis gate by design.

3. **Recommended follow-ups surfaced by analysis** (separate from feature 001):
   - Reconcile stale docs (README/HANDOFF window geometry, screenshot, config defaults) to code — F-01/F-02/F-03
   - Fix the inert notifications toggle (`config.py:99,123`) — F-05
   - Decide on shipping `ui_backup.py` — F-06

---

## Engineering Notes

### Single-Instance Architecture
- TCP socket bound to `127.0.0.1:39145`
- Secondary launches send `SHOW_GUI` signal and exit immediately
- Zero tray/window flicker on double-click

### Hardware Reset Mechanism
- **Primary Method**: WinRT Radio API via PowerShell (`SetStateAsync(Off)` → `SetStateAsync(On)`)
- **Fallback**: `Disable-NetAdapter` / `Enable-NetAdapter` PowerShell cmdlets
- **Final Fallback**: `netsh interface set interface admin=disabled|enabled`
- **Wait Times**: 15s disable → 15s enable → 15s stabilization = 45s total

### Standby Mode (Backup Router)
- When connected to non-target SSID (e.g., `Metalgear`), enter Standby (Blue 🔵)
- Suspend radio resets to prevent interruption
- Background scan for primary SSID (`lab5g`) with 1-click failback

### Testing
- **Unit Tests**: 26 tests / 141 subtests, all passing (confirmed by running the suite this session; includes `tests/test_animation.py` for the M6 engine's pure logic)
- **Verification Commands**:
  ```bash
  python -m compileall -q wifi_ac_guardian_win
  python -m pytest -q
  ```
- **GUI Launch**: `pythonw -m wifi_ac_guardian_win --gui`

---

## Document Maintenance

This file should be updated:
- After every feature completion
- After every version bump
- After every milestone completion
- At the start of every new development session
- When blockers are identified or resolved

**Maintained by**: AI Assistant + Zohaib Javed (Lead Developer)  
**Review Frequency**: Every session start
