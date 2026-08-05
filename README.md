# 🛡️ WiFi AC Guardian (Windows 11 Edition)

**WiFi AC Guardian** is a background utility for Windows 11 designed to keep your Wi-Fi interface connected at **Wi-Fi 5 (802.11ac)**, **Wi-Fi 6 (802.11ax)**, or **Wi-Fi 7 (802.11be)** with a link transmit/receive bitrate **strictly greater than 300.0 Mbps**.

If Windows 11 automatically downgrades your wireless connection to Wi-Fi 4 (802.11n), if the bitrate drops to 300 Mbps or lower, or if the connection switches to the wrong SSID, **WiFi AC Guardian** executes a **Hardware Wi-Fi Adapter Device Reset** (Wi-Fi-only Airplane mode toggle) to restore peak Wi-Fi 5+ performance.

---

## ✨ Hardware Device Toggle & Quality Rules

1. **Hardware Wi-Fi Device Radio Toggle (Wi-Fi Only Airplane Mode)**:
   - When a connection quality drop is detected, the application toggles the physical Wi-Fi network adapter OFF and ON.
   - **Disable Command**: `Disable-NetAdapter -Name "Wi-Fi" -Confirm:$false` *(fallback: `netsh interface set interface name="Wi-Fi" admin=disabled`)*.
   - **Wait 15.0s** while the adapter radio powers down.
   - **Enable Command**: `Enable-NetAdapter -Name "Wi-Fi" -Confirm:$false` *(fallback: `netsh interface set interface name="Wi-Fi" admin=enabled`)*.
   - **Wait 15.0s** while the adapter driver and radio stabilize.
   - **Reconnect Command**: `netsh wlan connect name="<SSID>" interface="Wi-Fi"`.
   - **Wait up to 15.0s** for link state stabilization.

2. **Strict Quality Threshold**:
   - Connection is **GOOD** only if:
     1. Radio type is 802.11ac (Wi-Fi 5), 802.11ax (Wi-Fi 6), or 802.11be (Wi-Fi 7).
     2. Transmit/Receive Bitrate is **strictly GREATER than 300.0 Mbps** (`> 300.0 Mbps`).
   - If Radio type is 802.11n (Wi-Fi 4) OR bitrate is `<= 300.0 Mbps`, the connection is treated as **DOWNGRADED** and triggers a Wi-Fi Adapter Device Reset.

3. **Timing & Attempt Defaults**:
   - **Check Interval** (`check_interval`): Default **15.0 seconds**.
   - **Reconnect Delay** (`reconnect_delay`): Default **15.0 seconds**.
   - **Max Attempts** (`max_attempts`): Default **0 (Unlimited continuous retries)**. Includes a 60-second cooldown before resetting attempts if a non-zero limit is set.

---

## 🚀 Quick Start / Installation

### Option 1: Automated Batch Installer (Recommended)
Double-click **`install.bat`** in this folder (`C:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows`). The installer will:
1. Install the Python package and dependencies via `pip`.
2. Generate a **Desktop Shortcut** (`WiFi AC Guardian`).
3. Generate a **Windows Startup Shortcut** (autostart protection on login).
4. Open the Control Panel GUI immediately.

### Option 2: Manual Pip Installation
Open PowerShell or Command Prompt in this folder and run:
```cmd
python -m pip install .
```

To launch the GUI manually:
```cmd
pythonw -m wifi_ac_guardian_win --gui
```

---

## 🖥️ Command Line Interface (CLI) Options

| Option | Flag | Description |
| :--- | :--- | :--- |
| **Control Panel GUI** | `-g`, `--gui` | Launch Tkinter Control Panel GUI window. |
| **Target SSID Lock** | `--target-ssid` | Lock onto specific SSID (e.g. `--target-ssid lab5g`). |
| **Status Report** | `-s`, `--status` | Output text-based status report to terminal and exit. |
| **Daemon Protection** | `-d`, `--daemon` | Run background monitoring service with System Tray applet. |
| **Manual Reconnect** | `-r`, `--reconnect` | Force immediate Hardware Wi-Fi Adapter Device Reset. |
| **Interface Selection** | `-i`, `--interface` | Specify wireless adapter (default: `Wi-Fi`). |
| **Poll Interval** | `-t`, `--interval` | Set check interval in seconds (default: `15.0`). |
| **Max Attempts** | `--max-attempts` | Set max retries (default: `0` for Unlimited). |

---

## ⚙️ Configuration & Settings

Settings are stored in JSON at:
`%APPDATA%\wifi-ac-guardian\config.json`

Example configuration:
```json
{
    "interface": "Wi-Fi",
    "target_ssid": "lab5g",
    "check_interval": 15.0,
    "reconnect_delay": 15.0,
    "max_attempts": 0,
    "log_file_path": "C:\\Users\\Zohaib\\wifi_ac_guardian_win.log",
    "enable_notifications": false,
    "enable_tray": true,
    "start_minimized": false,
    "is_paused": false
}
```

---

## 🗑️ Uninstallation

To uninstall WiFi AC Guardian, double-click **`uninstall.bat`** or run:
```cmd
python -m pip uninstall -y wifi-ac-guardian-win
```

---

## 📄 License
Antigravity Engineering - All Rights Reserved.
