# WiFi AC Guardian

<p align="center">
  <strong>Automated Wi-Fi 5 / 802.11ac Performance & Link Recovery Utility</strong><br>
  Maintained by <a href="https://www.zeejaylab.store/wifi-guardian">Zeejaylab</a>
</p>

---

## 🚀 Overview

**WiFi AC Guardian** is an automated background daemon for **Windows 11/10** and **Ubuntu Linux** that continuously monitors negotiated Wi-Fi speeds and link status. When your router station table silently downgrades your high-speed 5 GHz connection to legacy 802.11n (40 MHz), WiFi AC Guardian instantly triggers an active 5-step cache purge to renegotiate and lock full 802.11ac (80 MHz, 866.7+ Mbps) throughput.

---

## 📦 Downloads & Releases

Pre-compiled binary releases are available on the [GitHub Releases](https://github.com/zohaib-javd/wifi-ac-guardian/releases) page and on our official website:

🔗 **Official Website & Documentation:** [https://www.zeejaylab.store/wifi-guardian](https://www.zeejaylab.store/wifi-guardian)

### Available Distribution Packages:

| Platform | Type | Asset File |
| :--- | :--- | :--- |
| **Windows 10 / 11 (x64)** | **Portable** | [`WiFi-AC-Guardian-Windows-v1.5.7-Portable.exe`](https://github.com/zohaib-javd/wifi-ac-guardian/releases/download/v1.5.7/WiFi-AC-Guardian-Windows-v1.5.7-Portable.exe) |
| **Windows 10 / 11 (x64)** | **Installer** | [`WiFi-AC-Guardian-Windows-v1.5.7-Installer.exe`](https://github.com/zohaib-javd/wifi-ac-guardian/releases/download/v1.5.7/WiFi-AC-Guardian-Windows-v1.5.7-Installer.exe) |
| **Ubuntu Linux (AMD64)** | **Package** | [`WiFi-AC-Guardian-Ubuntu-v0.1-Beta-9.zip`](https://github.com/zohaib-javd/wifi-ac-guardian/releases/download/v1.5.7/WiFi-AC-Guardian-Ubuntu-v0.1-Beta-9.zip) |

---

## 🛡️ Key Features

- **Continuous Link Monitoring:** Real-time polling of PHY mode, signal strength, channel width, and link bitrate.
- **5-Step Cache Purging Engine:** Automatically issues IEEE deauthentication, DNS/ARP cache flush, airplane-mode radio toggling, and directed 5 GHz probe scanning.
- **Background Watchdog:** Runs silently in the system tray with minimal CPU/RAM overhead.
- **Smart Reconnection Observation:** Configurable check frequency and recovery limits to prevent connection loops.

---

## 📄 License & Distribution

WiFi AC Guardian is proprietary commercial software distributed by **Zeejaylab**.  
For inquiries and documentation, visit [zeejaylab.store](https://www.zeejaylab.store).
