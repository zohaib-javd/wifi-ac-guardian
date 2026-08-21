# Repository Analysis: WiFi AC Guardian

**Date**: 2026-08-06
**Scope**: Full repository, code + docs, at the pre-implementation gate for feature `001-premium-ui-design-system`.
**Method**: Direct source inspection and grep; every finding cites file:line evidence. Verification gates run this session: `compileall` clean, `pytest -q` → **6 passed**.

Severity: **High** (correctness / trust / feature bug) · **Medium** (maintainability / debt) · **Low** (cosmetic / doc).

---

## 1. Documentation ↔ Code Drift (High)

### F-01 (High) — Docs describe a UI that no longer ships
- **Evidence**: README (`Dashboard` section, "Responsive layout, minimum 760 × 600, fully maximizable"), HANDOFF.md (`Window Geometry … minimum 760 × 600`, `Maximization Enabled resizable(True, True)`), PROJECT_STATUS.md, ROADMAP.md all describe a wide, responsive, maximizable window with a 4-KPI horizontal strip and a separate "Connection Overview" panel. Actual code `ui.py:402-411`: fixed **540×740**, `resizable(False, False)`, `minsize == maxsize == 540×740`, a **2×2 KPI grid** (`ui.py:503-508`), connection metadata **merged into the hero** (`ui.py:552-554`), and a **"View Log"** toolbar button (`ui.py:616-618`) that no doc mentions.
- **Impact**: Every incoming agent/developer is briefed on a non-existent layout. HANDOFF explicitly instructs "Preserve responsive window behavior" — an instruction that contradicts the shipping product.
- **Recommendation**: Treat `ui.py` as ground truth; correct README/HANDOFF/PROJECT_STATUS/ROADMAP. Decide product direction on fixed-vs-responsive (Outstanding Question).

### F-02 (High) — Screenshot is stale
- **Evidence**: `current-ui.png` shows the wide 4-KPI + Connection-Overview layout, which matches `ui_backup.py` (908 lines), not `ui.py` (871 lines). README and both handoff docs embed it as "current".
- **Recommendation**: Regenerate the screenshot from the running `ui.py` after M3, or remove it until refreshed.

### F-03 (Medium) — Config-default values disagree three ways
- **Evidence**: Code `models.py:92-94` = `check_interval=10.0`, `reconnect_delay=15.0`, `max_attempts=99`; `config.py:95-97` loads the same defaults. README/PROJECT_STATUS/ROADMAP claim `15.0` / `max_attempts=0 (unlimited)`; HANDOFF claims `max_attempts=50`; the live screenshot shows `0 / 50` and `50 (Auto)`. UI layout literals bake in yet another set: `"0 / 99"`, `"99 (Auto)"`, `"10 sec"` (`ui.py:506,588,930-932`).
- **Impact**: No single trustworthy statement of the app's defaults.
- **Recommendation**: Code is authoritative; reconcile docs to `models.py`. (Changing the actual defaults is out of scope — behavioral, D-003.)

### F-04 (Medium) — "Single fixed port 39145" invariant is inaccurate
- **Evidence**: Constitution Development Standards + DECISIONS D-007 + README architecture-invariants table state a hard binding to `127.0.0.1:39145`. Code `single_instance.py:52` scans **39145–39149** and uses a lock file (`~/.wifi_ac_guardian_win/app.lock`).
- **Impact**: A "non-negotiable invariant" is stated more narrowly than the code behaves; a reviewer enforcing it literally would flag correct code.
- **Recommendation**: Reword the invariant to "loopback single-instance IPC in the 39145–39149 range with lock file", constitution PATCH bump.

---

## 2. Functional Bugs (High)

### F-05 (High) — Notifications toggle is inert
- **Evidence**: `config.py:99` (`enable_notifications=False` hardcoded on load) and `config.py:123` (`"enable_notifications": False` hardcoded on save). The Settings checkbox (`ui.py:757-762`) writes `self.config.enable_notifications`, but persistence overwrites it to `False` every time.
- **Impact**: A user-facing feature (toast notifications) can never be enabled through the UI; the toggle silently does nothing. README lists notifications as a shipped feature.
- **Recommendation**: Separate behavioral fix (not part of the presentation feature). Track as its own spec/bug. Do not remove the checkbox (Principle II).

---

## 3. Duplicate / Dead Code (Medium)

