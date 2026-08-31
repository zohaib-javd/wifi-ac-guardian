# HANDOFF DOCUMENTATION — WiFi AC Guardian (Windows & Cross-Platform)

**Date & Time**: August 5, 2026 — 14:06:00 PKT (UTC+5)  
**Author & Lead Developer**: Zohaib Javed  
**Project Path**: `C:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows`  

---

## Executive Overview

**WiFi AC Guardian** is an enterprise-grade, background Wi-Fi protection utility designed for Windows 11 and Ubuntu 26.04 LTS.

Unlike network analyzers, this application is a **Wi-Fi 5+ Enforcer**. It continuously monitors the active wireless link bitrate and PHY mode (`802.11ac`, `802.11ax`, `802.11be`). If the primary high-speed connection drops below **300.0 Mbps** or degrades to Wi-Fi 4 (`802.11n`), the guardian automatically triggers a hardware Wi-Fi adapter radio reset via WinRT / PowerShell to restore high-speed Wi-Fi 5+.

---

## 🌐 Real-World Environment & Dual-Router Architecture

1. **Primary Protected Router (`lab5g`)**:
   * **Hardware**: PTCL Huawei HG8141V5 ISP Flash Fiber router (Wi-Fi 5 / `802.11ac`).
   * **Problem**: Hardware bug randomly downgrades connection to Wi-Fi 4 (`802.11n`) or drops bitrate $\le 300\text{ Mbps}$.
   * **Guardian Action**: Active continuous enforcement. When degraded, triggers hardware radio reset to restore 5 GHz `802.11ac` ($>300\text{ Mbps}$).

2. **Backup Router (`Metalgear`)**:
   * **Hardware**: Rapidshare TP-Link TL-WR841N router (Wi-Fi 4 / `802.11n` only).
   * **Guardian Action**: **Standby Mode** (Blue Icon 🔵). Suspends radio resets so the backup connection is never interrupted. Periodically scans available SSIDs in the background and offers a 1-click failback switch to `lab5g` when back online.

---

## 🎨 UI/UX & Architectural Specifications

| Specification | Details |
| :--- | :--- |
| **Window Geometry** | Responsive desktop window, initially 820–900 px wide and up to 720 px high; minimum `760 × 600` |
| **Maximization** | Enabled (`resizable(True, True)`) |
| **Palette Tokens** | Background: `#121212` \| Cards: `#1D1D1D` \| Panels: `#252525` \| Accent: `#24C26A` \| Warning: `#F4B740` \| Error: `#E74C3C` \| Info: `#3B82F6` |
| **Bitrate Quality Meter** | Custom `SegmentedSpeedBar` canvas widget with 3 color zones: <br>• Red (`0 - 200 Mbps`, `#E74C3C`) <br>• Orange (`200 - 300 Mbps`, `#F39C12`) <br>• Green (`300 - 1000 Mbps`, `#2ECC71`) <br>Includes white `300 Mbps` threshold line and live current speed indicator cursor. |
| **Single-Instance IPC** | TCP Socket bound on `127.0.0.1:39145`. Secondary shortcut double-clicks send a `SHOW_GUI` signal and exit immediately with code 0 (zero window/tray flicker). |
| **Tray Applet** | `pystray` menu with visual status states (green Good, yellow Restoring, red Downgraded/Disconnected, blue Standby/Idle) and direct actions: Open Dashboard, Reconnect now, Stop/Start Protection, and Exit. |
| **Windows Startup** | Controlled via checkbox `[✓] Start WiFi AC Guardian when Windows starts`, creating/removing `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WiFi AC Guardian.lnk`. |
| **Retry Attempts** | Configurable; current saved value is **50** automatic attempts. |
| **Bottom Toolbar** | Two icon buttons: `⚙️ Settings` and `ℹ️ About`. |
| **About Dialog** | Credits **Zohaib Javed** as Creator & Lead Developer. |

## Current UI & Runtime Snapshot — August 5, 2026

![Current WiFi AC Guardian dashboard](./current-ui.png)

The screenshot is captured from the currently running GUI after the dashboard was restored to its full-width layout.

- The top row shows Status, TX Rate, RX Rate, and Retry State.
- The High-Speed Wi-Fi Active card spans the dashboard width and includes target SSID, live connection details, and the segmented quality meter.
- Connection Overview and Protection Engine sit side-by-side below the status card.
- Protection Engine exposes Reconnect now and Stop protection; Settings and About remain in the bottom toolbar.
- The active profile targets `lab5g` on `Wi-Fi`: check interval 5 seconds, reconnect delay 1 second, max attempts 50, tray enabled, notifications disabled, and Start minimized enabled.
- At capture: the link was GOOD / Protected, connected via 802.11ac (Wi-Fi 5), with 702 Mbps RX, 585 Mbps TX, and 81% signal.

## Current Verification

```powershell
python -m compileall -q wifi_ac_guardian_win
python -m pytest -q
```

Result: **6 tests passed**. The GUI was restarted after verification and is running as `pythonw.exe -m wifi_ac_guardian_win --gui`.

---

## 📁 Codebase Directory Layout

```
WiFi_AC_Guardian_Windows/
├── pyproject.toml                     # Build setup (requires-python >= 3.8)
├── setup.py                           # Package setuptools script
├── README.md                          # Application README
├── HANDOFF.md                         # Handoff file for AI Agents
└── wifi_ac_guardian_win/
    ├── __init__.py
    ├── cli.py                         # CLI entrypoint parser (--gui, --daemon)
    ├── config.py                      # JSON config persistence (~/wifi-ac-guardian/config.json) & autostart shortcut sync
    ├── icons.py                       # Pillow status tray icon generator (Green/Yellow/Red/Blue)
    ├── logger.py                      # Logging subsystem (~/wifi_ac_guardian_win.log)
    ├── single_instance.py             # Single-instance socket server/client (127.0.0.1:39145)
    ├── tray.py                        # System tray applet & COM thread wrapper
    ├── ui.py                          # Responsive Tkinter dashboard & SegmentedSpeedBar
    └── core/
        ├── __init__.py
        ├── models.py                  # Dataclasses: GuardianConfig, GuardianState, LinkInfo, StatusState, PhyMode
        ├── detector_win.py            # netsh wlan show interfaces & BSSID/SSID parser
        ├── reconnector_win.py         # Hardware Wi-Fi adapter radio reset engine
        └── guardian.py                # Main monitoring loop & primary network failback scanner
```

---

## 🧪 Verification & Commands

### Running Unit Tests
```bash
python -m unittest discover tests
```
*Expected Output*: `Ran 6 tests in 0.001s - OK`

### Launching GUI Mode
```bash
python -m wifi_ac_guardian_win --gui
# or via pythonw without cmd window:
pythonw -m wifi_ac_guardian_win --gui
```

### Stopping All App Instances
```powershell
Get-Process python*, wifi-ac-guardian* -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 📝 Information for Incoming AI Agents (Codex, Claude Code, OpenCode)

1. **Do not remove Single Instance Check**: `single_instance.py` enforces socket `127.0.0.1:39145` binding to ensure double-clicking the shortcut never creates duplicate processes or tray icons.
2. **Preserve responsive window behavior**: `ui.py` is resizable, with a minimum size of `760x600` and a compact desktop default width.
3. **Preserve Standby Protection**: The app MUST NOT reset the adapter while connected to secondary networks like `Metalgear`. It enters `StatusState.STANDBY` (Blue 🔵) and scans in the background for `lab5g`.
4. **Log Inspection**: All engine events log to `%USERPROFILE%\wifi_ac_guardian_win.log`.
