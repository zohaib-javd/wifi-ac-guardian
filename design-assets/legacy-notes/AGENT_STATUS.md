# 🤖 AI Agent Handoff & Architecture Specification (`AGENT_STATUS.md`)

> **Notice for AI Coding Agents**: This document is prepared specifically for AI agents (such as **Google Antigravity**, **Claude Code**, **OpenCode**, **Cursor**, **Windsurf**) working on **WiFi AC Guardian (Windows 11 Edition)**. Read this file carefully before making code changes or adding features.

---

## 📌 System Metadata & Active Installation Registry

- **Last Updated Date & Timestamp**: `2026-08-05T14:06:00+05:00`
- **Active Software Source Folder**: `C:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows`
- **Installation Info File**: `C:\Users\Zohaib\Documents\WiFi AC Guardian Installed Location.txt`
- **Python Executable (Console)**: `C:\Python314\python.exe`
- **Python Executable (Windowed GUI)**: `C:\Python314\pythonw.exe`
- **Installed Script Binary**: `C:\Users\Zohaib\AppData\Roaming\Python\Python314\Scripts\wifi-ac-guardian-win.exe`
- **Installed Package Location**: `C:\Users\Zohaib\AppData\Roaming\Python\Python314\site-packages\wifi_ac_guardian_win`
- **Desktop Shortcut**: `C:\Users\Zohaib\Desktop\WiFi AC Guardian.lnk`
- **Startup Shortcut**: `C:\Users\Zohaib\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WiFi AC Guardian.lnk`
- **User Configuration JSON**: `C:\Users\Zohaib\AppData\Roaming\wifi-ac-guardian\config.json`
- **System Log File**: `C:\Users\Zohaib\wifi_ac_guardian_win.log`

## Current UI & Runtime Snapshot — 2026-08-05

![Current WiFi AC Guardian dashboard](./current-ui.png)

- **Running process**: `pythonw.exe -m wifi_ac_guardian_win --gui` (verified after restart).
- **Protected network**: `lab5g` on interface `Wi-Fi`; current live state is **GOOD / Protected**.
- **Live link at capture**: 802.11ac (Wi-Fi 5), 702 Mbps receive rate, 585 Mbps transmit rate, 81% signal.
- **Protection configuration**: checks every 5 seconds, reconnect delay 1 second, 50 automatic retry attempts, protection enabled, tray enabled, notifications disabled, and start minimized enabled.
- **Dashboard layout**: four KPI cards; a full-width High-Speed Wi-Fi status and quality-meter panel; Connection Overview and Protection Engine panels side-by-side; Settings and About controls in the bottom toolbar.
- **Protection controls**: Reconnect now and Stop protection. Settings contains the Start minimized in system tray option.
- **UI assets**: router/status imagery is loaded from `wifi_ac_guardian_win/assets/router_status/`; Fluent UI imagery is loaded from `wifi_ac_guardian_win/assets/fluent/`; `current-ui.png` is the current captured dashboard image.
- **Verification**: `python -m compileall -q wifi_ac_guardian_win` and `python -m pytest -q` completed successfully (`6 passed`).

---

## ✅ VERIFIED HARDWARE RADIO TOGGLE & QUALITY ENGINE

### 1. Hardware Wi-Fi Adapter Reset (`Intel(R) Wi-Fi 6 AX201 160MHz`)
- **Primary Method (WinRT Radio API)**: Uses native `Windows.Devices.Radios.Radio` interop via PowerShell (`SetStateAsync(Off)` ➔ `SetStateAsync(On)`). Operates in user mode without requiring UAC admin elevation (`Allowed`).
- **Disable Sequence**: Toggles Wi-Fi radio OFF ➔ Sleeps `reconnect_delay` (15.0s).
- **Enable Sequence**: Toggles Wi-Fi radio ON ➔ Sleeps 15.0s for driver/radio stabilization.
- **Connect Command**: `netsh wlan connect name="<Target_SSID>" interface="Wi-Fi"`.
- **Stabilization Wait**: Polls up to 15.0s for link state stabilization.

### 2. Connection Quality Threshold (GOOD vs DOWNGRADED)
- Connection is **GOOD** only if:
  1. Radio type is **802.11ac (Wi-Fi 5)**, **802.11ax (Wi-Fi 6)**, or **802.11be (Wi-Fi 7)**.
  2. Transmit AND/OR Receive Bitrate is **strictly GREATER than 300.0 Mbps** (`> 300.0 Mbps`).
- Connection is treated as **DOWNGRADED** if:
  - Radio type is 802.11n (Wi-Fi 4) or lower, **OR**
  - Bitrate is `<= 300.0 Mbps` (e.g. 300 Mbps, 144 Mbps, 54 Mbps).

### 3. Timing & Retry Defaults
- **`check_interval`**: Default **15.0s** (Range: 2.0s to 120.0s).
- **`reconnect_delay`**: Default **15.0s** (Range: 1.0s to 60.0s).
- **`max_attempts`**: Default **0 (Unlimited continuous retries)**. Includes a 60-second cooldown period before resetting attempts if a non-zero limit is set.

---

## 🏗️ Architecture & Module Map

```
wifi_ac_guardian_win/
├── __init__.py          # Package initialization
├── __main__.py          # Package executable entrypoint
├── cli.py               # Command Line Interface parser & main launcher (--target-ssid)
├── config.py            # JSON configuration manager (%APPDATA%\wifi-ac-guardian\config.json)
├── icons.py             # PIL Pillow icon generator for tray applet
├── logger.py            # Rotating file and stream logging system
├── single_instance.py   # Local loopback (127.0.0.1:39145) socket IPC single-instance manager
├── tray.py              # pystray System Tray notification area icon manager
├── ui.py                # Tkinter Control Panel GUI window and dashboard
└── core/
    ├── __init__.py
    ├── detector_win.py  # netsh wlan show interfaces parser & max_bitrate_mbps calculation
    ├── guardian.py      # Background monitoring engine & 60s cooldown logic
    ├── models.py        # LinkInfo quality rules (>300Mbps threshold) & GuardianConfig defaults
    ├── notifier_win.py  # Native Windows balloon toast notification manager
    └── reconnector_win.py # WinRT Radio API & Disable/Enable-NetAdapter hardware reset engine
```

---

## 🛑 MANDATORY AI AGENT DESIGN RULES

When adding features or modifying this codebase, you **MUST** follow these 4 mandatory design rules:

### 1. Process & Console Isolation (`CREATE_NO_WINDOW`)
Every `subprocess.run()` or `subprocess.Popen()` call in Windows MUST pass `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)`.

### 2. Main Thread Dispatching for Tkinter (`self.after(0, ...)`)
Any callback triggered from a background thread that modifies Tkinter widgets MUST be dispatched using `widget.after(0, callback)`.

### 3. Win32 GDI Handle Caching in `pystray`
In `tray.py`, do NOT reassign `self.icon_instance.icon = new_image` every polling interval. Only update the icon when `state != self._last_icon_state`.

### 4. Single-Instance Enforcement (`SingleInstanceChecker`)
All GUI and daemon launchers MUST execute `SingleInstanceChecker.try_claim_single_instance(on_show_requested=...)`.

---

## 🧪 Testing Workflows

### Run Unit Tests
```cmd
python -m unittest discover tests
```
*Current test suite contains 6 tests (`Ran 6 tests in 0.001s - OK`).*
