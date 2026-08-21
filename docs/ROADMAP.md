# Product Roadmap — WiFi AC Guardian

High-level product direction organized by version. Items move from **Future Ideas** → a numbered
version once they have a specification.

**Legend**: ✅ Shipped · 🔨 In progress · 📋 Specified, not started · 💡 Idea, not specified

---

## v1.0.0 — Core Protection ✅ SHIPPED

The working foundation. Detects Wi-Fi degradation and restores high-speed connections automatically.

### Dashboard ✅
- Four KPI cards: Status, TX Rate, RX Rate, Retry State
- Full-width High-Speed Wi-Fi status card with hero router artwork
- `SegmentedSpeedBar` quality meter with red/orange/green zones and a 300 Mbps threshold line
- Connection Overview panel (SSID, BSSID, PHY mode, signal, channel)
- Protection Engine panel with Reconnect now / Stop protection controls
- Responsive layout, minimum `760 × 600`, maximizable

### Protection Engine ✅
- Continuous link monitoring at a configurable interval
- Strict quality rule: 802.11ac/ax/be **and** >300 Mbps
- Hardware radio reset via WinRT Radio API, with `Disable/Enable-NetAdapter` and `netsh` fallbacks
- Automatic reconnect to target SSID after reset
- Configurable retry attempts with a 60-second cooldown
- Standby mode on non-target networks with background failback scanning

### Settings ✅
- Interface selection, target SSID lock
- Check interval, reconnect delay, max attempts
- Tray enable/disable, notifications toggle, start minimized
- Windows startup shortcut management
- JSON persistence at `%APPDATA%\wifi-ac-guardian\config.json`

### System Tray ✅
- `pystray` applet with four visual states (Good / Restoring / Downgraded / Standby)
- Menu: Open Dashboard, Reconnect now, Stop/Start Protection, Exit
- GDI handle caching — icon reassigned only on state change

### Infrastructure ✅
- Single-instance enforcement via loopback socket `127.0.0.1:39145`
- Rotating file + stream logging to `%USERPROFILE%\wifi_ac_guardian_win.log`
- Full CLI: `--gui`, `--daemon`, `--status`, `--reconnect`, `--target-ssid`, `--interface`,
  `--interval`, `--max-attempts`
- `install.bat` / `uninstall.bat` with desktop and startup shortcut generation
- About dialog crediting Zohaib Javed as Creator & Lead Developer

### Governance ✅
- Constitution v1.0.0 ratified — 10 principles + Development Standards + Governance
- Spec Kit Plus workflow with PHR recording
- Project memory foundation (`PROJECT_STATUS.md`, `DECISIONS.md`, `ROADMAP.md`, `SESSION_LOG.md`)

---

## v1.1.0 — Premium Polish 📋 NEXT

Bring the interface up to the bar set by Constitution Principle III. No engine changes — presentation
only, per decision D-003.

> **Feature `001-premium-ui-design-system` specified 2026-08-06** covers the Design System Foundation,
> Terminology Pass, Accessibility Pass, and (optionally) Animations below. See
> `specs/001-premium-ui-design-system/` for spec, plan, tasks, and analysis. Not yet implemented.

### Design System Foundation 📋
- Extract the palette, spacing scale, type ramp, and corner radii into a single tokens module
- Replace every hardcoded color and spacing literal in `ui.py` with token references
- Document the design language so Principle VIII becomes mechanically checkable

### Terminology Pass 📋
- "Upload Link Speed" / "Download Link Speed" replacing "TX Rate" / "RX Rate" (decision D-010)
- Apply consistently across dashboard, tray tooltip, and `--status` CLI output

### Animations 📋
- Smooth state transitions between Good / Restoring / Downgraded / Standby
- Animated speed-bar cursor movement instead of instant jumps
- Subtle countdown progress during the 45-second reset sequence
- **Constraint**: must not violate Principle VI — measure frame cost before shipping
  (spec'd as budget-gated M6 with mandatory degrade-to-instant)

### Accessibility Pass 📋
- Full keyboard navigation across dashboard and settings
- Visible, consistent focus states on every interactive element
- Verified contrast ratios against WCAG AA for the dark palette
- Serves Principle VII, currently the least-implemented principle

### Connection Timeline 💡
- Rolling history of link quality over the session
- Visual markers for each reset event and its outcome
- Answers Principle I's "What should I do next?" by showing whether the problem is worsening

### Advanced Notifications 💡
- Richer Windows toast content (before/after bitrate, PHY mode change)
- Configurable notification triggers — reset only, degradation only, or all events
- Quiet hours
- **Note**: the current notifications toggle is inert (a persistence bug, analysis F-05); fixing it
  is a prerequisite and tracked separately from the presentation feature

---

## v2.0.0 — Platform Maturity 💡

### Auto Updates 💡
- Update check against a release feed
- In-app notification with release notes
- One-click update with clean restart

### Diagnostics 💡
- Built-in log viewer with severity filtering
- Adapter capability report (supported PHY modes, bands, driver version)
- Export a diagnostic bundle for support
- Reset-history statistics: success rate, mean time to recovery

### Installer Improvements 💡
- Proper MSI or signed installer replacing `install.bat`
- Code signing certificate to remove SmartScreen warnings
- Upgrade-in-place preserving user configuration
- Clean uninstall including config and log removal prompts

### Multi-Adapter Support 💡
- Detect and protect multiple wireless interfaces
- Per-adapter configuration profiles

---

## Future Ideas 💡

Unscheduled. No specification, no commitment.

- **Configurable quality thresholds** — expose the 300 Mbps rule and PHY-mode allowlist in Settings
  (currently hardcoded per decision D-009)
- **Multi-SSID priority list** — ordered preference with automatic promotion when a better network
  becomes available
- **Scheduled protection windows** — active only during defined hours
- **Router-specific profiles** — presets for known-buggy router models
- **Portable mode** — no-install execution with config alongside the executable
- **Localization** — multi-language UI
- **Light theme** — currently dark-only
- **Telemetry (opt-in, local only)** — aggregate reset frequency to help users identify whether the
  router or the adapter is at fault
- **Ubuntu 26.04 LTS port** — the cross-platform ambition noted in `HANDOFF.md`

---

## Explicitly Out of Scope

Recorded so they are not revisited without cause.

- **General network analysis** — this is a Wi-Fi 5+ enforcer, not a diagnostic suite
- **Bandwidth/throughput testing** — the Guardian reads link sync rates, not measured throughput
- **Router administration** — no router login, config, or firmware interaction
- **VPN or security features** — outside the protection mandate
- **Cloud sync or accounts** — the app is local-only by design

---

## Maintenance

Update this file when a version ships, when an item moves between versions, or when a Future Idea is
promoted to a specified feature. Version numbering follows semantic versioning and should stay in
sync with `pyproject.toml`.