### F-06 (Medium) — `ui_backup.py` ships to end users
- **Evidence**: `wifi_ac_guardian_win/ui_backup.py` (908 lines, 47.6 KB) sits inside the installed package next to `ui.py`; `setup.py`/`pyproject` package the whole directory. Nothing imports it.
- **Impact**: Dead code shipped to users; the source of the stale-screenshot confusion (F-02); doubles the UI surface a maintainer must mentally diff.
- **Recommendation**: Remove from the package (move to `docs/` history or delete). Flagged in SESSION_LOG Session 002 as awaiting approval — this analysis reaffirms it is safe internal dead code, not a user-facing feature.

### F-07 (Medium) — State→visual mapping duplicated across three surfaces
- **Evidence**: `ui.py:883-918` (per-state color/headline/artwork), `tray.py:141-175` (`_get_status_text`, `_get_reconnect_label`, `_get_protection_text`), `core/notifier_win.py`. Each independently maps `StatusState` to text/emoji/label; they can drift.
- **Impact**: Tray and dashboard can disagree about the same state (Principle IX risk); wording changes must be made in ≥3 places.
- **Recommendation**: The planned `status_presentation.py` (plan R-2) consolidates this. `tray._get_status_text`/`_get_phy_text` appear unused (no menu item references them) — dead code to remove.

### F-08 (Low) — Unused `LineIcon` widget
- **Evidence**: `ui.py:71-121` defines a full canvas icon set; no instantiation anywhere in `ui.py`. `_open_advanced_dialog` (`ui.py:803-811`) is also unreferenced.
- **Recommendation**: Adopt in the component pass or delete (tasks T033).

---

## 4. Maintainability / Consistency (Medium)

### F-09 (Medium) — ~39 raw color literals + scattered fonts in the UI layer
- **Evidence**: `grep '#[0-9A-Fa-f]{6}'` in `ui.py` → **39** occurrences (module constants plus inline literals inside `SegmentedSpeedBar.draw` such as `"#333333"`, `"#E74C3C"`, `"#F39C12"`, `"#2ECC71"` at `ui.py:184-203`, and one-off `"#0A1C11"`, `"#2AE07B"`, `"#FF6255"`, `"#303030"`). Settings dialog uses different font families (`"Segoe UI"`, `"Consolas"` at `ui.py:679,690,704`) than the dashboard's `FONT_UI`/`FONT_MONO`.
- **Impact**: Principle VIII (Consistency) is not mechanically checkable; a palette change requires hunting ~39 sites.
- **Recommendation**: Core driver for feature 001 (tokens). Target ≤5 residual literals (SC-002).

### F-10 (Medium) — Hardcoded example values baked into layout
- **Evidence**: `ui.py:506` `"0 / 99"`, `:552-554` `"lab5g"`, `"780 Mbps"`, `"95%"`, `"5805 MHz"`, `:588` `"99 (Auto)"`, `:930-932` `"10 sec"`. These render before the first refresh and can display values that contradict live config.
- **Recommendation**: Derive from config/state (task T032).

### F-11 (Low) — `lab5g` / `Metalgear` defaults hardcoded across layers
- **Evidence**: `lab5g` appears in `models.py:89`, `config.py:92,97`, `guardian.py`, `tray.py:169`, `ui.py` (multiple), and the fallback `or "lab5g"` idiom recurs ~10×. `Metalgear` referenced in comments/enums.
- **Impact**: A personal network name is a product default throughout the codebase — awkward for any other user; the repeated `or "lab5g"` fallback is a duplication smell.
- **Recommendation**: Not in scope for the UI feature, but a candidate for a future "first-run setup / no hardcoded SSID" item; note in ROADMAP.

---

## 5. Accessibility (High for a "premium" bar)

### F-12 (High vs. Principle VII) — Custom buttons are not keyboard-operable
- **Evidence**: `RoundedButton` extends `tk.Canvas` (`ui.py:309`) with only `<Enter>/<Leave>/<Button-1>` bindings; no `takefocus`, no focus-in/out, no `<Return>`/`<space>`. The primary actions (Reconnect, Stop/Start protection, Settings, View Log, About) are therefore mouse-only.
- **Impact**: Principle VII is materially unmet; the app is not operable without a mouse.
- **Recommendation**: Feature 001, task T050/T051.

### F-13 (Medium) — Contrast never verified
- **Evidence**: No contrast documentation anywhere; palette chosen by eye. `COLOR_TEXT_MUTED = "#666666"` on `COLOR_CARD = "#1E1E1E"` (`ui.py:44,29`) is used for labels (`ui.py:522,562,595`) and is borderline for small text against dark surfaces.
- **Recommendation**: Feature 001 adds a contrast unit test (T011) and records ratios (T053).

