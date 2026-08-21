# WiFi AC Guardian - AI Handoff Documentation

**Date & Timestamp:** 2026-08-13 15:08:00
**Primary Project Location:** `C:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows`
**Artifact Mirror Location:** `C:\Users\Zohaib\Desktop\Upwork\Portfolio Projects\WiFi AC Guardian App\Final Apps\Windows`

---

## 1. Project Overview & Architecture
WiFi AC Guardian is a hybrid application designed to monitor wireless networks and proactively prevent the router from downgrading the bit-rate. The project is split into two primary components:

### Backend: Python Guardian Daemon (`/wifi_ac_guardian_win`)
- **Core Function**: Monitors the Wi-Fi interface link quality and triggers reconnection resets if the connection quality falls below the specified threshold.
- **IPC Server**: Runs a local HTTP JSON RPC server on `http://127.0.0.1:39146`.
- **Endpoints**:
  - `GET /`: Returns live JSON telemetry (e.g., `linkSpeed`, `connected`, `ssid`, `reconnectAttempts`, `protectionRunning`).
  - `POST /` with payload `{"action": "toggle_protection"}`: Starts/Stops the protection engine.
  - `POST /` with payload `{"action": "reconnect_now"}`: Forces an immediate Wi-Fi reconnect.

### Frontend: Next.js + Electron UI (`/wifi-guardian-ui`)
- **Frameworks**: React, Next.js (Static Export), Tailwind CSS, Framer Motion, Electron.
- **Role**: A purely cosmetic, visual interface that pulls telemetry from the Python daemon. It has no native networking capabilities of its own.
- **Constraints**: 
  - The UI is designed for a strict mobile-viewport footprint (`430x720`).
  - Window maximization and resizing are strictly disabled in `main.js` to prevent the UI from breaking.
- **Build Process**: Run `npm run dist` inside `/wifi-guardian-ui` to generate the portable executable. Output goes to `/wifi-guardian-ui/build_app`.

---

## 2. Workspace Status
- The workspace has been thoroughly cleaned. All old wrapper `.exe` files, prototype design assets (like the `claude-code` dir), and legacy tracking documents have been safely moved to `C:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows\Archive`.
- **Only touch files in the root, `wifi_ac_guardian_win`, or `wifi-guardian-ui`.** Do not pull files back from the `Archive` folder.

## 3. Onboarding for Next AI Agents (Codex, Claude Code, OpenCode, Antigravity)
- **Starting point**: If you are modifying the UI, go to `wifi-guardian-ui/src/app/page.tsx` and ensure you run `npm run dev` to test changes before packaging.
- **Backend changes**: If modifying the backend logic, go to `wifi_ac_guardian_win` and restart the daemon script.
- **Deployments**: Any time the Electron app is re-built via `npm run dist`, you MUST copy the resulting executable (`WiFi AC Guardian 2.0.5.exe`) from `wifi-guardian-ui/build_app` into the Artifact Mirror Location at `C:\Users\Zohaib\Desktop\Upwork\Portfolio Projects\WiFi AC Guardian App\Final Apps\Windows`.