---

## 6. Security / Robustness Observations (Low–Medium)

### F-14 (Medium) — PowerShell command strings built via f-string interpolation
- **Evidence**: `reconnector_win.py:68,82,117,131` interpolate `interface` into PowerShell/`netsh` command strings; `config.py:34-43` interpolates paths/description into a WScript shell script.
- **Impact**: Command/script injection risk **if** these values ever became untrusted. Today `interface` defaults to `"Wi-Fi"` and config is local/user-controlled, so real-world risk is low — but the pattern is fragile (e.g. an interface name with a quote would break the script).
- **Recommendation**: Prefer argument lists over interpolated shell strings where feasible; at minimum validate/escape `interface` and SSID. Not a UI-feature task; note for a hardening pass.

### F-15 (Low) — Broad `except Exception: pass` blocks
- **Evidence**: Numerous silent catches (`single_instance.py:46-48,90-91`, `tray.py:42-46,232-235`, `ui.py:470-477`). Reasonable for a resilient background utility, but some swallow information that would aid diagnostics.
- **Recommendation**: Where cheap, log at debug level rather than silent `pass`. Low priority.

### F-16 (Low) — Elevated-relaunch fallbacks can spawn UAC prompts silently
- **Evidence**: `reconnector_win.py:79-89,128-138` issue `Start-Process … -Verb RunAs` as a fallback. If the WinRT path fails, this can surface a UAC prompt — contradicting the "no UAC required" claim in README/AGENT_STATUS.
- **Impact**: Edge-case UX surprise; not reached on the reference hardware where WinRT succeeds.
- **Recommendation**: Document the fallback's UAC implication; out of scope for UI work.

---

## 7. Performance Observations (Low)

### F-17 (Low) — Dual polling loops
- **Evidence**: The guardian loop polls every `check_interval` (default 10s) via `netsh`, and the UI independently polls every 2s (`ui.py:864 self.after(2000, …)`) spawning a detector thread each time. Two concurrent `netsh wlan show interfaces` cadences.
- **Impact**: Minor redundant subprocess load; not user-visible on modern hardware.
- **Recommendation**: The UI could read the guardian's last `state.current_link` instead of independently polling. Optimization opportunity, not required for feature 001.

### F-18 (Low) — Asset caching is correct — keep it
- **Evidence**: `_fluent_image`/`_router_status_image` cache by `(name,size)` (`ui.py:626-646`); tray icon reassigned only on state change (`tray.py:222`). This is good and satisfies Principle VI/FR-028.
- **Recommendation**: Preserve; do not regress during the component pass.

---

## 8. Cross-Artifact Consistency (this session's artifacts)

- **spec ↔ plan**: plan's milestones M1–M6 map 1:1 to spec user stories US1–US5 and FR groups; Constitution Check passes with no violations.
- **plan ↔ tasks**: every milestone has tasks; every task cites expected files that match plan's Source Code structure; no task touches `core/` behavior.
- **tasks ↔ spec success criteria**: SC-001..SC-008 each trace to at least one task checkpoint (SC-002→T002/T030, SC-003→T051, SC-004→T011/T053, SC-005→T041, SC-006→T003/all checkpoints, SC-007→T052, SC-008→M6).
- **No orphan requirements**: FR-001..FR-028 all have a task or are explicitly out-of-scope in spec.

---

## Prioritized Recommendation Summary

| # | Finding | Severity | Addressed by |
|---|---------|----------|--------------|
| F-01 | Docs describe non-existent UI | High | Doc sync (this session + follow-up) |
| F-05 | Notifications toggle inert | High | Separate bug fix (out of scope 001) |
| F-12 | Custom buttons not keyboard-operable | High | Feature 001 · T050/T051 |
| F-02 | Stale screenshot | High | Regenerate after M3 |
| F-03 | Config-default disagreement | Medium | Doc sync to code |
| F-04 | Port invariant wording wrong | Medium | Constitution PATCH |
| F-06 | `ui_backup.py` shipped | Medium | Remove (needs approval) |
| F-07 | State-mapping triplicated | Medium | Feature 001 · `status_presentation.py` |
| F-09 | ~39 raw literals | Medium | Feature 001 · tokens |
| F-14 | PS f-string interpolation | Medium | Hardening pass (future) |
| F-10/F-11/F-13/F-15/F-16/F-17 | Debt / robustness | Low–Med | Noted; mostly future work |

**No speculation**: every item above is backed by a cited line. Items marked out-of-scope are behavioral and excluded from the presentation-only feature per D-003.
